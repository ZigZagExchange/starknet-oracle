#
#  Synchronized publisher
#
from time import sleep
import zmq
import sys
from threading import Thread
from pickle import dumps, loads


PORT_NUM = 5559


def publisher():
    context = zmq.Context()

    publisher = context.socket(zmq.PUB)
    publisher.sndhwm = 1100000
    publisher.bind("tcp://*:{}".format(PORT_NUM))

    sleep(1)

    for i in range(1):

        # obj = {"name": "abc", "list": [
        #     1, 2, 3, 4, 5], "dict": {"a": 1, "b": 2}}
        obj = {"name": "abc"}

        x = zmq.Frame(dumps(obj))

        publisher.send_multipart([b"B", x.bytes])

        sleep(5)

    # publisher.send(b"END")


if __name__ == "__main__":
    Thread(target=publisher).start()
