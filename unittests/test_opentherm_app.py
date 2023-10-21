import unittest
from unittest.mock import patch, call
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
        control_ch_setpoint(50.0    )
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
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHWSET, 0x8000))
    def test_read_dhw_setpoint_negative(self, mock_opentherm_exchange):
        result = read_dhw_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0)
        self.assertEqual(result, -128.0)


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
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_MAXTSET, 0x8000))
    def test_read_maxch_setpoint_negative(self, mock_opentherm_exchange):
        result = read_maxch_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0)
        self.assertEqual(result, -128.0)

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


class TestOpenThermApp_send_primary_opentherm_version(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_OPENTHERM_VERSION_PRIMARY, 0))
    def test_send_primary_opentherm_version(self, mock_opentherm_exchange):
        send_primary_opentherm_version(2.2)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_OPENTHERM_VERSION_PRIMARY, 563)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_OPENTHERM_VERSION_PRIMARY, 0))
    def test_send_primary_opentherm_version_zero(self, mock_opentherm_exchange):
        send_primary_opentherm_version(0)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_OPENTHERM_VERSION_PRIMARY, 0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_OPENTHERM_VERSION_PRIMARY, 0))
    def test_send_primary_opentherm_version_max(self, mock_opentherm_exchange):
        send_primary_opentherm_version(3.9375)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_OPENTHERM_VERSION_PRIMARY, 1008)


class TestOpenThermApp_send_primary_product_version(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_PRIMARY_VERSION, 0))
    def test_send_primary_product_version(self, mock_opentherm_exchange):
        send_primary_product_version(0x01, 0x02)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_PRIMARY_VERSION, 0x0102)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_PRIMARY_VERSION, 0))
    def test_send_primary_product_version_max(self, mock_opentherm_exchange):
        send_primary_product_version(0xFF, 0xFF)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_PRIMARY_VERSION, 0xFFFF)


class TestOpenThermApp_read_secondary_opentherm_version(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_OPENTHERM_VERSION_SECONDARY, 0x0102))
    def test_read_secondary_opentherm_version(self, mock_opentherm_exchange):
        result = read_secondary_opentherm_version()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_OPENTHERM_VERSION_SECONDARY, 0)
        self.assertEqual(result, 1.0078125)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_OPENTHERM_VERSION_SECONDARY, 0x0200))
    def test_read_secondary_opentherm_version_v2(self, mock_opentherm_exchange):
        result = read_secondary_opentherm_version()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_OPENTHERM_VERSION_SECONDARY, 0)
        self.assertEqual(result, 2.0)

class TestOpenThermApp_read_secondary_product_version(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_SECONDARY_VERSION, 0x0102))
    def test_read_secondary_product_version(self, mock_opentherm_exchange):
        result = read_secondary_product_version()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_SECONDARY_VERSION, 0)
        self.assertEqual(result, (1, 2))

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_SECONDARY_VERSION, 0x0304))
    def test_read_secondary_product_version_another_version(self, mock_opentherm_exchange):
        result = read_secondary_product_version()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_SECONDARY_VERSION, 0)
        self.assertEqual(result, (3, 4))

class TestOpenThermApp_control_room_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TRSET, 0))
    def test_control_room_setpoint(self, mock_opentherm_exchange):
        control_room_setpoint(50)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TRSET, 50 * 256)

    def test_control_room_setpoint_invalid(self):
        with self.assertRaises(AssertionError):
            control_room_setpoint(-41)
        with self.assertRaises(AssertionError):
            control_room_setpoint(128)

class TestOpenThermApp_control_room_setpoint_ch2(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TRSETCH2, 0))
    def test_control_room_setpoint_ch2(self, mock_opentherm_exchange):
        control_room_setpoint_ch2(50)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TRSETCH2, 50 * 256)

    def test_control_room_setpoint_ch2_invalid(self):
        with self.assertRaises(AssertionError):
            control_room_setpoint_ch2(-41)
        with self.assertRaises(AssertionError):
            control_room_setpoint_ch2(128)

class TestOpenThermApp_control_room_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TR, 0))
    def test_control_room_temperature(self, mock_opentherm_exchange):
        control_room_temperature(20)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TR, 20 * 256)

    def test_control_room_temperature_invalid(self):
        with self.assertRaises(AssertionError):
            control_room_temperature(-41)
        with self.assertRaises(AssertionError):
            control_room_temperature(128)

