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

    boiler_flow_temperature_setpoint: float = 70.0
    boiler_flow_temperature_setpoint_rangemin: float = 0.0
    boiler_flow_temperature_setpoint_rangemax: float = 100.0

    boiler_dhw_temperature_setpoint: float = 65.0
    boiler_dhw_temperature_setpoint_rangemin: float = 0.0
    boiler_dhw_temperature_setpoint_rangemax: float = 100.0

boiler_values = BoilerValues()


STATUS_LOOP_DELAY_MS = 900
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

BOILER_CH_ENABLED_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/switch/boilerCHEnabled/state",
                                            "command_topic": "homeassistant/switch/boilerCHEnabled/command",
                                            "unique_id": "boilerCHEnabled",
                                            "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                            "name": "Heating Enabled",
                                            })

BOILER_CH_FLOW_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                     "state_topic": "homeassistant/sensor/boilerCHFlowTemperature/state",
                                                     "unit_of_measurement": "C",
                                                     "unique_id": "boilerCHFlowTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "name": "Heating Boiler Temperature",
                                                     })

BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerCHFlowTemperatureSetpoint/state",
                                                              "command_topic": "homeassistant/number/boilerCHFlowTemperatureSetpoint/command",
                                                              "device_class": "temperature",
                                                              "min": boiler_values.boiler_flow_temperature_setpoint_rangemin,
                                                              "max": boiler_values.boiler_flow_temperature_setpoint_rangemax,
                                                              "unit_of_measurement": "C",
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
                                                     "unit_of_measurement": "C",
                                                     "unique_id": "boilerDHWFlowTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "name": "Hot Water Temperature",
                                                     })

BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/number/boilerDHWFlowTemperatureSetpoint/state",
                                                              "command_topic": "homeassistant/number/boilerDHWFlowTemperatureSetpoint/command",
                                                              "device_class": "temperature",
                                                              "min": boiler_values.boiler_dhw_temperature_setpoint_rangemin,
                                                              "max": boiler_values.boiler_dhw_temperature_setpoint_rangemax,
                                                              "unit_of_measurement": "C",
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
        boiler_values.boiler_dhw_temperature = await opentherm_app.read_dhw_temperature()

        fault_flags = await opentherm_app.read_fault_flags()
        boiler_values.boiler_fault_low_water_pressure = fault_flags['low_water_pressure']
        boiler_values.boiler_fault_flame = fault_flags['flame_fault']
        boiler_values.boiler_fault_low_air_pressure = fault_flags['air_pressure_fault']
        boiler_values.boiler_fault_high_water_temperature = fault_flags['water_over_temp']
        last_get_detail_timestamp = time.ticks_ms()

    # write any changed things to the boiler
    if (time.ticks_ms() - last_write_settings_timestamp) > WRITE_SETTINGS_MS:
        if int(await opentherm_app.read_ch_setpoint()) != boiler_values.boiler_flow_temperature_setpoint:
            await opentherm_app.control_ch_setpoint(boiler_values.boiler_flow_temperature_setpoint)
        if int(await opentherm_app.read_dhw_setpoint()) != boiler_values.boiler_dhw_temperature_setpoint:
            await opentherm_app.control_dhw_setpoint(boiler_values.boiler_dhw_temperature_setpoint)
        last_write_settings_timestamp = time.ticks_ms()

    return last_get_detail_timestamp, last_write_settings_timestamp


