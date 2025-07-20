"""
Launch Cursor using the new execute_program command
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LaunchCursorExecute')

async def launch_cursor_with_execute(host='localhost', port=9998, client_id='client_108'):
    """Launch Cursor using execute_program command"""
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
        
        # Step 1: Check if hot reload worked
        logger.info("\n=== Step 1: Testing if execute_program command exists ===")
        await ws.send(json.dumps({
            'type': 'forward_command',
            'target_client': client_id,
            'command': {
                'type': 'command',
                'command': 'execute_program',
                'params': {
                    'program': 'echo',
                    'args': 'Testing execute_program',
                    'wait': True,
                    'shell': True
                }
            }
        }))
        
        await ws.recv()  # ack
        
        try:
            result = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(result)
            logger.info(f"Test result: {json.dumps(data, indent=2)}")
        except asyncio.TimeoutError:
            logger.error("Command timeout - hot reload may not have worked")
            return
        
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
        
        initial_count = 0
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                windows = result_data.get('data', {}).get('windows', [])
                initial_count = len(windows)
                logger.info(f"Initial window count: {initial_count}")
        
        # Step 3: Launch Cursor
        logger.info("\n=== Step 3: Launching Cursor.exe ===")
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
                    'wait': False,  # Don't wait for completion
                    'shell': False
                }
            }
        }))
        
        await ws.recv()  # ack
        result = await asyncio.wait_for(ws.recv(), timeout=10.0)
        data = json.loads(result)
        
        if data.get('type') == 'command_result':
            result_data = data.get('result', {})
            if isinstance(result_data, dict) and result_data.get('success'):
                pid = result_data.get('data', {}).get('pid')
                logger.info(f"✓ Cursor launched with PID: {pid}")
            else:
                logger.error(f"Failed to launch Cursor: {result_data}")
                return
        
        # Wait for Cursor to start
        logger.info("\nWaiting for Cursor to initialize...")
        await asyncio.sleep(5)
        
        # Step 4: Check for Cursor windows
        logger.info("\n=== Step 4: Looking for Cursor windows ===")
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
                    logger.info(f"\n✓ SUCCESS! Found {len(cursor_windows)} Cursor window(s):")
                    for w in cursor_windows:
                        logger.info(f"\n  Window: {w['title']}")
                        logger.info(f"  HWND: {w['hwnd']}")
                        logger.info(f"  Process: {w['process_name']} (PID: {w['pid']})")
                        logger.info(f"  Class: {w['class']}")
                else:
                    # Wait a bit more
                    logger.info("No windows yet, waiting 5 more seconds...")
                    await asyncio.sleep(5)
                    
                    # Try again
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
                                logger.info(f"\n✓ Now found {len(cursor_windows)} Cursor window(s)!")
                                for w in cursor_windows:
                                    logger.info(f"  - {w['title']}")
        
        # Step 5: Try to control Cursor if found
        if cursor_windows:
            cursor_hwnd = cursor_windows[0]['hwnd']
            logger.info(f"\n=== Step 5: Testing Cursor control ===")
            
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
            await asyncio.wait_for(ws.recv(), timeout=5.0)
            logger.info("✓ Window activated")
            
            # Type test text
            await asyncio.sleep(1)
            
            test_text = "// Hello from CyberCorp Node!"
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': client_id,
                'command': {
                    'type': 'command',
                    'command': 'send_keys',
                    'params': {
                        'keys': test_text
                    }
                }
            }))
            
            await ws.recv()  # ack
            await asyncio.wait_for(ws.recv(), timeout=5.0)
            logger.info(f"✓ Typed: {test_text}")
        
        await ws.close()
        logger.info("\n✓ Test completed!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    logger.info("Launching Cursor using execute_program command")
    logger.info("This uses the newly added execute_program functionality")
    logger.info("")
    
    asyncio.run(launch_cursor_with_execute())

if __name__ == '__main__':
    main()