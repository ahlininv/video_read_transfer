import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new

HOST=''
PORT=8089


def deserialize_frame(frame_bytes, dtype_name, frame_bytes_len, shape):
    assert(isinstance(frame_bytes, bytes))
    assert(isinstance(dtype_name, str))
    assert(isinstance(frame_bytes_len, int))
    assert(isinstance(shape, tuple))
    return np.frombuffer(frame_bytes, dtype_name, frame_bytes_len).reshape(shape)


if __name__ == "__main__":
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print ('Socket created')

    s.bind((HOST,PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn,addr=s.accept()

    data = b""
    payload_size_length = struct.calcsize("q 3q 10s")
    while True:
        data += conn.recv(payload_size_length)
        if not data:
            break
        msg_size = struct.unpack("q", data[:payload_size_length])[0]
        # print("msg_size ", msg_size)
        while len(data) < msg_size:
            data += conn.recv(4096)
        payload_data = data[:msg_size]
        data = data[msg_size:]

        print("msg_size ", msg_size)
        # print("payload_size ", payload_size)

        data_format = "q 3q 10s %ds" % (msg_size - payload_size_length)
        frame_shape = [-1, -1, -1]
        msg_size, frame_shape[0], frame_shape[1], frame_shape[2], dtype_name, data_payload = struct.unpack(data_format, payload_data)
        # print("data_format ", data_format)
        # print("frame size ", len(data_payload))
        frame = deserialize_frame(data, dtype_name, msg_size - payload_size_length, tuple(frame_shape))

        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
        cv2.imshow('frame',frame)

    print ("Server finished receiving!")