import opentherm_app
import time


def test():
    while True:
        try:
            print(opentherm_app.read_secondary_configuration())
        except Exception as ex:
            print(ex)
        time.sleep(1)
        input("Press a key")


def test2():
    while True:
        try:
            print(opentherm_app.read_secondary_configuration())
        except Exception as ex:
            print(ex)
        input("Press a key")

