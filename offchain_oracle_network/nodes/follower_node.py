import zmq
import sys
import json
from time import sleep
from pickle import dumps, loads
import threading

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify, private_to_stark_key


import helpers.helpers as h

from classes.report_class import Report
from follower import Follower


# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================

F = 10
NUM_NODES = 5  # 31 #?CHANGE LATER
MAX_ROUND = 20
T_ROUND = 30
T_GRACE = 10

NODE_IDX = int(sys.argv[1])
PORT_NUM = 5560 + NODE_IDX

temp_epoch_num = 12345


def follower_node(leader_id):
    context = zmq.Context()

    follower = Follower(NODE_IDX, temp_epoch_num, leader_id)
    follower.set_private_key(private_keys[NODE_IDX])

    # * This is the socket from which the node will brodcast messages to other oracles
    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    # * These sockets are used to receive messages from other oracles
    subscriptions = h.subscribe_to_other_nodes_follower(NUM_NODES, context)

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

        for sub in subscriptions:

            if sub in socks:
                msg = sub.recv_multipart()
                # ? ===============================================================
                # SECTION Send Signed Observation

                if msg[0] == b'OBSERVE-REQ':
                    if sub.get(zmq.IDENTITY).decode() != follower.leader_id:
                        print("Message sender should be the leader")
                        return
                    print(
                        "Received OBSERVE-REQ from {}".format(sub.get(zmq.IDENTITY).decode()))
                    round_n = loads(msg[1])["round_n"]
                    follower.round_num = round_n
                    if round_n > MAX_ROUND:
                        publisher.send_multipart([b'CHANGE-LEADER'])

                    follower.sentecho = None
                    follower.sentreport = False
                    follower.completedround = False
                    follower.receivedecho = [False] * NUM_NODES

                    observation = follower.get_price()
                    msg_hash = compute_hash_on_elements(
                        [follower.epoch, round_n, observation])
                    signature = sign(msg_hash, follower.private_key)
                    sleep(1)
                    publisher.send_multipart(
                        [b'OBSERVE', dumps({"round_n": round_n, "observation": observation, "signature": signature})])


                # _ !SECTION
                # # ? ===============================================================
                # SECTION Send Signed Observation
                # if msg[0] == b'REPORT-REQ':
                #     round_n, report = loads(
                #         msg[1])["round_n"], loads(msg[1])["report"]
                #     print(f"report_req: {str(report)}")
                #     # TODO: add follower.send_signed_report(round_n, report)
                #     sleep(1)
                #     publisher.send_multipart(
                #         [b'REPORT', dumps({"round_n": round_n, "report": report, "signature": (234, 567)})])
                # _ !SECTION
                # # ? ===============================================================
                # # ? ===============================================================
if __name__ == "__main__":
    follower_node("0")
