import utime
import network
import socket
import json
from machine import Pin, ADC

ssid = 'SteveGalaxy'
password = 'ChargeIt'

# Set WiFi to station interface
wlan = network.WLAN(network.STA_IF)
# Activate the network interface
wlan.active(True)

# Check if already connected
if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(ssid, password)

    max_wait = 10
    # Wait for connection
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            # Connection successful
            break
        max_wait -= 1
        print('Waiting for connection... ' + str(max_wait))
        utime.sleep(1)

    # Check connection
    if wlan.status() != 3:
        # No connection
        raise RuntimeError('Network connection failed')
else:
    print('Already connected to network')

# Connection successful
print('WLAN connected')
status = wlan.ifconfig()
pico_ip = status[0]
print('IP = ' + status[0])

# Open socket
addr = (pico_ip, 80)
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Listening on', addr)

led = Pin('LED', Pin.OUT)
led.off()
led_state = False

# Temperature sensor setup (assuming using ADC pin for a sensor)
adc = ADC(4)
conversion_factor = 3.3 / (65535)

def read_temperature():
    reading = adc.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return round(temperature, 2)

def load_html():
    with open("/index.html", "r") as file:
        return file.read()

# Main loop
while True:
    client, client_addr = s.accept()
    raw_request = client.recv(1024)
    raw_request = raw_request.decode("utf-8")
    print(raw_request)

    request_parts = raw_request.split()
    http_method = request_parts[0]
    request_url = request_parts[1]

    if request_url == "/":
        response = load_html()
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: text/html\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
    elif request_url == "/ledon":
        led_state = True
        led.on()
        response = json.dumps({"led": "ON"})
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: application/json\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
    elif request_url == "/ledoff":
        led_state = False
        led.off()
        response = json.dumps({"led": "OFF"})
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: application/json\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
    elif request_url == "/status":
        temperature = read_temperature()
        led_status = "ON" if led_state else "OFF"
        response = json.dumps({"led": led_status, "temperature": temperature})
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: application/json\n')
        client.send('Connection: close\n\n')
        client.sendall(response)
    else:
        client.send('HTTP/1.1 404 NOT FOUND\n')
        client.send('Content-Type: text/html\n')
        client.send('Connection: close\n\n')
        client.sendall("Page not found")
    
    client.close()
