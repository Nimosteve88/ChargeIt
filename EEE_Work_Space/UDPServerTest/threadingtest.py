import socket
import json
import time
import _thread

server_name = '192.168.0.103'  # Replace with current IP Address
server_port = 12000
client_port = 10001  # Change this to 11000 for the second client, every client must have a unique port number
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('', client_port))
client_socket.setblocking(False)

def send_message_to_server(message):
    print("UDP client running...")
    print("Connecting to server at IP:", server_name, "PORT:", server_port)
    # This checks the state of message and performs the necessary encoding to send the message to the server
    if isinstance(message, str):
        msg = message.encode()
    elif isinstance(message, (float, int)):
        msg = str(message).encode()
    elif isinstance(message, dict):
        msg = json.dumps(message).encode()
    else:
        print("Invalid message type. Please provide a string, float, integer, or dictionary.")
        return
    # Send the message to the server
    client_socket.sendto(msg, (server_name, server_port))
    # Print message sent confirmation
    print("Message has been successfully sent.")

def listen_for_messages():
    print("Listening for messages...")
    while True:
        try:
            data, server_address = client_socket.recvfrom(2048)
            if data:
                print("Message from Server:", data.decode())
        except:
            pass
        time.sleep(2)

# Start the listening thread
_thread.start_new_thread(listen_for_messages, ())

# Send the message
message = 'demand'
send_message_to_server(message)

# Main loop to keep the script running
while True:
    time.sleep(1)
