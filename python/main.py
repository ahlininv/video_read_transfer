import cv2
import struct
import numpy as np



# cap = cv2.VideoCapture("rtsp:/admin:12345Admin@172.18.12.127/h264/ch01/main/av_stream")
cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")

if __name__ == "__main__":
    while cap.isOpened():
        ret, frame = cap.read()
        if frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # data_type = frame.dtype.name
        # shape = frame.shape
        # data_str = frame.tobytes()
        # length = len(data_str)
        # print("Send:")
        # print("\tType: ", data_type)
        # print("\tshape: ", shape)
        # print("\tlength: ", length)
        #
        # packed = struct.pack("%ds" % length, data_str)
        # framebytes = struct.unpack("%ds" % length, packed)
        # print("Receive:")
        # print("Length: %d"% len(framebytes))
        # assert(framebytes == data_str)
        # #
        # # print(frame.tobytes())q
        # # print(framebytes)
        # # assert(frame.tobytes() == framebytes)
        # # decoded_frame = np.frombuffer(framebytes, data_type).reshape(shape)
        # # print(decoded_frame)

        cv2.imshow('frame', frame)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
