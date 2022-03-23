import zmq
from threading import Timer

node_identities = {
    "0": 5560,
    "1": 5561,
    "2": 5562,
    "3": 5563,
    "4": 5564,
    "5": 5565,
}


def subscribe_to_other_nodes_follower(N_nodes, context):
    subscriptions = []
    for name, port in node_identities.items():
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{port}")
        # TODO: add pacemaker events
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL')
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL-ECHO')
        sub.setsockopt(zmq.IDENTITY, name.encode())
        subscriptions.append(sub)
    return subscriptions


def subscribe_to_other_nodes_leader(N_nodes, context):
    subscriptions = []
    for name, port in node_identities.items():
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{port}")
        # TODO: add pacemaker events
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT')
        sub.setsockopt(zmq.SUBSCRIBE, b'START-EPOCH')
        sub.setsockopt(zmq.IDENTITY, name.encode())
        subscriptions.append(sub)
    return subscriptions


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
        self.timer.cancel()

    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()