async def boiler():
    global boiler_values
    global BOILER_CH_FLOW_SETPOINT_MAX_HASS_CONFIG, BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG

    while True:
        try:
            last_get_detail_timestamp: int = 0
            last_write_settings_timestamp: int = 0

            # try and read the limits we're able to; rely on defaults if they fail.
            # I assume these are static, so we can just read them once
            try:
                boiler_values.boiler_max_capacity, _ = await opentherm_app.read_capacity_and_min_modulation()
            except:
                pass
            try:
                boiler_values.boiler_dhw_temperature_setpoint_rangemin, boiler_values.boiler_dhw_temperature_setpoint_rangemax = await opentherm_app.read_dhw_setpoint_range()
                tmp = json.loads(BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
                tmp['min'] = boiler_values.boiler_dhw_temperature_setpoint_rangemin
                tmp['max'] = boiler_values.boiler_dhw_temperature_setpoint_rangemax
                BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG = json.dumps(tmp)
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

    if topic == b'homeassistant/switch/boilerCHEnabled/command':
        if msg == b'ON':
            boiler_values.boiler_ch_enabled = True
        elif msg == b'OFF':
            boiler_values.boiler_ch_enabled = False

    elif topic == b'homeassistant/number/boilerCHFlowTemperatureSetpoint/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_flow_temperature_setpoint_rangemin or v > boiler_values.boiler_flow_temperature_setpoint_rangemax:
                v = boiler_values.boiler_flow_temperature_setpoint_rangemax
            boiler_values.boiler_flow_temperature_setpoint = v
        except ValueError:
            pass

    elif topic == b'homeassistant/switch/boilerDHWEnabled/command':
        if msg == b'ON':
            boiler_values.boiler_dhw_enabled = True
        elif msg == b'OFF':
            boiler_values.boiler_dhw_enabled = False

    elif topic == b'homeassistant/number/boilerDHWFlowTemperatureSetpoint/command':
        try:
            v = int(float(msg))
            if v < boiler_values.boiler_dhw_temperature_setpoint_rangemin or v > boiler_values.boiler_dhw_temperature_setpoint_rangemax:
                v = boiler_values.boiler_dhw_temperature_setpoint_rangemax
            boiler_values.boiler_dhw_temperature_setpoint = v
        except ValueError:
            pass


async def conn_callback(client):
    await client.subscribe('homeassistant/switch/boilerCHEnabled/command')
    await client.subscribe('homeassistant/number/boilerCHFlowTemperatureSetpoint/command')
    await client.subscribe('homeassistant/switch/boilerDHWEnabled/command')
    await client.subscribe('homeassistant/number/boilerDHWFlowTemperatureSetpoint/command')


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

                await mqc.publish("homeassistant/switch/boilerCHEnabled/config", BOILER_CH_ENABLED_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerCHFlowTemperature/config", BOILER_CH_FLOW_TEMPERATURE_HASS_CONFIG)
                await mqc.publish("homeassistant/number/boilerCHFlowTemperatureSetpoint/config", BOILER_CH_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerCHActive/config", BOILER_CH_ACTIVE_HASS_CONFIG)

                await mqc.publish("homeassistant/switch/boilerDHWEnabled/config", BOILER_DHW_ENABLED_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/boilerDHWFlowTemperature/config", BOILER_DHW_FLOW_TEMPERATURE_HASS_CONFIG)
                await mqc.publish("homeassistant/number/boilerDHWFlowTemperatureSetpoint/config", BOILER_DHW_FLOW_TEMPERATURE_SETPOINT_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerDHWActive/config", BOILER_DHW_ACTIVE_HASS_CONFIG)

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

                await mqc.publish("homeassistant/sensor/boilerCHFlowTemperature/state", str(round(boiler_values.boiler_flow_temperature, 2)))
                await mqc.publish("homeassistant/switch/boilerCHEnabled/state", 'ON' if boiler_values.boiler_ch_enabled else 'OFF')
                await mqc.publish("homeassistant/number/boilerCHFlowTemperatureSetpoint/state", str(round(boiler_values.boiler_flow_temperature_setpoint, 2)))
                await mqc.publish("homeassistant/binary_sensor/boilerChActive/state", 'ON' if boiler_values.boiler_ch_active else 'OFF')

                await mqc.publish("homeassistant/sensor/boilerDHWFlowTemperature/state", str(round(boiler_values.boiler_dhw_temperature, 2)))
                await mqc.publish("homeassistant/switch/boilerDHWEnabled/state", 'ON' if boiler_values.boiler_dhw_enabled else 'OFF')
                await mqc.publish("homeassistant/number/boilerDHWFlowTemperatureSetpoint/state", str(round(boiler_values.boiler_dhw_temperature_setpoint, 2)))
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
