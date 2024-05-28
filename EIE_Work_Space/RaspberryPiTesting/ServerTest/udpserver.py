import socket

# Define the server port
server_port = 12000

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the server to the localhost at port server_port
server_socket.bind(('', server_port))

print('UDP Server running on port', server_port)

# Create a set to store client addresses
client_addresses = set()

while True:
    # Receive a message from a client and print it
    data, client_address = server_socket.recvfrom(2048)
    data = data.decode()
    if len(data) > 0:
        print("Message from Client at", client_address, ":", data)

        # Send confirmation back to the client that sent the message
        confirmation_message = "Message received! " + data
        server_socket.sendto(confirmation_message.encode(), client_address)

    # Store the client's address
    client_addresses.add(client_address)

    # Send the received message to all other clients
    for addr in client_addresses:
        if addr != client_address:
            server_socket.sendto(data.encode(), addr)

