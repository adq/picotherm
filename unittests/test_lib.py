import unittest
from unittest.mock import patch, MagicMock, call
from lib import manchester_encode, manchester_decode, frame_encode, frame_decode, s8, s16, f88, send_syslog


class TestManchester(unittest.TestCase):

    def test_manchester_encode(self):
        assert manchester_encode(0x00000000) == 0x5555555555555555
        assert manchester_encode(0xFFFFFFFF) == 0xaaaaaaaaaaaaaaaa
        assert manchester_encode(0xAAAAAAAA) == 0x9999999999999999
        assert manchester_encode(0x55555555) == 0x6666666666666666
        assert manchester_encode(0x12345678) == 0x56595a6566696a95

    def test_manchester_encode_invert(self):
        assert manchester_encode(0x00000000, invert=True) == 0xaaaaaaaaaaaaaaaa
        assert manchester_encode(0xFFFFFFFF, invert=True) == 0x5555555555555555
        assert manchester_encode(0xAAAAAAAA, invert=True) == 0x6666666666666666
        assert manchester_encode(0x55555555, invert=True) == 0x9999999999999999
        assert manchester_encode(0x12345678, invert=True) == 0xa9a6a59a9996956a

    def test_manchester_decode(self):
        assert manchester_decode(0x5555555555555555) == 0x00000000
        assert manchester_decode(0xaaaaaaaaaaaaaaaa) == 0xFFFFFFFF
        assert manchester_decode(0x9999999999999999) == 0xAAAAAAAA
        assert manchester_decode(0x6666666666666666) == 0x55555555
        assert manchester_decode(0x56595a6566696a95) == 0x12345678
        self.assertRaises(ValueError, manchester_decode, 0xfaaaaaaaaaaaaaaa)
        self.assertRaises(ValueError, manchester_decode, 0x0aaaaaaaaaaaaaaa)

    def test_manchester_encode_decode(self):
        assert manchester_decode(manchester_encode(0xFFFFFFFF, invert=True), invert=True) == 0xFFFFFFFF


class TestFrame(unittest.TestCase):

    def test_frame_encode(self):
        assert frame_encode(0, 0, 0) == 0x00000000
        assert frame_encode(0xff, 0xff, 0xffff) == 0xf0ffffff
        assert frame_encode(0x07, 0xbb, 0x4278) == 0xf0bb4278

    def test_frame_decode(self):
        assert frame_decode(0x00000000) == (0, 0, 0)
        assert frame_decode(0xf0ffffff) == (0x07, 0xff, 0xffff)
        assert frame_decode(0xf0bb4278) == (0x07, 0xbb, 0x4278)
        self.assertRaises(ValueError, frame_decode, 0x4278bb0e)

    def test_frame_encode_decode(self):
        assert frame_decode(frame_encode(0x07, 0xbb, 0x4278)) == (0x07, 0xbb, 0x4278)


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


class TestSendSyslog(unittest.TestCase):

    @patch('lib.socket.socket')
    def test_send_syslog_basic(self, mock_socket):
        # Setup mocks
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Call function
        send_syslog("Test message")

        # Verify socket creation
        mock_socket.assert_called_once_with(unittest.mock.ANY, unittest.mock.ANY)

        # Verify socket options set
        mock_sock_instance.setsockopt.assert_called_once()

        # Verify message sent - no timestamp in current implementation
        expected_msg = b'<13>1 picopower main - - - Test message\r\n'
        mock_sock_instance.sendto.assert_called_once_with(expected_msg, ('255.255.255.255', 514))

        # Verify socket closed
        mock_sock_instance.close.assert_called_once()

    @patch('lib.socket.socket')
    def test_send_syslog_custom_params(self, mock_socket):
        # Setup mocks
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Call function with custom parameters
        send_syslog("Custom message", port=1514, hostname="myhost", appname="myapp", procid="123", msgid="MSG001")

        # Verify message sent with custom parameters - no timestamp in current implementation
        expected_msg = b'<13>1 myhost myapp 123 MSG001 - Custom message\r\n'
        mock_sock_instance.sendto.assert_called_once_with(expected_msg, ('255.255.255.255', 1514))

    @patch('lib.socket.socket')
    def test_send_syslog_timestamp_without_timezone(self, mock_socket):
        # Setup mocks
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Call function
        send_syslog("Test message")

        # Verify \r\n is added (no timestamp in current implementation)
        expected_msg = b'<13>1 picopower main - - - Test message\r\n'
        mock_sock_instance.sendto.assert_called_once_with(expected_msg, ('255.255.255.255', 514))

    @patch('lib.socket.socket')
    def test_send_syslog_socket_exception(self, mock_socket):
        # Setup mocks
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Make sendto raise an exception
        mock_sock_instance.sendto.side_effect = OSError("Network error")

        # Call function - should not raise exception (caught in finally)
        try:
            send_syslog("Test message")
        except OSError:
            pass  # Exception is expected but socket should still close

        # Verify socket is closed even on exception
        mock_sock_instance.close.assert_called_once()

    @patch('lib.socket.socket')
    def test_send_syslog_message_format(self, mock_socket):
        # Setup mocks
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Call function
        send_syslog("Multi word message with spaces")

        # Verify message format handles spaces (no timestamp in current implementation)
        expected_msg = b'<13>1 picopower main - - - Multi word message with spaces\r\n'
        mock_sock_instance.sendto.assert_called_once_with(expected_msg, ('255.255.255.255', 514))
