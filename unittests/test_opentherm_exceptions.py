import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from opentherm_app import (
    _check_response_type,
    opentherm_exchange_retry,
    DataInvalidError,
    UnknownDataIdError,
    MSG_TYPE_READ_ACK,
    MSG_TYPE_WRITE_ACK,
    MSG_TYPE_DATA_INVALID,
    MSG_TYPE_UNKNOWN_DATA_ID,
    DATA_ID_STATUS,
    DATA_ID_TSET,
)


def async_test(coro):
    """Decorator to run async test methods"""
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


class TestCheckResponseType(unittest.TestCase):
    """Test the _check_response_type() helper function"""

    def test_valid_read_ack(self):
        """_check_response_type should not raise for valid READ_ACK with matching data_id"""
        # Should not raise any exception
        _check_response_type(MSG_TYPE_READ_ACK, MSG_TYPE_READ_ACK, DATA_ID_STATUS, DATA_ID_STATUS)

    def test_valid_write_ack(self):
        """_check_response_type should not raise for valid WRITE_ACK with matching data_id"""
        # Should not raise any exception
        _check_response_type(MSG_TYPE_WRITE_ACK, MSG_TYPE_WRITE_ACK, DATA_ID_TSET, DATA_ID_TSET)

    def test_data_invalid_raises_exception(self):
        """_check_response_type should raise DataInvalidError for DATA-INVALID response"""
        with self.assertRaises(DataInvalidError) as cm:
            _check_response_type(MSG_TYPE_DATA_INVALID, MSG_TYPE_READ_ACK, DATA_ID_STATUS, DATA_ID_STATUS)
        self.assertIn("DATA-INVALID", str(cm.exception))
        self.assertIn(str(DATA_ID_STATUS), str(cm.exception))

    def test_unknown_data_id_raises_exception(self):
        """_check_response_type should raise UnknownDataIdError for UNKNOWN-DATAID response"""
        with self.assertRaises(UnknownDataIdError) as cm:
            _check_response_type(MSG_TYPE_UNKNOWN_DATA_ID, MSG_TYPE_READ_ACK, DATA_ID_STATUS, DATA_ID_STATUS)
        self.assertIn("does not support", str(cm.exception))
        self.assertIn(str(DATA_ID_STATUS), str(cm.exception))

    def test_wrong_msg_type_raises_assertion(self):
        """_check_response_type should raise AssertionError for unexpected msg_type"""
        with self.assertRaises(AssertionError) as cm:
            _check_response_type(MSG_TYPE_WRITE_ACK, MSG_TYPE_READ_ACK, DATA_ID_STATUS, DATA_ID_STATUS)
        self.assertIn("Expected msg_type", str(cm.exception))

    def test_wrong_data_id_raises_assertion(self):
        """_check_response_type should raise AssertionError for unexpected data_id"""
        with self.assertRaises(AssertionError) as cm:
            _check_response_type(MSG_TYPE_READ_ACK, MSG_TYPE_READ_ACK, DATA_ID_TSET, DATA_ID_STATUS)
        self.assertIn("Expected data_id", str(cm.exception))
        self.assertIn(str(DATA_ID_STATUS), str(cm.exception))

    def test_data_invalid_takes_precedence(self):
        """DATA-INVALID should be checked before msg_type mismatch"""
        # Even though we expect READ_ACK but pass WRITE_ACK as expected,
        # DATA-INVALID should be detected first
        with self.assertRaises(DataInvalidError):
            _check_response_type(MSG_TYPE_DATA_INVALID, MSG_TYPE_WRITE_ACK, DATA_ID_STATUS, DATA_ID_STATUS)


