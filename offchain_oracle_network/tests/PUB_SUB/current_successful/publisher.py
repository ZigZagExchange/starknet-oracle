#
#  Synchronized publisher
#
from time import sleep
import zmq
import sys

#  We wait for 10 subscribers
SUBSCRIBERS_EXPECTED = 2

PORT_NUM = 5561 + 2*int(sys.argv[1])


def main():
    context = zmq.Context()

    # Socket to talk to clients
    publisher = context.socket(zmq.PUB)
    # set SNDHWM, so we don't drop messages for slow subscribers
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    # Socket to receive signals
    # syncservice = context.socket(zmq.REP)
    # syncservice.bind("tcp://*:{}".format(PORT_NUM + 1))

    # Get synchronization from subscribers
    # subscribers = 0
    # while subscribers < SUBSCRIBERS_EXPECTED:
    #     # wait for synchronization request
    #     msg = syncservice.recv()
    #     # send synchronization reply
    #     syncservice.send(b'')
    #     subscribers += 1
    #     print(f"+1 subscriber ({subscribers}/{SUBSCRIBERS_EXPECTED})")

    sleep(1)
    # Now broadcast exactly 1M updates followed by END
    for i in range(10):
        # print(f"Message {PORT_NUM}")

        publisher.send_multipart(
            [b"A", b"A Option", bytes.fromhex(hex(PORT_NUM)[2:])])
        publisher.send_multipart(
            [b"B", b"B Option", bytes.fromhex(hex(PORT_NUM)[2:])])
        sleep(0.5)

    publisher.send(b"END")


if __name__ == "__main__":
    main()
