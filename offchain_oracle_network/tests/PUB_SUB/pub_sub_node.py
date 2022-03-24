#
#  Synchronized publisher
#
from time import sleep
import zmq
import sys
from threading import Thread
from pickle import dumps, loads


PORT_NUM = 5560 + int(sys.argv[1])


def node():
    context = zmq.Context()

    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    starter_subscriber = None
    if int(sys.argv[1]) == 0:
        starter_subscriber = context.socket(zmq.SUB)
        starter_subscriber.connect("tcp://localhost:5559")
        starter_subscriber.setsockopt(zmq.SUBSCRIBE, b"A")
        starter_subscriber.setsockopt(zmq.SUBSCRIBE, b"B")

    subscriptions = []
    for i in range(5):
        sub = context.socket(zmq.SUB)
        sub.connect(f"tcp://localhost:{5560 + i}")
        sub.setsockopt(zmq.SUBSCRIBE, b'A')
        subscriptions.append(sub)

    sleep(1)

    poller = zmq.Poller()
    poller.register(publisher, zmq.POLLIN)
    if starter_subscriber is not None:
        poller.register(starter_subscriber, zmq.POLLIN)
    for sub in subscriptions:
        poller.register(sub, zmq.POLLIN)

    while True:

        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if starter_subscriber in socks:
            msg = starter_subscriber.recv_multipart()
            new_msg = loads(msg[1])
            new_msg["node_idx"] = int(sys.argv[1])
            publisher.send_multipart([b"A", dumps(new_msg)])

        for i, sub in enumerate(subscriptions):

            if sub in socks:
                msg = sub.recv_multipart()
                print(f"msg{i}:    {loads(msg[1])}")
                new_msg = loads(msg[1])
                new_msg["node_idx"] = int(sys.argv[1])
                sleep(1.5)
                publisher.send_multipart([b"A", dumps(new_msg)])
                if msg == b"END":
                    break


if __name__ == "__main__":
    node()
