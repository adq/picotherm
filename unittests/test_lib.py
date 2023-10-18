import unittest
from ..lib import manchester_encode, manchester_decode, frame_encode, frame_decode


class TestManchester(unittest.TestCase):

    def test_manchester_encode(self):
        assert manchester_encode(0x00000000) == 0x5555555555555555
        assert manchester_encode(0xFFFFFFFF) == 0xaaaaaaaaaaaaaaaa
        assert manchester_encode(0xAAAAAAAA) == 0x9999999999999999
        assert manchester_encode(0x55555555) == 0x6666666666666666
        assert manchester_encode(0x12345678) == 0x56595a6566696a95

    def test_manchester_decode(self):
        assert manchester_decode(0x5555555555555555) == 0x00000000
        assert manchester_decode(0xaaaaaaaaaaaaaaaa) == 0xFFFFFFFF
        assert manchester_decode(0x9999999999999999) == 0xAAAAAAAA
        assert manchester_decode(0x6666666666666666) == 0x55555555
        assert manchester_decode(0x56595a6566696a95) == 0x12345678


class TestFrame(unittest.TestCase):

    def test_frame_encode(self):
        assert frame_encode(0, 0, 0) == 0x00000000
        assert frame_encode(0xff, 0xff, 0xffff) == 0xffffff0f
        assert frame_encode(0x07, 0xbb, 0x4278) == 0x4278bb0f

    def test_frame_decode(self):
        assert frame_decode(0x00000000) == (0, 0, 0)
        assert frame_decode(0xffffff0f) == (0x07, 0xff, 0xffff)
        assert frame_decode(0x4278bb0f) == (0x07, 0xbb, 0x4278)
