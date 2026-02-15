import unittest
from unittest.mock import MagicMock, patch, call
import struct
from umqtt.simple import MQTTClient, MQTTException
from umqtt.robust import MQTTClient as RobustMQTTClient


class TestMQTTClientInit(unittest.TestCase):
    def test_init_defaults(self):
        client = MQTTClient("test_client", "test.server.com")
        self.assertEqual(client.client_id, "test_client")
        self.assertEqual(client.server, "test.server.com")
        self.assertEqual(client.port, 1883)
        self.assertIsNone(client.sock)
        self.assertIsNone(client.cb)
        self.assertEqual(client.keepalive, 0)

    def test_init_with_ssl(self):
        client = MQTTClient("test_client", "test.server.com", ssl=True)
        self.assertEqual(client.port, 8883)
        self.assertTrue(client.ssl)

    def test_init_with_custom_port(self):
        client = MQTTClient("test_client", "test.server.com", port=1234)
        self.assertEqual(client.port, 1234)

    def test_init_with_auth(self):
        client = MQTTClient("test_client", "test.server.com", user="user1", password="pass123")
        self.assertEqual(client.user, "user1")
        self.assertEqual(client.pswd, "pass123")

    def test_init_with_keepalive(self):
        client = MQTTClient("test_client", "test.server.com", keepalive=60)
        self.assertEqual(client.keepalive, 60)


class TestMQTTClientSetCallback(unittest.TestCase):
    def test_set_callback(self):
        client = MQTTClient("test_client", "test.server.com")
        callback = MagicMock()
        client.set_callback(callback)
        self.assertEqual(client.cb, callback)


class TestMQTTClientSetLastWill(unittest.TestCase):
    def test_set_last_will_basic(self):
        client = MQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", "offline")
        self.assertEqual(client.lw_topic, "status/test")
        self.assertEqual(client.lw_msg, "offline")
        self.assertEqual(client.lw_qos, 0)
        self.assertFalse(client.lw_retain)

    def test_set_last_will_with_qos(self):
        client = MQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", "offline", qos=1)
        self.assertEqual(client.lw_qos, 1)

    def test_set_last_will_with_retain(self):
        client = MQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", "offline", retain=True)
        self.assertTrue(client.lw_retain)

    def test_set_last_will_invalid_qos(self):
        client = MQTTClient("test_client", "test.server.com")
        with self.assertRaises(ValueError):
            client.set_last_will("status/test", "offline", qos=3)

    def test_set_last_will_empty_topic(self):
        client = MQTTClient("test_client", "test.server.com")
        with self.assertRaises(ValueError):
            client.set_last_will("", "offline")


class TestMQTTClientConnect(unittest.TestCase):
    @patch('umqtt.simple.socket.socket')
    @patch('umqtt.simple.socket.getaddrinfo')
    def test_connect_basic(self, mock_getaddrinfo, mock_socket):
        # Setup mocks
        mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.read.return_value = b'\x20\x02\x00\x00'

        # Test connection
        client = MQTTClient("test_client", "test.server.com")
        result = client.connect()

        # Verify
        mock_socket.assert_called_once()
        mock_sock_instance.connect.assert_called_once()
        self.assertFalse(result)  # session present flag

    @patch('umqtt.simple.socket.socket')
    @patch('umqtt.simple.socket.getaddrinfo')
    def test_connect_with_timeout(self, mock_getaddrinfo, mock_socket):
        mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.read.return_value = b'\x20\x02\x00\x00'

        client = MQTTClient("test_client", "test.server.com")
        client.connect(timeout=10)

        mock_sock_instance.settimeout.assert_called_once_with(10)

    @patch('umqtt.simple.socket.socket')
    @patch('umqtt.simple.socket.getaddrinfo')
    def test_connect_failure(self, mock_getaddrinfo, mock_socket):
        mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        # Return connection refused error code
        mock_sock_instance.read.return_value = b'\x20\x02\x00\x05'

        client = MQTTClient("test_client", "test.server.com")
        with self.assertRaises(MQTTException):
            client.connect()


class TestMQTTClientPublish(unittest.TestCase):
    def setUp(self):
        self.client = MQTTClient("test_client", "test.server.com")
        self.client.sock = MagicMock()

    def test_publish_qos0(self):
        self.client.publish("test/topic", b"Hello")

        # Verify socket writes were called
        self.assertTrue(self.client.sock.write.called)

        # Verify message was sent
        calls = self.client.sock.write.call_args_list
        self.assertTrue(len(calls) >= 3)  # header, topic, message

    def test_publish_with_retain(self):
        self.client.publish("test/topic", b"Hello", retain=True)

        # Check that retain flag is set in packet
        first_call = self.client.sock.write.call_args_list[0]
        packet = first_call[0][0]
        self.assertTrue(packet[0] & 0x01)  # retain bit

    def test_publish_empty_message(self):
        # Should not raise exception
        self.client.publish("test/topic", b"")
        self.assertTrue(self.client.sock.write.called)

    def test_publish_large_topic(self):
        # Test with a reasonably long topic
        long_topic = "a" * 1000
        self.client.publish(long_topic, b"test")
        self.assertTrue(self.client.sock.write.called)


