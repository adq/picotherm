import network
import utime
import rp2
import cfgsecrets

SSID = cfgsecrets.WIFI_SSID
SSID_PASSWORD = cfgsecrets.WIFI_PASSWORD

def do_connect():
    rp2.country('GB')

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, SSID_PASSWORD)
        while not sta_if.isconnected():
            print("Attempting to connect....")
            utime.sleep(1)
    print('Connected! Network config:', sta_if.ifconfig())

print("Connecting to your wifi...")
do_connect()
