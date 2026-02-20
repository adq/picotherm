import opentherm_app
import time
import network
import asyncio
import cfgsecrets
import json
import utime
import sys
import rp2
from lib import send_syslog
from async_mqtt_client import AsyncMQTTClient


class BoilerRestartDetected(Exception):
    """Raised when boiler power cycle counter changes, indicating a restart"""
    pass


class BoilerValues():
    # readable things
    boiler_flow_temperature: float = 0.0
    boiler_return_temperature: float = 0.0
    boiler_exhaust_temperature: float = 0.0
    boiler_dhw_temperature: float = 0.0
    boiler_fan_speed: float = 0.0
    boiler_modulation_level: float = 0.0
    boiler_ch_pressure: float = 0.0
    boiler_dhw_flow_rate: float = 0.0
    boiler_max_capacity: float = 0
    boiler_flame_active: bool = False
    boiler_ch_active: bool = False
    boiler_dhw_active: bool = False
    boiler_fault_active: bool = False
    boiler_fault_low_water_pressure: bool = False
    boiler_fault_flame: bool = False
    boiler_fault_low_air_pressure: bool = False
    boiler_fault_high_water_temperature: bool = False

    # writable things
    boiler_ch_enabled: bool = False
    boiler_dhw_enabled: bool = True

    boiler_flow_temperature_setpoint: float = 65.0
    boiler_flow_temperature_setpoint_rangemin: float = 0.0
    boiler_flow_temperature_setpoint_rangemax: float = 100.0

    boiler_dhw_temperature_setpoint: float = 60.0
    boiler_dhw_temperature_setpoint_rangemin: float = 0.0
    boiler_dhw_temperature_setpoint_rangemax: float = 100.0

    # RBP flags from boiler (None = not yet read, "rw" = read/write, "ro" = read-only)
    rbp_dhw_setpoint: str = None
    rbp_maxch_setpoint: str = None

    # Power cycle counter for restart detection (None = not yet read or unsupported)
    last_power_cycles: int = None

boiler_values = BoilerValues()
mqtt_client_instance = None


STATUS_LOOP_DELAY_MS = 750
GET_DETAILED_STATS_MS = 10 * 1000
WRITE_SETTINGS_MS = 10 * 1000
MQTT_PUBLISH_MS = 10 * 1000

BOILER_RETURN_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                    "state_topic": "homeassistant/sensor/boilerReturnTemperature/state",
                                                    "unit_of_measurement": "°C",
                                                    "unique_id": "boilerReturnTemperature",
                                                    "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                    "name": "Return Temperature",
                                                    })

BOILER_EXHAUST_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                     "state_topic": "homeassistant/sensor/boilerExhaustTemperature/state",
                                                     "unit_of_measurement": "°C",
                                                     "unique_id": "boilerExhaustTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "name": "Exhaust Temperature",
                                                     })

BOILER_FAN_SPEED_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerFanSpeed/state",
                                           "unit_of_measurement": "rpm",
                                           "unique_id": "boilerFanSpeed",
                                           "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                           "name": "Fan Speed",
                                           })

BOILER_MODULATION_LEVEL_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerModulationLevel/state",
                                                  "unit_of_measurement": "percent",
                                                  "unique_id": "boilerModulationLevel",
                                                  "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                  "name": "Current Modulation Level",
                                                  })

BOILER_CH_PRESSURE_HASS_CONFIG = json.dumps({"device_class": "pressure",
                                             "state_topic": "homeassistant/sensor/boilerChPressure/state",
                                             "unit_of_measurement": "bar",
                                             "unique_id": "boilerChPressure",
                                             "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                             "name": "CH Pressure",
                                             })

BOILER_DHW_FLOW_RATE_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerDhwFlowRate/state",
                                               "unit_of_measurement": "l/min",
                                               "unique_id": "boilerDhwFlowRate",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "HW Flow Rate",
                                               })

