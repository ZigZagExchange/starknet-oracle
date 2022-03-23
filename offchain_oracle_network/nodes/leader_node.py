import zmq
import sys
import json
import threading
from time import sleep
from pickle import dumps, loads

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify

from classes.report_class import Report
import helpers.helpers as h
from leader import Leader

# ? ===========================================================================
file_path = "../../tests/dummy_data/dummy_keys.json"
f = open(file_path, 'r')
keys = json.load(f)
f.close()

public_keys = keys["keys"]["public_keys"]
private_keys = keys["keys"]["private_keys"]
# ? ===========================================================================

F = 10
NUM_NODES = 31
R_MAX = 20
T_ROUND = 30
T_GRACE = 3


NODE_IDX = int(sys.argv[1])

PORT_NUM = 5560 + NODE_IDX

temp_epoch_num = 12345


def leader_node():
    context = zmq.Context()

    leader = Leader(PORT_NUM, temp_epoch_num)

    # * This is the socket from which the leader will brodcast messages to other oracles
    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    round_timer = h.ResettingTimer(T_ROUND, print, "Round time out")
    grace_timer = h.ResettingTimer(T_GRACE, leader.assemble_report, publisher)

    # * These sockets are used to receive messages from other oracles
    subscriptions = h.subscribe_to_other_nodes_leader(NUM_NODES, context)

    sleep(1)  # TODO: remove this sleep

    publisher.send_multipart([b"START-EPOCH"])

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
                # ? ==========================================================================
                # SECTION Start a new round
                if msg[0] == b'START-EPOCH':
                    leader.start_round()
                    round_timer.start()
                    publisher.send_multipart(
                        [b"OBSERVE-REQ", dumps({"round_n": leader.round_num})])
                    print("NEW EPOCH STARTED")
                # _ !SECTION
                # ? ==========================================================================
                # SECTION Recieve an observation
                if msg[0] == b'OBSERVE':
                    round_n, observation, signature = loads(msg[1])["round_n"], loads(msg[1])[
                        "observation"], loads(msg[1])["signature"]
                    node_idx = int(sub.get(zmq.IDENTITY).decode())
                    print("OBSERVE: round_n: {}, observation: {}, signature: {}".format(
                        round_n, observation, signature))

                    print("leader round num: ", leader.round_num)
                    if round_n != leader.round_num:
                        print("ERROR: Round number mismatch")
                        return
                    if not (leader.phase == "OBSERVE" or leader.phase == "GRACE"):
                        print("ERROR: Phase should be OBSERVE or GRACE")
                        return
                    try:
                        if leader.observations[node_idx]:
                            print(
                                "ERROR: Observation already received from this node for this round")
                            return
                        print("Inside try")
                    except IndexError:
                        msg_hash = compute_hash_on_elements(
                            [leader.epoch, round_n, observation])
                        if verify(msg_hash, signature[0], signature[1], public_keys[node_idx]):
                            leader.observations.append(
                                (observation, signature, node_idx))

                            if len(leader.observations) == 1:  # TODO: 2*F + 1:
                                if leader.phase != 'OBSERVE':
                                    print('ERROR: Phase must be OBSERVE')
                                    return

                                leader.phase = "GRACE"
                                grace_timer.start()
                                print("Grace Timer started")
                        else:
                            print("ERROR: Signature verification failed")
                # _ !SECTION
                # ? ===========================================================================


if __name__ == "__main__":
    leader_node()
