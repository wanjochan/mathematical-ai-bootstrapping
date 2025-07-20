"""
Test a simple command to debug the datetime issue
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('TestSimple')

async def test_simple(host='localhost', port=9998):
    """Test simple echo command"""
    url = f'ws://{host}:{port}'
    
    try:
        ws = await websockets.connect(url)
        
        # Register
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': 'admin',
            'client_start_time': '2024',
            'capabilities': {'management': True}
        }))
        
        response = await ws.recv()
        logger.info(f"Registration: {response}")
        
        # Send echo command (should always work)
        await ws.send(json.dumps({'type': 'request', 'command': 'echo', 'data': 'test'}))
        response = await ws.recv()
        logger.info(f"Echo response: {response}")
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        logger.info(f"Found {len(clients)} clients")
        
        if clients:
            # Test echo on first client
            client_id = clients[0]['id']
            
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'echo',
                    'params': {'message': 'Hello from test'}
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Client echo result: {result}")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_simple())