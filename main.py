import opentherm_app
import time
import asyncio
import mqtt_async
import cfgsecrets
import json
import sys

class BoilerValues():
    # readable things
    boiler_flow_temperature: float = 0.0
    boiler_return_temperature: float = 0.0
    boiler_exhaust_temperature: float = 0.0
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

    boiler_flow_temperature_setpoint: float = 70.0
    boiler_flow_temperature_setpoint_rangemin: float = 0.0
    boiler_flow_temperature_setpoint_rangemax: float = 100.0

    boiler_flow_temperature_max_setpoint: float = 80.0
    boiler_flow_temperature_max_setpoint_rangemin: float = 0.0
    boiler_flow_temperature_max_setpoint_rangemax: float = 100.0

    boiler_dhw_temperature_setpoint: float = 65.0
    boiler_dhw_temperature_setpoint_rangemin: float = 0.0
    boiler_dhw_temperature_setpoint_rangemax: float = 100.0

    boiler_room_temperature_setpoint: float = 0.0
    boiler_room_temperature_setpoint_rangemin: float = -40.0
    boiler_room_temperature_setpoint_rangemax: float = 127.0

    boiler_room_temperature: float = 0.0
    boiler_room_temperature_rangemin: float = -40.0
    boiler_room_temperature_rangemax: float = 127.0

    boiler_max_modulation: float = 100.0
    boiler_max_modulation_rangemin: float = 0.0
    boiler_max_modulation_rangemax: float = 100.0

boiler_values = BoilerValues()


STATUS_LOOP_DELAY_MS = 900
GET_DETAILED_STATS_MS = 60 * 1000
WRITE_SETTINGS_MS = 60 * 1000
MQTT_PUBLISH_MS = 60 * 1000

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

BOILER_DHW_FLOW_RATE_HASS_CONFIG = json.dumps({"device_class": "pressure",
                                               "state_topic": "homeassistant/sensor/boilerDhwFlowRate/state",
                                               "unit_of_measurement": "l/min",
                                               "unique_id": "boilerDhwFlowRate",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "HW Flow Rate",
                                               })

BOILER_MAX_CAPACITY_HASS_CONFIG = json.dumps({ "device_class": "energy",
                                               "state_topic": "homeassistant/sensor/boilerMaxCapacity/state",
                                               "unit_of_measurement": "kWh",
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

BOILER_CH_HASS_CONFIG = json.dumps({"current_temperature_topic": "homeassistant/water_heater/boilerCH/current_temperature_state",
                                    "mode_state_topic": "homeassistant/water_heater/boilerCH/mode_state",
                                    "power_command_topic": "homeassistant/water_heater/boilerCH/power_command",
                                    "temperature_command_topic": "homeassistant/water_heater/boilerCH/setpoint_command",
                                    "temperature_state_topic": "homeassistant/water_heater/boilerCH/setpoint_state",
                                    "min_temp": boiler_values.boiler_flow_temperature_setpoint_rangemin,
                                    "max_temp": boiler_values.boiler_flow_temperature_setpoint_rangemax,
                                    "unique_id": "boilerCH",
                                    "temperature_unit": "C",
                                    "device": {"identifiers": ["boiler"], "name": "boiler"},
                                    "name": "Heating",
                                    })

BOILER_CH_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
                                               "state_topic": "homeassistant/binary_sensor/boilerCHActive/state",
                                               "unique_id": "boilerCHActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Heating Active",
                                               })

BOILER_DHW_HASS_CONFIG = json.dumps({"mode_state_topic": "homeassistant/water_heater/boilerDHW/mode_state",
                                     "power_command_topic": "homeassistant/water_heater/boilerDHW/power_command",
                                     "temperature_command_topic": "homeassistant/water_heater/boilerDHW/setpoint_command",
                                     "temperature_state_topic": "homeassistant/water_heater/boilerDHW/setpoint_state",
                                     "min_temp": boiler_values.boiler_dhw_temperature_setpoint_rangemin,
                                     "max_temp": boiler_values.boiler_dhw_temperature_setpoint_rangemax,
                                     "unique_id": "boilerDHW",
                                     "temperature_unit": "C",
                                     "device": {"identifiers": ["boiler"], "name": "boiler"},
                                     "name": "Hot Water",
                                     })

