import time
import zmq
import threading

F = 10
NUM_NODES = 31
T_PROGRESS = 30
T_RESEND = 10


class Pacemaker:
    def __init__(self, index):
        self.current_epoch = 0
        self.current_leader = 0
        self.ne = 0
        self.new_epochs = []
        self.index = index
        self.resend_timer = threading.Timer(T_RESEND, self.on_resend)
        self.progress_timer = threading.Timer(
            T_PROGRESS, self.end_leader_campaign)

    def leader(self, epoch):
        # TODO: Implement a more secure leader function
        return (epoch + 123) % NUM_NODES

    def on_progress(self):
        restart_timer(self.progress_timer)

    def initilize(self, epoch, leader):
        # TODO: Initialize instance of report generation
        restart_timer(self.progress_timer)

    def send_new_epoch(self, new_e):
        # TODO: Send a message to all nodes (new epoch)
        self.ne = new_e
        restart_timer(self.resend_timer)

    def end_leader_campaign(self):
        self.progress_timer.cancel()
        self.send_new_epoch(max(self.current_epoch+1, self.ne))

    def on_resend(self):
        self.send_new_epoch(self.ne)

    def receive_new_epoch(self, e_new, pj):
        ''' Params:
            e_new - is the received new_epoch
            pj - is the jth node that sent the e_new'''
        self.new_epochs[pj] = max(self.new_epochs[pj], e_new)

    def request_proceed_to_next_epoch(self):
        '''
        This function is called if more than F nodes want to
        proceed to epoch that is grater than this nodes ne 
        <=> {p j ∈ P n | newepoch[j] > ne} > F
        '''
        sorted_new_epochs = self.new_epochs.copy()
        sorted_new_epochs.sort(reverse=True)
        e_new = sorted_new_epochs[F+1]

        self.send_new_epoch(max(e_new, self.ne))

    # if more than 2F nodes want to proceed to new epoch
    # {p j ∈ P n | newepoch[j] > e} > 2f

    def proceed_to_next_epoch(self):
        '''
        This function is called if more than 2F nodes want to
        proceed to a new epoch <=> {p j ∈ P n | newepoch[j] > e} > F
        this means that the leader is too slow??
        '''
        sorted_new_epochs = self.new_epochs.copy()
        sorted_new_epochs.sort(reverse=True)
        e_new = sorted_new_epochs[2*F+1]

        current_epoch = e_new
        current_leader = self.leader(e_new)
        ne = max(ne, e_new)

        self.initilize(current_epoch, current_leader)

        if current_leader == self.index:
            # TODO: Invoke event start_epoch(e,l)
            pass


def restart_timer(timer):
    timer.cancel()
    timer.start()


def main():

    while True:
        pass


if __name__ == "__main__":
    main()
