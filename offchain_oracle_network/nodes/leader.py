import time
import zmq
import threading

from offchain_oracle_network.classes.report_class import Report

F = 10
NUM_NODES = 31
R_MAX = 20
T_ROUND = 30
T_GRACE = 10


class Leader:
    def __init__(self, index, epoch):
        self.index = index   # index of the current node
        self.epoch = epoch  # the current epoch
        self.round_num = 0  # round number within the epoch
        # signed observations of the current round received in OBSERVE messages
        self.observations = []
        self.reports = []  # attested reports of the current round received in REPORT messages
        self.round_timer = threading.Timer(T_ROUND, self.start_round)
        self.grace_timer = threading.Timer(T_GRACE, self.assemble_report)
        # denotes phase within round in { OBSERVE , GRACE , REPORT , FINAL }
        self.phase = None

    def start_round(self):
        self.round_num += 1
        self.observations = []
        self.reports = []
        self.phase = 'OBSERVE'
        restart_timer(self.round_timer)
        # TODO: Send OBSERVE-REQ to all nodes

    # upon receiving message [OBSERVE]
    def receive_observation(self, round_n, observation, signature):

        node_idx = 5  # TODO: get node index from message

        if self.round_num != round_n:
            print('ERROR: Round number mismatch')
            return
        if not (self.phase == 'OBSERVE' or self.phase == 'GRACE'):
            print('ERROR: Phase should be OBSERVE or GRACE')
            return
        if self.observations[node_idx] != None:
            print('ERROR: Observation already received from this node for this round')
            return

        # TODO: Verify signature of observation
        if True:
            self.observations.append((observation, signature, node_idx))

    # when at least 2F+1 nodes have sent their observations
    def initiate_grace_period(self):
        count = 0
        for i in range(len(self.observations)):
            if self.observations[i] is not None:
                count += 1
        if count < 2*F+1:
            print('ERROR: Not enough observations received')
            return
        if self.phase != 'OBSERVE':
            print('ERROR: Phase must be OBSERVE')
            return

        restart_timer(self.grace_timer)
        self.phase = "GRACE"

    # upon event timeout of grace_timer
    def assemble_report(self):
        if not self.phase == 'GRACE':
            print('ERROR: Phase should be GRACE')
            return

        report_temp = [x for x in self.observations if x[0] is not None]
        report_temp.sort(key=lambda x: x[0])

        observations = []
        observers = []
        signatures = []
        for i in range(len(report_temp)):
            # ? report_temp[i] is a tuple of (observation, signature)
            observations.append(report_temp[i][0])
            signatures.append(report_temp[i][1])
            observers.append(report_temp[i][2])

        # observers = [k for k, v, s in report]
        config_digest = self.get_config_digest()
        epoch_and_round = hex(self.epoch)[2:] + hex(self.round_num)[2:]

        raw_report_context = config_digest + epoch_and_round
        raw_observers = self.indexes_list_to_hex_string(observers)

        report = Report(raw_report_context, raw_observers, observations)

        # TODO: Send REPORT message to all nodes [REPORT-REQ , r , R, sigs ]
        self.phase = "REPORT"

    # upon receiving message [REPORT, r , R, τ]
    def receive_report(self, round_n, report, signature):

        node_idx = 5  # TODO: get node index from message

        if self.round_num != round_n:
            print('ERROR: Round number mismatch')
            return
        if not (self.phase == 'REPORT'):
            print('ERROR: Phase should be REPORT')
            return
        if self.reports[node_idx] != None:
            print('ERROR: Attested report already received from this node for this round')
            return

        # TODO: Verify signature of report

        self.reports.append((report, signature, node_idx))

    def finalize_report(self, report):
        if not self.phase == 'REPORT':
            print('ERROR: Phase should be REPORT')
            return

        report, signatures, signers = self.count_reports(report)
        if report is None:
            print('ERROR: Not enough reports received')
            return

        # raw_signers = self.indexes_list_to_hex_string(signer_idxs)

        # O ← [e, r , R, sigs, signers]
        # TODO: send message [FINAL ,r , O] to all nodes, where O is the report bundle

        self.phase = 'FINAL'

    # * ====================================================================================
    # * HELPER FUNCTIONS

    def get_config_digest(self):
        # TODO: Get the config digest
        return 123456789

    def indexes_list_to_hex_string(self, idxs):
        hex_string = "0x"
        for idx in idxs:
            hex_string += hex(idx)[2:]

        return hex_string

    def count_reports(self, report):

        count = 0
        sigs = []
        idxs = []
        for i in range(len(self.reports)):
            if self.reports[i] is not None:
                rep = self.reports[i][0]
                sig = self.reports[i][1]
                idx = self.reports[i][2]

                if rep == report:
                    count += 1
                    sigs.append(sig)
                    idxs.append(idx)
                else:
                    print("ERROR: report missmatch")

        if count > F:
            return report, sigs, idxs

        else:
            return None, None, None


def restart_timer(timer):
    timer.cancel()
    timer.start()

#(report, signature, node_idx)

#

#

#


#
    # def count_reports(self):

    #     report_counts = {}
    #     report_idxs = []
    #     for i in range(len(self.reports)):
    #         if self.reports[i] is not None:
    #             rep = self.reports[i][0]

    #             report_counts[rep] = report_counts[rep] + \
    #                 1 if report_counts[rep] else 1

    #     report = max(report_counts, key=report_counts.get)
    #     count = report_counts[report]

    #     if count > F:
    #         return report
    #     else:
    #         return None
