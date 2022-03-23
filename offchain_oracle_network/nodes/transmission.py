import time
from offchain_oracle_network.nodes.leader import restart_timer
import zmq
import threading
import itertools as it
from queue import PriorityQueue


F = 10
NUM_NODES = 31
R_MAX = 20
T_TRANSMIT = 100
T_STAGE = 100
alpha = 0.005


class Transmission:
    def __init__(self, index):
        self.index = index
        # delays until next report should be transmitted
        self.transmit_timer = threading.Timer(T_TRANSMIT, ())
        # priority queue of time-report pairs (t, O), keyed on ascending time values
        self.reports_queue = PriorityQueue()
        # latest report accepted for transmission (e, r, R, sigs, signers)
        self.latest_report = (0, 0, 0, [], [])
        # latest report commited to C (on-chain) as known to this node (e, r, R, sigs, signers)
        self.latest_comitted_report = (0, 0, 0, [], [])

    def transmit(self, report_bundle):
        epoch, round_n, report, _, _ = report_bundle
        e_C, r_C, rep_C, _, _ = self.latest_comitted_report
        e_L, r_L, rep_L, _, _ = self.latest_report

        if int(str(epoch) + str(round_n)) <= int(str(e_C) + str(r_C)):
            print("ERROR: Report is outdated compared to the latest commited report")
            return

        if self.latest_report and int(str(epoch) + str(round_n)) <= int(str(e_C) + str(r_C)):
            print("ERROR: Report is outdated compared to the latest report")
            return

        if not self.latest_report or int(str(e_C) + str(r_C)) <= int(str(e_C) + str(r_C)) or (abs(median(report.observations) - median(rep_L.observations)))/median(rep_L.observations) > alpha:
            self.latest_report = report_bundle

        delay = self.transmit_delay(self.index, epoch, round_n)

        self.reports_queue.put((time.time() + delay, report_bundle))

        threading.Timer(delay, restart_timer, [self.transmit_timer]).start()

    def transmit_on_chain(self):
        if self.reports_queue.empty():
            return

        # TODO get_latest_commited_report() -> C

        _, report_bundle = self.reports_queue.get()
        epoch, round_n, report, _, _ = report_bundle
        e_C, r_C, rep_C, _, _ = self.latest_comitted_report

        if int(str(epoch) + str(round_n)) > int(str(e_C) + str(r_C)):
            # TODO: Send a transaction to the blockchain
            pass
        # TODO: retart_timer

        # * HELPERS * ==============================================================

    # TODO: See about this delay system

    def transmit_delay(self, i, e, r):
        k = self.permutation(i, e, r)
        return k * T_STAGE

        # # pseudo-random permutation of the nodes (for transmission delays)
        # TODO: make this a real permutation that equaly selects all nodes

    def permutation(self, i, e, r):
        return [self.nodes[((e*r+i)*n + 1) % NUM_NODES] for n in range(len(self.nodes))]


def restart_timer(timer):
    timer.cancel()
    timer.start()


def median(lst):
    return sorted(lst)[len(lst) // 2]
