#
#  Synchronized publisher
#
from time import sleep
import zmq
import sys
from threading import Thread
from pickle import dumps, loads

from classes.report_class import Report

F = 10
NUM_NODES = 31
R_MAX = 20
T_ROUND = 30
T_GRACE = 10


PORT_NUM = 5560 + int(sys.argv[1])


def leader_node():
    context = zmq.Context()

    # * This is the socket from which the leader will brodcast messages to other oracles
    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    # * These sockets are used to receive messages from other oracles
    subscriptions = []
    for i in range(5):
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{5560 + i}")
        # TODO: add pacemaker events
        sub.setsockopt(zmq.SUBSCRIBE, b'OBSERVE')
        sub.setsockopt(zmq.SUBSCRIBE, b'REPORT')
        subscriptions.append(sub)

    sleep(1)  # TODO: remove this sleep

    publisher.send_multipart([b"OBSERVE-REQ", dumps({"round_n": 123})])

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
                # ? ==========================================================================
                if msg[0] == b'OBSERVE':
                    round_n, observation, signature = loads(msg[1])["round_n"], loads(msg[1])[
                        "observation"], loads(msg[1])["signature"]
                    # TODO: add leader.receive_observation(round_n,observation, signature)
                    print("OBSERVE: round_n: {}, observation: {}, signature: {}".format(
                        round_n, observation, signature))

                    report = {"round_n": round_n, "report": Report(
                        "snovsvid", "odsmdsvpsod", [1, 2, 3, 4, 5])}
                    # {"rrc": "0x34f02abe", "rob": "0x12345", "observations": [
                    #     observation, 3200, 3100]}

                    sleep(1)
                    publisher.send_multipart([b'REPORT-REQ', dumps(report)])
                # ? ===========================================================================
                elif msg[0] == b'REPORT':
                    round_n, report, signature = loads(msg[1])["round_n"], loads(msg[1])[
                        "report"], loads(msg[1])["signature"]
                    print("REPORT: round_n: {}, {}, signature: {}".format(
                        round_n, report, signature))
                    # TODO: add leader.receive_report(round_n, report, signature )
                # ? ===========================================================================


if __name__ == "__main__":
    leader_node()
