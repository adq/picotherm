import opentherm_app
from opentherm_rp2 import opentherm_exchange
import time


def readtest(a, b):
    print(opentherm_exchange(opentherm_app.MSG_TYPE_READ_DATA, a, b))


def writetest(a, b):
    print(opentherm_exchange(opentherm_app.MSG_TYPE_WRITE_DATA, a, b))


def status():
    while True:
        try:
            print(opentherm_app.status_exchange())
        except Exception as ex:
            print("error", ex)
        time.sleep(1)


def status_ch():
    while True:
        try:
            print(opentherm_app.status_exchange(ch_enabled=True))
        except Exception as ex:
            print("error", ex)
        time.sleep(1)


def scan():
    for i in range(0, 256):
        while True:
            try:
                msg_type, data_id, data_value = opentherm_exchange(opentherm_app.MSG_TYPE_READ_DATA, i, 0, debug=False)
                if msg_type == opentherm_app.MSG_TYPE_READ_ACK:
                    print("OK", data_id, hex(data_value))
                break

            except:
                time.sleep(1)

        time.sleep(1)
