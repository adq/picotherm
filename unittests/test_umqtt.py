import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call
import struct
from async_mqtt_client import AsyncMQTTClient, MQTTException


class TestAsyncMQTTClientInit:
    def test_init_defaults(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        assert client.client_id == b"test_client"
        assert client.server == "test.server.com"
        assert client.port == 1883
        assert client.sock is None
        assert client.cb is None
        assert client.keepalive == 0
        assert client._reader is None
        assert client._writer is None

    def test_init_with_ssl(self):
        client = AsyncMQTTClient("test_client", "test.server.com", ssl=True)
        assert client.port == 8883
        assert client.ssl is True

    def test_init_with_custom_port(self):
        client = AsyncMQTTClient("test_client", "test.server.com", port=1234)
        assert client.port == 1234

    def test_init_with_auth(self):
        client = AsyncMQTTClient("test_client", "test.server.com", user="user1", password="pass123")
        assert client.user == b"user1"
        assert client.pswd == b"pass123"

    def test_init_with_keepalive(self):
        client = AsyncMQTTClient("test_client", "test.server.com", keepalive=60)
        assert client.keepalive == 60

    def test_init_with_ssl_params(self):
        ssl_params = {"certfile": "cert.pem"}
        client = AsyncMQTTClient("test_client", "test.server.com", ssl=True, ssl_params=ssl_params)
        assert client.ssl_params == ssl_params


class TestAsyncMQTTClientSetCallback:
    def test_set_callback(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        callback = MagicMock()
        client.set_callback(callback)
        assert client.cb == callback


class TestAsyncMQTTClientSetLastWill:
    def test_set_last_will_basic(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", b"offline")
        assert client.lw_topic == b"status/test"
        assert client.lw_msg == b"offline"
        assert client.lw_qos == 0
        assert client.lw_retain is False

    def test_set_last_will_with_qos(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", b"offline", qos=1)
        assert client.lw_qos == 1

    def test_set_last_will_with_retain(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        client.set_last_will("status/test", b"offline", retain=True)
        assert client.lw_retain is True

    def test_set_last_will_invalid_qos(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        with pytest.raises(ValueError, match="Invalid QoS"):
            client.set_last_will("status/test", b"offline", qos=3)

    def test_set_last_will_empty_topic(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            client.set_last_will("", b"offline")

    def test_set_last_will_requires_bytes_msg(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        with pytest.raises(TypeError, match="msg must be bytes"):
            client.set_last_will("status/test", "offline")


class TestAsyncMQTTClientConnect:
    @pytest.mark.asyncio
    async def test_connect_basic(self):
        # Mock the socket module that's imported inside connect()
        with patch('socket.socket') as mock_socket_class:
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                # Setup mocks
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

                # Mock asyncio streams
                mock_reader = AsyncMock()
                mock_writer = AsyncMock()

                # CONNACK response: 0x20 0x02 0x00 0x00
                mock_reader.readexactly.return_value = b'\x20\x02\x00\x00'

                client = AsyncMQTTClient("test_client", "test.server.com")

                with patch('asyncio.StreamReader', return_value=mock_reader):
                    with patch('asyncio.StreamWriter', return_value=mock_writer):
                        with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                            result = await client.connect()

                # Verify socket was created and configured
                mock_socket_class.assert_called_once()
                mock_sock.setblocking.assert_called_once_with(False)
                assert result is False  # session present flag

    @pytest.mark.asyncio
    async def test_connect_with_auth(self):
        with patch('socket.socket') as mock_socket_class:
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

                mock_reader = AsyncMock()
                mock_writer = AsyncMock()
                mock_reader.readexactly.return_value = b'\x20\x02\x00\x00'

                client = AsyncMQTTClient("test_client", "test.server.com", user="user1", password="pass123")

                with patch('asyncio.StreamReader', return_value=mock_reader):
                    with patch('asyncio.StreamWriter', return_value=mock_writer):
                        with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                            await client.connect()

                # Verify authentication credentials were included
                assert mock_writer.write.called
                assert client.user == b"user1"
                assert client.pswd == b"pass123"

    @pytest.mark.asyncio
    async def test_connect_with_last_will(self):
        with patch('socket.socket') as mock_socket_class:
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

                mock_reader = AsyncMock()
                mock_writer = AsyncMock()
                mock_reader.readexactly.return_value = b'\x20\x02\x00\x00'

                client = AsyncMQTTClient("test_client", "test.server.com")
                client.set_last_will("status/test", b"offline", retain=True, qos=1)

                with patch('asyncio.StreamReader', return_value=mock_reader):
                    with patch('asyncio.StreamWriter', return_value=mock_writer):
                        with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                            await client.connect()

                # Verify last will was included in CONNECT
                assert mock_writer.write.called

    @pytest.mark.asyncio
    async def test_connect_failure_bad_connack(self):
        with patch('socket.socket') as mock_socket_class:
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

                mock_reader = AsyncMock()
                mock_writer = AsyncMock()
                # Return connection refused error code
                mock_reader.readexactly.return_value = b'\x20\x02\x00\x05'

                client = AsyncMQTTClient("test_client", "test.server.com")

                with patch('asyncio.StreamReader', return_value=mock_reader):
                    with patch('asyncio.StreamWriter', return_value=mock_writer):
                        with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                            with pytest.raises(MQTTException):
                                await client.connect()

                # Verify socket was cleaned up
                assert client.sock is None
                assert client._reader is None
                assert client._writer is None

    @pytest.mark.asyncio
    async def test_connect_network_failure(self):
        with patch('socket.socket') as mock_socket_class:
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

                # Simulate connection failure
                mock_sock.connect.side_effect = OSError(111)  # Connection refused

                client = AsyncMQTTClient("test_client", "test.server.com")

                with pytest.raises(OSError):
                    await client.connect()

                # Verify cleanup
                assert client.sock is None


class TestAsyncMQTTClientPublish:
    @pytest.mark.asyncio
    async def test_publish_qos0(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        await client.publish("test/topic", b"Hello")

        # Verify write was called
        assert mock_writer.write.called
        assert mock_writer.drain.called

    @pytest.mark.asyncio
    async def test_publish_with_retain(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        await client.publish("test/topic", b"Hello", retain=True)

        # Check that retain flag is set in packet
        first_call = mock_writer.write.call_args_list[0]
        packet = first_call[0][0]
        assert packet[0] & 0x01  # retain bit

    @pytest.mark.asyncio
    async def test_publish_qos1_with_puback(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_reader = AsyncMock()
        client._writer = mock_writer
        client._reader = mock_reader

        # Mock PUBACK response
        mock_reader.readexactly.side_effect = [
            b'\x40',  # PUBACK opcode
            b'\x02',  # size
            b'\x00\x01'  # packet id
        ]

        await client.publish("test/topic", b"Hello", qos=1)

        # Verify publish and PUBACK handling
        assert mock_writer.write.called
        assert mock_writer.drain.called
        assert client.pid == 1

    @pytest.mark.asyncio
    async def test_publish_string_convenience(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        await client.publish_string("test/topic", "Hello World")

        # Verify write was called with encoded string
        assert mock_writer.write.called
        assert mock_writer.drain.called

    @pytest.mark.asyncio
    async def test_publish_requires_bytes(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        with pytest.raises(TypeError, match="msg must be bytes"):
            await client.publish("test/topic", "Hello")

    @pytest.mark.asyncio
    async def test_publish_empty_message(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        # Should not raise exception
        await client.publish("test/topic", b"")
        assert mock_writer.write.called

    @pytest.mark.asyncio
    async def test_publish_large_topic(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        # Test with a reasonably long topic
        long_topic = "a" * 1000
        await client.publish(long_topic, b"test")
        assert mock_writer.write.called

    @pytest.mark.asyncio
    async def test_publish_qos2_not_supported(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        with pytest.raises(NotImplementedError, match="QoS 2 not supported"):
            await client.publish("test/topic", b"test", qos=2)


class TestAsyncMQTTClientSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_without_callback(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        with pytest.raises(MQTTException, match="Callback not set"):
            await client.subscribe("test/topic")

    @pytest.mark.asyncio
    async def test_subscribe_success(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_reader = AsyncMock()
        client._writer = mock_writer
        client._reader = mock_reader
        client.set_callback(MagicMock())

        # Mock SUBACK response
        mock_reader.readexactly.side_effect = [
            b'\x90',  # SUBACK opcode
            b'\x03\x00\x01\x00'  # length and packet id
        ]

        await client.subscribe("test/topic")

        # Verify subscribe packet was sent
        assert mock_writer.write.called
        assert mock_writer.drain.called
        assert client.pid == 1

    @pytest.mark.asyncio
    async def test_subscribe_with_qos(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_reader = AsyncMock()
        client._writer = mock_writer
        client._reader = mock_reader
        client.set_callback(MagicMock())

        # Mock SUBACK response
        mock_reader.readexactly.side_effect = [
            b'\x90',
            b'\x03\x00\x01\x01'  # QoS 1
        ]

        await client.subscribe("test/topic", qos=1)
        assert mock_writer.write.called


class TestAsyncMQTTClientWaitMsg:
    @pytest.mark.asyncio
    async def test_wait_msg_pingresp(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        client._reader = mock_reader

        # PINGRESP packet
        mock_reader.readexactly.side_effect = [
            b'\xd0',  # PINGRESP
            b'\x00'   # length
        ]

        result = await client.wait_msg()
        assert result is None

    @pytest.mark.asyncio
    async def test_wait_msg_publish_qos0(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        client._reader = mock_reader
        callback = MagicMock()
        client.set_callback(callback)

        # PUBLISH packet with topic "test" and message "hello"
        # Variable length encoding for remaining length
        async def mock_recv_len():
            return 4 + 5  # topic length (2) + topic (4) + message (5)

        client._recv_len = mock_recv_len

        mock_reader.readexactly.side_effect = [
            b'\x30',  # PUBLISH QoS 0
            b'\x00\x04',  # topic length
            b'test',  # topic
            b'hello'  # message
        ]

        result = await client.wait_msg()

        # Verify callback was called with decoded topic
        callback.assert_called_once_with('test', b'hello')

    @pytest.mark.asyncio
    async def test_wait_msg_publish_qos1_sends_puback(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        client._reader = mock_reader
        client._writer = mock_writer
        callback = MagicMock()
        client.set_callback(callback)

        # PUBLISH packet with QoS 1
        async def mock_recv_len():
            return 2 + 4 + 2 + 5  # topic_len + topic + pid + message

        client._recv_len = mock_recv_len

        mock_reader.readexactly.side_effect = [
            b'\x32',  # PUBLISH QoS 1
            b'\x00\x04',  # topic length
            b'test',  # topic
            b'\x00\x01',  # packet id
            b'hello'  # message
        ]

        result = await client.wait_msg()

        # Verify callback was called
        callback.assert_called_once_with('test', b'hello')

        # Verify PUBACK was sent
        assert mock_writer.write.called
        assert mock_writer.drain.called

    @pytest.mark.asyncio
    async def test_wait_msg_empty_socket(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        client._reader = mock_reader

        # Empty socket raises OSError
        mock_reader.readexactly.side_effect = [b'']

        with pytest.raises(OSError):
            await client.wait_msg()


class TestAsyncMQTTClientCheckMsg:
    @pytest.mark.asyncio
    async def test_check_msg_no_data(self):
        with patch('async_mqtt_client.select.poll') as mock_poll_class:
            mock_poll = MagicMock()
            mock_poll_class.return_value = mock_poll
            mock_poll.poll.return_value = []  # No data available

            client = AsyncMQTTClient("test_client", "test.server.com")
            client.sock = MagicMock()
            client.set_callback(MagicMock())

            result = await client.check_msg()

            # No data available
            mock_poll.register.assert_called_once()
            mock_poll.poll.assert_called_once_with(0)
            assert result is None

    @pytest.mark.asyncio
    async def test_check_msg_with_data(self):
        with patch('async_mqtt_client.select.poll') as mock_poll_class:
            mock_poll = MagicMock()
            mock_poll_class.return_value = mock_poll
            mock_poll.poll.return_value = [(None, 1)]  # Data available

            client = AsyncMQTTClient("test_client", "test.server.com")
            client.sock = MagicMock()
            mock_reader = AsyncMock()
            client._reader = mock_reader
            client.set_callback(MagicMock())

            # Mock PINGRESP
            mock_reader.readexactly.side_effect = [
                b'\xd0',
                b'\x00'
            ]

            result = await client.check_msg()

            # Should have processed message
            mock_poll.register.assert_called_once()
            assert result is None  # PINGRESP returns None


class TestAsyncMQTTClientDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_sock = MagicMock()
        client._writer = mock_writer
        client.sock = mock_sock

        await client.disconnect()

        mock_writer.write.assert_called_once_with(b'\xe0\x00')
        mock_writer.drain.assert_called_once()
        mock_sock.close.assert_called_once()
        assert client._reader is None
        assert client._writer is None
        assert client.sock is None

    @pytest.mark.asyncio
    async def test_disconnect_cleanup_on_error(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_sock = MagicMock()
        client._writer = mock_writer
        client.sock = mock_sock

        # Simulate write failure
        mock_writer.write.side_effect = Exception("Write failed")

        # Should still cleanup
        await client.disconnect()

        mock_sock.close.assert_called_once()
        assert client.sock is None


class TestAsyncMQTTClientPing:
    @pytest.mark.asyncio
    async def test_ping(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        client._writer = mock_writer

        await client.ping()

        mock_writer.write.assert_called_once_with(b'\xc0\x00')
        mock_writer.drain.assert_called_once()


class TestAsyncMQTTProtocolCompliance:
    """Test MQTT protocol-level behavior"""

    @pytest.mark.asyncio
    async def test_packet_id_increments(self):
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = AsyncMock()
        mock_reader = AsyncMock()
        client._writer = mock_writer
        client._reader = mock_reader
        client.set_callback(MagicMock())

        initial_pid = client.pid

        # Mock SUBACK
        mock_reader.readexactly.side_effect = [
            b'\x90',
            b'\x03\x00\x01\x00'
        ]

        await client.subscribe("test/topic")

        assert client.pid == initial_pid + 1

    def test_send_str_format(self):
        """Verify _send_str sends correct length prefix"""
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_writer = MagicMock()
        client._writer = mock_writer

        test_string = b"hello"
        client._send_str(test_string)

        # Should write length (2 bytes) then string
        calls = mock_writer.write.call_args_list
        assert len(calls) == 2

        # First call should be length prefix
        length_bytes = calls[0][0][0]
        length = struct.unpack("!H", length_bytes)[0]
        assert length == len(test_string)

    @pytest.mark.asyncio
    async def test_recv_len_single_byte(self):
        """Test variable length decoding for small values"""
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        client._reader = mock_reader

        # Length 42 encoded as single byte
        mock_reader.readexactly.side_effect = [b'\x2a']

        length = await client._recv_len()
        assert length == 42

    @pytest.mark.asyncio
    async def test_recv_len_multibyte(self):
        """Test variable length decoding for larger values"""
        client = AsyncMQTTClient("test_client", "test.server.com")
        mock_reader = AsyncMock()
        client._reader = mock_reader

        # Length 321 = 0x141 = 0xC1 0x02 in MQTT variable length encoding
        mock_reader.readexactly.side_effect = [b'\xc1', b'\x02']

        length = await client._recv_len()
        assert length == 321


class TestAsyncMQTTClientIntegration:
    """Integration tests for more complex scenarios"""

    @pytest.mark.asyncio
    async def test_connect_subscribe_publish_disconnect(self):
        """Test full lifecycle"""
        with patch('async_mqtt_client.socket') as mock_socket_module:
            mock_sock = MagicMock()
            mock_socket_module.socket.return_value = mock_sock
            mock_socket_module.getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

            mock_reader = AsyncMock()
            mock_writer = AsyncMock()

            # CONNACK, SUBACK responses
            mock_reader.readexactly.side_effect = [
                b'\x20\x02\x00\x00',  # CONNACK
                b'\x90',  # SUBACK opcode
                b'\x03\x00\x01\x00',  # SUBACK data
            ]

            client = AsyncMQTTClient("test_client", "test.server.com")
            callback = MagicMock()
            client.set_callback(callback)

            with patch('asyncio.StreamReader', return_value=mock_reader):
                with patch('asyncio.StreamWriter', return_value=mock_writer):
                    with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                        # Connect
                        await client.connect()

                        # Subscribe
                        await client.subscribe("test/topic")

                        # Publish
                        await client.publish("test/topic", b"hello")

                        # Disconnect
                        await client.disconnect()

            # Verify all operations completed
            assert mock_sock.close.called

    @pytest.mark.asyncio
    async def test_reconnect_after_disconnect(self):
        """Test that client can reconnect after disconnect"""
        with patch('async_mqtt_client.socket') as mock_socket_module:
            mock_sock = MagicMock()
            mock_socket_module.socket.return_value = mock_sock
            mock_socket_module.getaddrinfo.return_value = [('', '', '', '', ('192.168.1.1', 1883))]

            mock_reader = AsyncMock()
            mock_writer = AsyncMock()

            # Two CONNACK responses for two connections
            mock_reader.readexactly.side_effect = [
                b'\x20\x02\x00\x00',  # First CONNACK
                b'\x20\x02\x00\x00',  # Second CONNACK
            ]

            client = AsyncMQTTClient("test_client", "test.server.com")

            with patch('asyncio.StreamReader', return_value=mock_reader):
                with patch('asyncio.StreamWriter', return_value=mock_writer):
                    with patch('asyncio.sleep_ms', new_callable=AsyncMock):
                        # First connection
                        await client.connect()
                        await client.disconnect()

                        # Second connection
                        await client.connect()

            # Verify both connections
            assert mock_socket_module.socket.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
