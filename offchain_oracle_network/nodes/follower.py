from random import random
import time
from classes.report_class import Report
import zmq
import threading
import json
import os

from helpers import helpers as h

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify

T_BETWEEN_COMMITS = 300
alpha = 0.0025

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


class FollowerState():
    def __init__(self, index, epoch, leader_id, priv_key, num_nodes, max_round):
        '''
        This is used to store and manipulate the state of the current node
        and reduce mental complexity of the PacemakerNode
        '''
        self.private_key = priv_key
        self.num_nodes = num_nodes
        self.max_round = max_round
        self.F = num_nodes//3
        self.index = index

        self.epoch = epoch
        self.leader_id = leader_id
        self.round_num = 0  # round number within the epoch
        self.sentecho = None  # echoed attested report which has been sent for this round
        self.sentreport = False  # indicates if REPORT message has been sent for this round
        self.completedround = False  # indicates if current round is finished
        # jth element true if received FINAL-ECHO message with valid attested report from node j
        self.receivedecho = [False] * self.num_nodes

    def reset_state(self, new_epoch, leader_id):
        self.epoch = new_epoch
        self.leader_id = leader_id
        self.round_num = 0
        self.sentecho = None
        self.sentreport = False
        self.completedround = False
        self.receivedecho = [False] * self.num_nodes

    def complete_round(self, publisher):
        self.completedround = True
        publisher.send_multipart([b'PROGRESS'])

    # * =============================================================================================
    # * HELPERS

    def verify_attested_report(self, report_bundle):
        e, r, report, signatures, signers = report_bundle

        report: Report
        if len(signatures) <= self.F:
            print("ERROR: Not enough signatures")
            return

        for i in range(len(signatures)):
            sig = signatures[i]
            node_idx = int(signers[2 + 2*i:4+2*i])
            pub_key = public_keys[node_idx]
            if not report.verify_report_signature(pub_key, sig):
                return False

        return True

    def get_price(self):
        # TODO: INSERT A PRICE GETTER FUNCTION HERE
        return 2687*10**8 + int(random()*10**8)

    def should_report(self, latest_comited_report, report):
        e_C, r_C, answer_C, t_C = latest_comited_report

        return answer_C == 0 or time.time() - t_C >= T_BETWEEN_COMMITS or \
            (abs(h.median(report.observations) - answer_C))/abs(answer_C) > alpha

    def verify_report_sorted(self, report: Report):
        # NOTE Maybe do something if observation prices are too far apart
        for i in range(len(report.observations) - 1):
            if report.observations[i] > report.observations[i + 1]:
                return False
        return True

    def observers_list_to_hex_string(self, observers):
        raw_observers = "0x"
        for observer in observers:
            raw_observers += hex(observer)[2:]

        return raw_observers

    def count_received_echoes(self):
        count = 0
        for x in self.receivedecho:
            count = count+1 if x else count

        return count
