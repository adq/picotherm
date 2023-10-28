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


GET_DETAILED_STATS_MS = 60 * 1000
WRITE_SETTINGS_MS = 60 * 1000

SHOWERL_HASS_CONFIG = json.dumps({"device_class": "illuminance",
                  "state_topic": "homeassistant/sensor/sensorShowerL/state",
                  "unit_of_measurement": "lx",
                  "unique_id": "light01ae",
                  "device": {"identifiers": ["shower01ae"], "name": "Shower"}
                 })

SHOWERT_HASS_CONFIG = json.dumps({"device_class": "temperature",
                  "state_topic": "homeassistant/sensor/sensorShowerT/state",
                  "unit_of_measurement": "°C",
                  "unique_id": "temp01ae",
                  "device": {"identifiers": ["shower01ae"], "name": "Shower"}
                 })

SHOWERH_HASS_CONFIG = json.dumps({"device_class": "humidity",
                  "state_topic": "homeassistant/sensor/sensorShowerH/state",
                  "unit_of_measurement": "%",
                  "unique_id": "hum01ae",
                  "device": {"identifiers": ["shower01ae"], "name": "Shower"}
                 })

SHOWERB_HASS_CONFIG = json.dumps({"device_class": "battery",
                  "state_topic": "homeassistant/sensor/sensorShowerB/state",
                  "unit_of_measurement": "%",
                  "unique_id": "bat01ae",
                  "device": {"identifiers": ["shower01ae"], "name": "Shower"}
                 })

SHOWERFAN_HASS_CONFIG = json.dumps({"state_topic": "homeassistant/fan/fanShower/state",
                    "command_topic": "homeassistant/fan/fanShower/command",
                    "percentage_state_topic": "homeassistant/fan/fanShower/pcstate",
                    "percentage_command_topic": "homeassistant/fan/fanShower/pccommand",
                    "unique_id": "fan01ae",
                    "device": {"identifiers": ["shower01ae"], "name": "Shower"}
                    })



async def boiler():
    global boiler_values
    while True:
        try:
            boiler_values.mark_all_changed()
            last_get_detail_timestamp = 0
            last_write_settings_timestamp = 0
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
                    boiler_values.boiler_max_capacity, boiler_values.boiler_min_modulation = await opentherm_app.read_capacity_and_min_modulation()

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

                # sleep for a sec and then do it all again
                await asyncio.sleep(1)

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
                await mqc.publish("homeassistant/sensor/sensorShowerH/config", SHOWERH_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/sensorShowerT/config", SHOWERT_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/sensorShowerB/config", SHOWERB_HASS_CONFIG)
                await mqc.publish("homeassistant/sensor/sensorShowerL/config", SHOWERL_HASS_CONFIG)
                await mqc.publish("homeassistant/fan/fanShower/config", SHOWERFAN_HASS_CONFIG)

                # publish sensor data
                if (time.ticks_ms() - sensor_last_seen) < 10000:
                    if sensor_humidity is not None:
                        await mqc.publish("homeassistant/sensor/sensorShowerH/state", str(round(sensor_humidity, 2)))
                    if sensor_temperature is not None:
                        await mqc.publish("homeassistant/sensor/sensorShowerT/state", str(round(sensor_temperature, 2)))
                    if sensor_battery is not None:
                        await mqc.publish("homeassistant/sensor/sensorShowerB/state", str(round(sensor_battery, 2)))

                # publish fan data
                if (time.ticks_ms() - fan_last_seen) < 10000:
                    if fan_illuminance is not None:
                        await mqc.publish("homeassistant/sensor/sensorShowerL/state", str(round(fan_illuminance)))
                    await mqc.publish("homeassistant/fan/fanShower/state", 'ON' if fan_desired_boost else 'OFF')

                await asyncio.sleep(5)

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