class TestMQTTClientSubscribe(unittest.TestCase):
    def setUp(self):
        self.client = MQTTClient("test_client", "test.server.com")
        self.client.sock = MagicMock()
        self.callback = MagicMock()
        self.client.set_callback(self.callback)

    def test_subscribe_without_callback(self):
        client = MQTTClient("test_client", "test.server.com")
        client.sock = MagicMock()

        with self.assertRaises(ValueError):
            client.subscribe("test/topic")

    def test_subscribe_success(self):
        # Mock successful subscription response
        self.client.sock.read.side_effect = [
            b'\x90',  # SUBACK
            b'\x03\x00\x01\x00'  # length and packet id
        ]

        self.client.subscribe("test/topic")

        # Verify subscribe packet was sent
        self.assertTrue(self.client.sock.write.called)

    def test_subscribe_with_qos(self):
        self.client.sock.read.side_effect = [
            b'\x90',
            b'\x03\x00\x01\x01'  # QoS 1
        ]

        self.client.subscribe("test/topic", qos=1)
        self.assertTrue(self.client.sock.write.called)


class TestMQTTClientWaitMsg(unittest.TestCase):
    def setUp(self):
        self.client = MQTTClient("test_client", "test.server.com")
        self.client.sock = MagicMock()
        self.callback = MagicMock()
        self.client.set_callback(self.callback)

    def test_wait_msg_pingresp(self):
        # PINGRESP packet
        self.client.sock.read.side_effect = [
            b'\xd0',  # PINGRESP
            b'\x00'   # length
        ]

        result = self.client.wait_msg()
        self.assertIsNone(result)

    def test_wait_msg_empty_socket(self):
        # Empty socket now returns None (non-blocking behavior)
        self.client.sock.read.return_value = b''

        result = self.client.wait_msg()
        self.assertIsNone(result)

    def test_wait_msg_none(self):
        self.client.sock.read.return_value = None

        result = self.client.wait_msg()
        self.assertIsNone(result)

    def test_wait_msg_publish(self):
        # PUBLISH packet with topic "test" and message "hello"
        self.client.sock.read.side_effect = [
            b'\x30',  # PUBLISH QoS 0
            b'\x04',  # topic length high
            b't', b'e', b's', b't',  # topic
            b'h', b'e', b'l', b'l', b'o'  # message
        ]

        # Mock _recv_len to return message length
        self.client._recv_len = MagicMock(return_value=4 + 5)  # topic + msg

        # Mock reading topic length and content
        self.client.sock.read = MagicMock(side_effect=[
            b'\x30',  # op
            b'\x00\x04',  # topic length
            b'test',  # topic
            b'hello'  # message
        ])

        result = self.client.wait_msg()

        # Verify callback was called
        self.callback.assert_called_once_with(b'test', b'hello')


class TestMQTTClientCheckMsg(unittest.TestCase):
    @patch('select.poll')
    def test_check_msg_sets_nonblocking(self, mock_poll_class):
        # Mock the poll instance and its methods
        mock_poll = MagicMock()
        mock_poll_class.return_value = mock_poll
        mock_poll.poll.return_value = []  # No data available

        client = MQTTClient("test_client", "test.server.com")
        client.sock = MagicMock()
        client.cb = MagicMock()

        result = client.check_msg()

        # check_msg uses poll to check for data non-blockingly
        mock_poll_class.assert_called_once()
        mock_poll.register.assert_called_once()
        mock_poll.poll.assert_called_once_with(0)  # 0ms timeout
        self.assertIsNone(result)  # No data available


class TestMQTTClientDisconnect(unittest.TestCase):
    def test_disconnect(self):
        client = MQTTClient("test_client", "test.server.com")
        client.sock = MagicMock()

        client.disconnect()

        client.sock.write.assert_called_once_with(b'\xe0\x00')
        client.sock.close.assert_called_once()


class TestMQTTClientPing(unittest.TestCase):
    def test_ping(self):
        client = MQTTClient("test_client", "test.server.com")
        client.sock = MagicMock()

        client.ping()

        client.sock.write.assert_called_once_with(b'\xc0\x00')


