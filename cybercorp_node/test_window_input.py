"""
Test window activation and keyboard input functionality
"""

import asyncio
import json
import websockets
import logging
import argparse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestWindowInput')

async def test_window_input(host='localhost', port=9998):
    """Test window activation and keyboard input"""
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
        
        # Test each client
        for client in clients:
            client_id = client['id']
            logger.info(f"\nTesting window input on client: {client_id}")
            
            # Test 1: Activate window
            logger.info("\n1. Testing window activation...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'activate_window'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', False)
                    if result:
                        logger.info("✓ Window activation successful")
                    else:
                        logger.error("✗ Window activation failed")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
                continue
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Test 2: Send keys
            logger.info("\n2. Testing send_keys...")
            test_keys = "Hello from test{SPACE}script"
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {
                        'keys': test_keys
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', False)
                    if result:
                        logger.info(f"✓ Send keys successful: '{test_keys}'")
                    else:
                        logger.error("✗ Send keys failed")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Test 3: Type text with special characters
            logger.info("\n3. Testing type_text with special characters...")
            test_text = "Testing: {brackets} [square] (parens) + special ^ chars %"
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'vscode_type_text',
                    'params': {
                        'text': test_text
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', False)
                    if result:
                        logger.info(f"✓ Type text successful: '{test_text}'")
                    else:
                        logger.error("✗ Type text failed")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Test 4: Send VSCode command
            logger.info("\n4. Testing VSCode command palette...")
            test_command = "View: Toggle Terminal"
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'vscode_send_command',
                    'params': {
                        'command': test_command
                    }
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', False)
                    if result:
                        logger.info(f"✓ VSCode command successful: '{test_command}'")
                    else:
                        logger.error("✗ VSCode command failed")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
            
            # Test 5: Get window content to verify
            logger.info("\n5. Getting window content to verify...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_window_content'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result = data.get('result', {})
                    if result:
                        logger.info(f"✓ Window content retrieved:")
                        logger.info(f"  - Title: {result.get('window_title', 'N/A')}")
                        logger.info(f"  - Active: {result.get('is_active', False)}")
                        logger.info(f"  - Content areas: {len(result.get('content_areas', []))}")
                    else:
                        logger.error("✗ Failed to get window content")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test window activation and keyboard input')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Starting window input tests...")
    logger.info("Make sure VSCode is open on the target machine!")
    logger.info("Tests will activate the window and send keystrokes.\n")
    
    asyncio.run(test_window_input(args.host, args.port))

if __name__ == '__main__':
    main()