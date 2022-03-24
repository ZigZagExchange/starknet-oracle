import zmq
import sys

context = zmq.Context()

PORT_NUM = 5559 + int(sys.argv[1])

router = context.socket(zmq.ROUTER)
router.bind("tcp://*:{}".format(PORT_NUM))


for i in range(5):
    msg = router.recv_multipart()
    print(f"Received request: {msg}")
    router.send_multipart(b"Hello")
