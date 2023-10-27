import opentherm_app
from opentherm_rp2 import opentherm_exchange
import time


def readtest(a, b):
    print(opentherm_exchange(opentherm_app.MSG_TYPE_READ_DATA, a, b))


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
