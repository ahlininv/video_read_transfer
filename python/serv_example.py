import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new

HOST=''
PORT=8089



try:
    from .tests.unittests import *
except ModuleNotFoundError:
    from tests.unittests import *
try:
    from .utils import *
except ModuleNotFoundError:
    from utils import *

import os

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print ('Socket created')

    s.bind((HOST,PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn, addr = s.accept()

    data = b""
    payload_size_length = struct.calcsize("q")
    while True:
        data += conn.recv(payload_size_length)
        if len(data) < payload_size_length:
            break
        msg_size = struct.unpack("q", data[:payload_size_length])[0]
        print("msg_size ", msg_size)
        while len(data) < msg_size:
            data += conn.recv(4096)
        payload_data = data[:msg_size]
        data = data[msg_size:]
        #
        print("msg_size ", msg_size)
        #
        # data_format = "q 3q 10s %ds" % (msg_size - payload_size_length)
        # frame_shape = [-1, -1, -1]
        # msg_size, frame_shape[0], frame_shape[1], frame_shape[2], dtype_name, data_payload = struct.unpack(data_format, payload_data)
        # print("data_format ", data_format)
        # print("frame size ", len(data_payload))
        # frame = deserialize_frame(data, dtype_name.decode('utf-8').strip(), msg_size - payload_size_length, tuple(frame_shape))
        #
        # if cv2.waitKey(20) & 0xFF == ord('q'):
        #     break
        # cv2.imshow('frame',frame)
        decoding_packet_size, decoding_packet_num, decoding_frame_bytes_len, frame_shape, frame_dtype, decoded_frame_bytes, \
            decoding_frame_bytes_len = packet_unpack(payload_data)
        decoded_frame = deserialize_frame(decoded_frame_bytes, frame_dtype,
                                          decoding_frame_bytes_len, frame_shape)

        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

        cv2.imshow('decoded_frame', decoded_frame)

    print ("Server finished receiving!")
