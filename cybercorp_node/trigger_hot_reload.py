"""
Trigger hot reload on the client
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TriggerReload')

async def trigger_reload(host='localhost', port=9998, client_id='client_108'):
    """Trigger hot reload"""
    url = f'ws://{host}:{port}'
    
    try:
        ws = await websockets.connect(url)
        
        # Register as admin
        await ws.send(json.dumps({
            'type': 'register',
            'user_session': 'admin',
            'client_start_time': '2024',
            'capabilities': {'management': True}
        }))
        
        response = await ws.recv()
        logger.info("Connected to server")
        
        # Trigger hot reload
        logger.info(f"\nTriggering hot reload on client {client_id}...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'hot_reload',
                'params': {
                    'action': 'reload_module',
                    'module_name': 'client'
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        logger.info(f"Result: {json.dumps(data, indent=2)}")
        
        # Wait a bit for reload to complete
        await asyncio.sleep(2)
        
        # Test if execute_program now exists
        logger.info("\nTesting execute_program command...")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_program',
                'params': {
                    'program': 'cmd',
                    'args': ['/c', 'echo', 'Hot reload successful!'],
                    'wait': True,
                    'shell': False
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data = json.loads(result)
        
        logger.info(f"Test result: {json.dumps(data, indent=2)}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Triggering hot reload on client")
    asyncio.run(trigger_reload())

if __name__ == '__main__':
    main()