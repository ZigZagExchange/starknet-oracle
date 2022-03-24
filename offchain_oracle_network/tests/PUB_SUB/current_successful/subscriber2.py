#
#  Synchronized publisher
#
from time import sleep
import zmq
import sys
from threading import Thread
from pickle import dumps, loads


PORT_NUM = 5563  # + 2*int(sys.argv[1])


def publisher():
    context = zmq.Context()

    # Socket to talk to clients
    publisher = context.socket(zmq.PUB)
    # set SNDHWM, so we don't drop messages for slow subscribers
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    sleep(1)

    for i in range(10):

        publisher.send_multipart(
            [b"B", b"B Option"])
        sleep(1)

    publisher.send(b"END")


def subscriber():
    context = zmq.Context()

    # First, connect our subscriber socket
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5561")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"A")

    # subscriber2 = context.socket(zmq.SUB)
    # subscriber2.connect("tcp://localhost:5563")
    # subscriber2.setsockopt(zmq.SUBSCRIBE, b'B')

    sleep(1)

    poller = zmq.Poller()
    poller.register(subscriber, zmq.POLLIN)
    # poller.register(subscriber2, zmq.POLLIN)

    while True:

        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if subscriber in socks:
            msg = subscriber.recv_multipart()
            print(f"msg:    {loads(msg[1])}")
            if msg == b"END":
                break

        # if subscriber2 in socks:
        #     msg = subscriber2.recv_multipart()
        #     print(f"msg2:    {msg[0]}")
        #     if msg == b"END":
        #         break


if __name__ == "__main__":
    Thread(target=publisher).start()
    Thread(target=subscriber).start()
