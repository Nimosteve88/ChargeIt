# client.py
import asyncio
import websockets
import time

async def send_messages(uri):
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = input("Enter message to send: ")
            starttime = time.time()
            await websocket.send(message)
            response = await websocket.recv()
            print("Time taken to complete process: ", time.time() - starttime)

async def main():
    uri = "ws://localhost:8765"
    await send_messages(uri)

if __name__ == "__main__":
    asyncio.run(main())
