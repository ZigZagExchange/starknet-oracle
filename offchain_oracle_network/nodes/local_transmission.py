
import json
import time
import sys
import zmq
import os
import asyncio
import pytest
from decouple import config
from queue import PriorityQueue

from starkware.starknet.testing.starknet import Starknet
from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import private_to_stark_key

from helpers import helpers as h
from classes.report_class import Report
from classes.utils import Transmitter


# ? ----------------------------------------------------------------------------
file_path = "tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ----------------------------------------------------------------------------
# ? ----------------------------------------------------------------------------
file_path = "offchain_oracle_network/nodes/config.json"
f = open(file_path, 'r')
config = json.load(f)
f.close()

config_digest = config["config"]["config_digest"]
signers = config["config"]["signers"]
transmitters = config["config"]["transmitters"]
threshold = config["config"]["threshold"]
config_version = config["config"]["config_version"]
config_hash = config["config"]["config_hash"]
# ? ----------------------------------------------------------------------------


NUM_NODES = 31
T_TRANSMIT = 100
T_STAGE = 10
alpha = 0.0005

NODE_IDX = int(sys.argv[1])


transmitter_path = "contracts/Accounts/Transmitter.cairo"
ofc_agg_path = "contracts/OffchainAggregator/OffchainAggregator.cairo"
# TRANSMITTER_PRIV_KEY = int(config('TRANSMITTER_PRIV_KEY'))
# TRANSMITTER_STARK_KEY = private_to_stark_key(TRANSMITTER_PRIV_KEY)


transmitter = Transmitter(private_keys[NODE_IDX])
t_pub_key = private_to_stark_key(private_keys[NODE_IDX])


class Transmission:
    def __init__(self, index):
        self.index = index
        # priority queue of time-report pairs (t, O), keyed on ascending time values
        self.reports_queue = PriorityQueue()
        # latest report accepted for transmission (e, r, R, sigs, signers)
        self.latest_report = (0, 0, 0, [], [])
        # latest report commited to C (on-chain) as known to this node (e, r, R, sigs, signers)
        # TODO: Replace this with a function
        self.latest_comitted_report = (0, 0, 0, [], [])
        self.transmission_timer = h.ResettingTimer(
            T_TRANSMIT, self.transmit_callback)
        # Local
        self.starknet = None
        self.transmitter_acc = None
        self.ofc_agg_contract = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.initialize())
        loop.close()

    def transmit_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.transmit_on_chain())
        loop.close()

    def transmit(self, report_bundle):
        epoch, round_n, report, _, _ = report_bundle
        # Todo: get_latest_commited_transmission_details()
        e_C, r_C, rep_C, _, _ = self.latest_comitted_report
        e_L, r_L, rep_L, _, _ = self.latest_report

        if int(str(epoch) + str(round_n)) <= int(str(e_C) + str(r_C)):
            print("ERROR: Report is outdated compared to the latest commited report")
            return

        if self.latest_report and int(str(epoch) + str(round_n)) <= int(str(e_L) + str(r_L)):
            print("ERROR: Report is outdated compared to the latest report")
            return

        if not self.latest_report or int(str(e_L) + str(r_L)) <= int(str(e_C) + str(r_C)) or (abs(median(report.observations) - median(rep_L.observations)))/abs(median(rep_L.observations)) > alpha:
            self.latest_report = report_bundle

            delay = 1  # self.transmit_delay(self.index, epoch, round_n)
            print("Transmission delay:", delay)

            # Insert negative time so that the queue is sorted ascendingly
            self.reports_queue.put((-(time.time() + delay), report_bundle))

            t, _ = self.reports_queue.queue[0]

            # reset transmission timer with new delay time
            self.transmission_timer.cancel()
            self.transmission_timer.interval = abs(t) - time.time()
            self.transmission_timer.start()

    async def transmit_on_chain(self):

        if self.reports_queue.empty():
            return

        # TODO: e_C, r_C = self.get_latest_commited_transmission_details()

        _, report_bundle = self.reports_queue.get()
        epoch, round_n, _, _, _ = report_bundle
        e_C, r_C, rep_C, _, _ = self.latest_comitted_report

        if int(str(epoch) + str(round_n)) > int(str(e_C) + str(r_C)):
            print("Sending a transaction to the blockchain")
            await self.send_on_chain(report_bundle)

        if self.reports_queue.qsize() > 0:
            t, _ = self.reports_queue.queue[0]
            self.transmission_timer.cancel()
            self.transmission_timer.interval = abs(t) - time.time()
            self.transmission_timer.start()

    async def send_on_chain(self, report_bundle):
        epoch, round_n, report, signatures, raw_signers = report_bundle
        report: Report

        r_sigs, s_sigs = zip(*signatures)
        r_sigs = list(r_sigs)
        s_sigs = list(s_sigs)

        calldata = [int(report.report_context, 16),
                    int(report.observers, 16),
                    report.observations,
                    r_sigs,
                    s_sigs,
                    int(raw_signers, 16)]

        res = await transmitter.send_transaction(
            account=self.transmitter_acc,
            to=self.ofc_agg_contract.contract_address,
            selector_name='transmit',
            calldata=calldata)

        print("\n==============================================================")
        print("Result of sending a report onchain: {}".format(res.result))
        print("\n==============================================================")

    async def initialize(self):
        print("Initializing...")
        self.starknet = await Starknet.empty()

        self.transmitter_acc = await self.starknet.deploy(
            transmitter_path,
            constructor_calldata=[t_pub_key]
        )

        self.ofc_agg_contract = await self.starknet.deploy(
            ofc_agg_path,
            constructor_calldata=[10**8, 10**11, 8,
                                  12345, int("126fa3eb40c24", 16)]
        )

        res = await self.ofc_agg_contract.set_config(
            list(reversed(signers[:6])),
            list(reversed(transmitters[:6])),
            threshold, config_version, config_hash).invoke()

        print("Initialization complete config_digest = {}".format(res.result.res))

    # * HELPERS * ==============================================================

    def transmit_delay(self, i, e, r):
        k = self.permutation(i, e, r)
        return k * T_STAGE

    def get_latest_commited_transmission_details(self):
        # config_digest, epoch, round, answer, timestamp = contract.latestTransmissionDetails.call()
        # return epoch, round
        pass

    # pseudo-random permutation of the nodes (for transmission delays)
    # TODO: make this a more secure permutation that equaly selects all nodes
    def permutation(self, i, e, r):
        return (e * r + i) % NUM_NODES


def median(lst):
    return sorted(lst)[len(lst) // 2]


# if __name__ == "__main__":
#     transmission = Transmission(NODE_IDX)

#     dummy_report = Report("482e7be5078322e168521cdf42067fef21", "0x00010203", [
#                           268700000000, 268700000000, 268700000000, 268700000000], [])

#     report_bundle = (2, 1, dummy_report,
#                      [(1577394959547856115555912366335945370481861442222975470039981306297641228978, 2387087374092900831587322963385741783217692324797487567405065999428037994098), (3002502018566415446187223691464214516193751947968564487065270189948034136435, 2623170164895083334330594166399208763262056873064808887851861065181475386812)], '0x0100')

#     transmission.transmit(report_bundle)
