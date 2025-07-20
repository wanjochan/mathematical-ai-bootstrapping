"""
Test hot reload to update clients with new command
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestHotReload')

async def test_hot_reload(host='localhost', port=9998):
    """Trigger hot reload on clients"""
    url = f'ws://{host}:{port}'
    
    try:
        # Connect as admin
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
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        
        if not clients:
            logger.warning("No clients found")
            return
        
        # Trigger hot reload on each client
        for client in clients:
            client_id = client['id']
            logger.info(f"\nTriggering hot reload on client: {client_id}")
            
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'hot_reload',
                    'params': {
                        'module': 'client'
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    if isinstance(result_data, dict) and result_data.get('success'):
                        logger.info(f"✓ Hot reload successful on client {client_id}")
                    else:
                        logger.error(f"✗ Hot reload failed on client {client_id}")
                    
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
                continue
            except Exception as e:
                logger.error(f"Error reloading client {client_id}: {e}")
                continue
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test hot reload')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Triggering hot reload on all clients...")
    logger.info("")
    
    asyncio.run(test_hot_reload(args.host, args.port))

if __name__ == '__main__':
    main()