BOILER_MAX_CAPACITY_HASS_CONFIG = json.dumps({ "device_class": "power",
                                               "state_topic": "homeassistant/sensor/boilerMaxCapacity/state",
                                               "unit_of_measurement": "kW",
                                               "unique_id": "boilerMaxCapacity",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Max Capacity",
                                               })

BOILER_FLAME_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
                                               "state_topic": "homeassistant/binary_sensor/boilerFlameActive/state",
                                               "unique_id": "boilerFlameActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Flame Active",
                                               })

BOILER_FAULT_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultActive/state",
                                               "unique_id": "boilerFaultActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Fault",
                                               })

BOILER_FAULT_LOW_WATER_PRESSURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultLowWaterPressure/state",
                                               "unique_id": "boilerFaultLowWaterPressure",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Low CH Water Pressure",
                                               })

BOILER_FAULT_FLAME_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultFlame/state",
                                               "unique_id": "boilerFaultFlame",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Flame",
                                               })

BOILER_FAULT_LOW_AIR_PRESSURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultLowAirPressure/state",
                                               "unique_id": "boilerFaultLowAirPressure",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Low Air Pressure",
                                               })

BOILER_FAULT_HIGH_WATER_TEMPERATURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                                "state_topic": "homeassistant/binary_sensor/boilerHighWaterTemperature/state",
                                                "unique_id": "boilerHighWaterTemperature",
                                                "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                "name": "High Water Temperature",
                                                })

BOILER_CH_ENABLED_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/switch/boilerCHEnabled/state",
                                            "command_topic": "homeassistant/switch/boilerCHEnabled/command",
                                            "unique_id": "boilerCHEnabled",
                                            "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                            "name": "Heating Enabled",
                                            })

BOILER_CH_FLOW_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                     "state_topic": "homeassistant/sensor/boilerCHFlowTemperature/state",
                                                     "unit_of_measurement": "°C",
                                                     "unique_id": "boilerCHFlowTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "name": "Heating Boiler Temperature",
                                                     })

BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerCHFlowTemperatureSetpoint/state",
                                                              "command_topic": "homeassistant/number/boilerCHFlowTemperatureSetpoint/command",
                                                              "device_class": "temperature",
                                                              "min": boiler_values.boiler_flow_temperature_setpoint_rangemin,
                                                              "max": boiler_values.boiler_flow_temperature_setpoint_rangemax,
                                                              "unit_of_measurement": "°C",
                                                              "unique_id": "boilerCHFlowTemperatureSetpoint",
                                                              "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                              "name": "Heating Boiler Setpoint",
                                                              })

BOILER_CH_ACTIVE_HASS_CONFIG = json.dumps({"device_class": "heat",
                                           "state_topic": "homeassistant/binary_sensor/boilerCHActive/state",
                                           "unique_id": "boilerCHActive",
                                           "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                           "name": "Heating Active",
                                           })

BOILER_DHW_ENABLED_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/switch/boilerDHWEnabled/state",
                                            "command_topic": "homeassistant/switch/boilerDHWEnabled/command",
                                            "unique_id": "boilerDHWEnabled",
                                            "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                            "name": "Hot Water Enabled",
                                            })

BOILER_DHW_FLOW_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                     "state_topic": "homeassistant/sensor/boilerDHWFlowTemperature/state",
                                                     "unit_of_measurement": "°C",
                                                     "unique_id": "boilerDHWFlowTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "name": "Hot Water Temperature",
                                                     })

BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerDHWFlowTemperatureSetpoint/state",
                                                              "command_topic": "homeassistant/number/boilerDHWFlowTemperatureSetpoint/command",
                                                              "device_class": "temperature",
                                                              "min": boiler_values.boiler_dhw_temperature_setpoint_rangemin,
                                                              "max": boiler_values.boiler_dhw_temperature_setpoint_rangemax,
                                                              "unit_of_measurement": "°C",
                                                              "unique_id": "boilerDHWFlowTemperatureSetpoint",
                                                              "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                              "name": "Hot Water Setpoint",
                                                              })