BOILER_DHW_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
                                               "state_topic": "homeassistant/binary_sensor/boilerDHWActive/state",
                                               "unique_id": "boilerDHWActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "name": "Hot Water Active",
                                               })


BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerCHFlowSetpointMax/state",
                                                      "command_topic": "homeassistant/number/boilerCHFlowSetpointMax/command",
                                                      "device_class": "temperature",
                                                      "min": boiler_values.boiler_flow_temperature_max_setpoint_rangemin,
                                                      "max": boiler_values.boiler_flow_temperature_max_setpoint_rangemax,
                                                      "unit_of_measurement": "C",
                                                      "unique_id": "boilerCHFlowSetpointMax",
                                                      "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                      "name": "CH Flow Setpoint Max",
                                                      })

BOILER_ROOM_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerRoomTemperatureSetpoint/state",
                                                      "command_topic": "homeassistant/number/boilerRoomTemperatureSetpoint/command",
                                                      "device_class": "temperature",
                                                      "min": boiler_values.boiler_room_temperature_setpoint_rangemin,
                                                      "max": boiler_values.boiler_room_temperature_setpoint_rangemax,
                                                      "unit_of_measurement": "C",
                                                      "unique_id": "boilerRoomTemperatureSetpoint",
                                                      "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                      "name": "Room Temperature Setpoint",
                                                      })

BOILER_ROOM_TEMPERATURE_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerRoomTemperature/state",
                                                  "command_topic": "homeassistant/number/boilerRoomTemperature/command",
                                                  "device_class": "temperature",
                                                  "min": boiler_values.boiler_room_temperature_rangemin,
                                                  "max": boiler_values.boiler_room_temperature_rangemax,
                                                  "unit_of_measurement": "C",
                                                  "unique_id": "boilerRoomTemperature",
                                                  "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                  "name": "Room Temperature Setpoint",
                                                  })

BOILER_MAX_MODULATION_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerMaxModulation/state",
                                                "command_topic": "homeassistant/number/boilerMaxModulation/command",
                                                "min": boiler_values.boiler_max_modulation_rangemin,
                                                "max": boiler_values.boiler_max_modulation_rangemax,
                                                "unit_of_measurement": "%",
                                                "unique_id": "boilerMaxModulation",
                                                "device": {"identifiers": ["boiler"], "name": "boiler"},
                                                "name": "Max Modulation",
                                                })


async def boiler_loop(last_get_detail_timestamp: int, last_write_settings_timestamp: int) -> tuple[int, int]:
    # normal status exchange, happens every second ish
    boiler_status = await opentherm_app.status_exchange(ch_enabled=boiler_values.boiler_ch_enabled,
                                                        dhw_enabled=boiler_values.boiler_dhw_enabled)
    boiler_values.boiler_flame_active = boiler_status['flame_active']
    boiler_values.boiler_ch_active = boiler_status['ch_active']
    boiler_values.boiler_dhw_active = boiler_status['dhw_active']
    boiler_values.boiler_fault_active = boiler_status['fault']

    # retrieve detailed stats
    if (time.ticks_ms() - last_get_detail_timestamp) > GET_DETAILED_STATS_MS:
        boiler_values.boiler_flow_temperature = await opentherm_app.read_boiler_flow_temperature()
        boiler_values.boiler_return_temperature = await opentherm_app.read_boiler_return_water_temperature()
        boiler_values.boiler_exhaust_temperature = await opentherm_app.read_exhaust_temperature()
        boiler_values.boiler_fan_speed = await opentherm_app.read_fan_speed()
        boiler_values.boiler_modulation_level = await opentherm_app.read_relative_modulation_level()
        boiler_values.boiler_ch_pressure = await opentherm_app.read_ch_water_pressure()
        boiler_values.boiler_dhw_flow_rate = await opentherm_app.read_dhw_flow_rate()

        fault_flags = await opentherm_app.read_fault_flags()
        boiler_values.boiler_fault_low_water_pressure = fault_flags['low_water_pressure']
        boiler_values.boiler_fault_flame = fault_flags['flame_fault']
        boiler_values.boiler_fault_low_air_pressure = fault_flags['air_pressure_fault']
        boiler_values.boiler_fault_high_water_temperature = fault_flags['water_over_temp']
        last_get_detail_timestamp = time.ticks_ms()

    # write any changed things to the boiler
    if (time.ticks_ms() - last_write_settings_timestamp) > WRITE_SETTINGS_MS:
        if await opentherm_app.read_ch_setpoint() != boiler_values.boiler_flow_temperature_setpoint:
            await opentherm_app.control_ch_setpoint(boiler_values.boiler_flow_temperature_setpoint)
        if await opentherm_app.read_maxch_setpoint() != boiler_values.boiler_flow_temperature_max_setpoint:
            await opentherm_app.control_maxch_setpoint(boiler_values.boiler_flow_temperature_max_setpoint)
        if await opentherm_app.read_dhw_setpoint() != boiler_values.boiler_dhw_temperature_setpoint:
            await opentherm_app.control_dhw_setpoint(boiler_values.boiler_dhw_temperature_setpoint)
        # if await opentherm_app.read_room_setpoint() != boiler_values.boiler_room_temperature_setpoint:
        #     await opentherm_app.control_room_setpoint(boiler_values.boiler_room_temperature_setpoint)
        # if await opentherm_app.read_room_temperature() != boiler_values.boiler_room_temperature:
        #     await opentherm_app.control_room_temperature(boiler_values.boiler_room_temperature)
        if await opentherm_app.read_max_relative_modulation_level() != boiler_values.boiler_max_modulation:
            await opentherm_app.control_max_relative_modulation_level(boiler_values.boiler_max_modulation)
        last_write_settings_timestamp = time.ticks_ms()

    return last_get_detail_timestamp, last_write_settings_timestamp


