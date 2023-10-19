import unittest
from unittest.mock import patch
from opentherm_app import *


class TestOpenThermApp_status_exchange(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_STATUS, 0xff))
    def test_status_exchange(self, mock_opentherm_exchange):
        result = status_exchange(ch_enabled=True, dhw_enabled=True)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, 0, 0x0300)
        self.assertEqual(result, {
            'fault': True,
            'ch_active': True,
            'dhw_active': True,
            'flame_active': True,
            'cooling_active': True,
            'ch2_active': True,
            'diagnostic_event': True
        })


class TestOpenThermApp_send_primary_configuration(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_PRIMARY_CONFIG, 0))
    def test_send_primary_configuration(self, mock_opentherm_exchange):
        send_primary_configuration(0x01)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_PRIMARY_CONFIG, 0x01)


class TestOpenThermApp_read_secondary_configuration(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_SECONDARY_CONFIG, 0xFF0F))
    def test_read_secondary_configuration(self, mock_opentherm_exchange):
        result = read_secondary_configuration()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_SECONDARY_CONFIG, 0)
        self.assertEqual(result, {
            'dhw_present': True,
            'control_type': 'onoff',
            'cooling_config': True,
            'dhw_config': 'storage',
            'low_off_and_pump_control': False,
            'ch2_supported': True,
            'memberid_code': 15
        })


class TestOpenThermApp_control_ch_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TSET, 0))
    def test_control_ch_setpoint(self, mock_opentherm_exchange):
        control_ch_setpoint(50)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TSET, 50 * 256)

    def test_control_ch_setpoint_invalid(self):
        with self.assertRaises(AssertionError):
            control_ch_setpoint(-1)
        with self.assertRaises(AssertionError):
            control_ch_setpoint(101)


class TestOpenThermApp_read_dhw_setpoint_range(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET_BOUNDS, 0x1F0A))
    def test_read_dhw_setpoint_range(self, mock_opentherm_exchange):
        result = read_dhw_setpoint_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET_BOUNDS, 0)
        self.assertEqual(result, (10, 31))


class TestOpenThermApp_control_dhw_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TDHWSET, 0))
    def test_control_dhw_setpoint(self, mock_opentherm_exchange):
        control_dhw_setpoint(50)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TDHWSET, 50 * 256)

    def test_control_dhw_setpoint_invalid(self):
        with self.assertRaises(AssertionError):
            control_dhw_setpoint(-1)
        with self.assertRaises(AssertionError):
            control_dhw_setpoint(101)

class TestOpenThermApp_read_dhw_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET, 0x1A00))
    def test_read_dhw_setpoint(self, mock_opentherm_exchange):
        result = read_dhw_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET, 0x0000))
    def test_read_dhw_setpoint_zero(self, mock_opentherm_exchange):
        result = read_dhw_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET, 0xFFFF))
    def test_read_dhw_setpoint_max(self, mock_opentherm_exchange):
        result = read_dhw_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0)
        self.assertEqual(result, 255.99609375)

    # @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET, 0x8000))
    # def test_read_dhw_setpoint_negative(self, mock_opentherm_exchange):
    #     result = read_dhw_setpoint()
    #     mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0)
    #     self.assertEqual(result, -128.0)


class TestOpenThermApp_read_maxch_setpoint_range(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET_BOUNDS, 0x1F0A))
    def test_read_maxch_setpoint_range(self, mock_opentherm_exchange):
        result = read_maxch_setpoint_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET_BOUNDS, 0)
        self.assertEqual(result, (10, 31))


class TestOpenThermApp_control_maxch_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_MAXTSET, 0))
    def test_control_maxch_setpoint(self, mock_opentherm_exchange):
        control_maxch_setpoint(50)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_MAXTSET, 50 * 256)


class TestOpenThermApp_read_maxch_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET, 0x1A00))
    def test_read_maxch_setpoint(self, mock_opentherm_exchange):
        result = read_maxch_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET, 0x0000))
    def test_read_maxch_setpoint_zero(self, mock_opentherm_exchange):
        result = read_maxch_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET, 0xFFFF))
    def test_read_maxch_setpoint_max(self, mock_opentherm_exchange):
        result = read_maxch_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0)
        self.assertEqual(result, 255.99609375)

    # @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET, 0x8000))
    # def test_read_maxch_setpoint_negative(self, mock_opentherm_exchange):
    #     result = read_maxch_setpoint()
    #     mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0)
    #     self.assertEqual(result, -128.0)

class TestOpenThermApp_read_extra_boiler_params(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_RBP_FLAGS, 0x33))
    def test_read_extra_boiler_params_support_rw(self, mock_opentherm_exchange):
        result = read_extra_boiler_params_support()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_RBP_FLAGS, 0)
        self.assertEqual(result, {
            'dhw_setpoint': 'rw',
            'maxch_setpoint': 'rw'
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_RBP_FLAGS, 0x30))
    def test_read_extra_boiler_params_support_ro(self, mock_opentherm_exchange):
        result = read_extra_boiler_params_support()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_RBP_FLAGS, 0)
        self.assertEqual(result, {
            'dhw_setpoint': 'ro',
            'maxch_setpoint': 'ro'
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_RBP_FLAGS, 0))
    def test_read_extra_boiler_params_support_none(self, mock_opentherm_exchange):
        result = read_extra_boiler_params_support()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_RBP_FLAGS, 0)
        self.assertEqual(result, {
            'dhw_setpoint': None,
            'maxch_setpoint': None
        })


class TestOpenThermApp_read_fault_flags(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x0100))
    def test_read_fault_flags_service_required(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': True,
            'blor_enabled': False,
            'low_water_pressure': False,
            'flame_fault': False,
            'air_pressure_fault': False,
            'water_over_temp': False,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x0200))
    def test_read_fault_flags_blor_enabled(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': True,
            'low_water_pressure': False,
            'flame_fault': False,
            'air_pressure_fault': False,
            'water_over_temp': False,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x0400))
    def test_read_fault_flags_low_water_pressure(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': False,
            'low_water_pressure': True,
            'flame_fault': False,
            'air_pressure_fault': False,
            'water_over_temp': False,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x0800))
    def test_read_fault_flags_flame_fault(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': False,
            'low_water_pressure': False,
            'flame_fault': True,
            'air_pressure_fault': False,
            'water_over_temp': False,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x1000))
    def test_read_fault_flags_air_pressure_fault(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': False,
            'low_water_pressure': False,
            'flame_fault': False,
            'air_pressure_fault': True,
            'water_over_temp': False,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0x2000))
    def test_read_fault_flags_water_over_temp(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': False,
            'low_water_pressure': False,
            'flame_fault': False,
            'air_pressure_fault': False,
            'water_over_temp': True,
            'oem_code': 0x00,
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_ASF_FAULT, 0xFF))
    def test_read_fault_flags_oem_code(self, mock_opentherm_exchange):
        result = read_fault_flags()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0)
        self.assertEqual(result, {
            'service_required': False,
            'blor_enabled': False,
            'low_water_pressure': False,
            'flame_fault': False,
            'air_pressure_fault': False,
            'water_over_temp': False,
            'oem_code': 0xFF,
        })


class TestOpenThermApp_read_oem_long_code(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_OEM_DIAGNOSTIC_CODE, 0x1234))
    def test_read_oem_long_code(self, mock_opentherm_exchange):
        result = read_oem_long_code()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_OEM_DIAGNOSTIC_CODE, 0)
        self.assertEqual(result, 0x1234)
