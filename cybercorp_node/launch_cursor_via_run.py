"""
Launch Cursor via Windows Run dialog
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LaunchCursorViaRun')

async def launch_cursor_via_run(host='localhost', port=9998, client_id='client_108'):
    """Launch Cursor using Windows Run dialog (Win+R)"""
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
        
        # Step 1: Get initial windows count
        logger.info("\n=== Step 1: Getting initial windows ===")
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
        
        initial_count = 0
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                windows = result_data.get('data', {}).get('windows', [])
                initial_count = len(windows)
                logger.info(f"Initial window count: {initial_count}")
        
        # Step 2: Open Run dialog (Win+R)
        logger.info("\n=== Step 2: Opening Run dialog (Win+R) ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '#r'  # Win+R
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info("Run dialog opened")
        
        # Wait for dialog to open
        await asyncio.sleep(1)
        
        # Step 3: Type Cursor path
        logger.info("\n=== Step 3: Typing Cursor path ===")
        cursor_path = r"d:\cursor\Cursor.exe"
        
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': cursor_path
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info(f"Typed: {cursor_path}")
        
        # Step 4: Press Enter to launch
        logger.info("\n=== Step 4: Pressing Enter to launch ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'send_keys',
                'params': {
                    'keys': '{ENTER}'
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=5.0)
        logger.info("Pressed Enter")
        
        # Wait for Cursor to start
        logger.info("\nWaiting for Cursor to start...")
        await asyncio.sleep(5)
        
        # Step 5: Check for new windows
        logger.info("\n=== Step 5: Checking for Cursor windows ===")
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
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                cursor_data = result_data.get('data', {})
                cursor_windows = cursor_data.get('cursor_windows', [])
                
                if cursor_windows:
                    logger.info(f"\n✓ Success! Found {len(cursor_windows)} Cursor window(s):")
                    for w in cursor_windows:
                        logger.info(f"  - Title: {w['title']}")
                        logger.info(f"    HWND: {w['hwnd']}")
                        logger.info(f"    Process: {w['process_name']} (PID: {w['pid']})")
                    
                    # Try to activate the first Cursor window
                    if cursor_windows:
                        cursor_hwnd = cursor_windows[0]['hwnd']
                        logger.info(f"\n=== Step 6: Activating Cursor window ===")
                        
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
                        logger.info("✓ Cursor window activated!")
                else:
                    logger.warning("No Cursor windows found yet")
                    
                    # Check all Chrome_WidgetWin_1 windows
                    chrome_windows = cursor_data.get('all_chrome_windows', [])
                    if chrome_windows:
                        logger.info(f"\nFound {len(chrome_windows)} Electron windows:")
                        for w in chrome_windows[:3]:
                            logger.info(f"  - {w['title'][:50]}... (Process: {w['process_name']})")
        
        await ws.close()
        logger.info("\n✓ Launch sequence completed!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Launching Cursor IDE via Windows Run dialog")
    logger.info("This method uses Win+R to launch Cursor")
    logger.info("")
    
    asyncio.run(launch_cursor_via_run())

if __name__ == '__main__':
    main()