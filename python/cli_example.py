import cv2
import numpy as np
import socket
import sys
import pickle
import struct ### new code
# cap=cv2.VideoCapture(0)
cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")

clientsocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
clientsocket.connect(('localhost',8089))
while True:
    ret,frame=cap.read()
    if not ret:
        break
    data_payload = pickle.dumps(frame) ### new code
    print("format of payload: ", type(data_payload))
    print("frame size ", len(frame))
    print("data_payload size ", len(data_payload))

    payload_size = len(data_payload)
    msg_size = struct.calcsize("q") + payload_size
    print("msg_size ", msg_size)
    print("payload_size ", payload_size)
    msg_format = "q %ds" % payload_size
    print("msg_format ", msg_format)
    clientsocket.sendall(struct.pack(msg_format, msg_size, data_payload))

print("Client finished sending!")