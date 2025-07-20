"""Correctly control Cursor IDE on wjchk"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def control_cursor():
    """Control Cursor IDE with correct protocol"""
    try:
        uri = "ws://localhost:9998"
        async with websockets.connect(uri) as ws:
            # Register as management client
            await ws.send(json.dumps({
                'type': 'register',
                'client_type': 'cursor_controller',
                'capabilities': {'management': True}
            }))
            
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"Connected: {json.loads(welcome)['client_id']}")
            
            # First get client list to find wjchk
            await ws.send(json.dumps({'type': 'list_clients'}))
            clients_resp = await ws.recv()
            clients_data = json.loads(clients_resp)
            
            # Find wjchk client
            wjchk_id = None
            for client in clients_data.get('clients', []):
                if client.get('user_session') == 'wjchk' or client.get('username') == 'wjchk':
                    wjchk_id = client['id']
                    logger.info(f"Found wjchk client: {wjchk_id}")
                    break
                    
            if not wjchk_id:
                logger.error("wjchk client not found")
                logger.info(f"Available clients: {json.dumps(clients_data.get('clients', []), indent=2)}")
                return
                
            # Now send commands using correct format
            # 1. Get windows
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client': wjchk_id,  # Note: target_client not target_client_id
                'command': {
                    'type': 'command',
                    'command': 'get_windows',
                    'command_id': f'cmd_windows_{datetime.now().timestamp()}'
                }
            }))
            
            # Wait for windows result
            windows_msg = await ws.recv()
            windows_data = json.loads(windows_msg)
            
            if windows_data.get('type') == 'command_result':
                result = windows_data.get('result', {})
                if result.get('success'):
                    windows = result.get('result', [])
                    logger.info(f"Got {len(windows)} windows")
                    
                    # Find Cursor
                    cursor_window = None
                    for w in windows:
                        title = w.get('title', '').lower()
                        if 'cursor' in title:
                            cursor_window = w
                            logger.info(f"Found Cursor: {w['title']}")
                            break
                            
                    if cursor_window:
                        # Activate Cursor window
                        await ws.send(json.dumps({
                            'type': 'forward_command',
                            'target_client': wjchk_id,
                            'command': {
                                'type': 'command',
                                'command': 'activate_window',
                                'params': {'hwnd': cursor_window['hwnd']},
                                'command_id': f'cmd_activate_{datetime.now().timestamp()}'
                            }
                        }))
                        
                        activate_resp = await ws.recv()
                        logger.info("Window activated")
                        
                        # Wait a bit
                        await asyncio.sleep(1)
                        
                        # Send the text
                        text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
                        
                        await ws.send(json.dumps({
                            'type': 'forward_command',
                            'target_client': wjchk_id,
                            'command': {
                                'type': 'command',
                                'command': 'send_keys',
                                'params': {'keys': text},
                                'command_id': f'cmd_keys_{datetime.now().timestamp()}'
                            }
                        }))
                        
                        keys_resp = await ws.recv()
                        logger.info("Text sent to Cursor")
                        
                        # Optional: Send Enter to execute
                        await asyncio.sleep(0.5)
                        await ws.send(json.dumps({
                            'type': 'forward_command',
                            'target_client': wjchk_id,
                            'command': {
                                'type': 'command',
                                'command': 'send_keys',
                                'params': {'keys': '{ENTER}'},
                                'command_id': f'cmd_enter_{datetime.now().timestamp()}'
                            }
                        }))
                        
                        enter_resp = await ws.recv()
                        logger.info("Enter key sent")
                        
                    else:
                        logger.error("Cursor window not found")
                        logger.info("Available windows (first 10):")
                        for w in windows[:10]:
                            logger.info(f"  - {w.get('title', 'No title')}")
                            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(control_cursor())