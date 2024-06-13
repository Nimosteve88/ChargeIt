import usocket as socket
import uselect as select
import json
import utime
import network
import socket
from machine import Pin, ADC
import time


def send_message_to_server(message):
    start_time = time.time()
    # Define the server name and port client wishes to access
<<<<<<< Updated upstream
    server_name = '192.168.0.103'   # Replace with current IP Address
    server_port = 12000
=======
    server_name = '192.168.194.236'   # Replace with current IP Address
    server_port = 12001
>>>>>>> Stashed changes
    client_port = 10001  # Change this to 11000 for the second client, every client must have unique port number
    # Create a UDP client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('', client_port))
    print("UDP client running...")
    print("Connecting to server at IP:", server_name, "PORT:", server_port)
    #This checks the state of message and performs the necessary encoding in order to send the message to the server
    if type(message) == str:
        msg = message.encode()
    elif type(message) == float or type(message) == int:
        msg = str(message).encode()
    elif type(message) == dict:
        msg = json.dumps(message).encode()
    else:
        print("Invalid message type. Please provide a string, float, integer or dictionary.")
        return
    # Send the message to the server
    client_socket.sendto(msg, (server_name, server_port))
    # Set up the polling object for timeout handling
    poll = select.poll()
    poll.register(client_socket, select.POLLIN)
    # Wait for a response with a timeout of 2 seconds
    events = poll.poll(2000)  # 2000 milliseconds
    if events:
        for event in events:
            if event[1] & select.POLLIN:
                data, server_address = client_socket.recvfrom(2048)
                if data:
                    print("Message from Server:", data.decode())
    else:
        print("No response from server within timeout period.")
    # Close the socket
    client_socket.close()
    # Print message sent confirmation
    print("Message has been successfully sent in", time.time() - start_time, "seconds")

<<<<<<< Updated upstream
# ssid = 'Ade_13'
# password = 'praisethelord'
=======
ssid = 'SteveGalaxy'
password = "ChargeIt"
>>>>>>> Stashed changes

# # Set WiFi to station interface
# wlan = network.WLAN(network.STA_IF)
# # Activate the network interface
# wlan.active(True)

# # Check if already connected
# if not wlan.isconnected():
#     print('Connecting to network...')
#     wlan.connect(ssid, password)

#     max_wait = 10
#     # Wait for connection
#     while max_wait > 0:
#         if wlan.status() < 0 or wlan.status() >= 3:
#             # Connection successful
#             break
#         max_wait -= 1
#         print('Waiting for connection... ' + str(max_wait))
#         utime.sleep(1)

#     # Check connection
#     if wlan.status() != 3:
#         # No connection
#         raise RuntimeError('Network connection failed')
# else:
#     print('Already connected to network')

# # Connection successful
# print('WLAN connected')
# status = wlan.ifconfig()
# pico_ip = status[0]
# print('IP = ' + status[0])

# Example usage:
<<<<<<< Updated upstream
while True:
    message = input("Enter message: ")
    send_message_to_server(message)
    utime.sleep(2)  

=======
Power = "Hello, World!"
send_message_to_server(Power)
>>>>>>> Stashed changes
