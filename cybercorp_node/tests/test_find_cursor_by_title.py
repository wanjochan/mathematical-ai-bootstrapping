"""
Find Cursor by window title pattern
"""

import asyncio
import json
import websockets
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FindCursorByTitle')

async def find_cursor_by_title(host='localhost', port=9998):
    """Find Cursor IDE by searching window titles"""
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
            logger.info(f"\nChecking windows on client: {client_id}")
            
            # Get all windows
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'get_windows'
                }
            }))
            
            await ws.recv()  # ack
            
            try:
                result = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(result)
                
                if data.get('type') == 'command_result':
                    result_data = data.get('result', {})
                    
                    # Check if result has success field
                    if isinstance(result_data, dict) and 'success' in result_data:
                        if result_data['success']:
                            windows_data = result_data.get('data', {})
                            windows = windows_data.get('windows', [])
                        else:
                            logger.error(f"Command failed: {result_data.get('error', 'Unknown error')}")
                            continue
                    elif isinstance(result_data, list):
                        # Direct list of windows
                        windows = result_data
                    else:
                        logger.error(f"Unexpected result format: {type(result_data)}")
                        continue
                    
                    logger.info(f"Found {len(windows)} windows")
                    
                    # Search for Cursor by various patterns
                    cursor_patterns = [
                        'cursor',  # Basic pattern
                        'Cursor',  # Case sensitive
                        'cursor - ',  # With dash
                        'Cursor - ', # Case sensitive with dash
                        ' - Cursor',  # At end
                        'cursor.exe', # Process name in title
                    ]
                    
                    cursor_candidates = []
                    
                    for window in windows:
                        title = window.get('title', '')
                        class_name = window.get('class', '')
                        hwnd = window.get('hwnd')
                        
                        # Check if title contains any cursor pattern
                        for pattern in cursor_patterns:
                            if pattern in title:
                                cursor_candidates.append({
                                    'window': window,
                                    'pattern': pattern,
                                    'score': 10 if pattern.lower() == 'cursor' else 5
                                })
                                break
                        
                        # Also check if it's an Electron app that might be Cursor
                        if class_name == 'Chrome_WidgetWin_1' and pattern not in title:
                            # Could be Cursor if title doesn't indicate other apps
                            known_apps = ['Chrome', 'Edge', 'Brave', 'VSCode', 'Visual Studio Code', '腾讯']
                            is_known = any(app in title for app in known_apps)
                            
                            if not is_known:
                                cursor_candidates.append({
                                    'window': window,
                                    'pattern': 'Unknown Electron App',
                                    'score': 1
                                })
                    
                    if cursor_candidates:
                        # Sort by score
                        cursor_candidates.sort(key=lambda x: x['score'], reverse=True)
                        
                        logger.info(f"\n✓ Found {len(cursor_candidates)} potential Cursor window(s):")
                        for candidate in cursor_candidates:
                            window = candidate['window']
                            logger.info(f"\n  Title: {window['title']}")
                            logger.info(f"  HWND: {window['hwnd']}")
                            logger.info(f"  Class: {window['class']}")
                            logger.info(f"  Match: {candidate['pattern']} (score: {candidate['score']})")
                        
                        # Use the best match
                        best_match = cursor_candidates[0]['window']
                        cursor_hwnd = best_match['hwnd']
                        
                        # Try to activate and control it
                        logger.info(f"\n\nTrying to control best match: {best_match['title']}")
                        
                        # Activate window
                        await ws.send(json.dumps({
                            'type': 'forward_command',
                            'target_client': client_id,
                            'command': {
                                'type': 'command',
                                'command': 'activate_window',
                                'params': {
                                    'hwnd': cursor_hwnd
                                }
                            }
                        }))
                        
                        await ws.recv()  # ack
                        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(result)
                        
                        if data.get('type') == 'command_result':
                            logger.info("✓ Window activation command sent")
                        
                        # Type test text
                        await asyncio.sleep(1)
                        
                        test_text = "// Testing Cursor IDE control"
                        await ws.send(json.dumps({
                            'type': 'forward_command',
                            'target_client': client_id,
                            'command': {
                                'type': 'command',
                                'command': 'type_text',
                                'params': {
                                    'text': test_text
                                }
                            }
                        }))
                        
                        await ws.recv()  # ack
                        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        data = json.loads(result)
                        
                        if data.get('type') == 'command_result':
                            logger.info(f"✓ Typed text: {test_text}")
                            
                    else:
                        logger.warning("\n✗ No Cursor windows found by title pattern")
                        
                        # Show some windows for debugging
                        logger.info("\nShowing first 10 windows:")
                        for window in windows[:10]:
                            logger.info(f"  - {window['title'][:60]}... (Class: {window['class']})")
                    
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
    parser = argparse.ArgumentParser(description='Find Cursor IDE by title')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=9998, help='Server port')
    
    args = parser.parse_args()
    
    logger.info("Finding Cursor IDE by window title patterns...")
    logger.info("")
    
    asyncio.run(find_cursor_by_title(args.host, args.port))

if __name__ == '__main__':
    main()