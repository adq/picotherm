from lib import s8, s16, f88
# import datetime
# from typing import Optional

try:
    from opentherm_rp2 import opentherm_exchange

except ImportError:
    # dummy implementation so it loads on non-pico for unit tests
    def opentherm_exchange(msg_type: int, data_id: int, data_value: int, timeout_ms: int = 1000) -> tuple[int, int, int]:
        raise NotImplementedError("opentherm_exchange not implemented on this platform")  # pragma: nocover


MSG_TYPE_READ_DATA = 0
MSG_TYPE_WRITE_DATA = 1
MSG_TYPE_INVALID_DATA = 2
MSG_TYPE_READ_ACK = 4
MSG_TYPE_WRITE_ACK = 5
MSG_TYPE_DATA_INVALID = 6
MSG_TYPE_UNKNOWN_DATA_ID = 7

DATA_ID_STATUS = 0
DATA_ID_TSET = 1
DATA_ID_PRIMARY_CONFIG = 2
DATA_ID_SECONDARY_CONFIG = 3
DATA_ID_COMMAND = 4
DATA_ID_ASF_FAULT = 5
DATA_ID_RBP_FLAGS = 6
DATA_ID_COOLING_CONTROL = 7
DATA_ID_TSETCH2 = 8
DATA_ID_TROVERRIDE = 9
DATA_ID_TSP_COUNT = 10
DATA_ID_TSP_DATA = 11
DATA_ID_FHB_COUNT = 12
DATA_ID_FHB_DATA = 13
DATA_ID_MAX_REL_MODULATION = 14
DATA_ID_MAX_CAPACITY_MIN_MODULATION = 15
DATA_ID_TRSET = 16
DATA_ID_REL_MOD_LEVEL = 17
DATA_ID_CH_PRESSURE = 18
DATA_ID_DHW_FLOW_RATE = 19
DATA_ID_DAY_TIME = 20
DATA_ID_DATE = 21
DATA_ID_YEAR = 22
DATA_ID_TRSETCH2 = 23
DATA_ID_TR = 24
DATA_ID_TBOILER = 25
DATA_ID_TDHW = 26
DATA_ID_TOUTSIDE = 27
DATA_ID_TRET = 28
DATA_ID_TSTORAGE = 29
DATA_ID_TCOLLECTOR = 30
DATA_ID_TFLOWCH2 = 31
DATA_ID_TDHW2 = 32
DATA_ID_TEXHAUST = 33
DATA_ID_BOILER_FAN_SPEED = 35

DATA_ID_TDHWSET_BOUNDS = 48
DATA_ID_MAXTSET_BOUNDS = 49
DATA_ID_HCRATIO_BOUNDS = 50

DATA_ID_TDHWSET = 56
DATA_ID_MAXTSET = 57
DATA_ID_HCRATIO = 58

DATA_ID_REMOTE_OVERRIDE_FUNCTION = 100
DATA_ID_OEM_DIAGNOSTIC_CODE = 115
DATA_ID_BURNER_STARTS = 116
DATA_ID_CH_PUMP_STARTS = 117
DATA_ID_DHW_PUMP_STARTS = 118
DATA_ID_DHW_BURNER_STARTS = 119
DATA_ID_BURNER_OPERATION_HOURS = 120
DATA_ID_CH_PUMP_OPERATION_HOURS = 121
DATA_ID_DHW_PUMP_OPERATION_HOURS = 122
DATA_ID_DHW_BURNER_OPERATION_HOURS = 123
DATA_ID_OPENTHERM_VERSION_PRIMARY = 124
DATA_ID_OPENTHERM_VERSION_SECONDARY = 125
DATA_ID_PRIMARY_VERSION = 126
DATA_ID_SECONDARY_VERSION = 127

REMOTE_COMAND_BLOR = 1  # boiler lock out reset command
REMOTE_COMAND_CHWF = 2  # CH water filling command


def status_exchange(
    ch_enabled=False,
    dhw_enabled=False,
    cooling_enabled=False,
    otc_enabled=False,
    ch2_enabled=False,
) -> dict:
    data = 0
    data |= 0x0100 if ch_enabled else 0
    data |= 0x0200 if dhw_enabled else 0
    data |= 0x0400 if cooling_enabled else 0
    data |= 0x0800 if otc_enabled else 0
    data |= 0x1000 if ch2_enabled else 0

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_STATUS, data
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_STATUS

    result = dict(
        fault=True if r_data & 0x01 else False,
        ch_active=True if r_data & 0x02 else False,
        dhw_active=True if r_data & 0x04 else False,
        flame_active=True if r_data & 0x08 else False,
        cooling_active=True if r_data & 0x10 else False,
        ch2_active=True if r_data & 0x20 else False,
        diagnostic_event=True if r_data & 0x40 else False,
    )
    return result


def send_primary_configuration(memberid_code: int):
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_PRIMARY_CONFIG, memberid_code & 0xFF
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_PRIMARY_CONFIG


