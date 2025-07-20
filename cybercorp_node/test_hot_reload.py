"""
Test hot reload functionality
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestHotReload')

async def test_hot_reload(host='localhost', port=9998):
    """Test hot reload commands"""
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
        
        clients = [c for c in data.get('clients', []) if 'hot_reload' in c.get('capabilities', {})]
        
        if not clients:
            logger.warning("No clients with hot reload capability found")
            return
        
        # Test each client
        for client in clients:
            client_id = client['id']
            logger.info(f"\nTesting hot reload on client: {client_id}")
            
            # Get hot reload status
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'hot_reload',
                    'params': {'action': 'status'}
                }
            }))
            
            await ws.recv()  # ack
            result = await ws.recv()
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result = data.get('result', {})
                if result.get('success'):
                    stats = result.get('stats', {})
                    logger.info(f"Hot reload status: {json.dumps(stats, indent=2)}")
                else:
                    logger.error(f"Hot reload error: {result.get('error')}")
            
            # Try to reload a module
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'hot_reload',
                    'params': {
                        'action': 'reload_module',
                        'module_name': 'utils.window_cache'
                    }
                }
            }))
            
            await ws.recv()  # ack
            result = await ws.recv()
            data = json.loads(result)
            
            if data.get('type') == 'command_result':
                result = data.get('result', {})
                if result.get('success'):
                    logger.info(f"Module reloaded: {result.get('module')}")
                else:
                    logger.error(f"Module reload failed: {result.get('error')}")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test hot reload functionality')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    asyncio.run(test_hot_reload(args.host, args.port))

if __name__ == '__main__':
    main()