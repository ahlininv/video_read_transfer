
# ATTENTION: runnable from python/ and from python/tests/, else cannot find anything.

import numpy as np
from unittest import TestCase
import cv2
from queue import Queue, Full, Empty  # it's Queue exception

try:
    from utils import *
except ModuleNotFoundError:
    from ..utils import *


import pickle
import struct
import os
from threading import Thread
import time



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
        path = guess_path(test_video_path)
        self.cap = cv2.VideoCapture(path)

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
        num_enc = 0
        num_dec = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if frame is None:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame_to_encode = gray
            encoded_frame_bytes = serialize_frame(frame_to_encode)
            stream_to_network = packet_pack(encoded_frame_bytes, frame_to_encode.dtype.name, frame_to_encode.shape, num_enc)
            num_enc += 1

            # Network was here=)
            stream_from_network = stream_to_network
            packet_stream = stream_from_network
            # Network finished here

            decoding_packet_size, num_dec, decoding_frame_bytes_len, frame_shape, frame_dtype, decoded_frame_bytes, \
                decoding_frame_bytes_len = packet_unpack(packet_stream)
            decoded_frame = deserialize_frame(decoded_frame_bytes, frame_dtype,
                                              decoding_frame_bytes_len, frame_shape)

            self.assertTrue (np.array_equiv(decoded_frame, gray))
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

            cv2.imshow('decoded_frame', decoded_frame)


class TestVideoStream(TestCase):
    def setUp(self):
        path = guess_path(test_video_path)
        self.stream = VideoStream(path, "VideoStream")
        self.stream.start()

    def tearDown(self):
        self.stream.stop()

    def test_video_stream(self):
        self.assertTrue(self.stream.isOpened())
        for i in range(50):  # there are more than 25 good frames in that video test_video.avi, all of them must be read
            ret, frame = self.stream.read()
            if i < 20:
                self.assertTrue(ret)
            if not ret:
                self.assertTrue(frame is None)
                break
        self.stream.stop()


class TestVideoCaptureToScreen(TestCase):
    def setUp(self):
        path = guess_path(test_video_path)
        if not os.path.exists(path):
            raise Exception(
                "test video not found. check path and run tests from root of repository, python/, python/tests/")
        self.stream = cv2.VideoCapture(path)

    def tearDown(self):
        pass

    def test_cv2_display(self):
        run_video(self.stream)

    def test_cv2_videostream_display(self):
        run_video(self.stream)


class FakeVideoSource():
    def __init__(self):
        self.frame_n = 0
        self.frame = np.array([[[1, 1, 1], [2, 2, 2]], [[1, 1, 1], [2, 2, 2]], [[1, 1, 1], [2, 2, 2]]], dtype=np.uint8)

    def isOpened(self):
        return True

    def read(self):
        self.frame_n += 1
        if self.frame_n < 100:
            return True, self.frame
        else:
            return False, None

    def release(self):
        pass



class TestVideoStreamToScreen(TestCase):
    def setUp(self):
        path = guess_path(test_video_path)
        if not os.path.exists(path):
            raise Exception(
                "test video not found. check path and run tests from root of repository, python/, python/tests/")
        self.stream = VideoStream(path, "VideoStream", 10)
        self.stream.start()

    def tearDown(self):
        self.stream.stop()

    def test_video_stream_display(self):
        run_video(self.stream)


    def test_video_stream_serial_deserial_display(self):
        packer = NetworkEnoder("packer", self.stream)
        packer.start()
        unpacker = NetworkDecoder("unpacker", packer)
        unpacker.start()
        run_video(unpacker)

    def video_server_thread_func(self):
        # single_thread_server.py
        server = Server('localhost', 8089)
        print("1", threading.enumerate())
        server_thread = threading.Thread(target=server.server_run)
        server_thread.start()
        print("2", threading.enumerate())
        while True:
            with server.server_connections_lock:
                for conn in server.server_connections:
                    print("conn ", conn)
                    if not conn.working:
                        conn.join()
                        print("Finished monothread receiving ", conn)
                        server.server_connections.remove(conn)
                        return
            with server.server_connections_lock:
                if server.server_connections:
                    receiver = server.server_connections[0]
                    print("server_connections connections")
                    unpacker = NetworkDecoder("unpacker", receiver)
                    unpacker.start()
                    run_video(unpacker)

    def video_client_thread_func(self):
        # single_thread_client.py
        # stream = FakeVideoSource()
        stream = VideoStream("tests/test_video.avi", "videostream")
        stream.start()
        packer = NetworkEnoder("packer", stream)
        packer.start()
        a = NetworkSender("sender", 'localhost', 8089, packer)
        a.start()

    # def test_video_stream_with_network_monothread(self):
    #     thread_server = Thread(target=self.video_server_thread_func)
    #     thread_client = Thread(target=self.video_client_thread_func)
    #
    #     thread_server.start()
    #     thread_client.start()
    #     thread_client.join(10)
    #     thread_server.join(10)