class TestOpenThermApp_read_relative_modulation_level(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REL_MOD_LEVEL, 0x7F00))
    def test_read_relative_modulation_level(self, mock_opentherm_exchange):
        result = read_relative_modulation_level()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REL_MOD_LEVEL, 0)
        self.assertEqual(result, 127.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REL_MOD_LEVEL, 0x0000))
    def test_read_relative_modulation_level_zero(self, mock_opentherm_exchange):
        result = read_relative_modulation_level()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REL_MOD_LEVEL, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REL_MOD_LEVEL, 0xFFFF))
    def test_read_relative_modulation_level_max(self, mock_opentherm_exchange):
        result = read_relative_modulation_level()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REL_MOD_LEVEL, 0)
        self.assertEqual(result, -0.00390625)

class TestOpenThermApp_read_ch_water_pressure(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PRESSURE, 0x1A00))
    def test_read_ch_water_pressure(self, mock_opentherm_exchange):
        result = read_ch_water_pressure()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PRESSURE, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PRESSURE, 0x0000))
    def test_read_ch_water_pressure_zero(self, mock_opentherm_exchange):
        result = read_ch_water_pressure()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PRESSURE, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PRESSURE, 0xFFFF))
    def test_read_ch_water_pressure_max(self, mock_opentherm_exchange):
        result = read_ch_water_pressure()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PRESSURE, 0)
        self.assertEqual(result, -0.00390625)

class TestOpenThermApp_read_dhw_flow_rate(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_FLOW_RATE, 0x6400))
    def test_read_dhw_flow_rate(self, mock_opentherm_exchange):
        result = read_dhw_flow_rate()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_FLOW_RATE, 0)
        self.assertEqual(result, 100.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_FLOW_RATE, 0x0000))
    def test_read_dhw_flow_rate_zero(self, mock_opentherm_exchange):
        result = read_dhw_flow_rate()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_FLOW_RATE, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_FLOW_RATE, 0xFFFF))
    def test_read_dhw_flow_rate_max(self, mock_opentherm_exchange):
        result = read_dhw_flow_rate()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_FLOW_RATE, 0)
        self.assertEqual(result, -0.00390625)

class TestOpenThermApp_read_boiler_flow_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TBOILER, 0x1A00))
    def test_read_boiler_flow_temperature(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TBOILER, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TBOILER, 0x0000))
    def test_read_boiler_flow_temperature_zero(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TBOILER, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TBOILER, 0xFFFF))
    def test_read_boiler_flow_temperature_max(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TBOILER, 0)
        self.assertEqual(result, -0.00390625)

class TestOpenThermApp_read_boiler_flow_temperature_ch2(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TFLOWCH2, 0x1A00))
    def test_read_boiler_flow_temperature_ch2(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature_ch2()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TFLOWCH2, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TFLOWCH2, 0x0000))
    def test_read_boiler_flow_temperature_ch2_zero(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature_ch2()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TFLOWCH2, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TFLOWCH2, 0xFFFF))
    def test_read_boiler_flow_temperature_ch2_max(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature_ch2()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TFLOWCH2, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TFLOWCH2, 0x8000))
    def test_read_boiler_flow_temperature_ch2_negative(self, mock_opentherm_exchange):
        result = read_boiler_flow_temperature_ch2()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TFLOWCH2, 0)
        self.assertEqual(result, -128.0)


class TestOpenThermApp_read_dhw_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW, 0x1A00))
    def test_read_dhw_temperature(self, mock_opentherm_exchange):
        result = read_dhw_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW, 0x0000))
    def test_read_dhw_temperature_zero(self, mock_opentherm_exchange):
        result = read_dhw_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW, 0xFFFF))
    def test_read_dhw_temperature_max(self, mock_opentherm_exchange):
        result = read_dhw_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW, 0x8000))
    def test_read_dhw_temperature_negative(self, mock_opentherm_exchange):
        result = read_dhw_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_dhw2_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW2, 0x1A00))
    def test_read_dhw2_temperature(self, mock_opentherm_exchange):
        result = read_dhw2_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW2, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW2, 0x0000))
    def test_read_dhw2_temperature_zero(self, mock_opentherm_exchange):
        result = read_dhw2_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW2, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW2, 0xFFFF))
    def test_read_dhw2_temperature_max(self, mock_opentherm_exchange):
        result = read_dhw2_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW2, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TDHW2, 0x8000))
    def test_read_dhw2_temperature_negative(self, mock_opentherm_exchange):
        result = read_dhw2_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TDHW2, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_exhaust_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TEXHAUST, 0x1A00))
    def test_read_exhaust_temperature(self, mock_opentherm_exchange):
        result = read_exhaust_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TEXHAUST, 0)
        self.assertEqual(result, 0x1a00)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TEXHAUST, 0x0000))
    def test_read_exhaust_temperature_zero(self, mock_opentherm_exchange):
        result = read_exhaust_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TEXHAUST, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TEXHAUST, 0xFFFF))
    def test_read_exhaust_temperature_max(self, mock_opentherm_exchange):
        result = read_exhaust_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TEXHAUST, 0)
        self.assertEqual(result, -1)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TEXHAUST, 0x8000))
    def test_read_exhaust_temperature_negative(self, mock_opentherm_exchange):
        result = read_exhaust_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TEXHAUST, 0)
        self.assertEqual(result, -32768)

