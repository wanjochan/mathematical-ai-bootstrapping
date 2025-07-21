"""
Test finding Cursor IDE windows specifically
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestFindCursor')

async def test_find_cursor(host='localhost', port=9998):
    """Test finding Cursor IDE windows"""
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
            logger.info(f"\nChecking for Cursor IDE on client: {client_id}")
            
            # Use the new find_cursor_windows command
            logger.info("Using find_cursor_windows command...")
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'find_cursor_windows'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    
                    if isinstance(result_data, dict) and result_data.get('success'):
                        cursor_data = result_data.get('data', {})
                        cursor_windows = cursor_data.get('cursor_windows', [])
                        chrome_windows = cursor_data.get('all_chrome_windows', [])
                        
                        if cursor_windows:
                            logger.info(f"\n✓ Found {len(cursor_windows)} Cursor IDE window(s):")
                            for window in cursor_windows:
                                logger.info(f"  - {window['title']}")
                                logger.info(f"    HWND: {window['hwnd']}")
                                logger.info(f"    Process: {window['process_name']} (PID: {window['pid']})")
                                logger.info(f"    Class: {window['class']}")
                        else:
                            logger.warning("\n✗ No Cursor IDE windows found!")
                            logger.info(f"\nFound {len(chrome_windows)} Chrome_WidgetWin_1 windows:")
                            for window in chrome_windows[:5]:
                                logger.info(f"  - {window['title']}")
                                logger.info(f"    Process: {window['process_name']}")
                    else:
                        logger.error(f"Command failed: {result_data.get('error', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id} not responding")
                continue
            except Exception as e:
                logger.error(f"Error testing client {client_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test finding Cursor IDE windows')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Testing Cursor IDE window detection...")
    logger.info("Make sure Cursor IDE is running on the target machine!")
    logger.info("")
    
    asyncio.run(test_find_cursor(args.host, args.port))

if __name__ == '__main__':
    main()