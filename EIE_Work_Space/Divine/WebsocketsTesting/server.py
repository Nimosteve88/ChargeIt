import uasyncio as asyncio
import usocket as socket
import ustruct as struct
from ubinascii import b2a_base64

class WebSocket:
    def __init__(self, uri):
        self.uri = uri
        self.socket = None

    async def connect(self):
        url = self.uri.split("://")[1]
        host, port = url.split(":")
        port = int(port)

        self.socket = socket.socket()
        self.socket.connect((host, port))

        websocket_key = b"abcd1234"
        handshake = b"GET / HTTP/1.1\r\n" \
                    b"Host: " + host.encode() + b":" + str(port).encode() + b"\r\n" \
                    b"Upgrade: websocket\r\n" \
                    b"Connection: Upgrade\r\n" \
                    b"Sec-WebSocket-Key: " + b2a_base64(websocket_key) + b"\r\n" \
                    b"Sec-WebSocket-Version: 13\r\n\r\n"

        self.socket.send(handshake)

        response = self.socket.recv(1024)
        if b"Sec-WebSocket-Accept" not in response:
            raise Exception("WebSocket handshake failed")

    async def send(self, message):
        message = message.encode("utf-8")
        header = struct.pack("B", 0x81)  # Text frame, FIN bit set
        payload_len = len(message)
        if payload_len < 126:
            header += struct.pack("B", payload_len)
        elif payload_len < (1 << 16):
            header += struct.pack("!BH", 126, payload_len)
        else:
            header += struct.pack("!BQ", 127, payload_len)

        self.socket.send(header + message)

    async def receive(self):
        header = self.socket.recv(2)
        payload_len = header[1] & 0x7F
        if payload_len == 126:
            payload_len = struct.unpack("!H", self.socket.recv(2))[0]
        elif payload_len == 127:
            payload_len = struct.unpack("!Q", self.socket.recv(8))[0]

        payload = self.socket.recv(payload_len)
        return payload.decode("utf-8")

    async def close(self):
        self.socket.close()

async def main():
    ws = WebSocket("ws://localhost:8765")
    await ws.connect()
    print("Connected to WebSocket server")

    try:
        while True:
            await ws.send("Hello from MicroPython!")
            response = await ws.receive()
            print(f"Received: {response}")
            await asyncio.sleep(5)
    finally:
        await ws.close()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
