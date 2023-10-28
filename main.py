import opentherm_app
import time
import asyncio
import mqtt_async
import cfgsecrets
import json

class BoilerValues():
    # readable things
    boiler_flow_temperature = 0.0
    boiler_return_temperature = 0.0
    boiler_exhaust_temperature = 0.0
    boiler_fan_speed = 0.0
    boiler_modulation_level = 0.0
    boiler_ch_pressure = 0.0
    boiler_dhw_flow_rate = 0.0
    boiler_max_capacity = 0
    boiler_min_modulation = 0
    boiler_flame_active = False
    boiler_ch_active = False
    boiler_dhw_active = False
    boiler_fault_active = False
    boiler_fault_low_water_pressure = False
    boiler_fault_flame = False
    boiler_fault_low_air_pressure = False
    boiler_fault_high_water_temperature = False

    # writable things
    boiler_ch_enabled = True
    boiler_dhw_enabled = True

    boiler_flow_temperature_setpoint = 70.0
    boiler_flow_temperature_setpoint_changed = False

    boiler_flow_temperature_setpoint_max = 80.0
    boiler_flow_temperature_setpoint_max_changed = False

    boiler_dhw_temperature_setpoint = 65.0
    boiler_dhw_temperature_setpoint_changed = False

    boiler_room_temperature_setpoint = 0.0
    boiler_room_temperature_setpoint_changed = False

    boiler_room_temperature = 0.0
    boiler_room_temperature_changed = False

    boiler_max_modulation = 100.0
    boiler_max_modulation_changed = False

    def mark_all_changed(self):
        self.boiler_flow_temperature_setpoint_changed = True
        self.boiler_flow_temperature_setpoint_max_changed = True
        self.boiler_dhw_temperature_setpoint_changed = True
        self.boiler_room_temperature_setpoint_changed = True
        self.boiler_room_temperature_changed = True
        self.boiler_max_modulation_changed = True

boiler_values = BoilerValues()


STATUS_LOOP_DELAY_MS = 1000
GET_DETAILED_STATS_MS = 60 * 1000
WRITE_SETTINGS_MS = 60 * 1000
MQTT_PUBLISH_MS = 60 * 1000

BOILER_RETURN_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                    "state_topic": "homeassistant/sensor/boilerReturnTemperature/state",
                                                    "unit_of_measurement": "°C",
                                                    "unique_id": "boilerReturnTemperature",
                                                    "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                    "friendly_name": "Return Temperature",
                                                    })

BOILER_EXHAUST_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
                                                     "state_topic": "homeassistant/sensor/boilerExhaustTemperature/state",
                                                     "unit_of_measurement": "°C",
                                                     "unique_id": "boilerExhaustTemperature",
                                                     "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                     "friendly_name": "Exhaust Temperature",
                                                     })

BOILER_FAN_SPEED_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerFanSpeed/state",
                                           "unit_of_measurement": "rpm",
                                           "unique_id": "boilerFanSpeed",
                                           "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                           "friendly_name": "Fan Speed",
                                           })

BOILER_MODULATION_LEVEL_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerModulationLevel/state",
                                                  "unit_of_measurement": "percent",
                                                  "unique_id": "boilerModulationLevel",
                                                  "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                  "friendly_name": "Current Modulation Level",
                                                  })

BOILER_CH_PRESSURE_HASS_CONFIG = json.dumps({"device_class": "pressure",
                                             "state_topic": "homeassistant/sensor/boilerChPressure/state",
                                             "unit_of_measurement": "bar",
                                             "unique_id": "boilerChPressure",
                                             "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                             "friendly_name": "CH Pressure",
                                             })

BOILER_DHW_FLOW_RATE_HASS_CONFIG = json.dumps({"device_class": "pressure",
                                               "state_topic": "homeassistant/sensor/boilerDhwFlowRate/state",
                                               "unit_of_measurement": "l/min",
                                               "unique_id": "boilerDhwFlowRate",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "HW Flow Rate",
                                               })

BOILER_MAX_CAPACITY_HASS_CONFIG = json.dumps({ "device_class": "energy",
                                               "state_topic": "homeassistant/sensor/boilerMaxCapacity/state",
                                               "unit_of_measurement": "kWh",
                                               "unique_id": "boilerMaxCapacity",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Max Capacity",
                                               })

BOILER_MIN_MODULATION_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/sensor/boilerMinModulationLevel/state",
                                               "unit_of_measurement": "percent",
                                               "unique_id": "boilerMinModulationLevel",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Min Modulation Level",
                                               })