class TestOpenThermApp_read_outside_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TOUTSIDE, 0x1A00))
    def test_read_outside_temperature(self, mock_opentherm_exchange):
        result = read_outside_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TOUTSIDE, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TOUTSIDE, 0x0000))
    def test_read_outside_temperature_zero(self, mock_opentherm_exchange):
        result = read_outside_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TOUTSIDE, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TOUTSIDE, 0xFFFF))
    def test_read_outside_temperature_max(self, mock_opentherm_exchange):
        result = read_outside_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TOUTSIDE, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TOUTSIDE, 0x8000))
    def test_read_outside_temperature_negative(self, mock_opentherm_exchange):
        result = read_outside_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TOUTSIDE, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_boiler_return_water_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TRET, 0x1A00))
    def test_read_boiler_return_water_temperature(self, mock_opentherm_exchange):
        result = read_boiler_return_water_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TRET, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TRET, 0x0000))
    def test_read_boiler_return_water_temperature_zero(self, mock_opentherm_exchange):
        result = read_boiler_return_water_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TRET, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TRET, 0xFFFF))
    def test_read_boiler_return_water_temperature_max(self, mock_opentherm_exchange):
        result = read_boiler_return_water_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TRET, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TRET, 0x8000))
    def test_read_boiler_return_water_temperature_negative(self, mock_opentherm_exchange):
        result = read_boiler_return_water_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TRET, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_solar_storage_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSTORAGE, 0x1A00))
    def test_read_solar_storage_temperature(self, mock_opentherm_exchange):
        result = read_solar_storage_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSTORAGE, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSTORAGE, 0x0000))
    def test_read_solar_storage_temperature_zero(self, mock_opentherm_exchange):
        result = read_solar_storage_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSTORAGE, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSTORAGE, 0xFFFF))
    def test_read_solar_storage_temperature_max(self, mock_opentherm_exchange):
        result = read_solar_storage_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSTORAGE, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSTORAGE, 0x8000))
    def test_read_solar_storage_temperature_negative(self, mock_opentherm_exchange):
        result = read_solar_storage_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSTORAGE, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_solar_collector_temperature(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TCOLLECTOR, 0x1A00))
    def test_read_solar_collector_temperature(self, mock_opentherm_exchange):
        result = read_solar_collector_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TCOLLECTOR, 0)
        self.assertEqual(result, 0x1a00)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TCOLLECTOR, 0x0000))
    def test_read_solar_collector_temperature_zero(self, mock_opentherm_exchange):
        result = read_solar_collector_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TCOLLECTOR, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TCOLLECTOR, 0xFFFF))
    def test_read_solar_collector_temperature_max(self, mock_opentherm_exchange):
        result = read_solar_collector_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TCOLLECTOR, 0)
        self.assertEqual(result, -1)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TCOLLECTOR, 0x8000))
    def test_read_solar_collector_temperature_negative(self, mock_opentherm_exchange):
        result = read_solar_collector_temperature()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TCOLLECTOR, 0)
        self.assertEqual(result, -32768)

class TestOpenThermApp_read_burner_starts(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_STARTS, 0x1234))
    def test_read_burner_starts(self, mock_opentherm_exchange):
        result = read_burner_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_STARTS, 0)
        self.assertEqual(result, 0x1234)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_STARTS, 0xFFFF))
    def test_read_burner_starts_max(self, mock_opentherm_exchange):
        result = read_burner_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_STARTS, 0)
        self.assertEqual(result, 0xFFFF)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_STARTS, 0x0000))
    def test_read_burner_starts_zero(self, mock_opentherm_exchange):
        result = read_burner_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_STARTS, 0)
        self.assertEqual(result, 0x0000)

