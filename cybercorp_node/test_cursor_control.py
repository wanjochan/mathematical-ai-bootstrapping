"""Test script to control Cursor IDE"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def control_cursor():
    """Control Cursor IDE on wjchk"""
    try:
        # Connect to server
        uri = "ws://localhost:9998"
        async with websockets.connect(uri) as ws:
            logger.info("Connected to server")
            
            # Register as test client
            await ws.send(json.dumps({
                'type': 'register',
                'client_type': 'cursor_control'
            }))
            
            # Wait for registration response
            response = await ws.recv()
            logger.info(f"Registration response: {response}")
            
            # List clients
            await ws.send(json.dumps({'type': 'list_clients'}))
            clients_response = await ws.recv()
            clients = json.loads(clients_response)
            logger.info(f"Clients: {json.dumps(clients, indent=2)}")
            
            # Find wjchk client
            wjchk_client = None
            for client in clients.get('clients', []):
                if client.get('username') == 'wjchk':
                    wjchk_client = client
                    break
                    
            if not wjchk_client:
                logger.error("Client 'wjchk' not found")
                return
                
            client_id = wjchk_client['id']
            logger.info(f"Found wjchk client: {client_id}")
            
            # Get windows
            await ws.send(json.dumps({
                'type': 'forward_command',
                'target_client_id': client_id,
                'command': 'get_windows'
            }))
            
            windows_response = await ws.recv()
            windows_data = json.loads(windows_response)
            
            if windows_data.get('success'):
                windows = windows_data.get('result', [])
                
                # Find Cursor window
                cursor_window = None
                for window in windows:
                    title = window.get('title', '').lower()
                    if 'cursor' in title:
                        cursor_window = window
                        logger.info(f"Found Cursor window: {window}")
                        break
                        
                if not cursor_window:
                    logger.error("Cursor window not found")
                    # List all windows for debugging
                    logger.info("Available windows:")
                    for w in windows[:10]:  # Show first 10
                        logger.info(f"  - {w.get('title')} (class: {w.get('class')})")
                    return
                    
                # Now try to interact with Cursor
                # First activate the window
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client_id': client_id,
                    'command': 'activate_window',
                    'params': {'hwnd': cursor_window['hwnd']}
                }))
                
                activate_response = await ws.recv()
                logger.info(f"Activate response: {activate_response}")
                
                # Wait a bit for window to activate
                await asyncio.sleep(1)
                
                # Now send the text
                text_to_send = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
                
                # Send keys to input the text
                await ws.send(json.dumps({
                    'type': 'forward_command',
                    'target_client_id': client_id,
                    'command': 'send_keys',
                    'params': {'keys': text_to_send}
                }))
                
                keys_response = await ws.recv()
                logger.info(f"Send keys response: {keys_response}")
                
            else:
                logger.error(f"Failed to get windows: {windows_data}")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        
if __name__ == "__main__":
    asyncio.run(control_cursor())