import socket
import sys
import cv2
import pickle
import numpy as np
import struct ## new

HOST=''
PORT=8089

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print ('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()

### new
data = b""
payload_size_length = struct.calcsize("q")
while True:
    data += conn.recv(payload_size_length)
    if not data:
        break
    msg_size = struct.unpack("q", data[:payload_size_length])[0]
    print("msg_size ", msg_size)
    while len(data) < msg_size:
        data += conn.recv(4096)
    payload_data = data[:msg_size]
    data = data[msg_size:]
    data_format = "q %ds" % (msg_size - payload_size_length)
    data_unpacked = struct.unpack(data_format, payload_data)
    data_payload = data_unpacked[1]
    print("data_format ", data_format)
    print("frame size ", len(data_payload))
    frame = pickle.loads(data_payload)

    if cv2.waitKey(20) & 0xFF == ord('q'):
        break
    cv2.imshow('frame',frame)

print ("Server finished receiving!")