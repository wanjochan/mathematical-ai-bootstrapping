"""Simple WebSocket client for testing"""

import asyncio
import websockets
import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SimpleClient')

async def client():
    uri = "ws://localhost:8888"
    logger.info(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri, compression=None) as websocket:
            logger.info("Connected!")
            
            # Receive welcome
            welcome = await websocket.recv()
            logger.info(f"Received: {welcome}")
            
            # Send test message
            test_msg = {
                'type': 'test',
                'user': os.environ.get('USERNAME', 'unknown'),
                'message': 'Hello from client'
            }
            await websocket.send(json.dumps(test_msg))
            
            # Receive response
            response = await websocket.recv()
            logger.info(f"Response: {response}")
            
            # Keep connection alive
            await asyncio.sleep(10)
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(client())