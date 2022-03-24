import zmq
import sys

context = zmq.Context()


def f1():

    PORT_NUM = int(sys.argv[1])

    frontend = context.socket(zmq.ROUTER)
    backend = context.socket(zmq.DEALER)
    frontend.connect(f"tcp://localhost:{PORT_NUM}")
    backend.bind(f"tcp://*:{PORT_NUM+1}")

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)

    # Switch messages between sockets
    while True:
        socks = dict(poller.poll())

        if socks.get(frontend) == zmq.POLLIN:
            print("frontend")
            message = frontend.recv_multipart()
            backend.send_multipart(message)

        if socks.get(backend) == zmq.POLLIN:
            print("backend")
            message = backend.recv_multipart()
            frontend.send_multipart(message)


def main():
    while True:
        f1()


if __name__ == "__main__":
    main()