async def boiler():
    global boiler_values
    global BOILER_MAX_MODULATION_HASS_CONFIG, BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG, BOILER_DHW_HASS_CONFIG

    while True:
        try:
            last_get_detail_timestamp: int = 0
            last_write_settings_timestamp: int = 0

            # try and read the limits we're able to; rely on defaults if they fail.
            # I assume these are static, so we can just read them once
            try:
                boiler_values.boiler_max_capacity, boiler_values.boiler_max_modulation_rangemin = await opentherm_app.read_capacity_and_min_modulation()
                tmp = json.loads(BOILER_MAX_MODULATION_HASS_CONFIG)
                tmp['min'] = boiler_values.boiler_max_modulation_rangemin
                BOILER_MAX_MODULATION_HASS_CONFIG = json.dumps(tmp)
            except:
                pass
            try:
                boiler_values.boiler_dhw_temperature_setpoint_rangemin, boiler_values.boiler_dhw_temperature_setpoint_rangemax = await opentherm_app.read_dhw_setpoint_range()
                tmp = json.loads(BOILER_DHW_HASS_CONFIG)
                tmp['min_temp'] = boiler_values.boiler_dhw_temperature_setpoint_rangemin
                tmp['max_temp'] = boiler_values.boiler_dhw_temperature_setpoint_rangemax
                BOILER_DHW_HASS_CONFIG = json.dumps(tmp)
            except:
                pass
            try:
                boiler_values.boiler_flow_temperature_max_setpoint_rangemin, boiler_values.boiler_flow_temperature_max_setpoint_rangemax = await opentherm_app.read_maxch_setpoint_range()
                tmp = json.loads(BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG)
                tmp['min'] = boiler_values.boiler_flow_temperature_max_setpoint_rangemin
                tmp['max'] = boiler_values.boiler_flow_temperature_max_setpoint_rangemax
                BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG = json.dumps(tmp)
            except:
                pass

            while True:
                # errors happen all the damn time, so we just ignore them as per the protocol
                try:
                    last_get_detail_timestamp, last_write_settings_timestamp = await boiler_loop(last_get_detail_timestamp, last_write_settings_timestamp)
                except Exception as ex:
                    sys.print_exception(ex)

                # sleep and then do it all again
                await asyncio.sleep_ms(STATUS_LOOP_DELAY_MS)

        except Exception as ex:
            print("BOILERFAIL")
            sys.print_exception(ex)
            await asyncio.sleep(5)



