"""
Test client restart functionality
"""

import asyncio
import json
import websockets
import logging
import argparse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestRestart')

async def test_restart(host='localhost', port=9998):
    """Test client restart functionality"""
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
            logger.info(f"\nTesting restart on client: {client_id}")
            
            # Get current client info
            logger.info("\n1. Getting client info before restart...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_system_info'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    if result_data.get('success'):
                        system_info = result_data.get('data', {})
                        logger.info(f"  Client info: {system_info.get('hostname')} ({system_info.get('user')})")
                        
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
                continue
            
            # Test different restart scenarios
            restart_tests = [
                {
                    'name': 'Quick restart with watchdog',
                    'params': {
                        'delay': 3,
                        'use_watchdog': True,
                        'reason': 'Test restart with watchdog'
                    }
                },
                {
                    'name': 'Delayed restart without watchdog',
                    'params': {
                        'delay': 5,
                        'use_watchdog': False,
                        'reason': 'Test direct restart'
                    }
                }
            ]
            
            for test in restart_tests:
                logger.info(f"\n2. Testing: {test['name']}")
                
                # Send restart command
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client': client_id,
                    'command': {
                        'type': 'command',
                        'command': 'restart_client',
                        'params': test['params']
                    }
                }))
                
                await ws.recv()  # ack
                
                try:
                    result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(result)
                    
                    if data.get('type') == 'command_result':
                        result_data = data.get('result', {})
                        if result_data.get('success'):
                            logger.info(f"✓ Restart scheduled: {result_data.get('message')}")
                            delay = test['params']['delay']
                            
                            # Wait for restart
                            logger.info(f"  Waiting {delay + 5} seconds for client to restart...")
                            await asyncio.sleep(delay + 5)
                            
                            # Check if client reconnected
                            logger.info("  Checking if client reconnected...")
                            
                            # Get updated client list
                            await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
                            response = await ws.recv()
                            data = json.loads(response)
                            
                            new_clients = data.get('clients', [])
                            
                            # Look for the client (might have new ID)
                            found = False
                            for new_client in new_clients:
                                # Check by user session (should be same)
                                if new_client.get('user_session') == client.get('user_session'):
                                    found = True
                                    new_id = new_client['id']
                                    if new_id != client_id:
                                        logger.info(f"✓ Client reconnected with new ID: {new_id}")
                                    else:
                                        logger.info(f"✓ Client reconnected with same ID: {new_id}")
                                    break
                            
                            if not found:
                                logger.error("✗ Client did not reconnect after restart")
                            else:
                                # Test if client is responsive
                                await ws.send(json.dumps({
                                    'type': 'forward_command',
                                    'target_client': new_id,
                                    'command': {
                                        'type': 'command',
                                        'command': 'health_status'
                                    }
                                }))
                                
                                await ws.recv()  # ack
                                
                                try:
                                    result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                                    data = json.loads(result)
                                    
                                    if data.get('type') == 'command_result':
                                        result_data = data.get('result', {})
                                        if result_data.get('success'):
                                            health = result_data.get('data', {}).get('health', {})
                                            logger.info(f"✓ Client is healthy after restart: {health.get('overall')}")
                                        else:
                                            logger.error("✗ Client unhealthy after restart")
                                            
                                except asyncio.TimeoutError:
                                    logger.error("✗ Client not responding after restart")
                        else:
                            logger.error(f"✗ Restart failed: {result_data.get('error')}")
                            
                except asyncio.TimeoutError:
                    logger.error(f"✗ No response from client {client_id}")
                
                # Only test first scenario to avoid multiple restarts
                break
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test client restart functionality')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Testing client restart functionality...")
    logger.info("This will restart the client - make sure it's safe to do so!")
    logger.info("")
    
    # Give user time to cancel
    logger.info("Starting in 3 seconds... (Ctrl+C to cancel)")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        logger.info("\nTest cancelled by user")
        return
    
    asyncio.run(test_restart(args.host, args.port))

if __name__ == '__main__':
    main()