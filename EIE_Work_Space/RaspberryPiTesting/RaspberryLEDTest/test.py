import utime
import network
import socket
from machine import Pin
from NetworkCredentials import NetworkCredentials

ssid = 'WIFI_NAME'
password = 'WIFI_PASSWORD'

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

def load_html():
    with open("simpleled.html", "r") as file:
        return file.read()

# Main loop
while True:
    client, client_addr = s.accept()
    raw_request = client.recv(1024)
    # Translate byte string to normal string variable
    raw_request = raw_request.decode("utf-8")
    print(raw_request)

    # Break request into words (split at spaces)
    request_parts = raw_request.split()
    http_method = request_parts[0]
    request_url = request_parts[1]

    if request_url.find("/ledon") != -1:
        # Turn LED on
        led_state = True
        led.on()
    elif request_url.find("/ledoff") != -1:
        # Turn LED off
        led_state = False
        led.off()
    else:
        # Do nothing
        pass

    led_state_text = "OFF"
    if led_state:
        led_state_text = "ON"

    html = load_html()
    response = html.replace('**ledState**', led_state_text)
    client.send('HTTP/1.1 200 OK\n')
    client.send('Content-Type: text/html\n')
    client.send('Connection: close\n\n')
    client.sendall(response)
    client.close()
