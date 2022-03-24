import zmq

context = zmq.Context()


socket = context.socket(zmq.PUSH)
socket.bind("tcp://*:5557")

#  Do 10 requests, waiting each time for a response
for request in range(10):
    socket.send(b"test message")

    # #  Get the reply.
    # message = socket.recv()
    # print("Received reply %s [ %s ]" % (request, message))