BOILER_FLAME_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
                                               "state_topic": "homeassistant/binary_sensor/boilerFlameActive/state",
                                               "unique_id": "boilerFlameActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Flame Active",
                                               })

BOILER_FAULT_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultActive/state",
                                               "unique_id": "boilerFaultActive",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Fault",
                                               })

BOILER_FAULT_LOW_WATER_PRESSURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultLowWaterPressure/state",
                                               "unique_id": "boilerFaultLowWaterPressure",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Low CH Water Pressure",
                                               })

BOILER_FAULT_FLAME_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultFlame/state",
                                               "unique_id": "boilerFaultFlame",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Flame",
                                               })

BOILER_FAULT_LOW_AIR_PRESSURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                               "state_topic": "homeassistant/binary_sensor/boilerFaultLowAirPressure/state",
                                               "unique_id": "boilerFaultLowAirPressure",
                                               "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                               "friendly_name": "Low Air Pressure",
                                               })

BOILER_FAULT_HIGH_WATER_TEMPERATURE_HASS_CONFIG = json.dumps({ "device_class": "problem",
                                                "state_topic": "homeassistant/binary_sensor/boilerHighWaterTemperature/state",
                                                "unique_id": "boilerHighWaterTemperature",
                                                "device": {"identifiers": ["boiler"], "name": "Boiler"},
                                                "friendly_name": "High Water Temperature",
                                                })

# BOILER_FLOW_TEMPERATURE_HASS_CONFIG = json.dumps({"device_class": "temperature",
#                                                   "state_topic": "homeassistant/sensor/boilerFlowTemperature/state",
#                                                   "unit_of_measurement": "°C",
#                                                   "unique_id": "boilerFlowTemperature",
#                                                   "device": {"identifiers": ["boiler"], "name": "Boiler"},
#                                                   "friendly_name": "Flow Temperature",
#                                                   })

# BOILER_CH_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
#                                                "state_topic": "homeassistant/binary_sensor/boilerChActive/state",
#                                                "unique_id": "boilerChActive",
#                                                "device": {"identifiers": ["boiler"], "name": "Boiler"},
#                                                "friendly_name": "Heating Active",
#                                                })

# BOILER_DHW_ACTIVE_HASS_CONFIG = json.dumps({ "device_class": "heat",
#                                                "state_topic": "homeassistant/binary_sensor/boilerDhwActive/state",
#                                                "unique_id": "boilerDhwActive",
#                                                "device": {"identifiers": ["boiler"], "name": "Boiler"},
#                                                "friendly_name": "Hot Water Active",
#                                                })

    # boiler_ch_enabled = True
    # boiler_flow_temperature_setpoint = 70.0

    # boiler_dhw_enabled = True
    # boiler_dhw_temperature_setpoint = 65.0

    # boiler_flow_temperature_setpoint_max = 80.0
    # boiler_room_temperature_setpoint = 0.0
    # boiler_room_temperature = 0.0
    # boiler_max_modulation = 100.0

# SHOWERFAN_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/fan/fanShower/state",
#                     "command_topic": "homeassistant/fan/fanShower/command",
#                     "percentage_state_topic": "homeassistant/fan/fanShower/pcstate",
#                     "percentage_command_topic": "homeassistant/fan/fanShower/pccommand",
#                     "unique_id": "fan01ae",
#                     "device": {"identifiers": ["shower01ae"], "name": "Shower"}
#                     })



async def boiler():
    global boiler_values
    while True:
        try:
            boiler_values.mark_all_changed()
            last_get_detail_timestamp = 0
            last_write_settings_timestamp = 0

            # I think these are static, so we can just read them once
            boiler_values.boiler_max_capacity, boiler_values.boiler_min_modulation = await opentherm_app.read_capacity_and_min_modulation()

            while True:
                # normal status exchange, happens every second
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
                    if boiler_values.boiler_flow_temperature_setpoint_changed:
                        await opentherm_app.control_ch_setpoint(boiler_values.boiler_flow_temperature_setpoint)
                        boiler_values.boiler_flow_temperature_setpoint_changed = False
                    if boiler_values.boiler_flow_temperature_setpoint_max_changed:
                        await opentherm_app.control_maxch_setpoint(boiler_values.boiler_flow_temperature_setpoint_max)
                        boiler_values.boiler_flow_temperature_setpoint_max_changed = False
                    if boiler_values.boiler_dhw_temperature_setpoint_changed:
                        await opentherm_app.control_dhw_setpoint(boiler_values.boiler_dhw_temperature_setpoint)
                        boiler_values.boiler_dhw_temperature_setpoint_changed = False
                    if boiler_values.boiler_room_temperature_setpoint_changed:
                        await opentherm_app.control_room_setpoint(boiler_values.boiler_room_temperature_setpoint)
                        boiler_values.boiler_room_temperature_setpoint_changed = False
                    if boiler_values.boiler_room_temperature_changed:
                        await opentherm_app.control_room_temperature(boiler_values.boiler_room_temperature)
                        boiler_values.boiler_room_temperature_changed = False
                    if boiler_values.boiler_max_modulation_changed:
                        await opentherm_app.control_max_relative_modulation_level(boiler_values.boiler_max_modulation)
                        boiler_values.boiler_max_modulation_changed = False
                    last_write_settings_timestamp = time.ticks_ms()

                # sleep and then do it all again
                await asyncio.sleep_ms(STATUS_LOOP_DELAY_MS)

        except Exception as ex:
            print("BOILERFAIL")
            print(ex)
            # raise
            await asyncio.sleep(5)