class TestOpenThermApp_read_ch_pump_starts(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PUMP_STARTS, 0x05))
    def test_read_ch_pump_starts(self, mock_opentherm_exchange):
        result = read_ch_pump_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_STARTS, 0)
        self.assertEqual(result, 5)

class TestOpenThermApp_read_dhw_pump_starts(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_PUMP_STARTS, 0x05))
    def test_read_dhw_pump_starts(self, mock_opentherm_exchange):
        result = read_dhw_pump_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_STARTS, 0)
        self.assertEqual(result, 5)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_PUMP_STARTS, 0xFF))
    def test_read_dhw_pump_starts_max(self, mock_opentherm_exchange):
        result = read_dhw_pump_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_STARTS, 0)
        self.assertEqual(result, 255)

class TestOpenThermApp_read_dhw_burner_starts(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_BURNER_STARTS, 0x05))
    def test_read_dhw_burner_starts(self, mock_opentherm_exchange):
        result = read_dhw_burner_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_STARTS, 0)
        self.assertEqual(result, 5)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_BURNER_STARTS, 0xFF))
    def test_read_dhw_burner_starts_max(self, mock_opentherm_exchange):
        result = read_dhw_burner_starts()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_STARTS, 0)
        self.assertEqual(result, 255)

class TestOpenThermApp_read_burner_operation_hours(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_OPERATION_HOURS, 0x1234))
    def test_read_burner_operation_hours(self, mock_opentherm_exchange):
        result = read_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x1234)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_OPERATION_HOURS, 0xFFFF))
    def test_read_burner_operation_hours_max(self, mock_opentherm_exchange):
        result = read_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0xFFFF)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_BURNER_OPERATION_HOURS, 0x0000))
    def test_read_burner_operation_hours_zero(self, mock_opentherm_exchange):
        result = read_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x0000)

class TestOpenThermApp_read_ch_pump_operation_hours(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PUMP_OPERATION_HOURS, 0x1234))
    def test_read_ch_pump_operation_hours(self, mock_opentherm_exchange):
        result = read_ch_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x1234)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PUMP_OPERATION_HOURS, 0xFFFF))
    def test_read_ch_pump_operation_hours_max(self, mock_opentherm_exchange):
        result = read_ch_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0xFFFF)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_CH_PUMP_OPERATION_HOURS, 0x0000))
    def test_read_ch_pump_operation_hours_zero(self, mock_opentherm_exchange):
        result = read_ch_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x0000)

class TestOpenThermApp_read_dhw_pump_operation_hours(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0x1234))
    def test_read_dhw_pump_operation_hours(self, mock_opentherm_exchange):
        result = read_dhw_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x1234)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0xFFFF))
    def test_read_dhw_pump_operation_hours_max(self, mock_opentherm_exchange):
        result = read_dhw_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0xFFFF)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0x0000))
    def test_read_dhw_pump_operation_hours_zero(self, mock_opentherm_exchange):
        result = read_dhw_pump_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x0000)

class TestOpenThermApp_read_dhw_burner_operation_hours(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0x1234))
    def test_read_dhw_burner_operation_hours(self, mock_opentherm_exchange):
        result = read_dhw_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x1234)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0xFFFF))
    def test_read_dhw_burner_operation_hours_max(self, mock_opentherm_exchange):
        result = read_dhw_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0xFFFF)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0x0000))
    def test_read_dhw_burner_operation_hours_zero(self, mock_opentherm_exchange):
        result = read_dhw_burner_operation_hours()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0)
        self.assertEqual(result, 0x0000)

class TestOpenThermApp_control_ch2_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_TSETCH2, 0))
    def test_control_ch2_setpoint(self, mock_opentherm_exchange):
        control_ch2_setpoint(50.0)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_TSETCH2, 50 * 256)

    def test_control_ch2_setpoint_invalid(self):
        with self.assertRaises(AssertionError):
            control_ch2_setpoint(-1)
        with self.assertRaises(AssertionError):
            control_ch2_setpoint(101)

