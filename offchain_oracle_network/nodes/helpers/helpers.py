import zmq
from threading import Timer
import asyncio

node_identities = {
    "0": 5560,
    "1": 5561,
    "2": 5562,
    "3": 5563,
    # "4": 5564,
    # "5": 5565,
}


def subscribe_to_other_nodes_follower(context, leader_id):
    subscriptions = []
    for name, port in node_identities.items():
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{port}")
        # if int(name) == leader_id:
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL')
        # else:
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL-ECHO')

        sub.setsockopt(zmq.IDENTITY, name.encode())
        subscriptions.append(sub)
    return subscriptions


def subscribe_to_other_nodes_leader(context):
    subscriptions = []
    for name, port in node_identities.items():
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{port}")
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT')
        sub.setsockopt(zmq.SUBSCRIBE, b'START-EPOCH')
        sub.setsockopt(zmq.SUBSCRIBE, b'NEW-ROUND')
        sub.setsockopt(zmq.IDENTITY, name.encode())
        subscriptions.append(sub)
    return subscriptions


def subscribe_to_other_nodes_pacemaker(context):
    subscriptions = []
    for name, port in node_identities.items():
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{port}")
        sub.setsockopt(zmq.SUBSCRIBE, b'PROGRESS')
        sub.setsockopt(zmq.SUBSCRIBE, b'CHANGE-LEADER')
        sub.setsockopt(zmq.SUBSCRIBE, b'NEW-EPOCH')
        sub.setsockopt(zmq.SUBSCRIBE, b'SEND-NEW-EPOCH')
        sub.setsockopt(zmq.IDENTITY, name.encode())
        subscriptions.append(sub)
    return subscriptions


def median(lst):
    if len(lst):
        return sorted(lst)[len(lst) // 2]


class ResettingTimer(object):

    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f = f
        self.args = args
        self.kwargs = kwargs

        self.timer = None

    def callback(self):
        self.f(*self.args, **self.kwargs)

    def cancel(self):
        if self.timer:
            self.timer.cancel()

    def start(self):
        self.cancel()
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()
