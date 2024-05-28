import usocket as socket
import uselect as select
import json

# Define the server name and port client wishes to access
server_name = '192.168.0.103'
server_port = 12000
client_port = 10001  # Change this to 11000 for the second client

# Create a UDP client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('', client_port))

print("UDP client running...")
print("Connecting to server at IP:", server_name, "PORT:", server_port)

terminate = False
while not terminate:
    # Get user input and send it to the server
    # msg = input("Enter a message you want to send to the server: ")

    # Create a dictionary
    msg_dict = {"energy": 55, "reserve": 523}
    msg = json.dumps(msg_dict).encode()  # Convert the dictionary to a JSON string and then encode it to bytes

    # Check if the user wants to terminate the chat
    if msg.lower() == 'cancel'.encode():
        terminate = True

    client_socket.sendto(msg, (server_name, server_port))

    # Set up the polling object for timeout handling
    poll = select.poll()
    poll.register(client_socket, select.POLLIN)

    # Wait for a response with a timeout of 2 seconds
    events = poll.poll(5000)  # 2000 milliseconds

    if events:
        for event in events:
            if event[1] & select.POLLIN:
                data, server_address = client_socket.recvfrom(2048)
                if data:
                    print("Message from Server:", data.decode())
                    terminate = True
    else:
        print("No response from server within timeout period.")

client_socket.close()
