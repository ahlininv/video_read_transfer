import cv2
import numpy as np
import socket
import sys
import pickle
import struct ### new code



try:
    from .tests.unittests import *
except ModuleNotFoundError:
    from tests.unittests import *
try:
    from .utils import *
except ModuleNotFoundError:
    from utils import *

import os


def serialize_frame(frame):
    assert(frame is not None)
    assert(np.array_equiv(frame, np.frombuffer(frame.tobytes(), frame.dtype.name, len(frame.tobytes())).reshape(frame.shape)))
    return frame.tobytes()


if __name__ == "__main__":
    # cap=cv2.VideoCapture(0)
    # cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")
    cap = cv2.VideoCapture("tests/test_video.avi")

    clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    clientsocket.connect(('localhost',8089))

    #
    # while True:
    #     ret,frame = cap.read()
    #     if frame is None:
    #         break
    #     data_payload = serialize_frame(frame)
    #     # print("format of payload: ", type(data_payload))
    #     # print("frame size ", len(frame))
    #     # print("data_payload size ", len(data_payload))
    #
    #     payload_size = len(data_payload) + struct.calcsize("q 3q 10s")
    #     msg_size = struct.calcsize("q") + payload_size
    #     # print("msg_size ", msg_size)
    #     # print("payload_size ", payload_size)
    #     msg_format = "q 3q 10s %ds" % payload_size
    #     print("msg_format ", msg_format)

    while cap.isOpened():
        ret, frame = cap.read()
        if frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        frame_to_encode = gray
        encoded_frame_bytes = serialize_frame(frame_to_encode)
        stream_to_network = packet_pack(encoded_frame_bytes, frame_to_encode.dtype.name, frame_to_encode.shape)
        sended_size = 0
        packet_size = 10000
        while(sended_size < len(stream_to_network)):
            sended = clientsocket.send(stream_to_network[sended_size:min(sended_size+10000, len(stream_to_network))])
            print("sended: ", sended)
            sended_size += sended
    print("Client finished sending!")
