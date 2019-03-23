import cv2
import numpy as np
import socket
import sys
import pickle
import struct ### new code


def serialize_frame(frame):
    assert(frame is not None)
    assert(np.array_equiv(frame, np.frombuffer(frame.tobytes(), frame.dtype.name, len(frame.tobytes())).reshape(frame.shape)))
    return frame.tobytes()


if __name__ == "__main__":
    # cap=cv2.VideoCapture(0)
    cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")

    clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    clientsocket.connect(('localhost',8089))
    while True:
        ret,frame = cap.read()
        if frame is None:
            break
        data_payload = serialize_frame(frame)
        # print("format of payload: ", type(data_payload))
        # print("frame size ", len(frame))
        # print("data_payload size ", len(data_payload))

        payload_size = len(data_payload) + struct.calcsize("q 3q 10s")
        msg_size = struct.calcsize("q") + payload_size
        # print("msg_size ", msg_size)
        # print("payload_size ", payload_size)
        msg_format = "q 3q 10s %ds" % payload_size
        print("msg_format ", msg_format)
        clientsocket.sendall(struct.pack(msg_format, msg_size, frame.shape[0], frame.shape[1], frame.shape[2], "%10s" % frame.dtype.name, data_payload))
    print("Client finished sending!")
