
# ATTENTION: runnable from python/ and from python/tests/, else cannot find anything.

import numpy as np
from unittest import TestCase
import cv2

try:
    from utils import serialize_frame, deserialize_frame
    from utils import VideoStream
    from utils import VideoScreen
except ModuleNotFoundError:
    from ..utils import serialize_frame, deserialize_frame
    from ..utils import VideoStream
    from ..utils import VideoScreen


import pickle
import struct
import os
from threading import Thread


test_video_path = "test_video.avi"


class TestUtils(TestCase):
    def test_serialize_deserialize3d(self):
        frame = np.array(
            [[[3, 3, 3], [1, 1, 1]], [[3, 3, 3], [1, 1, 1]], [[3, 3, 3], [1, 1, 1]], [[3, 3, 3], [1, 1, 1]]])
        # print("shape:", frame.shape)
        serialized = serialize_frame(frame)
        deserialized = deserialize_frame(serialized, frame.dtype.name, frame.shape[0] * frame.shape[1] * frame.shape[2],
                                         frame.shape)
        # print("serialized:", serialized)
        # print("frame:", frame)
        # print("deserialized:", deserialized)
        assert (np.array_equiv(frame, np.frombuffer(deserialized, frame.dtype.name,
                                                    frame.shape[0] * frame.shape[1] * frame.shape[2]).reshape(frame.shape)))

    def test_serialize_deserialize2d(self):
        frame = np.array([[2, 1], [2, 1], [2, 1], [2, 1]])
        # print("shape:", frame.shape)
        serialized = serialize_frame(frame)
        deserialized = deserialize_frame(serialized, frame.dtype.name, frame.shape[0] * frame.shape[1], frame.shape)
        # print("serialized:", serialized)
        # print("frame:", frame)
        # print("deserialized:", deserialized)
        assert (np.array_equiv(frame, np.frombuffer(deserialized, frame.dtype.name, frame.shape[0] * frame.shape[1]).reshape(frame.shape)))


class TestPackUnpack(TestCase):
    def setUp(self):
        self.cap = cv2.VideoCapture(test_video_path)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(os.path.join("tests", test_video_path))
        if not self.cap.isOpened():
            raise Exception("Cannot open video in %s" % os.path.join(os.path.abspath("."), test_video_path))

    def tearDown(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def test_size_and_data_pickle(self):
        self.assertTrue(self.cap.isOpened())
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if frame is None:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame_to_encode = gray

            frame_bytes = pickle.dumps(frame_to_encode)
            # print("format of payload: ", type(frame_bytes))
            # print("frame1 size ", len(gray))
            # print("frame_bytes size ", len(frame_bytes))

            payload_size = len(frame_bytes)
            msg_size = struct.calcsize("q") + payload_size
            # print("msg_size ", msg_size)
            # print("payload_size ", payload_size)
            msg_format = "q %ds" % payload_size
            # print("msg_format ", msg_format)
            data_to_network = struct.pack(msg_format, msg_size, frame_bytes)

            # Network was here=)
            data_from_network = data_to_network
            packet_stream = data_from_network
            # Network finished here

            header_length = struct.calcsize("q")
            msg_size_subheader_length = struct.calcsize("q")
            msg_size = struct.unpack("q", packet_stream[:msg_size_subheader_length])[0]
            # print("msg_size ", msg_size)
            decode_packet = packet_stream[:msg_size]
            packet_stream = packet_stream[msg_size:]

            # print("msg_size ", msg_size)
            # print("payload_size ", payload_size)

            packet_fmt = "q %ds" % (msg_size - header_length)
            msg_size, frame_bytes = struct.unpack(packet_fmt, decode_packet)
            # print("packet_fmt ", packet_fmt)
            # print("frame size ", len(frame_bytes))
            frame = pickle.loads(frame_bytes)

            self.assertTrue (np.array_equiv(frame, gray))
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            cv2.imshow('frame1', frame)

    def test_size_shape_type_and_data_np_tobytes(self):
        self.assertTrue(self.cap.isOpened())
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if frame is None:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame_to_encode = gray
            encoded_frame_bytes = serialize_frame(frame_to_encode)
            # print("format of payload: ", type(encoded_frame_bytes))
            # print("frame size ", len(frame))
            # print("encoded_frame_bytes size ", len(encoded_frame_bytes))

            encoding_packet_size = len(encoded_frame_bytes) + struct.calcsize("q 3q 10s")
            encoding_frame_bytes_size = len(encoded_frame_bytes)
            # print("encoding_packet_size ", encoding_packet_size)
            # print("encoding_frame_bytes_size ", encoding_frame_bytes_size)
            encoding_packet_fmt = "q 3q 10s %ds" % encoding_frame_bytes_size
            # print("encoding_packet_fmt ", encoding_packet_fmt)
            stream_to_network = struct.pack(encoding_packet_fmt, encoding_packet_size, frame_to_encode.shape[0], frame_to_encode.shape[1],
                                            frame_to_encode.shape[2] if len(frame_to_encode.shape) == 3 else -1, ("%10s" % frame_to_encode.dtype.name).encode('utf-8'),
                                            encoded_frame_bytes)

            # Network was here=)
            stream_from_network = stream_to_network
            packet_stream = stream_from_network
            # Network finished here

            header_length = struct.calcsize("q 3q 10s")
            decode_subhdr_length = struct.calcsize("q")
            decoding_packet_size = struct.unpack("q", packet_stream[:decode_subhdr_length])[0]
            # print("decoding_packet_size ", decoding_packet_size)
            decode_packet = packet_stream[:decoding_packet_size]
            packet_stream = packet_stream[decoding_packet_size:]

            # print("decoding_packet_size ", decoding_packet_size)
            # print("payload_size ", payload_size)

            decoding_frame_bytes_len = decoding_packet_size - header_length
            decoding_packet_fmt = "q 3q 10s %ds" % decoding_frame_bytes_len
            decoding_packet_size, shape0, shape1, shape2, frame_dtype, decoded_frame_bytes = struct.unpack(
                decoding_packet_fmt, decode_packet)
            # print("decoding_packet_fmt ", decoding_packet_fmt)
            # print("frame size ", len(decoded_frame_bytes))
            frame_shape = (shape0, shape1, shape2) if shape2 != -1 else (shape0, shape1)
            decoded_frame = deserialize_frame(decoded_frame_bytes, frame_dtype.decode('utf-8').strip(),
                                              decoding_frame_bytes_len, frame_shape)

            self.assertTrue (np.array_equiv(decoded_frame, gray))
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            cv2.imshow('decoded_frame', decoded_frame)


class TestVideoStream(TestCase):
    def setUp(self):
        path = test_video_path
        if not os.path.exists(path):
            path = os.path.join("tests", path)
        if not os.path.exists(path):
            path = os.path.join("python", path)
        if not os.path.exists(path):
            raise Exception("test video not found. check path and run tests from root of repository, python/, python/tests/")
        self.stream = VideoStream(path)
        self.stream.start()

    def tearDown(self):
        self.stream.stop()

    def test_video_stream(self):
        self.assertTrue(self.stream.started)
        import time
        time.sleep(0.3)
        # self.assertTrue(self.stream.full())
        for i in range(70):
            frame = self.stream.read()
            self.assertTrue(frame is not None)
        self.stream.stop()

    def test_video_stream_video_screen(self):
        screen = VideoScreen()
        screen.set_source(self.stream)

