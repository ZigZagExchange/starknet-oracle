import zmq
import sys
import json
import threading
from time import sleep
from pickle import dumps, loads

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
F = 0
NUM_NODES = 31
R_MAX = 20
T_ROUND = 10
T_GRACE = 3


NODE_IDX = int(sys.argv[1])

PORT_NUM = 5560 + NODE_IDX

temp_epoch_num = 12345


class LeaderNode(LeaderState):
    def __init__(self, index, epoch, ):
        super().__init__(index, epoch)
        self.context = zmq.Context()
        # * This is the socket from which the follower will brodcast messages to other oracles
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.sndhwm = 1100000
        self.publisher.bind("tcp://*:{}".format(PORT_NUM))
        # * These sockets are used to receive messages from other oracles
        self.subscriptions = h.subscribe_to_other_nodes_leader(self.context)
        # * Poller is used to reduce the cpu strain
        self.poller = zmq.Poller()
        self.poller.register(self.publisher, zmq.POLLIN)
        for sub in self.subscriptions:
            self.poller.register(sub, zmq.POLLIN)
        # * Timers
        self.round_timer = h.ResettingTimer(
            T_ROUND, self.emit_new_round_event, self.publisher)
        self.grace_timer = h.ResettingTimer(
            T_GRACE, self.assemble_report, self.publisher)

    def run(self):
        sleep(1)
        self.publisher.send_multipart([b"START-EPOCH"])
        while True:

            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break

            for sub in self.subscriptions:

                if sub in socks:
                    msg = sub.recv_multipart()
                    # ? ==========================================================================
                    # SECTION Start a new round
                    if msg[0] == b'START-EPOCH' or msg[0] == b'NEW-ROUND':
                        self.start_round()
                        self.round_timer.start()
                        self.publisher.send_multipart(
                            [b"OBSERVE-REQ", dumps({"round_n": self.round_num})])
                        print("NEW EPOCH STARTED")
                    # _ !SECTION
                    # ? ==========================================================================
                    # SECTION Recieve an observation
                    if msg[0] == b'OBSERVE':
                        round_n, observation, signature = loads(msg[1])["round_n"], loads(msg[1])[
                            "observation"], loads(msg[1])["signature"]
                        node_idx = int(sub.get(zmq.IDENTITY).decode())

                        if round_n != self.round_num:
                            print("ERROR: Round number mismatch")
                            return
                        if not (self.phase == "OBSERVE" or self.phase == "GRACE"):
                            print("ERROR: Phase should be OBSERVE or GRACE")
                            return
                        try:
                            if self.observations[node_idx]:
                                print(
                                    "ERROR: Observation already received from this node for this round")
                                return
                            print("Inside try")
                        except IndexError:
                            msg_hash = compute_hash_on_elements(
                                [self.epoch, round_n, observation])
                            if verify(msg_hash, signature[0], signature[1], public_keys[node_idx]):
                                self.observations.append(
                                    (observation, signature, node_idx))

                                if len(self.observations) == 2*F + 1:
                                    if self.phase != 'OBSERVE':
                                        print(
                                            'ERROR: Phase must be OBSERVE')
                                        return

                                    self.phase = "GRACE"
                                    self.grace_timer.start()
                            else:
                                print("ERROR: Signature verification failed")
                    # _ !SECTION
                    # ? ===========================================================================
                    # SECTION Recieve an observation
                    if msg[0] == b'REPORT':
                        print("RECEIVED REPORT")
                        round_n, report, signature = loads(msg[1])["round_n"], loads(msg[1])[
                            "report"], loads(msg[1])["signature"]

                        if self.current_report.msg_hash() != report.msg_hash():
                            print("ERROR: Report mismatch")
                            return

                        node_idx = int(sub.get(zmq.IDENTITY).decode())
                        public_key = public_keys[node_idx]

                        if self.current_report.verify_report_signature(public_key, signature):
                            self.reports.append(
                                (report, signature, node_idx))
                            if len(self.reports) == 4:  # TODO: > F:
                                self.finalize_report(
                                    report, self.publisher)

                        else:
                            print("ERROR: Signature verification failed")

                    # _ !SECTION
                    # ? ===========================================================================


if __name__ == "__main__":
    leader_node = LeaderNode(NODE_IDX, temp_epoch_num)
    leader_node.run()
