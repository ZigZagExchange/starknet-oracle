
#
#  Synchronized subscriber
#
import time
import zmq
import sys

# NODE_IDX = int(sys.argv[1])


def main():
    context = zmq.Context()

    # First, connect our subscriber socket
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5563")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"A")

    subscriber2 = context.socket(zmq.SUB)
    subscriber2.connect("tcp://localhost:5561")
    subscriber2.setsockopt(zmq.SUBSCRIBE, b'B')

    time.sleep(1)

    poller = zmq.Poller()
    poller.register(subscriber, zmq.POLLIN)
    poller.register(subscriber2, zmq.POLLIN)

    while True:

        # msg = subscriber.recv_multipart()
        # msg2 = subscriber2.recv_multipart()
        # print(f"msg from:   {msg}")
        # print(f"msg2 from:   {msg2}")

        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if subscriber in socks:
            msg = subscriber.recv_multipart()
            print(f"msg:    {msg}")
            if msg == b"END":
                break

        if subscriber2 in socks:
            msg = subscriber2.recv_multipart()
            print(f"msg2:    {msg}")
            if msg == b"END":
                break


if __name__ == "__main__":
    main()
