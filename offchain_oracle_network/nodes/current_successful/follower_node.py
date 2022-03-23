
from pickle import dumps, loads
from threading import Thread

from time import sleep
import zmq
import sys

# from classes.report_class import Report

F = 10
NUM_NODES = 5  # 31 #?CHANGE LATER
R_MAX = 20
T_ROUND = 30
T_GRACE = 10


PORT_NUM = 5560 + int(sys.argv[1])


def follower_node():
    context = zmq.Context()

    # * This is the socket from which the node will brodcast messages to other oracles
    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    # * This is the socket from which the node will send messages only to the leader
    # leader_publisher = context.socket(zmq.PUB)
    # leader_publisher.sndhwm = 1100000
    # leader_publisher.bind("tcp://*:{}".format(PORT_NUM))

    # * These sockets are used to receive messages from other oracles
    subscriptions = []
    for i in range(NUM_NODES):
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{5560 + i}")
        # TODO: add pacemaker events
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT-REQ')
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL')
        sub.setsockopt(zmq.SUBSCRIBE, b'FINAL-ECHO')
        subscriptions.append(sub)

    sleep(1)  # TODO: remove this sleep with someting else

    # * This is to reduce the cpu strain
    poller = zmq.Poller()
    poller.register(publisher, zmq.POLLIN)
    for sub in subscriptions:
        poller.register(sub, zmq.POLLIN)

    while True:

        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for i, sub in enumerate(subscriptions):

            # TODO: Remove enumerate and replece with get node_idx from sub
            if sub in socks:
                msg = sub.recv_multipart()
                # ? ===============================================================
                if msg[0] == b'OBSERVE-REQ':
                    round_n = loads(msg[1])["round_n"]
                    # TODO: add follower.send_signed_observation(round_n)
                    print("OBSERVE-REQ: round_n: {}".format(round_n))
                    obs = 3000
                    sig = (123, 456)
                    sleep(1)
                    publisher.send_multipart(
                        [b'OBSERVE', dumps({"round_n": round_n, "observation": obs, "signature": sig})])
                # ? ===============================================================
                if msg[0] == b'REPORT-REQ':
                    round_n, report = loads(
                        msg[1])["round_n"], loads(msg[1])["report"]
                    print(f"report_req: {str(report)}")
                    # TODO: add follower.send_signed_report(round_n, report)
                    sleep(1)
                    publisher.send_multipart(
                        [b'REPORT', dumps({"round_n": round_n, "report": report, "signature": (234, 567)})])
                # ? ===============================================================

                # ? ===============================================================


if __name__ == "__main__":
    follower_node()
