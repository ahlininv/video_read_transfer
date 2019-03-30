
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
    tutils = TestUtils()
    tpackunpack = TestPackUnpack()
    tvs = TestVideoStreamToScreen()
    #
    # tutils.setUp()
    # tutils.test_serialize_deserialize2d()
    # tutils.tearDown()
    # tutils.setUp()
    # tutils.test_serialize_deserialize3d()
    # tutils.tearDown()
    # tpackunpack.setUp()
    # tpackunpack.test_size_and_data_pickle()
    # tpackunpack.tearDown()
    # tpackunpack.setUp()
    # tpackunpack.test_size_shape_type_and_data_np_tobytes()
    # tpackunpack.tearDown()

    # tvs.setUp()
    # tvs.test_video_stream_display()
    # tvs.tearDown()

    # fake_stream = FakeVideoSource()
    # packer = NetworkEnoder("packer", fake_stream)
    # packer.start()
    # unpacker = NetworkDecoder("unpacker", packer)
    # unpacker.start()
    # run_video(unpacker)
    a = Connection('localhost', 8089)
    a.connect()
    a.send("hello".encode('utf-8'))
    r = a.receive_packet()
    print("received:", r)
    a.send("fraaaaaaamedata".encode('utf-8'))