class TestRobustMQTTClient(unittest.TestCase):
    def test_robust_inherits_simple(self):
        self.assertTrue(issubclass(RobustMQTTClient, MQTTClient))

    def test_robust_has_delay(self):
        client = RobustMQTTClient("test", "server")
        self.assertEqual(client.DELAY, 2)

    @patch('umqtt.robust.time.sleep')
    def test_delay_method(self, mock_sleep):
        client = RobustMQTTClient("test", "server")
        client.delay(1)
        mock_sleep.assert_called_once_with(2)

    def test_log_with_debug_off(self):
        client = RobustMQTTClient("test", "server")
        client.DEBUG = False
        # Should not raise exception
        client.log(True, Exception("test"))

    @patch('builtins.print')
    def test_log_with_debug_on(self, mock_print):
        client = RobustMQTTClient("test", "server")
        client.DEBUG = True
        client.log(True, Exception("test"))
        mock_print.assert_called_once()

    @patch('umqtt.robust.time.sleep')
    @patch('umqtt.simple.socket.socket')
    @patch('umqtt.simple.socket.getaddrinfo')
    def test_reconnect_succeeds_first_try(self, mock_getaddrinfo, mock_socket, mock_sleep):
        mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.read.return_value = b'\x20\x02\x00\x00'

        client = RobustMQTTClient("test", "server")
        result = client.reconnect()

        # Should not have called delay/sleep
        mock_sleep.assert_not_called()

    @patch('umqtt.robust.time.sleep')
    @patch('umqtt.simple.socket.socket')
    @patch('umqtt.simple.socket.getaddrinfo')
    def test_reconnect_retries_on_failure(self, mock_getaddrinfo, mock_socket, mock_sleep):
        mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance

        # Fail twice, then succeed
        mock_sock_instance.connect.side_effect = [
            OSError("Connection failed"),
            OSError("Connection failed"),
            None
        ]
        mock_sock_instance.read.return_value = b'\x20\x02\x00\x00'

        client = RobustMQTTClient("test", "server")
        result = client.reconnect()

        # Should have retried and called delay
        self.assertEqual(mock_sleep.call_count, 2)

    def test_robust_publish_with_retry(self):
        client = RobustMQTTClient("test", "server")
        client.sock = MagicMock()

        # Mock reconnect to reset the socket
        def reconnect_mock():
            client.sock = MagicMock()
        client.reconnect = MagicMock(side_effect=reconnect_mock)

        # First publish attempt fails, triggers reconnect, second succeeds
        first_sock = client.sock
        first_sock.write.side_effect = OSError("Write failed")

        client.publish("test/topic", b"message")

        # Should have called reconnect once
        client.reconnect.assert_called_once()

    def test_robust_wait_msg_with_retry(self):
        client = RobustMQTTClient("test", "server")
        client.sock = MagicMock()
        client.cb = MagicMock()

        # First call fails, second succeeds
        client.sock.read.side_effect = [OSError("Read failed"), None]
        client.reconnect = MagicMock()

        result = client.wait_msg()

        # Should have called reconnect once
        client.reconnect.assert_called_once()

    @patch('select.poll')
    def test_robust_check_msg_with_attempts(self, mock_poll_class):
        # Mock the poll instance to return no data available
        # This simulates the case where check_msg returns None (no message)
        mock_poll = MagicMock()
        mock_poll_class.return_value = mock_poll
        mock_poll.poll.return_value = []  # No data available

        client = RobustMQTTClient("test", "server")
        client.sock = MagicMock()
        client.cb = MagicMock()

        # Mock reconnect to prevent actual connection attempts
        client.reconnect = MagicMock()

        # check_msg with no data should return None without reconnecting
        result = client.check_msg(attempts=2)

        # Should return None and not reconnect since no error occurred
        self.assertIsNone(result)
        self.assertEqual(client.reconnect.call_count, 0)


class TestMQTTProtocolCompliance(unittest.TestCase):
    """Test MQTT protocol-level behavior"""

    def test_packet_id_increments(self):
        client = MQTTClient("test", "server")
        client.sock = MagicMock()

        initial_pid = client.pid

        # Trigger pid increment (subscribe does this)
        client.cb = MagicMock()
        client.sock.read.side_effect = [b'\x90', b'\x03\x00\x01\x00']
        client.subscribe("test/topic")

        self.assertEqual(client.pid, initial_pid + 1)

    def test_send_str_format(self):
        """Verify _send_str sends correct length prefix"""
        client = MQTTClient("test", "server")
        client.sock = MagicMock()

        test_string = b"hello"
        client._send_str(test_string)

        # Should write length (2 bytes) then string
        calls = client.sock.write.call_args_list
        self.assertEqual(len(calls), 2)

        # First call should be length prefix
        length_bytes = calls[0][0][0]
        length = struct.unpack("!H", length_bytes)[0]
        self.assertEqual(length, len(test_string))

    def test_recv_len_single_byte(self):
        """Test variable length decoding for small values"""
        client = MQTTClient("test", "server")
        client.sock = MagicMock()

        # Length 42 encoded as single byte
        client.sock.read.return_value = b'\x2a'

        length = client._recv_len()
        self.assertEqual(length, 42)

    def test_recv_len_multibyte(self):
        """Test variable length decoding for larger values"""
        client = MQTTClient("test", "server")
        client.sock = MagicMock()

        # Length 321 = 0x141 = 0xC1 0x02 in MQTT variable length encoding
        client.sock.read.side_effect = [b'\xc1', b'\x02']

        length = client._recv_len()
        self.assertEqual(length, 321)


if __name__ == '__main__':
    unittest.main()
