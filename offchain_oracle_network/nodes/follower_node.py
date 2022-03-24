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

# TODO: Change constants
F = 0
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
                # SECTION Send Signed OBSERVATION to Leader

                if msg[0] == b'OBSERVE-REQ':
                    print("RECEIVED OBSERVE-REQ")
                    if sub.get(zmq.IDENTITY).decode() != follower.leader_id:
                        print("Message sender should be the leader")
                        return

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

                    if NODE_IDX % 2 == 0:
                        sleep(0.1 * NODE_IDX)
                    sleep(1 + 0.02 * NODE_IDX)
                    publisher.send_multipart(
                        [b'OBSERVE', dumps({"round_n": round_n, "observation": observation, "signature": signature})])

                # _ !SECTION
                # ? ===============================================================
                # SECTION Send Signed REPORT to Leader
                if msg[0] == b'REPORT-REQ':
                    print("RECEIVED REPORT-REQ")
                    if sub.get(zmq.IDENTITY).decode() != follower.leader_id:
                        print("Message sender should be the leader")
                        return

                    round_n, report = loads(
                        msg[1])["round_n"], loads(msg[1])["report"]

                    if round_n != follower.round_num:
                        print("Round number mismatch")
                        return
                    if follower.sentreport:
                        print("Report already sent")
                        return
                    if follower.completedround:
                        print("Round already completed")
                        return

                    if not follower.verify_report_sorted(report):
                        print('ERROR: Report is not sorted')
                        return

                    for i in range(len(report.observations)):
                        msg_hash = compute_hash_on_elements(
                            [follower.epoch, round_n, observation])
                        node_idx = int(report.observers[2+2*i:4+2*i], 16)

                        r_sig, s_sig = report.signatures[i]
                        if not verify(msg_hash, r_sig, s_sig, public_keys[node_idx]):
                            print('ERROR: Signature verification failed')
                            return

                    # TODO: If should_report else complete_round

                    signature = report.sign_report(follower.private_key)

                    sleep(1)
                    follower.sentreport = True
                    publisher.send_multipart(
                        [b'REPORT', dumps({"round_n": round_n, "report": report, "signature": signature})])

                # _ !SECTION
                # ? ===============================================================
                # _ SECTION Receive Final report and send echo to other nodes
                if msg[0] == b'FINAL':
                    print("RECEIVED FINAL")

                    # Where report bundle is (epoch, round_n, report, signatures, signers)
                    round_n, report_bundle = loads(
                        msg[1])["round_n"], loads(msg[1])["report_bundle"]
                    e, r, report, signatures, signers = report_bundle

                    if round_n != follower.round_num or r != follower.round_num:
                        print("Round number mismatch")
                        return
                    if follower.sentecho:
                        print("Echo already sent")
                        return

                    if follower.verify_attested_report(report_bundle):
                        follower.sentecho = report_bundle

                        publisher.send_multipart(
                            [b'FINAL-ECHO', dumps({"round_n": round_n, "report_bundle": report_bundle})])

                # _ !SECTION
                # ? ===============================================================
                 # ? ===============================================================
                # _ SECTION Receive Final echo
                if msg[0] == b'FINAL-ECHO':
                    print("RECEIVED FINAL-ECHO")

                    # Where report bundle is (epoch, round_n, report, signatures, signers)
                    round_n, report_bundle = loads(
                        msg[1])["round_n"], loads(msg[1])["report_bundle"]
                    e, r, report, signatures, signers = report_bundle

                    node_idx = int(sub.get(zmq.IDENTITY).decode())

                    if round_n != follower.round_num or r != follower.round_num:
                        print("Round number mismatch")
                        return
                    if follower.receivedecho[node_idx]:
                        print("ERROR: Already received an echo from this node")
                        return
                    if follower.completedround:
                        print('ERROR: Round has already been completed')

                    if follower.verify_attested_report(report_bundle):
                        follower.receivedecho[node_idx] = True
                        if not follower.sentecho:
                            follower.sentecho = report_bundle
                            publisher.send_multipart(
                                [b'FINAL-ECHO', dumps({"round_n": round_n, "report_bundle": report_bundle})])

                        if follower.count_received_echoes() == 4:  # TODO > F:
                            print("Invoking Transmission")
                            # TODO: Invoke transmit and complete_round
                            follower.complete_round()
                    else:
                        print("Report attestation failed")
                # _ !SECTION
                # ? ===============================================================


if __name__ == "__main__":
    follower_node("0")
