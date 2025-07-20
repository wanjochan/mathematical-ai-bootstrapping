"""
Launch Cursor IDE and observe window changes
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LaunchCursor')

async def launch_and_observe(host='localhost', port=9998, client_id='client_108'):
    """Launch Cursor and observe window changes"""
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
        logger.info(f"Connected as: {json.loads(response).get('client_id')}")
        
        # Step 1: Get current processes (only current user)
        logger.info("\n=== Step 1: Getting current user processes ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'get_processes'
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                processes = result_data.get('data', {}).get('processes', [])
                cursor_processes = [p for p in processes if 'cursor' in p.get('name', '').lower()]
                logger.info(f"Current user Cursor processes: {len(cursor_processes)}")
                for p in cursor_processes:
                    logger.info(f"  - {p['name']} (PID: {p['pid']})")
        
        # Step 2: Get initial windows
        logger.info("\n=== Step 2: Getting initial windows ===")
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
        
        initial_windows = []
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                initial_windows = result_data.get('data', {}).get('windows', [])
                logger.info(f"Initial windows count: {len(initial_windows)}")
        
        # Step 3: Launch Cursor
        logger.info("\n=== Step 3: Launching Cursor IDE ===")
        cursor_path = r"d:\cursor\Cursor.exe"
        
        # Use shell execute to launch Cursor
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'shell_execute',
                'params': {
                    'command': f'start "" "{cursor_path}"'
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            logger.info(f"Launch result: {result_data}")
        
        # Wait for Cursor to start
        logger.info("Waiting for Cursor to start...")
        await asyncio.sleep(5)
        
        # Step 4: Get windows again
        logger.info("\n=== Step 4: Getting windows after launch ===")
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
        
        new_windows = []
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                new_windows = result_data.get('data', {}).get('windows', [])
                logger.info(f"Windows after launch: {len(new_windows)}")
                
                # Find new windows
                initial_hwnds = set(w['hwnd'] for w in initial_windows)
                new_window_list = [w for w in new_windows if w['hwnd'] not in initial_hwnds]
                
                if new_window_list:
                    logger.info(f"\n✓ Found {len(new_window_list)} new window(s):")
                    for w in new_window_list:
                        logger.info(f"  - Title: {w['title']}")
                        logger.info(f"    Class: {w['class']}")
                        logger.info(f"    HWND: {w['hwnd']}")
        
        # Step 5: Use find_cursor_windows
        logger.info("\n=== Step 5: Finding Cursor windows by process ===")
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
                    logger.info(f"✓ Found {len(cursor_windows)} Cursor window(s):")
                    for w in cursor_windows:
                        logger.info(f"  - {w['title']}")
                        logger.info(f"    Process: {w['process_name']} (PID: {w['pid']})")
                else:
                    # Check Chrome_WidgetWin_1 windows
                    chrome_windows = cursor_data.get('all_chrome_windows', [])
                    logger.info(f"No Cursor windows found, but found {len(chrome_windows)} Electron windows")
        
        await ws.close()
        logger.info("\n✓ Observation completed!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Launching Cursor IDE and observing window changes...")
    logger.info("This will help us understand how Cursor creates windows")
    logger.info("")
    
    asyncio.run(launch_and_observe())

if __name__ == '__main__':
    main()