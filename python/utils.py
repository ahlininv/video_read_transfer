import numpy as np
from itertools import accumulate
import operator
from functools import reduce
import unittest

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