BOILER_DHW_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
                                               "state_topic": "homeassistant/binary_sensor/boilerDHWActive/state",
                                               "unique_id": "boilerDHWActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Hot Water Active",
                                               })


async def boiler_loop(last_get_detail_timestamp: int, last_write_settings_timestamp: int) -> tuple[int, int]:
    # OT spec 5.3.1: status exchange is mandatory every cycle
    boiler_status = await opentherm_app.status_exchange(ch_enabled=boiler_values.boiler_ch_enabled,
                                                        dhw_enabled=boiler_values.boiler_dhw_enabled)
    # Check for fault state changes
    prev_fault = boiler_values.boiler_fault_active
    boiler_values.boiler_flame_active = boiler_status['flame_active']
    boiler_values.boiler_ch_active = boiler_status['ch_active']
    boiler_values.boiler_dhw_active = boiler_status['dhw_active']
    boiler_values.boiler_fault_active = boiler_status['fault']

    if boiler_values.boiler_fault_active and not prev_fault:
        # Read fault flags to get details about what faulted
        try:
            fault_flags = await opentherm_app.read_fault_flags()
            fault_details = []
            if fault_flags['low_water_pressure']:
                fault_details.append("low water pressure")
            if fault_flags['flame_fault']:
                fault_details.append("flame fault")
            if fault_flags['air_pressure_fault']:
                fault_details.append("low air pressure")
            if fault_flags['water_over_temp']:
                fault_details.append("high water temperature")
            if fault_flags['oem_code']:
                fault_details.append(f"OEM code {fault_flags['oem_code']}")

            if fault_details:
                send_syslog(f"FAULT DETECTED: {', '.join(fault_details)}")
            else:
                send_syslog("FAULT DETECTED: boiler fault active (no specific flags set)")
        except Exception as ex:
            send_syslog(f"FAULT DETECTED: boiler fault active (unable to read fault details: {str(ex)})")

    # OT spec 5.2: master MUST send ID 1 (TSet) with WRITE_DATA every cycle
    await opentherm_app.control_ch_setpoint(boiler_values.boiler_flow_temperature_setpoint)

    # retrieve detailed stats
    if (time.ticks_ms() - last_get_detail_timestamp) > GET_DETAILED_STATS_MS:
        boiler_values.boiler_flow_temperature = await opentherm_app.read_boiler_flow_temperature()
        boiler_values.boiler_return_temperature = await opentherm_app.read_boiler_return_water_temperature()
        boiler_values.boiler_exhaust_temperature = await opentherm_app.read_exhaust_temperature()

        # Fan speed: ID 35 added in OT v4.2 (not in v2.2). Some older boilers may not support it.
        # Isolate it so UNKNOWN-DATAID doesn't crash the entire detail poll.
        try:
            boiler_values.boiler_fan_speed = await opentherm_app.read_fan_speed()
        except (opentherm_app.UnknownDataIdError, opentherm_app.DataInvalidError) as ex:
            # Boiler doesn't support fan speed reading - leave at last known value
            send_syslog(f"Fan speed read skipped: {str(ex)}")

        boiler_values.boiler_modulation_level = await opentherm_app.read_relative_modulation_level()
        boiler_values.boiler_ch_pressure = await opentherm_app.read_ch_water_pressure()
        boiler_values.boiler_dhw_flow_rate = await opentherm_app.read_dhw_flow_rate()
        boiler_values.boiler_dhw_temperature = await opentherm_app.read_dhw_temperature()

        fault_flags = await opentherm_app.read_fault_flags()

        # Log specific fault changes
        if fault_flags['low_water_pressure'] and not boiler_values.boiler_fault_low_water_pressure:
            send_syslog("FAULT: Low water pressure detected")
        if fault_flags['flame_fault'] and not boiler_values.boiler_fault_flame:
            send_syslog("FAULT: Flame fault detected")
        if fault_flags['air_pressure_fault'] and not boiler_values.boiler_fault_low_air_pressure:
            send_syslog("FAULT: Low air pressure detected")
        if fault_flags['water_over_temp'] and not boiler_values.boiler_fault_high_water_temperature:
            send_syslog("FAULT: High water temperature detected")

        boiler_values.boiler_fault_low_water_pressure = fault_flags['low_water_pressure']
        boiler_values.boiler_fault_flame = fault_flags['flame_fault']
        boiler_values.boiler_fault_low_air_pressure = fault_flags['air_pressure_fault']
        boiler_values.boiler_fault_high_water_temperature = fault_flags['water_over_temp']
        last_get_detail_timestamp = time.ticks_ms()

        # Check for boiler restart via power cycle counter
        if boiler_values.last_power_cycles is not None:
            try:
                current_power_cycles = await opentherm_app.read_power_cycles()
                if current_power_cycles != boiler_values.last_power_cycles:
                    send_syslog(f"BOILER RESTART DETECTED: power cycles {boiler_values.last_power_cycles} -> {current_power_cycles}")
                    boiler_values.last_power_cycles = current_power_cycles
                    raise BoilerRestartDetected(f"Power cycles changed: {boiler_values.last_power_cycles} -> {current_power_cycles}")
            except BoilerRestartDetected:
                raise  # Re-raise to break out of inner loop
            except Exception as ex:
                send_syslog(f"Failed to read power cycles: {str(ex)}")

    # write settings periodically
    if (time.ticks_ms() - last_write_settings_timestamp) > WRITE_SETTINGS_MS:
        # OT spec 5.3.8.2: max relative modulation level (ID 14)
        await opentherm_app.control_max_relative_modulation_level(100.0)
        # DHW setpoint (ID 56 is R/W per spec) - only write if RBP flags allow it
        if boiler_values.rbp_dhw_setpoint == "rw":
            await opentherm_app.control_dhw_setpoint(boiler_values.boiler_dhw_temperature_setpoint)
        last_write_settings_timestamp = time.ticks_ms()

    return last_get_detail_timestamp, last_write_settings_timestamp