def msg_callback(topic, msg, retained, qos, dup):
    global boiler_values

    if topic == b'homeassistant/water_heater/boilerCH/power_command':
        if msg == b'ON':
            boiler_values.boiler_ch_enabled = True
        elif msg == b'OFF':
            boiler_values.boiler_ch_enabled = False

    elif topic == b'homeassistant/water_heater/boilerCH/setpoint_command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_flow_temperature_setpoint_rangemin or v > boiler_values.boiler_flow_temperature_setpoint_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_flow_temperature_setpoint = v
        except ValueError:
            pass

    elif topic == b'homeassistant/water_heater/boilerDHW/power_command':
        if msg == b'ON':
            boiler_values.boiler_dhw_enabled = True
        elif msg == b'OFF':
            boiler_values.boiler_dhw_enabled = False

    elif topic == b'homeassistant/water_heater/boilerDHW/setpoint_command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_dhw_temperature_setpoint_rangemin or v > boiler_values.boiler_dhw_temperature_setpoint_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_dhw_temperature_setpoint = v
        except ValueError:
            pass

    elif topic == b'homeassistant/number/boilerCHFlowSetpointMax/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_flow_temperature_max_setpoint_rangemin or v > boiler_values.boiler_flow_temperature_max_setpoint_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_flow_temperature_max_setpoint = v
        except ValueError:
            pass

    elif topic == b'homeassistant/number/boilerRoomTemperatureSetpoint/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_room_temperature_setpoint_rangemin or v > boiler_values.boiler_room_temperature_setpoint_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_room_temperature_setpoint = v
        except ValueError:
            pass

    elif topic == b'homeassistant/number/boilerRoomTemperature/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_room_temperature_rangemin or v > boiler_values.boiler_room_temperature_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_room_temperature = v
        except ValueError:
            pass

    elif topic == b'homeassistant/number/boilerMaxModulation/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_max_modulation_rangemin or v > boiler_values.boiler_max_modulation_rangemax:
                raise ValueError("out of range")
            boiler_values.boiler_max_modulation = v
        except ValueError:
            pass


async def conn_callback(client):
    await client.subscribe('homeassistant/water_heater/boilerCH/power_command')
    await client.subscribe('homeassistant/water_heater/boilerCH/setpoint_command')
    await client.subscribe('homeassistant/water_heater/boilerDHW/power_command')
    await client.subscribe('homeassistant/water_heater/boilerDHW/setpoint_command')
    await client.subscribe('homeassistant/number/boilerCHFlowSetpointMax/command')
    await client.subscribe('homeassistant/number/boilerRoomTemperatureSetpoint/command')
    await client.subscribe('homeassistant/number/boilerRoomTemperature/command')
    await client.subscribe('homeassistant/number/boilerMaxModulation/command')


