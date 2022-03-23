import time
import zmq
import threading

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify

from pacemaker import Pacemaker

F = 10
NUM_NODES = 31
MAX_ROUND = 20
T_PROGRESS = 30
T_RESEND = 10

round_error_msg = "ERROR: Round number mismatch"
completed_round_error = 'ERROR: Round has already been completed'


class Follower(Pacemaker):
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

    # Upon receiving OBSERVE-REQ
    def send_signed_observation(self, round_n):
        self.round_num = round_n
        if round_n > MAX_ROUND:
            # TODO: Invoke change_leader event
            return "CHANGE-LEADER"

        self.sentecho = None
        self.sentreport = False
        self.completedround = False
        self.receivedecho = [False] * NUM_NODES

        observation = self.get_price()  # Current rounds' observation
        msg_hash = compute_hash_on_elements([self.epoch, round_n, observation])
        signature = sign(msg_hash, self.private_key)
        # TODO: Send message to leader with round observation and signature [r, v, σ]

    def send_signed_report(self, round_n, report):

        if round_n != self.round_num:
            print(round_error_msg)
            return
        if self.sentreport:
            print('ERROR: Report has already been sent')
            return
        if self.completedround:
            print(completed_round_error)
            return

        if not self.verify_sorted(report):
            print('ERROR: Report is not sorted')
            return
        # TODO: Verify all signatures are valid for the report.observations

        # ? if should_report() else complete_round

        signature = report.sign_report(self.private_key)

        self.sentreport = True
        # TODO: Send message to leader with compressed report and signature [r, R, σ]

    def receive_final_report(self, report_bundle):

        if report_bundle[1] != self.round_num:
            print(round_error_msg)
            return
        if self.sentecho:
            print('ERROR: Echo has already been sent')
            return

        self.verify_attested_report(report_bundle)

        self.sentecho = report_bundle
        # TODO: send message [FINAL-ECHO , report_bundle] to all nodes

    def receive_final_echo(self, report_bundle):

        node_idx = 5  # TODO: get node indexs

        if report_bundle[1] != self.round_num:
            print(round_error_msg)
            return
        if self.receivedecho[node_idx]:
            print("ERROR: Already received an echo from this node")
            return
        if self.completedround:
            print(completed_round_error)

        self.verify_attested_report(report_bundle)
        self.receivedecho[node_idx] = True

        if self.sentecho == None:
            self.sentecho = report_bundle
            # TODO: send message [FINAL-ECHO , report_bundle] to all nodes

    def invoke_transmission(self):

        if self.count_echoes() <= F:
            print("ERROR: Not enough echoes received")
            return

        if self.completedround:
            print(completed_round_error)
            return

        # TODO: Invoke transmit()
        self.complete_round()

    # * =============================================================================================
    # * HELPERS

    def get_price(self):
        # TODO: Implement a function that returns the current price of an asset
        return 2687*10**8

    def verify_sorted(self, report):
        # assert that the array of tuples is sorted by first element
        for i in range(len(report) - 1):
            if report[i][0] > report[i + 1][0]:
                return False

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

    def verify_attested_report(self, report_bundle):

        e, r, report, signatures, signers = report_bundle

        if len(signatures) <= F:
            print("ERROR: Not enough signatures")
            return

        for i in range(len(signatures)):
            # TODO: Verify ith signature against report.msg_hash() and ith public_key
            pass

        return True  # Depending on wheter tests passed

    def count_echoes(self):
        count = 0
        for x in self.receivedecho:
            count = count+1 if x else count

        return count

    def complete_round(self):
        self.complete_round = True
        # TODO: Invoke event progress