async def boiler_setup():
    global boiler_values
    global BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG, BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG

    send_syslog("Running boiler setup sequence")

    # OT spec 5.3.2: recommended to exchange config before control/status
    # Write master configuration (ID 2) - MemberID 0 = non-specific
    try:
        await opentherm_app.send_primary_configuration(0)
    except Exception as ex:
        send_syslog(f"Failed to write master config: {str(ex)}")

    # OT spec 5.2: master MUST read slave configuration (ID 3) at startup
    try:
        slave_config = await opentherm_app.read_secondary_configuration()
        send_syslog(f"Slave config: {slave_config}")
    except Exception as ex:
        send_syslog(f"Failed to read slave config: {str(ex)}")

    # Read RBP flags (ID 6) to check remote parameter support
    try:
        rbp_flags = await opentherm_app.read_extra_boiler_params_support()
        boiler_values.rbp_dhw_setpoint = rbp_flags['dhw_setpoint']
        boiler_values.rbp_maxch_setpoint = rbp_flags['maxch_setpoint']
        send_syslog(f"RBP flags: {rbp_flags}")
    except Exception as ex:
        send_syslog(f"Failed to read RBP flags: {str(ex)}")

    # Read static limits; rely on defaults if they fail
    try:
        boiler_values.boiler_max_capacity, _ = await opentherm_app.read_capacity_and_min_modulation()
    except Exception as ex:
        send_syslog(f"Failed to read boiler capacity: {str(ex)}")
    try:
        boiler_values.boiler_dhw_temperature_setpoint_rangemin, boiler_values.boiler_dhw_temperature_setpoint_rangemax = await opentherm_app.read_dhw_setpoint_range()
        tmp = json.loads(BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
        tmp['min'] = boiler_values.boiler_dhw_temperature_setpoint_rangemin
        tmp['max'] = boiler_values.boiler_dhw_temperature_setpoint_rangemax
        BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps(tmp)
    except Exception as ex:
        send_syslog(f"Failed to read DHW setpoint range: {str(ex)}")
    # OT spec 5.3.5: also read max CH setpoint bounds (ID 49)
    try:
        boiler_values.boiler_flow_temperature_setpoint_rangemin, boiler_values.boiler_flow_temperature_setpoint_rangemax = await opentherm_app.read_maxch_setpoint_range()
        tmp = json.loads(BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
        tmp['min'] = boiler_values.boiler_flow_temperature_setpoint_rangemin
        tmp['max'] = boiler_values.boiler_flow_temperature_setpoint_rangemax
        BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps(tmp)
    except Exception as ex:
        send_syslog(f"Failed to read max CH setpoint range: {str(ex)}")


async def boiler():
    global boiler_values

    while True:
        try:
            last_get_detail_timestamp: int = 0
            last_write_settings_timestamp: int = 0

            await boiler_setup()

            # Read initial power cycle count for restart detection
            try:
                boiler_values.last_power_cycles = await opentherm_app.read_power_cycles()
                send_syslog(f"Boiler power cycles: {boiler_values.last_power_cycles}")
            except (opentherm_app.UnknownDataIdError, opentherm_app.DataInvalidError):
                boiler_values.last_power_cycles = None
                send_syslog("Boiler does not support power cycle counter (ID 97)")

            while True:
                # errors happen all the damn time, so we just ignore them as per the protocol
                try:
                    last_get_detail_timestamp, last_write_settings_timestamp = await boiler_loop(last_get_detail_timestamp, last_write_settings_timestamp)
                except BoilerRestartDetected as ex:
                    send_syslog(f"Breaking out of status loop: {str(ex)}")
                    break  # Exit inner loop, will re-run boiler_setup() at top of outer loop
                except Exception as ex:
                    send_syslog(str(ex))
                    sys.print_exception(ex)

                # sleep and then do it all again
                await asyncio.sleep_ms(STATUS_LOOP_DELAY_MS)

        except Exception as ex:
            send_syslog(f"BOILERFAIL: {str(ex)}")
            sys.print_exception(ex)
            await asyncio.sleep(5)


def mqtt_callback(topic, msg):
    """MQTT callback handler

    Args:
        topic: String topic (already decoded from UTF-8)
        msg: Bytes payload
    """
    global boiler_values
    global mqtt_client_instance

    send_syslog(f"MQTT CALLBACK: topic={topic[:50]} msg={msg[:30]}")

    if topic == 'homeassistant/switch/boilerCHEnabled/command':
        if msg == b'ON':
            send_syslog("MQTT CMD: CH enabled ON")
            boiler_values.boiler_ch_enabled = True
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/switch/boilerCHEnabled/state", 'ON'))
        elif msg == b'OFF':
            send_syslog("MQTT CMD: CH enabled OFF")
            boiler_values.boiler_ch_enabled = False
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/switch/boilerCHEnabled/state", 'OFF'))

    elif topic == 'homeassistant/number/boilerCHFlowTemperatureSetpoint/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_flow_temperature_setpoint_rangemin or v > boiler_values.boiler_flow_temperature_setpoint_rangemax:
                v = boiler_values.boiler_flow_temperature_setpoint_rangemax
            send_syslog(f"MQTT CMD: CH setpoint -> {v}")
            boiler_values.boiler_flow_temperature_setpoint = v
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/number/boilerCHFlowTemperatureSetpoint/state", str(round(v, 2))))
        except ValueError:
            send_syslog(f"MQTT CMD: Invalid CH setpoint: {msg}")

    elif topic == 'homeassistant/switch/boilerDHWEnabled/command':
        if msg == b'ON':
            send_syslog("MQTT CMD: DHW enabled ON")
            boiler_values.boiler_dhw_enabled = True
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/switch/boilerDHWEnabled/state", 'ON'))
        elif msg == b'OFF':
            send_syslog("MQTT CMD: DHW enabled OFF")
            boiler_values.boiler_dhw_enabled = False
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/switch/boilerDHWEnabled/state", 'OFF'))

    elif topic == 'homeassistant/number/boilerDHWFlowTemperatureSetpoint/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_dhw_temperature_setpoint_rangemin or v > boiler_values.boiler_dhw_temperature_setpoint_rangemax:
                v = boiler_values.boiler_dhw_temperature_setpoint_rangemax
            send_syslog(f"MQTT CMD: DHW setpoint -> {v}")
            boiler_values.boiler_dhw_temperature_setpoint = v
            # Immediately publish requested state back to avoid bouncing
            if mqtt_client_instance:
                asyncio.create_task(mqtt_client_instance.publish_string("homeassistant/number/boilerDHWFlowTemperatureSetpoint/state", str(round(v, 2))))
        except ValueError:
            send_syslog(f"MQTT CMD: Invalid DHW setpoint: {msg}")

async def mqtt_publish(mqc):
    global boiler_values

    # publish all the config jsons
    await mqc.publish_string("homeassistant/sensor/boilerReturnTemperature/config", BOILER_RETURN_TEMPERATURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerExhaustTemperature/config", BOILER_EXHAUST_TEMPERATURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerFanSpeed/config", BOILER_FAN_SPEED_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerModulationLevel/config", BOILER_MODULATION_LEVEL_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerChPressure/config", BOILER_CH_PRESSURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerDhwFlowRate/config", BOILER_DHW_FLOW_RATE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerMaxCapacity/config", BOILER_MAX_CAPACITY_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerFlameActive/config", BOILER_FLAME_ACTIVE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultActive/config", BOILER_FAULT_ACTIVE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultLowWaterPressure/config", BOILER_FAULT_LOW_WATER_PRESSURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultFlame/config", BOILER_FAULT_FLAME_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultLowAirPressure/config", BOILER_FAULT_LOW_AIR_PRESSURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerHighWaterTemperature/config", BOILER_FAULT_HIGH_WATER_TEMPERATURE_HASS_CONFIG)

    await mqc.publish_string("homeassistant/switch/boilerCHEnabled/config", BOILER_CH_ENABLED_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerCHFlowTemperature/config", BOILER_CH_FLOW_TEMPERATURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/number/boilerCHFlowTemperatureSetpoint/config", BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerCHActive/config", BOILER_CH_ACTIVE_HASS_CONFIG)

    await mqc.publish_string("homeassistant/switch/boilerDHWEnabled/config", BOILER_DHW_ENABLED_HASS_CONFIG)
    await mqc.publish_string("homeassistant/sensor/boilerDHWFlowTemperature/config", BOILER_DHW_FLOW_TEMPERATURE_HASS_CONFIG)
    await mqc.publish_string("homeassistant/number/boilerDHWFlowTemperatureSetpoint/config", BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
    await mqc.publish_string("homeassistant/binary_sensor/boilerDHWActive/config", BOILER_DHW_ACTIVE_HASS_CONFIG)

    # publish all the states
    await mqc.publish_string("homeassistant/sensor/boilerReturnTemperature/state", str(round(boiler_values.boiler_return_temperature, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerExhaustTemperature/state", str(round(boiler_values.boiler_exhaust_temperature, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerFanSpeed/state", str(round(boiler_values.boiler_fan_speed, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerModulationLevel/state", str(round(boiler_values.boiler_modulation_level, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerChPressure/state", str(round(boiler_values.boiler_ch_pressure, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerDhwFlowRate/state", str(round(boiler_values.boiler_dhw_flow_rate, 2)))
    await mqc.publish_string("homeassistant/sensor/boilerMaxCapacity/state", str(boiler_values.boiler_max_capacity))
    await mqc.publish_string("homeassistant/binary_sensor/boilerFlameActive/state", 'ON' if boiler_values.boiler_flame_active else 'OFF')
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultActive/state", 'ON' if boiler_values.boiler_fault_active else 'OFF')
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultLowWaterPressure/state", 'ON' if boiler_values.boiler_fault_low_water_pressure else 'OFF')
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultFlame/state", 'ON' if boiler_values.boiler_fault_flame else 'OFF')
    await mqc.publish_string("homeassistant/binary_sensor/boilerFaultLowAirPressure/state", 'ON' if boiler_values.boiler_fault_low_air_pressure else 'OFF')
    await mqc.publish_string("homeassistant/binary_sensor/boilerHighWaterTemperature/state", 'ON' if boiler_values.boiler_fault_high_water_temperature else 'OFF')

    await mqc.publish_string("homeassistant/sensor/boilerCHFlowTemperature/state", str(round(boiler_values.boiler_flow_temperature, 2)))
    await mqc.publish_string("homeassistant/switch/boilerCHEnabled/state", 'ON' if boiler_values.boiler_ch_enabled else 'OFF')
    await mqc.publish_string("homeassistant/number/boilerCHFlowTemperatureSetpoint/state", str(round(boiler_values.boiler_flow_temperature_setpoint, 2)))
    await mqc.publish_string("homeassistant/binary_sensor/boilerCHActive/state", 'ON' if boiler_values.boiler_ch_active else 'OFF')

    await mqc.publish_string("homeassistant/sensor/boilerDHWFlowTemperature/state", str(round(boiler_values.boiler_dhw_temperature, 2)))
    await mqc.publish_string("homeassistant/switch/boilerDHWEnabled/state", 'ON' if boiler_values.boiler_dhw_enabled else 'OFF')
    await mqc.publish_string("homeassistant/number/boilerDHWFlowTemperatureSetpoint/state", str(round(boiler_values.boiler_dhw_temperature_setpoint, 2)))
    await mqc.publish_string("homeassistant/binary_sensor/boilerDHWActive/state", 'ON' if boiler_values.boiler_dhw_active else 'OFF')


async def mqtt():
    global boiler_values
    global mqtt_client_instance

    mqc = None
    while True:
        try:
            mqc = AsyncMQTTClient("picotherm", cfgsecrets.MQTT_HOST, keepalive=60)
            await mqc.connect()
            mqtt_client_instance = mqc

            mqc.set_callback(mqtt_callback)
            await mqc.subscribe('homeassistant/switch/boilerCHEnabled/command')
            await mqc.subscribe('homeassistant/number/boilerCHFlowTemperatureSetpoint/command')
            await mqc.subscribe('homeassistant/switch/boilerDHWEnabled/command')
            await mqc.subscribe('homeassistant/number/boilerDHWFlowTemperatureSetpoint/command')
            send_syslog("MQTT connected")

            last_publish_stamp = time.ticks_ms()
            while True:
                if time.ticks_ms() - last_publish_stamp >= MQTT_PUBLISH_MS:
                    print('MQTT PING')
                    await mqtt_publish(mqc)
                    last_publish_stamp = time.ticks_ms()

                await asyncio.sleep_ms(10)
                try:
                    await mqc.check_msg()
                except Exception as check_ex:
                    send_syslog(f"MQTT check_msg error: {str(check_ex)}")

        except Exception as ex:
            if mqc:
                try:
                    await mqc.disconnect()
                except Exception as close_ex:
                    send_syslog(f"MQTT disconnect error: {str(close_ex)}")
                mqc = None
                mqtt_client_instance = None
            send_syslog(f"MQTT error: {str(ex)}")
            sys.print_exception(ex)
            await asyncio.sleep(5)


async def main():
    send_syslog("picotherm starting")
    what = [
        boiler(),
        mqtt()
    ]
    await asyncio.gather(*what)


time.sleep(5)

def do_connect():
    rp2.country('GB')

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(cfgsecrets.WIFI_SSID, cfgsecrets.WIFI_PASSWORD)
        while not sta_if.isconnected():
            print("Attempting to connect....")
            utime.sleep(1)
    print('Connected! Network config:', sta_if.ifconfig())

print("Connecting to your wifi...")
do_connect()

time.sleep(5)
asyncio.run(main())
