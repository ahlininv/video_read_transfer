import numpy as np
from itertools import accumulate
import operator
from functools import reduce
import unittest
import cv2
from queue import Queue, Full, Empty  # it's Queue exception
from threading import Condition, RLock, Lock, Thread
import threading
import abc
import struct
import os
from collections import deque
import socket
import time


def empty_locked(queue, queue_guard):
    assert (queue_guard.locked())
    return len(queue) == 0


def size_locked(queue, queue_guard):
    assert (queue_guard.locked())
    return len(queue)


def pop_front(queue, queue_guard):
    assert (queue_guard.locked())
    return queue.popleft()


def push_back(queue, queue_guard, frame):
    assert (queue_guard.locked())
    return queue.append(frame)


def deserialize_frame(frame_bytes, dtype_name, frame_bytes_len, shape):
    assert(isinstance(frame_bytes, bytes))
    assert(isinstance(dtype_name, str))
    assert(isinstance(frame_bytes_len, int))
    assert(isinstance(shape, tuple))
    shape_in_use = shape if len(shape) == 3 else (shape[0], shape[1])
    return np.frombuffer(frame_bytes, dtype_name, frame_bytes_len).reshape(shape_in_use)


def serialize_frame(frame):
    assert(frame is not None)
    a2 = np.frombuffer(frame.tobytes(), frame.dtype.name, reduce(lambda x, y: x * y, frame.shape))
    assert(np.array_equiv(frame, a2.reshape(frame.shape)))
    return frame.tobytes()


def packet_pack(frame_bytes, dtype_name, shape, packet_num):
    packet_size = len(frame_bytes) + struct.calcsize("q q 3q 10s")
    encoding_frame_bytes_size = len(frame_bytes)
    encoding_packet_fmt = "q q 3q 10s %ds" % encoding_frame_bytes_size
    stream_to_network = struct.pack(encoding_packet_fmt, packet_size, packet_num, shape[0],
                                    shape[1],
                                    shape[2] if len(shape) == 3 else -1,
                                    ("%10s" % dtype_name).encode('utf-8'),
                                    frame_bytes)
    return stream_to_network


def packet_unpack(packet_stream):
    header_length = struct.calcsize("q q 3q 10s")
    assert len(packet_stream) > header_length
    subheader_length = struct.calcsize("q")
    subheader = packet_stream[:subheader_length]
    packet_size, = struct.unpack("q", subheader)
    decode_packet = packet_stream[:packet_size]
    packet_stream = packet_stream[packet_size:]

    frame_bytes_len = packet_size - header_length
    packet_fmt = "q q 3q 10s %ds" % frame_bytes_len
    packet_size, packet_num, shape0, shape1, shape2, frame_dtype, frame_bytes = \
        struct.unpack(packet_fmt, decode_packet)
    frame_shape = (shape0, shape1, shape2) if shape2 != -1 else (shape0, shape1)
    frame_dtype = frame_dtype.decode('utf-8').strip()
    return packet_size, packet_num, frame_bytes_len, frame_shape, frame_dtype, frame_bytes, frame_bytes_len


def guess_path(path):
    if not os.path.exists(path):
        path = os.path.join("tests", path)
    if not os.path.exists(path):
        path = os.path.join("python", path)
    if not os.path.exists(path):
        raise Exception(
            "test video not found. check path and run tests from root of repository, python/, python/tests/")
    return path


