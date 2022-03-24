import zmq
import sys

# Lowest port number => 5559
PORT_NUM = int(sys.argv[1])

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.bind(f"tcp://*:{PORT_NUM}")

#  Do 10 requests, waiting each time for a response
for request in range(1, 11):
    socket.send(b"Hello")
    message = socket.recv()
    print(f"Received reply {request} [{message}]")
