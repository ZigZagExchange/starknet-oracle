import pickle
import zmq
import sys
import json
from time import sleep
from pickle import dumps, loads
import threading

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify, private_to_stark_key


import helpers.helpers as h

from classes.report_class import Report
from pacemaker import PacemakerState


# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================

# TODO: Change constants
F = 1
T_PROGRESS = 90
T_RESEND = 20

NODE_IDX = int(sys.argv[1])
PORT_NUM = 5560 + NODE_IDX

temp_epoch_num = 12345


class PaceMaker(PacemakerState):
    def __init__(self, index):
        super().__init__(index)
        self.context = zmq.Context()
        # * This is the socket from which the follower will brodcast messages to other oracles
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.sndhwm = 1100000
        self.publisher.bind("tcp://*:{}".format(PORT_NUM))
        # * These sockets are used to receive messages from other oracles
        self.subscriptions = h.subscribe_to_other_nodes_pacemaker(self.context)
        # * Poller is used to reduce the cpu strain
        self.poller = zmq.Poller()
        self.poller.register(self.publisher, zmq.POLLIN)
        for sub in self.subscriptions:
            self.poller.register(sub, zmq.POLLIN)
        # * Timers
        self.progress_timer = h.ResettingTimer(
            # T_PROGRESS, self.abort_generation_instance)
            T_PROGRESS, self.emit_change_leader_event, self.publisher)
        self.resend_timer = h.ResettingTimer(
            T_RESEND, self.emit_send_new_epoch_event, self.publisher)

    def run(self):
        sleep(3)
        self.initilize(1, self.progress_timer, self.publisher)
        # self.publisher.send_multipart(
        #     [b"NEW-EPOCH", dumps({"new_epoch": self.ne})])
        while True:

            try:
                socks = dict(self.poller.poll())
            except KeyboardInterrupt:
                break

            for sub in self.subscriptions:

                if sub in socks:
                    msg = sub.recv_multipart()
                    # ? ===============================================================
                    # SECTION Send Signed OBSERVATION to Leader

                    if msg[0] == b'PROGRESS':
                        self.progress_timer.cancel()
                        self.progress_timer.start()

                    if msg[0] == b'SEND-NEW-EPOCH':
                        self.send_new_epoch(
                            self.ne, self.publisher, self.resend_timer)

                    if msg[0] == b'CHANGE-LEADER':
                        # print("CHANGE-LEADER epoch {} from {} ".format(
                        # self.current_epoch, sub.get(zmq.IDENTITY).decode()))
                        self.progress_timer.cancel()
                        self.send_new_epoch(
                            max(self.ne, self.current_epoch + 1), self.publisher, self.resend_timer)

                    if msg[0] == b"NEW-EPOCH":
                        node_idx = int(sub.get(zmq.IDENTITY).decode())
                        try:
                            new_epoch = loads(msg[1])["new_epoch"]
                        except pickle.UnpicklingError:
                            print("PICKLE ERROR: ", int(
                                sub.get(zmq.IDENTITY).decode()))
                        self.new_epochs[node_idx] = max(
                            self.new_epochs[node_idx], new_epoch)
                        if self.count_new_epochs() > F:
                            self.request_proceed_to_next_epoch(
                                self.publisher, self.resend_timer)
                        if self.count_new_epochs2() > 2*F:
                            self.proceed_to_next_epoch(
                                self.publisher, self.progress_timer)


if __name__ == "__main__":
    pace_maker = PaceMaker(NODE_IDX)
    pace_maker.run()