def send_primary_opentherm_version(version: float):
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_OPENTHERM_VERSION_PRIMARY, int(version * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_OPENTHERM_VERSION_PRIMARY


def send_primary_product_version(type: int, version: int):
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_PRIMARY_VERSION, ((type & 0xff) << 8) | (version & 0xff)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_PRIMARY_VERSION


def read_secondary_configuration() -> dict:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_SECONDARY_CONFIG, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_SECONDARY_CONFIG

    result = dict(
        dhw_present=True if r_data & 0x0100 else False,
        control_type="onoff" if r_data & 0x0200 else "modulating",
        cooling_config=True if r_data & 0x0400 else False,
        dhw_config="storage" if r_data & 0x0800 else "instantaneous",
        low_off_and_pump_control=True if not (r_data & 0x1000) else False,
        ch2_supported=True if r_data & 0x2000 else False,
        memberid_code=r_data & 0xFF,
    )
    return result


def read_secondary_opentherm_version() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_OPENTHERM_VERSION_SECONDARY, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_OPENTHERM_VERSION_SECONDARY
    return f88(r_data)


def read_secondary_product_version() -> tuple[int, int]:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_SECONDARY_VERSION, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_SECONDARY_VERSION
    return r_data >> 8, r_data & 0xff


def control_ch_setpoint(setpoint: float):
    assert setpoint >= 0 and setpoint <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TSET, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TSET


def control_ch2_setpoint(setpoint: float):
    assert setpoint >= 0 and setpoint <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TSETCH2, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TSETCH2


# FIXME: can we read the ch setpoint?


def read_dhw_setpoint_range() -> tuple[int, int]:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TDHWSET_BOUNDS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TDHWSET_BOUNDS

    return s8(r_data & 0xFF), s8(r_data >> 8)


def control_dhw_setpoint(setpoint: int):
    assert setpoint >= 0 and setpoint <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TDHWSET, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TDHWSET


def read_dhw_setpoint() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TDHWSET, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TDHWSET
    return f88(r_data)


def control_room_setpoint(setpoint: float):
    assert setpoint >= -40 and setpoint <= 127

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TRSET, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TRSET


def control_room_setpoint_ch2(setpoint: float):
    assert setpoint >= -40 and setpoint <= 127

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TRSETCH2, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TRSETCH2


def control_room_temperature(setpoint: float):
    assert setpoint >= -40 and setpoint <= 127

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_TR, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_TR


def control_cooling(signal: float):
    assert signal >= 0 and signal <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_COOLING_CONTROL, int(signal * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_COOLING_CONTROL


def read_maxch_setpoint_range() -> tuple[int, int]:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_MAXTSET_BOUNDS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_MAXTSET_BOUNDS

    return s8(r_data & 0xFF), s8(r_data >> 8)


def control_maxch_setpoint(setpoint: float):
    assert setpoint >= 0 and setpoint <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_MAXTSET, int(setpoint * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_MAXTSET


def read_maxch_setpoint() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_MAXTSET, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_MAXTSET
    return f88(r_data)



def read_hcratio_range() -> tuple[int, int]:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_HCRATIO_BOUNDS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_HCRATIO_BOUNDS

    return s8(r_data & 0xFF), s8(r_data >> 8)


def control_hcratio(ratio: float):
    assert ratio >= 0 and ratio <= 100

    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_HCRATIO, int(ratio * 256)
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_HCRATIO


def read_hcratio() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_HCRATIO, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_HCRATIO
    return f88(r_data)


def read_extra_boiler_params_support() -> dict:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_RBP_FLAGS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_RBP_FLAGS

    dhw_setpoint = None
    if r_data & 0x0100:
        if r_data & 0x01:
            dhw_setpoint = "rw"
        else:
            dhw_setpoint = "ro"

    maxch_setpoint = None
    if r_data & 0x200:
        if r_data & 0x02:
            maxch_setpoint = "rw"
        else:
            maxch_setpoint = "ro"

    result = dict(dhw_setpoint=dhw_setpoint, maxch_setpoint=maxch_setpoint)
    return result


def read_fault_flags() -> dict:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_ASF_FAULT, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_ASF_FAULT

    result = dict(
        service_required=True if r_data & 0x0100 else False,
        blor_enabled=True if r_data & 0x0200 else False,
        low_water_pressure=True if r_data & 0x0400 else False,
        flame_fault=True if r_data & 0x0800 else False,
        air_pressure_fault=True if r_data & 0x1000 else False,
        water_over_temp=True if r_data & 0x2000 else False,
        oem_code=r_data & 0xFF,
    )
    return result


def read_oem_long_code() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_OEM_DIAGNOSTIC_CODE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_OEM_DIAGNOSTIC_CODE
    return r_data


def read_relative_modulation_level() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_REL_MOD_LEVEL, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_REL_MOD_LEVEL
    return f88(r_data)


def read_ch_water_pressure() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_CH_PRESSURE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_CH_PRESSURE
    return f88(r_data)


def read_dhw_flow_rate() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_DHW_FLOW_RATE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_DHW_FLOW_RATE
    return f88(r_data)


def read_boiler_flow_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TBOILER, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TBOILER
    return f88(r_data)


def read_boiler_flow_temperature_ch2() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TFLOWCH2, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TFLOWCH2
    return f88(r_data)


def read_dhw_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TDHW, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TDHW
    return f88(r_data)


def read_dhw2_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TDHW2, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TDHW2
    return f88(r_data)


def read_exhaust_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TEXHAUST, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TEXHAUST
    return s16(r_data)


def read_outside_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TOUTSIDE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TOUTSIDE
    return f88(r_data)


def read_boiler_return_water_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TRET, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TRET
    return f88(r_data)


def read_solar_storage_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TSTORAGE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TSTORAGE
    return f88(r_data)


def read_solar_collector_temperature() -> float:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TCOLLECTOR, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TCOLLECTOR
    return s16(r_data)


def read_burner_starts() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_BURNER_STARTS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_BURNER_STARTS
    return r_data


def read_ch_pump_starts() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_STARTS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_CH_PUMP_STARTS
    return r_data


def read_dhw_pump_starts() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_STARTS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_DHW_PUMP_STARTS
    return r_data


def read_dhw_burner_starts() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_STARTS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_DHW_BURNER_STARTS
    return r_data


def read_burner_operation_hours() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_BURNER_OPERATION_HOURS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_BURNER_OPERATION_HOURS
    return r_data


def read_ch_pump_operation_hours() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_CH_PUMP_OPERATION_HOURS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_CH_PUMP_OPERATION_HOURS
    return r_data


def read_dhw_pump_operation_hours() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_DHW_PUMP_OPERATION_HOURS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_DHW_PUMP_OPERATION_HOURS
    return r_data


def read_dhw_burner_operation_hours() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_DHW_BURNER_OPERATION_HOURS, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_DHW_BURNER_OPERATION_HOURS
    return r_data


# def control_date_time(t: Optional[datetime.datetime] = None):
#     if t is None:
#         t = datetime.datetime.now()  # pragma: nocover

#     r_msg_type, r_data_id, r_data = opentherm_exchange(
#         MSG_TYPE_WRITE_DATA, DATA_ID_YEAR, t.year
#     )
#     assert r_msg_type == MSG_TYPE_WRITE_ACK
#     assert r_data_id == DATA_ID_YEAR

#     r_msg_type, r_data_id, r_data = opentherm_exchange(
#         MSG_TYPE_WRITE_DATA, DATA_ID_DATE, (t.month << 8) | t.day
#     )
#     assert r_msg_type == MSG_TYPE_WRITE_ACK
#     assert r_data_id == DATA_ID_DATE

#     r_msg_type, r_data_id, r_data = opentherm_exchange(
#         MSG_TYPE_WRITE_DATA, DATA_ID_DAY_TIME, (t.isoweekday() << 13) | (t.hour << 8) | t.minute
#     )
#     assert r_msg_type == MSG_TYPE_WRITE_ACK
#     assert r_data_id == DATA_ID_DAY_TIME


def read_tsp_count() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TSP_COUNT, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TSP_COUNT
    return r_data >> 8


def read_tsp(index: int) -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TSP_DATA, (index << 8)
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TSP_DATA
    assert r_data >> 8 == index
    return r_data & 0xff


def read_fhb_count() -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_FHB_COUNT, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_FHB_COUNT
    return r_data >> 8


def read_fhb(index: int) -> int:
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_FHB_DATA, (index << 8)
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_FHB_DATA
    assert r_data >> 8 == index
    return r_data & 0xff


def control_remote_command(command: int):
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_WRITE_DATA, DATA_ID_COMMAND, command << 8
    )
    assert r_msg_type == MSG_TYPE_WRITE_ACK
    assert r_data_id == DATA_ID_COMMAND
    assert r_data >> 8 == command
    return r_data & 0xff


def read_remote_override_room_setpoint():
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_TROVERRIDE, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_TROVERRIDE
    return f88(r_data)


def read_remote_override_function():
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_REMOTE_OVERRIDE_FUNCTION, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_REMOTE_OVERRIDE_FUNCTION

    result = dict(manual_change_priority=True if r_data & 0x01 else False,
                  program_change_priority=True if r_data & 0x02 else False)
    return result


def read_capacity_and_min_modulation():
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_MAX_CAPACITY_MIN_MODULATION, 0
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_MAX_CAPACITY_MIN_MODULATION

    return r_data >> 8, r_data & 0xff


def control_max_relative_modulation_level(l: int):
    r_msg_type, r_data_id, r_data = opentherm_exchange(
        MSG_TYPE_READ_DATA, DATA_ID_MAX_REL_MODULATION, int(l * 256)
    )
    assert r_msg_type == MSG_TYPE_READ_ACK
    assert r_data_id == DATA_ID_MAX_REL_MODULATION
