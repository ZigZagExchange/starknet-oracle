import random
import threading
import time
import sys
from traceback import print_last
import zmq
import os
import json
import ast
import asyncio
from pathlib import Path
from queue import PriorityQueue
from dataclasses import dataclass
from decouple import config

from helpers import helpers as h
from classes.report_class import Report
from classes.Transmitter import Transmitter


from starkware.crypto.signature.signature import private_to_stark_key
from starknet_py.net.client import Client
from starknet_py.net.account.account_client import AccountClient, KeyPair
from starknet_py.contract import Contract


NUM_NODES = 4
T_TRANSMIT = 100
T_STAGE = 60
T_BETWEEN_COMMITS = 300
alpha = -1  # 0.0025


# ? ----------------------------------------------------------------------------
file_path = os.path.join(
    os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + os.pardir),
    "tests/dummy_data/dummy_keys.json")

f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ----------------------------------------------------------------------------
# ? ----------------------------------------------------------------------------
file_path = os.path.join(
    os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + os.pardir),
    "offchain_oracle_network/nodes/config.json")
f = open(file_path, 'r')
config = json.load(f)
f.close()

config_digest = config["config"]["config_digest"]
signers = config["config"]["signers"]
transmitters = config["config"]["transmitters"]
threshold = config["config"]["threshold"]
config_version = config["config"]["config_version"]
config_hash = config["config"]["config_hash"]

ofc_aggregator_address = config["config"]["contract_address"]
# ? ----------------------------------------------------------------------------


# TRANSMITTER_PRIV_KEY = int(config('TRANSMITTER_PRIV_KEY'))

# ...............................................................................
transmitter_abi = Path("abis/Transmitter.json").read_text()
transmitter_abi = ast.literal_eval(transmitter_abi)

ofc_aggregator_abi = Path("abis/OffchainAggregator.json").read_text()
ofc_aggregator_abi = ast.literal_eval(ofc_aggregator_abi)

local_network_client = Client("testnet")
# ...............................................................................


class Transmission:
    def __init__(self, index):
        self.index = index
        # latest report accepted for transmission (e, r, R, sigs, signers)
        self.latest_report = (0, 0, None, [], [])
        # latest report commited to C (on-chain) as known to this node (e, r, answer)
        self.latest_comitted_report = (0, 0, 0, 0)
        self.transmission_timer = h.ResettingTimer(
            T_TRANSMIT, self.transmit_on_chain)
        self.pending_report = None
        # ==============
        self.transmitter = Transmitter(private_keys[self.index])
        self.transmitter_acc = Contract(address=transmitters[self.index], abi=transmitter_abi,
                                        client=local_network_client)
        self.ofc_aggregator = Contract(address=ofc_aggregator_address, abi=ofc_aggregator_abi,
                                       client=local_network_client)

        self.start_time = time.time()

    def transmit(self, report_bundle):
        epoch, round_n, report, _, _ = report_bundle
        report: Report
        e_C, r_C, answer_C, t_C = self.latest_comitted_report
        e_L, r_L, rep_L, _, _ = self.latest_report

        if int(str(epoch) + str(round_n)) <= int(str(e_C) + str(r_C)):
            print("ERROR: Report is outdated compared to the latest commited report")
            return

        if self.latest_report and int(str(epoch) + str(round_n)) <= int(str(e_L) + str(r_L)):
            print("ERROR: Report is outdated compared to the latest report")
            return

        if not rep_L or int(str(e_L) + str(r_L)) <= int(str(e_C) + str(r_C)) or time.time() - t_C >= T_BETWEEN_COMMITS \
                or (abs(h.median(report.observations) - h.median(rep_L.observations)))/abs(h.median(rep_L.observations)) > alpha:
            self.latest_report = report_bundle

            delay = self.transmit_delay(
                self.index, epoch, round_n, report.observers)

            print("Delay: ", delay)
            if delay > 2 * T_STAGE:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.get_latest_commited_transmission_details())
                loop.close()
                return

            self.pending_report = report_bundle

            # reset transmission timer with new delay time
            self.transmission_timer.cancel()
            self.transmission_timer.interval = delay
            self.transmission_timer.start()

            if delay > 0:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.get_latest_commited_transmission_details())
                loop.close()

    def transmit_on_chain(self):
        if not self.pending_report:
            return

        epoch, round_n, report, _, _ = self.pending_report
        report: Report
        e_C, r_C, answer_C, _ = self.latest_comitted_report

        diff = (abs(h.median(report.observations) - answer_C)) / \
            abs(answer_C) if answer_C else 1

        if int(str(epoch) + str(round_n)) > int(str(e_C) + str(r_C)) and diff > alpha:
            print("Sending a transaction to the blockchain for round:", round_n)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.send_on_chain(self.pending_report))
            loop.close()

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

        # print(calldata)
        invocation = await self.transmitter.send_transaction(
            account=self.transmitter_acc,
            to=self.ofc_aggregator.address,
            selector_name='transmit',
            calldata=calldata)

        print("Invocation_sent for round {}".format(round_n))

    # * HELPERS * ==============================================================

    def transmit_delay(self, i, e, r, raw_observers):
        raw_observers = raw_observers[2:]
        observers = [int(raw_observers[i:i+2], 16)
                     for i in range(0, len(raw_observers), 2)]

       # shuffle observers pseudo randomly based on e and r
        random.seed(int(str(e) + str(r)))
        random.shuffle(observers)
        transmitter_index = observers.index(self.index)

        return transmitter_index * T_STAGE

    async def get_latest_commited_transmission_details(self):
        _, epoch, round_n, answer, _ = await self.ofc_aggregator.functions["latestTransmissionDetails"].call()
        self.latest_comitted_report = (epoch, round_n, answer, time.time())


#

#

#

#

#


# NODE_IDX = int(sys.argv[1])
# if __name__ == "__main__":

#     calldata = [
#         238383044233932263057806377059118148824068886889218,
#         16974336, [268709830381, 268776485065, 268782096543, 268785113740],
#         [288917873877700639730427941230238049094321494035204488587102278194676853269,
#          115562032174727461168681328237989349222471706350399469296643855259217005324],
#         [1503863774529188982832049491218833769354610905918870872218095791046835609876,
#             1397869743061753512568694830842162347614567646486365533324929920482057989571],
#         512]

#     trasnmission = Transmission(index=0)

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     loop.run_until_complete(trasnmission.test_transmit(calldata))
#     loop.close()