class ThreadWorker(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.working_guard = Lock()
        self.working = False
        self.name = name
        self.thread = None
        self.it = 0

    def started(self):
        with self.working_guard:
            busy = self.working
        return busy

    def worker_thread(self):
        while True:
            with self.working_guard:
                if not self.working:
                    break
            self.it += 1
            self.work_iteration()

    def start(self):
        with self.working_guard:
            self.working = True
            print(self.name + " started")
            self.thread = Thread(target=self.worker_thread)
            self.thread.start()

    def stop(self):
        with self.working_guard:
            self.working = False
            print("stopping thread ", self.thread.name)

    def join(self):
        assert threading.current_thread().name != self.thread.name
        self.thread.join()

    def release(self):
        pass

    def isOpened(self):
        return True

    @abc.abstractmethod
    def work_iteration(self):
        pass


class Producer:
    def __init__(self, queue_size=20):
        self.out_elems_lock = Lock()
        self.max_deque_size = queue_size
        self.out_queues = deque()

    def read(self):
        with self.out_elems_lock:
            if not empty_locked(self.out_queues, self.out_elems_lock):
                frame = pop_front(self.out_queues, self.out_elems_lock)
            else:
                return True, None  # means empty (we added this case to interface)
        if frame is None:
            return False, None  # video is over (do as cv2.VideoCapture)
        return True, frame  # normal frame (do as cv2.VideoCapture)


class VideoStream(ThreadWorker):
    def __init__(self, path, name, queue_size=20):
        ThreadWorker.__init__(self, name)
        self.producer = Producer(queue_size)
        self.source = cv2.VideoCapture(path)

    def work_iteration(self):
        with self.producer.out_elems_lock:
            if size_locked(self.producer.out_queues, self.producer.out_elems_lock) == self.producer.max_deque_size:
                return
            ret, frame = self.source.read()
            # print(self.name, " ", (ret, frame is not None))
            if not ret and frame is None:  # end of video
                push_back(self.producer.out_queues, self.producer.out_elems_lock, None)  # to flush all threads, too
                self.stop()
                return

            if frame is None:  # True, None --> empty queue, try again
                return
            # print(self.name, "+")
            push_back(self.producer.out_queues, self.producer.out_elems_lock, frame)  # True, frame is not None: normal frame

    def read(self):
        return self.producer.read()


class StreamProcessor(ThreadWorker, metaclass=abc.ABCMeta):
    def __init__(self, name, source=None, max_queue_size=20):
        ThreadWorker.__init__(self, name)
        self.producer = Producer(max_queue_size)
        self.source = source
        # self.pr_i = 0

    def read(self):
        return self.producer.read()

    def subscribe(self, source):
        assert(isinstance(source, Producer))
        self.source = source

    def unsubscribe(self, source_name):
        if self.source.name == source_name:
            self.source = None

    def work_iteration(self):
        assert self.source , "worker withour source"
        with self.producer.out_elems_lock:
            if size_locked(self.producer.out_queues, self.producer.out_elems_lock) == self.producer.max_deque_size:
                return
            ret, frame = self.source.read()
            # self.pr_i += 1
            # print(self.name, " ", (ret, frame is not None), ", frame ", self.pr_i)
            if not ret and frame is None:  # end of video
                push_back(self.producer.out_queues, self.producer.out_elems_lock, None)  # to flush all threads, too
                self.stop()
                return

            if frame is None:  # True, None --> empty queue, try again
                # print(self.name, "-", end=",")
                return

            if self.process is not None:
                frame = self.process(frame)

            push_back(self.producer.out_queues, self.producer.out_elems_lock, frame)  # True, frame is not None: normal frame

    @abc.abstractmethod
    def process(self, input_data):
        pass


class NetworkEnoder(StreamProcessor):
    def __init__(self, name, source=None):
        StreamProcessor.__init__(self, name, source)
        self.packet_num = 0

    def process(self, frame_to_encode):
        assert frame_to_encode is not None
        encoded_frame_bytes = serialize_frame(frame_to_encode)
        stream_to_network = packet_pack(encoded_frame_bytes, frame_to_encode.dtype.name, frame_to_encode.shape, self.packet_num)
        self.packet_num += 1
        return stream_to_network


class NetworkDecoder(StreamProcessor):
    def __init__(self, name, source=None):
        StreamProcessor.__init__(self, name, source)
        print("Network_decoder created")

    def process(self, packet_stream):
        # print("process")
        assert packet_stream is not None
        decoding_packet_size, decoding_packet_num, decoding_frame_bytes_len, frame_shape, frame_dtype, decoded_frame_bytes, \
            decoding_frame_bytes_len = packet_unpack(packet_stream)
        decoded_frame = deserialize_frame(decoded_frame_bytes, frame_dtype,
                                          decoding_frame_bytes_len, frame_shape)
        print("deoded " , decoding_packet_num, "th packet")
        return decoded_frame


class Connection:
    def __init__(self, ip, port, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            print("sock manually set")
            self.sock = sock
        self.ip = ip
        self.port = port
        self.connected = False
        self.max_attempts_connect = 100
        self.timeout_small = 1
        self.server_connections_lock = Lock()
        self.server_connections = []
        self.data_stream = b""

    def connect(self):
        for i in range(self.max_attempts_connect):
            try:
                self.sock.connect((self.ip, self.port))
                break
            except Exception as e:
                print(e)
                time.sleep(self.timeout_small)
        self.connected = True

    def send(self, data_bytes):
        sended_size = 0
        packet_size = 10000
        while(sended_size < len(data_bytes)):
            sended = self.sock.send(data_bytes[sended_size:min(sended_size+10000, len(data_bytes))])
            # print("sended: ", sended)
            sended_size += sended
        print("Frame sended, size ", len(data_bytes))

    def receive_packet(self):
        """
        Receives bytes(for packets with packet size in header) from socket.
        Returns None when there is no packet header
        Returns data if there is header and all packet data. Pops this data from common stream.
        """
        payload_size_length = struct.calcsize("q")
        # Receive header
        while len(self.data_stream) < payload_size_length:
            print("receive header", end=",")
            received_bytes = self.sock.recv(payload_size_length)
            # print((self.name if self.name else "Connection") + " receive now ", len(received_bytes), " bytes ",  self.sock)
            if not len(received_bytes):
                if len(self.data_stream) == 0:
                    print("Finished transmitting. All's ok")
                    return None
                print(self.name + ": bad packet. Header incomplete.")
                return None
            self.data_stream += received_bytes
            # print("receive now ok")

        packet_size = struct.unpack("q", self.data_stream[:payload_size_length])[0]
        # print("msg_size ", packet_size)

        # receive body of packet
        while len(self.data_stream) < packet_size:
            # print("continue receiving now")
            received_bytes = self.sock.recv(4096)
            if not received_bytes:
                print("packet incomplete")
                break
            self.data_stream += received_bytes
        # print("packet received, size ", packet_size)
        payload_data = self.data_stream[:packet_size]
        self.data_stream = self.data_stream[packet_size:]
        return payload_data

    def server_run(self):
        print("server run on ", self.ip, ":", self.port)
        self.sock.bind((self.ip, self.port))
        print('Socket bind complete')
        self.sock.listen(10)
        print('Socket now listening')

        while True:
            conn, addr = self.sock.accept()
            print("conn:", conn)
            print("addr:", addr)
            new_connection = NetworkReceiver("Conn%d" % len(self.server_connections), addr[0], addr[1], None, conn)
            with self.server_connections_lock:
                self.server_connections.append(new_connection)
            new_connection.start()


class Server(Connection):
    def __init__(self, ip, port):
        Connection.__init__(self, ip, port)


class NetworkSender(ThreadWorker, Connection):
    def __init__(self, name, ip, port, source=None, sock=None):
        ThreadWorker.__init__(self, name)
        Connection.__init__(self, ip, port, sock)
        if source is not None:
            self.subscribe(source)
        self.connect()

    def subscribe(self, source):
        # assert isinstance(source, Producer)
        self.__source = source

    def work_iteration(self):
        ret, frame = self.__source.read()
        # print(self.name, " ", (ret, frame is not None))
        if not ret and frame is None:  # end of video
            self.stop()
            return

        if frame is None:  # True, None --> empty queue, try again
            return

        # True, frame is not None: normal frame. Send it.
        if not self.connected:
            return

        # print("send")
        self.send(frame)


class NetworkReceiver(ThreadWorker, Connection):
    def __init__(self, name, ip, port, source=None, sock=None):
        print("NetworkReceiver running")
        ThreadWorker.__init__(self, name)
        self.producer = Producer(100000)  # very much, this class cannot wait.
        Connection.__init__(self, ip, port, sock)
        if source is not None:
            self.subscribe(source)

    def subscribe(self, source):
        # assert isinstance(source, Producer)
        self.source = source

    def work_iteration(self):
        frame_bytes = self.receive_packet()
        if not frame_bytes:
            self.stop()
            with self.producer.out_elems_lock:
                push_back(self.producer.out_queues, self.producer.out_elems_lock, None)
        with self.producer.out_elems_lock:
            if False:  # todo later!!! size_locked(self.frames, self.out_elems_lock) == self.max_deque_size:
                return
            push_back(self.producer.out_queues, self.producer.out_elems_lock, frame_bytes)

    def read(self):
        return self.producer.read()


class Muxer(StreamProcessor):
    pass


def run_video(source):
    assert source.isOpened()
    n = 0
    while source.isOpened():
        ret, frame = source.read()
        n += 1
        print("read ", (ret, frame is not None), ", n = ", n)
        if ret and frame is None:
                continue
        if not ret and frame is None:
                break
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        cv2.imshow('frame', frame)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
    source.release()
    cv2.destroyAllWindows()
