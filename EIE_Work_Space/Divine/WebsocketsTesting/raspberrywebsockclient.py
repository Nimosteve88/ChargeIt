# client.py
import uasyncio as asyncio
import usocket as socket
import time

class WebSocket:
    def __init__(self, uri):
        self.uri = uri
        self.sock = None

    async def connect(self):
        addr_info = socket.getaddrinfo(self.uri, 80)
        addr = addr_info[0][-1]
        self.sock = socket.socket()
        self.sock.connect(addr)
        self.sock.setblocking(False)
        # Perform the WebSocket handshake here if necessary

    async def send(self, message):
        self.sock.send(message.encode('utf-8'))

    async def recv(self):
        data = self.sock.recv(1024)
        return data.decode('utf-8')

    async def close(self):
        self.sock.close()

async def send_messages(uri):
    ws = WebSocket(uri)
    await ws.connect()
    while True:
        message = input("Enter message to send: ")
        starttime = time.time()
        await ws.send(message)
        response = await ws.recv()
        print("Time taken to complete process: ", time.time() - starttime)

async def main():
    uri = "localhost"
    await send_messages(uri)

if __name__ == "__main__":
    asyncio.run(main())
