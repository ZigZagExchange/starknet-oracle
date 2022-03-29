import zmq
import sys
import json
import os
from time import sleep
from pickle import dumps, loads
import threading

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify, private_to_stark_key


import helpers.helpers as h
from transmission import Transmission

from classes.report_class import Report
from follower import FollowerState


# ? ===========================================================================
file_path = os.path.join(
    os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + os.pardir),
    "tests/dummy_data/dummy_keys.json")
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================


class FollowerNode(FollowerState):

    '''
    This node is run consistently, in contrast to the LeaderNode,
    and only resets its state, when it receives a new epoch.
    It is listening for requests from the leader and sending signed observations.
    Nodes that fall offline can connect back to the network,
    but will likely only sync back on the next epoch.

    @arguments:
        - index: the index of the current node (to identify participants in the network)
        - epoch: the epoch number
        - leader_id: the current leader's index
        - publisher: the publisher socket (see below)
        - num_nodes: the number of nodes in the network
        - max_round: the maximum number of rounds leader is allowed to run before choosing a new one
    '''

    def __init__(self, index, epoch, leader_id, priv_key, publisher, num_nodes, max_round):
        super().__init__(index, epoch, leader_id, priv_key, num_nodes, max_round)
        self.context = zmq.Context()
        # * This is the socket from which the follower will brodcast messages to other oracles
        self.publisher = publisher
        # * These sockets are used to receive messages from other oracles
        self.subscriptions = h.subscribe_to_other_nodes_follower(
            self.context, leader_id)
        # * Poller is used to reduce the cpu strain
        self.poller = zmq.Poller()
        self.poller.register(self.publisher, zmq.POLLIN)
        for sub in self.subscriptions:
            self.poller.register(sub, zmq.POLLIN)
        self.transmission = Transmission(self.index)

    def run_(self):

        while True:

            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
                continue

            for sub in self.subscriptions:

                if sub in socks:
                    try:
                        msg = sub.recv_multipart()
                        # ? ===============================================================
                        # SECTION Send Signed OBSERVATION to Leader
                        if msg[0] == b'OBSERVE-REQ':
                            if int(sub.get(zmq.IDENTITY).decode()) != self.leader_id:
                                print("Message sender should be the leader\n")
                                continue

                            round_n = loads(msg[1])["round_n"]
                            self.round_num = round_n
                            if round_n > self.max_round:
                                self.publisher.send_multipart(
                                    [b'CHANGE-LEADER'])
                                continue

                            self.sentecho = None
                            self.sentreport = False
                            self.completedround = False
                            self.receivedecho = [False] * self.num_nodes

                            observation = self.get_price()
                            msg_hash = compute_hash_on_elements(
                                [self.epoch, round_n, observation])
                            signature = sign(msg_hash, self.private_key)

                            if self.index % 2 == 0:
                                sleep(0.1 * self.index)
                            sleep(1 + 0.02 * self.index)
                            self.publisher.send_multipart(
                                [b'OBSERVE', dumps({"round_n": round_n, "observation": observation, "signature": signature})])

                        # _ !SECTION
                        # ? ===============================================================
                        # SECTION Send Signed REPORT to Leader
                        if msg[0] == b'REPORT-REQ':
                            if int(sub.get(zmq.IDENTITY).decode()) != self.leader_id:
                                print("Message sender should be the leader")
                                continue

                            round_n, report = loads(
                                msg[1])["round_n"], loads(msg[1])["report"]

                            if round_n != self.round_num:
                                print("Round number mismatch in report REQ")
                                continue
                            if self.sentreport:
                                print("Report already sent")
                                continue
                            if self.completedround:
                                print("Round already completed")
                                continue

                            if not self.verify_report_sorted(report):
                                print('ERROR: Report is not sorted')
                                continue

                            for i in range(len(report.observations)):
                                msg_hash = compute_hash_on_elements(
                                    [self.epoch, round_n, observation])
                                node_idx = int(
                                    report.observers[2+2*i:4+2*i], 16)

                                r_sig, s_sig = report.signatures[i]
                                if not verify(msg_hash, r_sig, s_sig, public_keys[node_idx]):
                                    # print(
                                    #     'ERROR: Signature verification FAILED in REPORT-REQ')
                                    continue

                            signature = report.sign_report(self.private_key)

                            sleep(1)
                            self.sentreport = True
                            self.publisher.send_multipart(
                                [b'REPORT', dumps({"round_n": round_n, "report": report, "signature": signature})])

                        # _ !SECTION
                        # ? ===============================================================
                        # _ SECTION Receive Final report and send echo to other nodes
                        if msg[0] == b'FINAL':
                            if int(sub.get(zmq.IDENTITY).decode()) != self.leader_id:
                                print("Message sender should be the leader")
                                continue

                            # Where report bundle is (epoch, round_n, report, signatures, signers)
                            round_n, report_bundle = loads(
                                msg[1])["round_n"], loads(msg[1])["report_bundle"]
                            e, r, report, signatures, signers = report_bundle

                            if round_n != self.round_num or r != self.round_num:
                                print("Round number mismatch in FINAL")
                                continue
                            if self.sentecho:
                                print("Echo already sent")
                                continue

                            if self.verify_attested_report(report_bundle):
                                self.sentecho = report_bundle

                                self.publisher.send_multipart(
                                    [b'FINAL-ECHO', dumps({"round_n": round_n, "report_bundle": report_bundle})])

                        # _ !SECTION
                        # ? ===============================================================
                        # ? ===============================================================
                        # _ SECTION Receive Final echo
                        if msg[0] == b'FINAL-ECHO':
                            # Where report bundle is (epoch, round_n, report, signatures, signers)
                            round_n, report_bundle = loads(
                                msg[1])["round_n"], loads(msg[1])["report_bundle"]
                            e, r, report, signatures, signers = report_bundle

                            node_idx = int(sub.get(zmq.IDENTITY).decode())

                            if round_n != self.round_num or r != self.round_num:
                                print("Round number mismatch in FINAL-ECHO")
                                continue
                            if self.receivedecho[node_idx]:
                                print(
                                    "ERROR: Already received an echo from this node")
                                continue
                            if self.completedround:
                                # print('ERROR: Round has already been completed')
                                continue

                            if self.verify_attested_report(report_bundle):
                                self.receivedecho[node_idx] = True
                                if not self.sentecho:
                                    self.sentecho = report_bundle
                                    self.publisher.send_multipart(
                                        [b'FINAL-ECHO', dumps({"round_n": round_n, "report_bundle": report_bundle})])

                                if self.count_received_echoes() > self.F:
                                    print(
                                        f"\nNode {self.index} invoking Transmission for round {self.round_num}  \n")
                                    self.transmission.transmit(report_bundle)
                                    self.complete_round(self.publisher)
                            else:
                                print("Report attestation failed")
                        # _ !SECTION
                        # ? ===============================================================
                    except zmq.error.ZMQError as e:
                        print(e)
                        continue
                    except Exception as e:
                        print(e)
                        continue

    def reset(self, new_epoch, new_leader):
        '''
        This function resets the node to a new epoch and leader.
        '''
        self.reset_state(new_epoch, new_leader)
        print("leader: ", self.leader_id)

    def run(self):
        '''
        This function runs the node as a thread, so that it can run parallel with the LeaderNode
        '''
        thread = threading.Thread(target=self.run_)
        thread.start()