def msg_callback(topic, msg, retained, qos, dup):
    global fan_desired_boost

    if topic == b'homeassistant/fan/fanShower/command':
        if msg == b'ON':
            fan_desired_boost = True
        else:
            fan_desired_boost = False

    elif topic == b'homeassistant/fan/fanShower/pccommand':
        if msg != b'0':
            fan_desired_boost = True
        else:
            fan_desired_boost = False


async def conn_callback(client):
    await client.subscribe('homeassistant/fan/fanShower/command', 0)
    await client.subscribe('homeassistant/fan/fanShower/pccommand', 0)


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
                await mqc.publish("homeassistant/sensor/boilerMinModulationLevel/config", BOILER_MIN_MODULATION_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFlameActive/config", BOILER_FLAME_ACTIVE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultActive/config", BOILER_FAULT_ACTIVE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowWaterPressure/config", BOILER_FAULT_LOW_WATER_PRESSURE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultFlame/config", BOILER_FAULT_FLAME_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowAirPressure/config", BOILER_FAULT_LOW_AIR_PRESSURE_HASS_CONFIG)
                await mqc.publish("homeassistant/binary_sensor/boilerHighWaterTemperature/config", BOILER_FAULT_HIGH_WATER_TEMPERATURE_HASS_CONFIG)

                # publish all the states
                await mqc.publish("homeassistant/sensor/boilerReturnTemperature/state", str(round(boiler_values.boiler_return_temperature, 2)))
                await mqc.publish("homeassistant/sensor/boilerExhaustTemperature/state", str(round(boiler_values.boiler_exhaust_temperature, 2)))
                await mqc.publish("homeassistant/sensor/boilerFanSpeed/state", str(round(boiler_values.boiler_fan_speed, 2)))
                await mqc.publish("homeassistant/sensor/boilerModulationLevel/state", str(round(boiler_values.boiler_modulation_level, 2)))
                await mqc.publish("homeassistant/sensor/boilerChPressure/state", str(round(boiler_values.boiler_ch_pressure, 2)))
                await mqc.publish("homeassistant/sensor/boilerDhwFlowRate/state", str(round(boiler_values.boiler_dhw_flow_rate, 2)))
                await mqc.publish("homeassistant/sensor/boilerMaxCapacity/state", str(boiler_values.boiler_max_capacity))
                await mqc.publish("homeassistant/sensor/boilerMinModulationLevel/state", str(boiler_values.boiler_min_modulation))
                await mqc.publish("homeassistant/binary_sensor/boilerFlameActive/state", 'ON' if boiler_values.boiler_flame_active else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultActive/state", 'ON' if boiler_values.boiler_fault_active else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowWaterPressure/state", 'ON' if boiler_values.boiler_fault_low_water_pressure else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultFlame/state", 'ON' if boiler_values.boiler_fault_flame else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerFaultLowAirPressure/state", 'ON' if boiler_values.boiler_fault_low_air_pressure else 'OFF')
                await mqc.publish("homeassistant/binary_sensor/boilerHighWaterTemperature/state", 'ON' if boiler_values.boiler_fault_high_water_temperature else 'OFF')

                # FIXME: the other stuff

                await asyncio.sleep_ms(MQTT_PUBLISH_MS)

        except Exception as ex:
            print("MQTTFAIL")
            print(ex)
            # raise
            await asyncio.sleep(5)


async def main():
    what = [
        boiler(),
        mqtt()
    ]
    await asyncio.gather(*what)

asyncio.run(main())
