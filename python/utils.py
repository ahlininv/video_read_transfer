import numpy as np
from itertools import accumulate
import operator
from functools import reduce
import unittest
import cv2
from queue import Queue
from queue import Full  # it's Queue exception
from threading import Condition, RLock, Thread
import abc


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


class ThreadWorker(metaclass=abc.ABCMeta):
    def __init__(self):
        self.working_guard = RLock()
        self.working = False

    def started(self):
        with self.working_guard:
            return self.working

    def worker_thread(self):
        while True:
            with self.working_guard:
                if not self.working:
                    break
            self.work_iteration()

    def start(self):
        with self.working_guard:
            self.working = True
            self.thread = Thread(target=self.worker_thread)
            self.thread.start()

    def stop(self):
        with self.working_guard:
            self.working = False

    @abc.abstractmethod
    def work_iteration(self):
        pass


class FramesProducer:
    def __init__(self, queue_size):
        self.queue_cv = Condition()
        self.max_deque_size = queue_size
        self.read_frames_queue = Queue(self.max_deque_size)

    def read(self):  # we use notify(1 by default), so there's no other reader that could see queue empty.
        with self.queue_cv:
            while self.read_frames_queue.empty():
                self.queue_cv.wait()
            return self.read_frames_queue.get()


class VideoStream(ThreadWorker, FramesProducer):
    def __init__(self, path, queue_size=50):
        ThreadWorker.__init__(self)
        FramesProducer.__init__(self, queue_size)
        self.source = cv2.VideoCapture(path)

    def full(self):
        return self.read_frames_queue.full()

    def __del__(self):
        self.source.release()

    def work_iteration(self):
        assert(self.source.isOpened())
        if not self.read_frames_queue.full():
            try:
                with self.queue_cv:
                    self.read_frames_queue.put(self.source.read(), block=True)
                    self.queue_cv.notify()
            except Full as e:
                pass


# for 2 streams of sending
def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    iterators = deque(map(iter, iterables))
    while iterators:
        try:
            while True:
                yield next(iterators[0])
                iterators.rotate(-1)
        except StopIteration:
            # Remove an exhausted iterator.
            iterators.popleft()