class TestOpenThermApp_read_hcratio_range(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO_BOUNDS, 0x1F0A))
    def test_read_hcratio_range(self, mock_opentherm_exchange):
        result = read_hcratio_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO_BOUNDS, 0)
        self.assertEqual(result, (10, 31))

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO_BOUNDS, 0x0000))
    def test_read_hcratio_range_zero(self, mock_opentherm_exchange):
        result = read_hcratio_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO_BOUNDS, 0)
        self.assertEqual(result, (0, 0))

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO_BOUNDS, 0xFFFF))
    def test_read_hcratio_range_max(self, mock_opentherm_exchange):
        result = read_hcratio_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO_BOUNDS, 0)
        self.assertEqual(result, (-1, -1))

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO_BOUNDS, 0x8000))
    def test_read_hcratio_range_negative(self, mock_opentherm_exchange):
        result = read_hcratio_range()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO_BOUNDS, 0)
        self.assertEqual(result, (0, -128))

class TestOpenThermApp_control_hcratio(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_HCRATIO, 0))
    def test_control_hcratio(self, mock_opentherm_exchange):
        control_hcratio(50.0)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_HCRATIO, int(50.0 * 256))

    def test_control_hcratio_invalid(self):
        with self.assertRaises(AssertionError):
            control_hcratio(-1)
        with self.assertRaises(AssertionError):
            control_hcratio(101)

class TestOpenThermApp_read_hcratio(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO, 0x7FFF))
    def test_read_hcratio(self, mock_opentherm_exchange):
        result = read_hcratio()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO, 0)
        self.assertEqual(result, 127.99609375)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO, 0x0000))
    def test_read_hcratio_zero(self, mock_opentherm_exchange):
        result = read_hcratio()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_HCRATIO, 0x8000))
    def test_read_hcratio_negative(self, mock_opentherm_exchange):
        result = read_hcratio()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_HCRATIO, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_control_cooling(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_COOLING_CONTROL, 0))
    def test_control_cooling(self, mock_opentherm_exchange):
        control_cooling(50.0)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_COOLING_CONTROL, int(50.0 * 256))

    def test_control_cooling_invalid(self):
        with self.assertRaises(AssertionError):
            control_cooling(-1)
        with self.assertRaises(AssertionError):
            control_cooling(101)


class TestOpenThermApp_control_date_time(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', side_effect=[(MSG_TYPE_WRITE_ACK, DATA_ID_YEAR, 2022),
                                                            (MSG_TYPE_WRITE_ACK, DATA_ID_DATE, 0x0108),
                                                            (MSG_TYPE_WRITE_ACK, DATA_ID_DAY_TIME, 0xd70A)])
    def test_control_date_time(self, mock_opentherm_exchange):
        control_date_time(datetime.datetime(2022, 1, 8, 23, 10))
        mock_opentherm_exchange.assert_has_calls([call(MSG_TYPE_WRITE_DATA, DATA_ID_YEAR, 2022),
                                                   call(MSG_TYPE_WRITE_DATA, DATA_ID_DATE, 0x0108),
                                                   call(MSG_TYPE_WRITE_DATA, DATA_ID_DAY_TIME, 0xd70A)])


class TestOpenThermApp_read_tsp_count(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSP_COUNT, 0x0102))
    def test_read_tsp_count(self, mock_opentherm_exchange):
        result = read_tsp_count()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSP_COUNT, 0)
        self.assertEqual(result, 1)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSP_COUNT, 0x0A0B))
    def test_read_tsp_count_max(self, mock_opentherm_exchange):
        result = read_tsp_count()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSP_COUNT, 0)
        self.assertEqual(result, 10)


class TestOpenThermApp_read_tsp(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TSP_DATA, 0x1234))
    def test_read_tsp(self, mock_opentherm_exchange):
        result = read_tsp(0x12)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TSP_DATA, 0x1200)
        self.assertEqual(result, 0x34)


class TestOpenThermApp_read_fhb_count(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_COUNT, 0x1234))
    def test_read_fhb_count(self, mock_opentherm_exchange):
        result = read_fhb_count()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_COUNT, 0)
        self.assertEqual(result, 0x12)

