
import zmq
import sys

# Highest port number => 5562*
PORT_NUM = int(sys.argv[1])

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect(f"tcp://localhost:{PORT_NUM}")

while True:
    message = socket.recv()
    print(f"Received request: {message}")
    socket.send(b"World")
