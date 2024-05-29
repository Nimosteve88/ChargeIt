import socket

def udp_server():
    server_port = 12000

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the server to the localhost at port server_port
    server_socket.bind(('', server_port))

    print('UDP Server running on port', server_port)

    while True:
        # Receive a message from a client and print it
        data, client_address = server_socket.recvfrom(2048)
        data = data.decode()
        if data:
            print("Message from Client at", client_address, ":", data)

            # Echo the received message back to the client
            server_socket.sendto(data.encode(), client_address)

if __name__ == "__main__":
    udp_server()
