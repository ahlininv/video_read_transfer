import cv2
import numpy as np
import socket
import sys
import pickle
import struct ### new code
# cap=cv2.VideoCapture(0)
cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")

if __name__ == "__main__":
    while cap.isOpened():
        ret, frame = cap.read()
        if frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        data_payload = pickle.dumps(gray) ### new code
        print("format of payload: ", type(data_payload))
        print("frame1 size ", len(gray))
        print("data_payload size ", len(data_payload))

        payload_size = len(data_payload)
        msg_size = struct.calcsize("q") + payload_size
        print("msg_size ", msg_size)
        print("payload_size ", payload_size)
        msg_format = "q %ds" % payload_size
        print("msg_format ", msg_format)
        data_to_network = struct.pack(msg_format, msg_size, data_payload)

        # Network was here=)
        data_from_network = data_to_network
        data = data_from_network
        payload_size_length = struct.calcsize("q")
        if not data:
            break
        msg_size = struct.unpack("q", data[:payload_size_length])[0]
        print("msg_size ", msg_size)
        payload_data = data[:msg_size]
        data = data[msg_size:]
        data_format = "q %ds" % (msg_size - payload_size_length)
        data_unpacked = struct.unpack(data_format, payload_data)
        data_payload = data_unpacked[1]
        print("data_format ", data_format)
        print("frame size ", len(data_payload))
        frame = pickle.loads(data_payload)
        assert(np.array_equiv(frame, gray))
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

        cv2.imshow('frame1', frame)
    cap.release()
    cv2.destroyAllWindows()
