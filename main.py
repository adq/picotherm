import opentherm_app
import time


def test():
    while True:
        try:
            print(opentherm_app.read_secondary_configuration())
        except Exception as ex:
            print("error", ex)
        input("Press a key")


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
