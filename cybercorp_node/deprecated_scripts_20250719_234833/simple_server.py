"""Simple WebSocket server for testing"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SimpleServer')

connected_clients = {}
client_counter = 0

async def handle_client(websocket, path):
    global client_counter
    client_counter += 1
    client_id = f"client_{client_counter}"
    
    # Store client info
    client_info = {
        'id': client_id,
        'websocket': websocket,
        'connected_at': datetime.now().isoformat(),
        'address': websocket.remote_address
    }
    connected_clients[client_id] = client_info
    
    logger.info(f"Client {client_id} connected from {websocket.remote_address}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'client_id': client_id,
            'message': 'Connected to CyberCorp Server'
        }))
        
        # Handle messages
        async for message in websocket:
            data = json.loads(message)
            logger.info(f"Received from {client_id}: {data}")
            
            # Echo back
            await websocket.send(json.dumps({
                'type': 'response',
                'echo': data
            }))
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        del connected_clients[client_id]

async def main():
    logger.info("Starting simple server on port 8888")
    
    # Use simple configuration
    async with websockets.serve(
        handle_client,
        "localhost",
        8888,
        compression=None,
        ping_interval=None
    ):
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")