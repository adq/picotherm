import opentherm_app

while True:
    try:
        print(opentherm_app.read_secondary_configuration())
    except Exception as ex:
        print(ex)
    input("Press a key")