async def mqtt():
    global boiler_values

    mqtt_async.config['ssid'] = cfgsecrets.WIFI_SSID
    mqtt_async.config['wifi_pw'] = cfgsecrets.WIFI_PASSWORD
    mqtt_async.config['server'] = cfgsecrets.MQTT_HOST
    mqtt_async.config['subs_cb'] = msg_callback
    mqtt_async.config['connect_coro'] = conn_callback

    while True:
        try:
            mqc = mqtt_async.MQTTClient(mqtt_async.config)
            await mqc.connect()
            print("MQTT connected")

            while True:
                # publish all the config jsons
                await mqc.publish("homeassistant/sensor/boilerReturnTemperature/config", BOILER_RETURN_TEMPERATURE_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerExhaustTemperature/config", BOILER_EXHAUST_TEMPERATURE_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerFanSpeed/config", BOILER_FAN_SPEED_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerModulationLevel/config", BOILER_MODULATION_LEVEL_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerChPressure/config", BOILER_CH_PRESSURE_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerDhwFlowRate/config", BOILER_DHW_FLOW_RATE_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerMaxCapacity/config", BOILER_MAX_CAPACITY_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFlameActive/config", BOILER_FLAME_ACTIVE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultActive/config", BOILER_FAULT_ACTIVE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowWaterPressure/config", BOILER_FAULT_LOW_WATER_PRESSURE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultFlame/config", BOILER_FAULT_FLAME_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowAirPressure/config", BOILER_FAULT_LOW_AIR_PRESSURE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerHighWaterTemperature/config", BOILER_FAULT_HIGH_WATER_TEMPERATURE_HASS_CONFIG)

                await mqc.publish("homeassistant/water_heater/boilerCH/config", BOILER_CH_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerCHActive/config", BOILER_CH_ACTIVE_HASS_CONFIG)

                await mqc.publish("homeassistant/water_heater/boilerDHW/config", BOILER_DHW_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerDHWActive/config", BOILER_DHW_ACTIVE_HASS_CONFIG)

                await mqc.publish("homeassistant/number/boilerCHFlowSetpointMax/config", BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG)
                await mqc.publish("homeassistant/number/boilerRoomTemperatureSetpoint/config", BOILER_ROOM_TEMPERATURE_SETPOINT_HASS_CONFIG)
                await mqc.publish("homeassistant/number/boilerRoomTemperature/config", BOILER_ROOM_TEMPERATURE_HASS_CONFIG)
                await mqc.publish("homeassistant/number/boilerMaxModulation/config", BOILER_MAX_MODULATION_HASS_CONFIG)

                # publish all the states
                await mqc.publish("homeassistant/sensor/boilerReturnTemperature/state", str(round(boiler_values.boiler_return_temperature, 2)))
                await mqc.publish("homeassistant/sensor/boilerExhaustTemperature/state", str(round(boiler_values.boiler_exhaust_temperature, 2)))
                await mqc.publish("homeassistant/sensor/boilerFanSpeed/state", str(round(boiler_values.boiler_fan_speed, 2)))
                await mqc.publish("homeassistant/sensor/boilerModulationLevel/state", str(round(boiler_values.boiler_modulation_level, 2)))
                await mqc.publish("homeassistant/sensor/boilerChPressure/state", str(round(boiler_values.boiler_ch_pressure, 2)))
                await mqc.publish("homeassistant/sensor/boilerDhwFlowRate/state", str(round(boiler_values.boiler_dhw_flow_rate, 2)))
                await mqc.publish("homeassistant/sensor/boilerMaxCapacity/state", str(boiler_values.boiler_max_capacity))
                await mqc.publish("homeassistant/binary_sensor/boilerFlameActive/state", 'ON' if boiler_values.boiler_flame_active else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultActive/state", 'ON' if boiler_values.boiler_fault_active else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowWaterPressure/state", 'ON' if boiler_values.boiler_fault_low_water_pressure else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultFlame/state", 'ON' if boiler_values.boiler_fault_flame else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowAirPressure/state", 'ON' if boiler_values.boiler_fault_low_air_pressure else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerHighWaterTemperature/state", 'ON' if boiler_values.boiler_fault_high_water_temperature else 'OFF')

                await mqc.publish("homeassistant/number/boilerCHFlowSetpointMax/state", str(round(boiler_values.boiler_flow_temperature_max_setpoint, 2)))
                await mqc.publish("homeassistant/number/boilerRoomTemperatureSetpoint/state", str(round(boiler_values.boiler_room_temperature_setpoint, 2)))
                await mqc.publish("homeassistant/number/boilerRoomTemperature/state", str(round(boiler_values.boiler_room_temperature, 2)))
                await mqc.publish("homeassistant/number/boilerMaxModulation/state", str(round(boiler_values.boiler_max_modulation, 2)))

                await mqc.publish("homeassistant/water_heater/boilerCH/current_temperature_state", str(round(boiler_values.boiler_flow_temperature, 2)))
                await mqc.publish("homeassistant/water_heater/boilerCH/mode_state", 'ON' if boiler_values.boiler_ch_enabled else 'OFF')
                await mqc.publish("homeassistant/water_heater/boilerCH/setpoint_state", str(round(boiler_values.boiler_flow_temperature_setpoint, 2)))
                await mqc.publish("homeassistant/binary_sensor/boilerChActive/state", 'ON' if boiler_values.boiler_ch_active else 'OFF')

                await mqc.publish("homeassistant/water_heater/boilerDHW/current_temperature_state", str(round(boiler_values.boiler_flow_temperature, 2)))
                await mqc.publish("homeassistant/water_heater/boilerDHW/mode_state", 'ON' if boiler_values.boiler_dhw_enabled else 'OFF')
                await mqc.publish("homeassistant/water_heater/boilerDHW/setpoint_state", str(round(boiler_values.boiler_dhw_temperature_setpoint, 2)))
                await mqc.publish("homeassistant/binary_sensor/boilerDHWActive/state", 'ON' if boiler_values.boiler_dhw_active else 'OFF')

                await asyncio.sleep_ms(MQTT_PUBLISH_MS)

        except Exception as ex:
            print("MQTTFAIL")
            sys.print_exception(ex)
            await asyncio.sleep(5)


async def main():
    what = [
        boiler(),
        mqtt()
    ]
    await asyncio.gather(*what)

asyncio.run(main())
