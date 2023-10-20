import unittest
from ..lib import manchester_encode, manchester_decode, frame_encode, frame_decode, s8, s16, f88


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
        self.assertRaises(ValueError, manchester_decode, 0xfaaaaaaaaaaaaaaa)
        self.assertRaises(ValueError, manchester_decode, 0x0aaaaaaaaaaaaaaa)


class TestFrame(unittest.TestCase):

    def test_frame_encode(self):
        assert frame_encode(0, 0, 0) == 0x00000000
        assert frame_encode(0xff, 0xff, 0xffff) == 0xffffff0f
        assert frame_encode(0x07, 0xbb, 0x4278) == 0x4278bb0f

    def test_frame_decode(self):
        assert frame_decode(0x00000000) == (0, 0, 0)
        assert frame_decode(0xffffff0f) == (0x07, 0xff, 0xffff)
        assert frame_decode(0x4278bb0f) == (0x07, 0xbb, 0x4278)
        self.assertRaises(ValueError, frame_decode, 0x4278bb0e)

class TestSS2(unittest.TestCase):

    def test_s16(self):
        assert s16(0x0000) == 0x0000
        assert s16(0x7fff) == 0x7fff
        assert s16(0x8000) == -32768
        assert s16(0xffff) == -1
        assert s16(0x1234) == 0x1234
        assert s16(0x4321) == 0x4321
        assert s16(0x5555) == 0x5555
        assert s16(0xaaaa) == -21846
        assert s16(0x7f7f) == 0x7f7f
        assert s16(0x8080) == -32640
        assert s16(0x0101) == 0x0101
        assert s16(0xfeff) == -257
        assert s16(0x7f00) == 0x7f00
        assert s16(0x00ff) == 0x00ff
        assert s16(0x0080) == 128
        assert s16(0xff7f) == -129


class TestS2(unittest.TestCase):

    def test_s8(self):
        assert s8(0x00) == 0
        assert s8(0x7f) == 127
        assert s8(0x80) == -128
        assert s8(0xff) == -1
        assert s8(0x55) == 85
        assert s8(0xaa) == -86

class TestF88(unittest.TestCase):

    def test_f88(self):
        self.assertAlmostEqual(f88(0), 0)
        self.assertAlmostEqual(f88(256), 1)
        self.assertAlmostEqual(f88(512), 2)
        self.assertAlmostEqual(f88(1024), 4)
        self.assertAlmostEqual(f88(2048), 8)
        self.assertAlmostEqual(f88(4095), 15.99609375)
        self.assertAlmostEqual(f88(32768), -128)
        self.assertAlmostEqual(f88(65535), -0.00390625)
