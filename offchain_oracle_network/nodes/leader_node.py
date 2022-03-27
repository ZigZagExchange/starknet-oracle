from datetime import datetime
import zmq
import sys
import json
import threading
from time import sleep, time
from pickle import dumps, loads
import signal

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify

from classes.report_class import Report
import helpers.helpers as h
from leader import LeaderState

# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================

# TODO: Change the constants
T_ROUND = 19
T_GRACE = 3


class LeaderNode(LeaderState):
    def __init__(self, index, epoch, leader, publisher, num_nodes, max_round):
        super().__init__(index, epoch, leader, num_nodes, max_round)
        self.context = zmq.Context()
        # # * This is the socket from which the follower will brodcast messages to other oracles
        self.publisher = publisher
        # * These sockets are used to receive messages from other oracles
        self.subscriptions = h.subscribe_to_other_nodes_leader(self.context)
        # * Poller is used to reduce the cpu strain
        self.poller = zmq.Poller()
        for sub in self.subscriptions:
            self.poller.register(sub, zmq.POLLIN)
        # * Timers
        self.round_timer = h.ResettingTimer(
            T_ROUND, self.emit_new_round_event, self.publisher)
        self.grace_timer = h.ResettingTimer(
            T_GRACE, self.assemble_report, self.publisher)
        self.stop_event = threading.Event()

    def run_(self):
        sleep(1)
        # self.publisher.send_multipart([b"START-EPOCH"])
        print("Leader Running")
        while True:

            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("Exception: {}".format(e))
                continue

            for sub in self.subscriptions:

                if self.stop_event.is_set():
                    print(f"Stopping leader_node {self.index}")
                    return

                if sub in socks and self.leader == self.index:
                    msg = sub.recv_multipart()
                    # ? ==========================================================================
                    # SECTION Start a new round
                    if msg[0] == b'START-EPOCH' or msg[0] == b'NEW-ROUND':
                        print(datetime.now(), ":", "START-ROUND")
                        self.start_round()
                        self.round_timer.start()
                        self.publisher.send_multipart(
                            [b"OBSERVE-REQ", dumps({"round_n": self.round_num})])
                        print("NEW ROUND STARTED {} from {}".format(
                            self.round_num, sub.get(zmq.IDENTITY).decode()))
                    # _ !SECTION
                    # ? ==========================================================================
                    # SECTION Recieve an observation
                    if msg[0] == b'OBSERVE':
                        round_n, observation, signature = loads(msg[1])["round_n"], loads(msg[1])[
                            "observation"], loads(msg[1])["signature"]
                        node_idx = int(sub.get(zmq.IDENTITY).decode())

                        if round_n != self.round_num:
                            print("ERROR: Round number mismatch in OBSERVE\n")
                            print("round_n", round_n)
                            print("self.round_num", self.round_num)
                            continue
                        if not (self.phase == "OBSERVE" or self.phase == "GRACE"):
                            print("ERROR: Phase should be OBSERVE or GRACE")
                            continue

                        if self.observations[node_idx]:
                            print(
                                "ERROR: Observation already received from this node for this round")
                            print("\n ", (observation, signature, node_idx))
                            continue

                        msg_hash = compute_hash_on_elements(
                            [self.epoch, round_n, observation])
                        if verify(msg_hash, signature[0], signature[1], public_keys[node_idx]):
                            self.observations[node_idx] = (
                                (observation, signature, node_idx))

                            if len([1 for x in self.observations if x]) == 2*self.F + 1:
                                if self.phase != 'OBSERVE':
                                    print(
                                        'ERROR: Phase must be OBSERVE')
                                    continue

                                print("GRACE TIMER STARTED")
                                self.phase = "GRACE"
                                self.grace_timer.start()
                        else:
                            print("ERROR: Signature verification failed")
                    # _ !SECTION
                    # ? ===========================================================================
                    # SECTION Recieve an observation
                    if msg[0] == b'REPORT':
                        round_n, report, signature = loads(msg[1])["round_n"], loads(msg[1])[
                            "report"], loads(msg[1])["signature"]

                        if self.current_report.msg_hash() != report.msg_hash():
                            print("ERROR: Report mismatch")
                            continue

                        node_idx = int(sub.get(zmq.IDENTITY).decode())
                        public_key = public_keys[node_idx]

                        if self.current_report.verify_report_signature(public_key, signature):
                            self.reports.append(
                                (report, signature, node_idx))

                            if len(self.reports) > self.F:
                                self.finalize_report(
                                    report, self.publisher)
                        else:
                            print("ERROR: Signature verification failed")

                    # _ !SECTION
                    # ? ===========================================================================

    def run(self):
        self.stop_event.clear()
        thread = threading.Thread(target=self.run_)
        thread.start()

    def start(self, new_epoch, new_leader):
        self.reset_state(new_epoch, new_leader)
        self.run()

    def stop(self):
        self.round_timer.cancel()
        self.stop_event.set()
        self.context.destroy()


# if __name__ == "__main__":
#     leader_node = LeaderNode(NODE_IDX, temp_epoch_num)
#     leader_node.run()
