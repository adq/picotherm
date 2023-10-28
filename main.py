import opentherm_app
import time
import asyncio
import mqtt_async
import cfgsecrets
import json


# readable things
boiler_flow_temperature = 0
boiler_return_temperature = 0
boiler_exhaust_temperature = 0
boiler_fan_speed = 0
boiler_modulation_level = 0
boiler_ch_pressure = 0
boiler_dhw_flow_rate = 0
boiler_max_capacity = 0
boiler_min_modulation = 0
boiler_flame_active = False
boiler_ch_active = False
boiler_dhw_active = False
boiler_fault_actie = False
boiler_fault_low_water_pressure = False
boiler_fault_flame = False
boiler_fault_low_air_pressure = False
boiler_fault_high_water_temperature = False

# writable things
boiler_ch_enabled = True
boiler_ch_enabled_changed = False
boiler_dhw_enabled = True
boiler_dhw_enabled_changed = False
boiler_flow_temperature_setpoint = 70
boiler_flow_temperature_setpoint_changed = False
boiler_flow_temperature_setpoint_max = 80
boiler_flow_temperature_setpoint_max_changed = False
boiler_dhw_temperature_setpoint = 65
boiler_dhw_temperature_setpoint_changed = False
boiler_room_temperature_setpoint = 0
boiler_room_temperature_setpoint_changed = False
boiler_room_temperature = 0
boiler_room_temperature_changed = False
boiler_max_modulation = 100
boiler_max_modulation_changed = False


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
    while True:
        try:
            # mqc = mqtt_async.MQTTClient(mqtt_async.config)
            # await mqc.connect()
            # print("MQTT connected")

            while True:
                # # publish all the config jsons
                # await mqc.publish("homeassistant/sensor/sensorShowerH/config", SHOWERH_HASS_CONFIG)
                # await mqc.publish("homeassistant/sensor/sensorShowerT/config", SHOWERT_HASS_CONFIG)
                # await mqc.publish("homeassistant/sensor/sensorShowerB/config", SHOWERB_HASS_CONFIG)
                # await mqc.publish("homeassistant/sensor/sensorShowerL/config", SHOWERL_HASS_CONFIG)
                # await mqc.publish("homeassistant/fan/fanShower/config", SHOWERFAN_HASS_CONFIG)

                # # publish sensor data
                # if (time.ticks_ms() - sensor_last_seen) < 10000:
                #     if sensor_humidity is not None:
                #         await mqc.publish("homeassistant/sensor/sensorShowerH/state", str(round(sensor_humidity, 2)))
                #     if sensor_temperature is not None:
                #         await mqc.publish("homeassistant/sensor/sensorShowerT/state", str(round(sensor_temperature, 2)))
                #     if sensor_battery is not None:
                #         await mqc.publish("homeassistant/sensor/sensorShowerB/state", str(round(sensor_battery, 2)))

                # # publish fan data
                # if (time.ticks_ms() - fan_last_seen) < 10000:
                #     if fan_illuminance is not None:
                #         await mqc.publish("homeassistant/sensor/sensorShowerL/state", str(round(fan_illuminance)))
                #     await mqc.publish("homeassistant/fan/fanShower/state", 'ON' if fan_desired_boost else 'OFF')

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
