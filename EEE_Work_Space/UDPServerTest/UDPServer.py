import socket

def send_message_to_client(message, client_address, client_port):
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Send the message
        s.sendto(message.encode(), (client_address, client_port))
    except Exception as e:
        print(f"Error in send_message_to_client: {e}")
    finally:
        # Close the socket
        s.close()

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
        # add the data to the confirmation message
        confirmation_message = "Message received! "
        server_socket.sendto(confirmation_message.encode(), client_address)

        confirmation_message = "Message received! "
        send_message_to_client(confirmation_message, client_address[0], client_address[1])
        
    # Store the client's address
    client_addresses.add(client_address)
    # Send the received message to all other clients
    for addr in client_addresses:
        if addr != client_address:
            server_socket.sendto(data.encode(), addr)