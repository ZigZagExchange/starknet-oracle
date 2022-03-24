import time
from classes.report_class import Report
import zmq
import threading
import json

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify

from pacemaker import Pacemaker

# TODO: change constants
F = 0
NUM_NODES = 31
MAX_ROUND = 20
T_PROGRESS = 30
T_RESEND = 10

# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================


class FollowerState(Pacemaker):
    def __init__(self, index, epoch, leader_id):
        super().__init__(index)
        self.private_key = 0
        self.index = index
        self.epoch = epoch
        self.leader_id = leader_id
        self.round_num = 0  # round number within the epoch
        self.sentecho = None  # echoed attested report which has been sent for this round
        self.sentreport = False  # indicates if REPORT message has been sent for this round
        self.completedround = False  # indicates if current round is finished
        # jth element true if received FINAL-ECHO message with valid attested report from node j
        self.receivedecho = [False] * NUM_NODES

    def set_private_key(self, priv_key):
        self.private_key = priv_key

    def complete_round(self):
        self.completedround = True
        # TODO: Invoke event progress

    # * =============================================================================================
    # * HELPERS

    def verify_attested_report(self, report_bundle):

        e, r, report, signatures, signers = report_bundle

        report: Report
        if len(signatures) <= F:
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
        # TODO: Implement a function that returns the current price of an asset
        return 2687*10**8

    def verify_report_sorted(self, report: Report):
        # NOTE Maybe do something if observation prices are too far apart
        for i in range(len(report.observations) - 1):
            if report.observations[i] > report.observations[i + 1]:
                return False
        return True

    def should_report(self, report):
        R, t_R = self.get_last_report()
        # TODO: Return true iff report should be reported

    def get_last_report(self):

        # TODO: Return the last attested report (R, t)
        return (0, 0)

    def get_config_digest(self):
        # TODO: Get the config digest
        return 123456789

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
