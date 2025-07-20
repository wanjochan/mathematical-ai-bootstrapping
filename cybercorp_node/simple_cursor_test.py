"""Simple test to control Cursor"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cursor():
    """Simple cursor control test"""
    uri = "ws://localhost:9998"
    
    async with websockets.connect(uri) as ws:
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'client_type': 'test'
        }))
        
        welcome = await ws.recv()
        logger.info(f"Welcome: {welcome}")
        
        # Try different message formats
        # Format 1: Direct command
        msg = {
            'type': 'command',
            'command': 'list_clients'
        }
        
        await ws.send(json.dumps(msg))
        logger.info("Sent list_clients command")
        
        # Keep connection alive to receive response
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Response: {response}")
                
                # Parse response
                data = json.loads(response)
                if 'clients' in data:
                    logger.info(f"Found {len(data['clients'])} clients")
                    for client in data['clients']:
                        logger.info(f"  - {client}")
                        
        except asyncio.TimeoutError:
            logger.info("No more messages")
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cursor())