class TestOpenThermApp_read_fhb(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_DATA, 0x1234))
    def test_read_fhb(self, mock_opentherm_exchange):
        result = read_fhb(0x12)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, 0x1200)
        self.assertEqual(result, 0x34)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_DATA, 0x5678))
    def test_read_fhb_different_index(self, mock_opentherm_exchange):
        result = read_fhb(0x56)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, 0x5600)
        self.assertEqual(result, 0x78)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_DATA, 0x9ABC))
    def test_read_fhb_max_value(self, mock_opentherm_exchange):
        result = read_fhb(0x9A)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, 0x9A00)
        self.assertEqual(result, 0xBC)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_DATA, 0x00))
    def test_read_fhb_min_value(self, mock_opentherm_exchange):
        result = read_fhb(0x00)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, 0x0000)
        self.assertEqual(result, 0x00)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_FHB_DATA, 0xFFFF))
    def test_read_fhb_max_byte_value(self, mock_opentherm_exchange):
        result = read_fhb(0xFF)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, 0xFF00)
        self.assertEqual(result, 0xFF)

class TestOpenThermApp_read_remote_override_room_setpoint(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TROVERRIDE, 0x1A00))
    def test_read_remote_override_room_setpoint(self, mock_opentherm_exchange):
        result = read_remote_override_room_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TROVERRIDE, 0)
        self.assertEqual(result, 26.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TROVERRIDE, 0x0000))
    def test_read_remote_override_room_setpoint_zero(self, mock_opentherm_exchange):
        result = read_remote_override_room_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TROVERRIDE, 0)
        self.assertEqual(result, 0.0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TROVERRIDE, 0xFFFF))
    def test_read_remote_override_room_setpoint_max(self, mock_opentherm_exchange):
        result = read_remote_override_room_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TROVERRIDE, 0)
        self.assertEqual(result, -0.00390625)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_TROVERRIDE, 0x8000))
    def test_read_remote_override_room_setpoint_negative(self, mock_opentherm_exchange):
        result = read_remote_override_room_setpoint()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_TROVERRIDE, 0)
        self.assertEqual(result, -128.0)

class TestOpenThermApp_read_remote_override_function(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0b00000011))
    def test_read_remote_override_function_both_priorities(self, mock_opentherm_exchange):
        result = read_remote_override_function()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0)
        self.assertEqual(result, {
            'manual_change_priority': True,
            'program_change_priority': True
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0b00000001))
    def test_read_remote_override_function_manual_priority(self, mock_opentherm_exchange):
        result = read_remote_override_function()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0)
        self.assertEqual(result, {
            'manual_change_priority': True,
            'program_change_priority': False
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0b00000010))
    def test_read_remote_override_function_program_priority(self, mock_opentherm_exchange):
        result = read_remote_override_function()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0)
        self.assertEqual(result, {
            'manual_change_priority': False,
            'program_change_priority': True
        })

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_READ_ACK, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0b00000000))
    def test_read_remote_override_function_no_priority(self, mock_opentherm_exchange):
        result = read_remote_override_function()
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_READ_DATA, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0)
        self.assertEqual(result, {
            'manual_change_priority': False,
            'program_change_priority': False
        })

class TestOpenThermApp_control_remote_command(unittest.TestCase):
    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_COMMAND, 10 << 8))
    def test_control_remote_command(self, mock_opentherm_exchange):
        result = control_remote_command(10)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_COMMAND, 10 << 8)
        self.assertEqual(result, 0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_COMMAND, 0xffff))
    def test_control_remote_command_max(self, mock_opentherm_exchange):
        result = control_remote_command(255)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_COMMAND, 0xff00)
        self.assertEqual(result, 255)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_COMMAND, 0))
    def test_control_remote_command_min(self, mock_opentherm_exchange):
        result = control_remote_command(0)
        mock_opentherm_exchange.assert_called_once_with(MSG_TYPE_WRITE_DATA, DATA_ID_COMMAND, 0 << 8)
        self.assertEqual(result, 0)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_DATA, DATA_ID_COMMAND, 0))
    def test_control_remote_command_wrong_msg_type(self, mock_opentherm_exchange):
        with self.assertRaises(AssertionError):
            control_remote_command(10)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_STATUS, 0))
    def test_control_remote_command_wrong_data_id(self, mock_opentherm_exchange):
        with self.assertRaises(AssertionError):
            control_remote_command(10)

    @patch('opentherm_app.opentherm_exchange', return_value=(MSG_TYPE_WRITE_ACK, DATA_ID_COMMAND, 0))
    def test_control_remote_command_wrong_data(self, mock_opentherm_exchange):
        with self.assertRaises(AssertionError):
            control_remote_command(10)

