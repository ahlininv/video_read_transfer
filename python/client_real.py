
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
    # fake_stream = FakeVideoSource()
    fake_stream = VideoStream("tests/test_video.avi", "videostream")
    fake_stream.start()
    packer = NetworkEnoder("packer", fake_stream)
    packer.start()
    a = NetworkSender("sender", 'localhost', 8089, packer)
    a.start()
    #

