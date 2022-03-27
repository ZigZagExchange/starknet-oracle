from datetime import datetime
import time
from pickle import dumps
import sys
import json
import time
from follower_node import FollowerNode
from leader_node import LeaderNode
from helpers.helpers import ResettingTimer
import zmq
import threading

# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================


# TODO Change the constants

NUM_NODES = 4
MAX_ROUNDS = 5
F = NUM_NODES//3

NODE_IDX = int(sys.argv[1])


class PacemakerState:
    '''
    This is used to store and manipulate the state of the current node
    and reduce mental complexity of the PacemakerNode
    '''

    def __init__(self, index):
        self.current_epoch = 0
        self.current_leader = 0
        self.ne = 0
        self.new_epochs = [0] * NUM_NODES
        self.index = index
        self.follower_node = None
        self.leader_node = None
        self.latest_init_time = 0

    def leader(self, epoch):
        # TODO: Implement a more secure leader function
        return (3 * epoch + 123) % NUM_NODES

    def on_progress(self):
        self.progress_timer.start()

    def initilize(self, epoch, timer: ResettingTimer, publisher):
        self.current_epoch = epoch
        self.current_leader = self.leader(epoch)
        self.ne = epoch

        print("INITILIZING epoch {}".format(epoch))

        t = time.time()
        if t - self.latest_init_time < timer.interval:
            print("ERROR: Node {} is trying to initialize epoch {} too fast —> Skipping ...".format(
                self.index, self.current_epoch))
            return
        self.latest_init_time = t

        if not self.follower_node:
            self.follower_node = FollowerNode(
                self.index, epoch, self.current_leader, private_keys[self.index],
                publisher, NUM_NODES, MAX_ROUNDS)
            self.follower_node.run()
        else:
            self.follower_node.reset(
                epoch, self.leader(epoch))

        if not self.leader_node and self.current_leader == self.index:
            self.leader_node = LeaderNode(
                self.index, epoch, publisher, NUM_NODES, MAX_ROUNDS)
            self.leader_node.run()
            print("Leader node started")
        elif self.leader_node:
            self.leader_node.stop()
            self.leader_node = None

        print("Sleeping 3 seconds for nodes to fall back in sync")
        time.sleep(3)
        timer.start()
        print(
            "========================================================================\n")

    def send_new_epoch(self, new_e, publisher, resend_timer):
        publisher.send_multipart(
            [b"NEW-EPOCH", dumps({"new_epoch": new_e})])
        self.ne = new_e
        resend_timer.start()

    def request_proceed_to_next_epoch(self, publisher, timer):
        '''
        This function is called if more than F nodes want to
        proceed to epoch that is grater than this nodes ne 
        <=> {pj ∈ Pn | newepoch[j] > ne} > F
        '''
        sorted_new_epochs = self.new_epochs.copy()
        sorted_new_epochs.sort(reverse=True)
        e_new = sorted_new_epochs[F]
        self.send_new_epoch(max(e_new, self.ne), publisher, timer)

    def proceed_to_next_epoch(self, publisher, progress_timer):
        '''
        This function is called if more than 2F nodes want to
        proceed to a new epoch <=> {p j ∈ P n | newepoch[j] > e} > 2F
        This usually  means that the leader is too slow
        '''
        sorted_new_epochs = self.new_epochs.copy()
        sorted_new_epochs.sort(reverse=True)
        e_new = sorted_new_epochs[2*F]  # 2F+1-th element

        current_epoch = e_new
        # current_leader = self.leader(e_new)
        self.ne = max(self.ne, e_new)

        self.initilize(current_epoch, progress_timer, publisher)

        # progress_timer.cancel()
        # progress_timer.start()
        if self.current_leader == self.index:
            print("Sending START-EPOCH from node {}".format(self.index))
            publisher.send_multipart([b"START-EPOCH"])

    # * HELPERS ==========================================================

    def emit_change_leader_event(self, publisher):
        publisher.send_multipart([b"CHANGE-LEADER"])

    def emit_send_new_epoch_event(self, publisher):
        publisher.send_multipart([b"SEND-NEW-EPOCH"])

    def count_new_epochs(self):
        count = 0
        for e in self.new_epochs:
            if e > self.ne:
                count += 1

        return count

    def count_new_epochs2(self):
        count = 0
        for e in self.new_epochs:
            if e > self.current_epoch:
                count += 1

        return count