class TestOpenThermExchangeRetry(unittest.TestCase):
    """Test the retry behavior of opentherm_exchange_retry()"""

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_success_on_first_try(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should return immediately on success"""
        mock_exchange.return_value = (MSG_TYPE_READ_ACK, DATA_ID_STATUS, 0xFF)
        result = await opentherm_exchange_retry(0, DATA_ID_STATUS, 0)
        self.assertEqual(result, (MSG_TYPE_READ_ACK, DATA_ID_STATUS, 0xFF))
        self.assertEqual(mock_exchange.call_count, 1)

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_retry_on_generic_exception(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should retry on generic exceptions"""
        # First call raises, second succeeds
        mock_exchange.side_effect = [
            Exception("Timeout"),
            (MSG_TYPE_READ_ACK, DATA_ID_STATUS, 0xFF)
        ]
        result = await opentherm_exchange_retry(0, DATA_ID_STATUS, 0, max_retries=1)
        self.assertEqual(result, (MSG_TYPE_READ_ACK, DATA_ID_STATUS, 0xFF))
        self.assertEqual(mock_exchange.call_count, 2)

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_no_retry_on_data_invalid(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should NOT retry on DataInvalidError

        Per OpenTherm spec and docstring, DATA-INVALID is a valid protocol response
        that should not be retried - the boiler recognizes the data ID but the data
        is unavailable or invalid.
        """
        mock_exchange.side_effect = DataInvalidError("Data invalid for ID 0")

        with self.assertRaises(DataInvalidError):
            await opentherm_exchange_retry(0, DATA_ID_STATUS, 0, max_retries=10)

        # Should only be called once, no retries
        self.assertEqual(mock_exchange.call_count, 1)

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_no_retry_on_unknown_data_id(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should NOT retry on UnknownDataIdError

        Per OpenTherm spec and docstring, UNKNOWN-DATAID is a valid protocol response
        that should not be retried - the boiler does not support or recognize this data ID.
        """
        mock_exchange.side_effect = UnknownDataIdError("Unknown data ID 35")

        with self.assertRaises(UnknownDataIdError):
            await opentherm_exchange_retry(0, 35, 0, max_retries=10)

        # Should only be called once, no retries
        self.assertEqual(mock_exchange.call_count, 1)

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_max_retries_exceeded(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should raise after max_retries exceeded"""
        mock_exchange.side_effect = Exception("Persistent error")

        with self.assertRaises(Exception) as cm:
            await opentherm_exchange_retry(0, DATA_ID_STATUS, 0, max_retries=2)

        self.assertIn("Persistent error", str(cm.exception))
        # Should be called max_retries + 1 times (initial + retries)
        self.assertEqual(mock_exchange.call_count, 3)

    @patch('asyncio.sleep_ms', new_callable=AsyncMock, create=True)
    @patch('opentherm_app.opentherm_exchange', new_callable=AsyncMock)
    @async_test
    async def test_retry_then_data_invalid(self, mock_exchange, mock_sleep):
        """opentherm_exchange_retry should retry generic errors but NOT DataInvalidError

        This verifies that the retry logic differentiates between transient errors
        (which should be retried) and valid protocol responses (which should not).
        """
        # First call: generic exception (should retry)
        # Second call: DataInvalidError (should NOT retry)
        mock_exchange.side_effect = [
            Exception("Timeout"),
            DataInvalidError("Data invalid")
        ]

        with self.assertRaises(DataInvalidError):
            await opentherm_exchange_retry(0, DATA_ID_STATUS, 0, max_retries=10)

        # Should be called twice: once for initial Timeout, once for retry that gets DataInvalidError
        self.assertEqual(mock_exchange.call_count, 2)


class TestExceptionTypes(unittest.TestCase):
    """Test that the custom exception types are proper Exception subclasses"""

    def test_data_invalid_error_is_exception(self):
        """DataInvalidError should be an Exception subclass"""
        err = DataInvalidError("test message")
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), "test message")

    def test_unknown_data_id_error_is_exception(self):
        """UnknownDataIdError should be an Exception subclass"""
        err = UnknownDataIdError("test message")
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), "test message")

    def test_exceptions_can_be_caught_separately(self):
        """DataInvalidError and UnknownDataIdError should be catchable separately"""
        try:
            raise DataInvalidError("data invalid")
        except UnknownDataIdError:
            self.fail("DataInvalidError should not be caught as UnknownDataIdError")
        except DataInvalidError as e:
            self.assertEqual(str(e), "data invalid")

        try:
            raise UnknownDataIdError("unknown id")
        except DataInvalidError:
            self.fail("UnknownDataIdError should not be caught as DataInvalidError")
        except UnknownDataIdError as e:
            self.assertEqual(str(e), "unknown id")


if __name__ == '__main__':
    unittest.main()
