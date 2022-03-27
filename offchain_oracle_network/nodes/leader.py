from pickle import dumps
import time
import zmq
import threading

from classes.report_class import Report

# TODO: Change the constants
# F = 0


class LeaderState:
    def __init__(self, index, epoch, num_nodes, max_round):
        '''
        This is used to store and manipulate the state of the current node
        and reduce mental complexity of the LeaderNode
        '''

        self.index = index
        self.num_nodes = num_nodes
        self.max_round = max_round
        self.F = num_nodes//3

        self.epoch = epoch
        self.round_num = 0
        # signed observations of the current round received in OBSERVE messages
        # (observation, signature, node_idx)
        self.observations = [None] * num_nodes
        self.reports = []  # attested reports of the current round received in REPORT messages
        # the current report sent out for signing (for consistency reasons)
        self.current_report = None
        # denotes phase within round in { OBSERVE , GRACE , REPORT , FINAL }
        self.phase = None

    def start_round(self):
        self.round_num += 1
        self.observations = [None] * self.num_nodes
        self.reports = []
        self.current_report = None
        self.phase = 'OBSERVE'

    def emit_new_round_event(self, publisher):
        publisher.send_multipart([b"NEW-ROUND"])

    def assemble_report(self, publisher):
        if not self.phase == "GRACE":
            print("ERROR: Phase should be GRACE")
            return

        # where x = (observation, signature, node_idx)

        report_temp = [x for x in self.observations if x]
        report_temp.sort(key=lambda x: x[0])

        observations = []
        observers = []
        signatures = []
        for i in range(len(report_temp)):
            observations.append(report_temp[i][0])
            signatures.append(report_temp[i][1])
            observers.append(report_temp[i][2])

        # NOTE Maybe do something if observation prices are too far apart

        config_digest = self.get_config_digest()  # TODO
        epoch_and_round = hex(self.epoch)[2:] + hex(self.round_num)[2:]

        raw_report_context = hex(config_digest)[2:] + epoch_and_round
        raw_observers = self.indexes_list_to_hex_string(observers)

        report = Report(raw_report_context, raw_observers,
                        observations, signatures)

        self.current_report = report
        self.phase = "REPORT"
        report_msg = {"round_n": self.round_num, "report": report}
        publisher.send_multipart([b"REPORT-REQ", dumps(report_msg)])

    def finalize_report(self, report, publisher):
        if not self.phase == 'REPORT':
            # print('ERROR: Phase should be REPORT')
            return

        report, signatures, signer_idxs = self.count_reports(report)
        if not report:
            print('ERROR: Not enough valid reports received')
            return

        raw_signers = self.indexes_list_to_hex_string(signer_idxs)

        report_bundle = (self.epoch, self.round_num,
                         report, signatures, raw_signers)

        msg = {"round_n": self.round_num, "report_bundle": report_bundle}
        publisher.send_multipart([b"FINAL", dumps(msg)])
        self.phase = 'FINAL'

    # * ====================================================================================
    # * HELPER FUNCTIONS

    def get_config_digest(self):
        # TODO: Get the config digest
        return 123456789932728419024823509129473805294812389473419247 % 2**128

    def indexes_list_to_hex_string(self, idxs):
        hex_string = "0x"
        for idx in idxs:
            hex_string += hex(idx)[2:] if idx >= 16 else "0" + hex(idx)[2:]

        return hex_string

    def count_reports(self, report: Report):

        count = 0
        sigs = []
        idxs = []
        for i in range(len(self.reports)):
            if self.reports[i]:
                rep: Report = self.reports[i][0]
                sig = self.reports[i][1]
                idx = self.reports[i][2]

                if rep.msg_hash() == report.msg_hash():
                    count += 1
                    sigs.append(sig)
                    idxs.append(idx)
                else:
                    print("ERROR: report missmatch")

        if count > self.F:
            return report, sigs, idxs

        else:
            return None, None, None
