"""
Final attempt to launch and control Cursor
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LaunchCursorFinal')

async def launch_cursor_final(host='localhost', port=9998):
    """Launch and control Cursor"""
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
        
        # Get client list
        await ws.send(json.dumps({'type': 'request', 'command': 'list_clients'}))
        response = await ws.recv()
        data = json.loads(response)
        
        clients = data.get('clients', [])
        if not clients:
            logger.error("No clients found")
            return
        
        # Use the newest client
        sorted_clients = sorted(clients, key=lambda c: int(c['id'].split('_')[1]))
        client = sorted_clients[-1]
        client_id = client['id']
        logger.info(f"Using client: {client_id}")
        
        # Step 1: Check current windows
        logger.info("\n=== Step 1: Current windows ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_windows'
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                windows = result_data.get('data', {}).get('windows', [])
                logger.info(f"Current windows: {len(windows)}")
        
        # Step 2: Launch Cursor using execute_program
        logger.info("\n=== Step 2: Launching Cursor ===")
        cursor_path = r"d:\cursor\Cursor.exe"
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_program',
                'params': {
                    'program': cursor_path,
                    'args': [],
                    'wait': False,
                    'shell': False
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
                    pid = result_data.get('data', {}).get('pid')
                    logger.info(f"✓ Cursor launched! PID: {pid}")
                else:
                    error = result_data.get('error', {})
                    logger.error(f"Failed to launch: {error}")
                    
                    # If execute_program doesn't exist, we need to restart the client
                    if 'Unknown command' in str(error):
                        logger.info("\n!!! The client needs to be restarted manually to load new commands !!!")
                        logger.info("Please:")
                        logger.info("1. Stop the current client (Ctrl+C in its console)")
                        logger.info("2. Start it again: python client.py")
                        logger.info("3. Run this script again")
                        return
        except asyncio.TimeoutError:
            logger.error("Launch command timeout")
            return
        
        # Wait for Cursor to start
        logger.info("\nWaiting for Cursor to start...")
        await asyncio.sleep(8)
        
        # Step 3: Find Cursor windows
        logger.info("\n=== Step 3: Finding Cursor windows ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'find_cursor_windows'
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        cursor_windows = []
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                cursor_data = result_data.get('data', {})
                cursor_windows = cursor_data.get('cursor_windows', [])
                
                if cursor_windows:
                    logger.info(f"✓ Found {len(cursor_windows)} Cursor window(s)!")
                    for w in cursor_windows:
                        logger.info(f"\n  Window: {w['title']}")
                        logger.info(f"  HWND: {w['hwnd']}")
                        logger.info(f"  PID: {w['pid']}")
                        logger.info(f"  Class: {w['class']}")
                else:
                    logger.warning("No Cursor windows found yet")
        
        # Step 4: Control Cursor
        if cursor_windows:
            cursor_hwnd = cursor_windows[0]['hwnd']
            logger.info(f"\n=== Step 4: Controlling Cursor ===")
            
            # Activate
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'activate_window',
                    'params': {'hwnd': cursor_hwnd}
                }
            }))
            
            await ws.recv()  # ack
            await asyncio.wait_for(ws.recv(), timeout=5.0)
            logger.info("✓ Window activated")
            
            await asyncio.sleep(1)
            
            # Type text
            test_text = "// CyberCorp Node - Cursor Control Success!"
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {'keys': test_text}
                }
            }))
            
            await ws.recv()  # ack
            await asyncio.wait_for(ws.recv(), timeout=5.0)
            logger.info(f"✓ Typed: {test_text}")
            
            # Take screenshot
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'screenshot',
                    'params': {'hwnd': cursor_hwnd}
                }
            }))
            
            await ws.recv()  # ack
            result = await asyncio.wait_for(ws.recv(), timeout=10.0)
            logger.info("✓ Screenshot taken")
            
            logger.info("\n🎉 SUCCESS! Cursor has been launched and controlled!")
        
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Final attempt to launch and control Cursor")
    logger.info("This script will:")
    logger.info("1. Find the newest client")
    logger.info("2. Launch Cursor.exe")
    logger.info("3. Find and control the Cursor window")
    logger.info("")
    
    asyncio.run(launch_cursor_final())

if __name__ == '__main__':
    main()