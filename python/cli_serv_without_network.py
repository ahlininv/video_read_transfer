
try:
    from .tests.unittests import TestPackUnpack
except ModuleNotFoundError:
    from tests.unittests import TestPackUnpack
try:
    from .tests.unittests import TestUtils
except ModuleNotFoundError:
    from tests.unittests import TestUtils


if __name__ == "__main__":
    tutils = TestUtils()
    tpackunpack = TestPackUnpack()

    tutils.test_serialize_deserialize2d()
    tutils.test_serialize_deserialize3d()
    tpackunpack.test_size_and_data_pickle()
    tpackunpack.test_size_shape_type_and_data_np_tobytes()
