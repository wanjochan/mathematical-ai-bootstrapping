"""Test getting windows from wjchk client"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_wjchk_windows():
    """Test windows retrieval from wjchk"""
    try:
        uri = "ws://localhost:9998"
        async with websockets.connect(uri) as ws:
            # Register
            await ws.send(json.dumps({
                'type': 'register',
                'client_type': 'test_windows'
            }))
            
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"Welcome: {welcome}")
            
            # Send raw forward command
            command_data = {
                'type': 'forward_command',
                'target_client_id': 'wjchk',  # Try direct username
                'command': 'get_windows',
                'command_id': f'cmd_{datetime.now().timestamp()}'
            }
            
            await ws.send(json.dumps(command_data))
            logger.info("Sent get_windows command")
            
            # Wait for response
            response = await ws.recv()
            result = json.loads(response)
            
            if 'error' in result:
                logger.error(f"Error: {result['error']}")
                
                # Try to get client list first
                await ws.send(json.dumps({'type': 'list_clients'}))
                clients_resp = await ws.recv()
                logger.info(f"Clients response: {clients_resp}")
            else:
                logger.info("Windows data received")
                
                # Parse and find Cursor
                if result.get('success') and result.get('result'):
                    windows = result['result']
                    logger.info(f"Total windows: {len(windows)}")
                    
                    # Look for Cursor
                    for w in windows:
                        title = w.get('title', '')
                        if 'cursor' in title.lower() or 'visual' in title.lower():
                            logger.info(f"Found IDE: {title}")
                            
                    # Show first 10 windows
                    logger.info("\nFirst 10 windows:")
                    for w in windows[:10]:
                        logger.info(f"  - {w.get('title', 'No title')[:60]}")
                        
    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_wjchk_windows())