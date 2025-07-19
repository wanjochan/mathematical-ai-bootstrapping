"""
CyberCorp Control Client - Stable Version
Runs in target user session with VSCode, connects to control server
"""

import asyncio
import websockets
import json
import logging
import platform
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import base64
import configparser

# Windows-specific imports
if platform.system() == 'Windows':
    import win32api
    import win32con
    import win32gui
    import win32process
    import psutil
    import pyautogui
    from PIL import ImageGrab
    import pywinauto
    from pywinauto import Desktop, Application
    from pywinauto.keyboard import send_keys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CyberCorpClient')

class VSCodeController:
    """Controls VSCode window interactions"""
    
    def __init__(self):
        self.vscode_window = None
        self.app = None
        
    def find_vscode_window(self):
        """Find VSCode window in current session"""
        try:
            desktop = Desktop(backend="uia")
            
            for window in desktop.windows():
                try:
                    title = window.window_text()
                    class_name = window.class_name()
                    
                    if ('Visual Studio Code' in title or 
                        'VSCode' in title or 
                        class_name == 'Chrome_WidgetWin_1'):
                        
                        # Verify it's VSCode by checking process
                        hwnd = window.handle
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        
                        if 'code' in process.name().lower():
                            self.vscode_window = window
                            self.app = Application(backend="uia").connect(handle=hwnd)
                            logger.info(f"Found VSCode: {title}")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Error checking window: {e}")
                    
            logger.warning("VSCode window not found")
            return False
            
        except Exception as e:
            logger.error(f"Error finding VSCode: {e}")
            return False
    
    def get_window_content(self):
        """Extract VSCode window content including Roo Code dialog"""
        if not self.vscode_window:
            if not self.find_vscode_window():
                return None
                
        try:
            content = {
                'window_title': self.vscode_window.window_text(),
                'is_active': self.vscode_window.has_keyboard_focus(),
                'rectangle': str(self.vscode_window.rectangle()),
                'content_areas': []
            }
            
            # Deep scan for content
            self._extract_content(self.vscode_window, content['content_areas'])
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting window content: {e}")
            return None
    
    def _extract_content(self, element, content_list, depth=0, max_depth=10):
        """Recursively extract text content from UI elements"""
        if depth > max_depth:
            return
            
        try:
            # Get element info
            elem_info = {
                'type': element.element_info.control_type,
                'name': element.element_info.name or '',
                'texts': []
            }
            
            # Get texts
            try:
                texts = element.texts()
                elem_info['texts'] = [t for t in texts if t and len(t) > 3]
            except:
                pass
            
            # Add if has content
            if elem_info['texts'] or 'Roo Code' in elem_info['name']:
                content_list.append(elem_info)
            
            # Process children
            for child in element.children():
                self._extract_content(child, content_list, depth + 1, max_depth)
                
        except:
            pass
    
    def activate_window(self):
        """Bring VSCode window to foreground"""
        if not self.vscode_window:
            if not self.find_vscode_window():
                return False
                
        try:
            self.vscode_window.set_focus()
            return True
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False
    
    def send_keys_to_vscode(self, keys: str):
        """Send keystrokes to VSCode"""
        if not self.activate_window():
            return False
            
        try:
            time.sleep(0.1)  # Small delay for window activation
            send_keys(keys)
            return True
        except Exception as e:
            logger.error(f"Error sending keys: {e}")
            return False
    
    def type_text(self, text: str):
        """Type text in VSCode"""
        # Escape special characters
        escaped_text = text.replace('{', '{{').replace('}', '}}')
        return self.send_keys_to_vscode(escaped_text)
    
    def send_command(self, command: str):
        """Send command to VSCode (Ctrl+Shift+P)"""
        if not self.activate_window():
            return False
            
        try:
            # Open command palette
            send_keys('^+p')
            time.sleep(0.5)
            
            # Type command
            send_keys(command)
            time.sleep(0.1)
            
            # Execute
            send_keys('{ENTER}')
            return True
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

class CyberCorpClient:
    def __init__(self, server_url=None):
        # Load configuration
        self.config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        if os.path.exists(config_path):
            self.config.read(config_path)
            logger.info(f"Loaded configuration from {config_path}")
        
        # Client configuration with fallbacks
        server_host = self.config.get('client', 'server_host', fallback='localhost')
        server_port = self.config.getint('client', 'server_port', fallback=9998)
        
        # Allow URL override, then config, then environment
        self.server_url = server_url or os.environ.get('CYBERCORP_SERVER', f'ws://{server_host}:{server_port}')
        self.reconnect_delay = self.config.getint('client', 'reconnect_interval', fallback=5)
        self.heartbeat_interval = self.config.getint('client', 'heartbeat_interval', fallback=30)
        self.client_id = None
        self.ws = None
        self.running = True
        self.vscode_controller = VSCodeController()
        self.reconnect_delay = 5
        self.start_time = datetime.now()
        
    async def connect(self):
        """Connect to control server with auto-reconnect"""
        while self.running:
            try:
                logger.info(f"Connecting to {self.server_url}...")
                
                self.ws = await websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                logger.info("Connected to control server")
                
                # Register with server
                await self._register()
                
                # Start heartbeat
                heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                try:
                    # Handle messages
                    async for message in self.ws:
                        await self._handle_message(message)
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed")
                    
                heartbeat_task.cancel()
                
            except Exception as e:
                logger.error(f"Connection error: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
    
    async def _register(self):
        """Register client with server"""
        registration = {
            'type': 'register',
            'user_session': os.environ.get('USERNAME', 'unknown'),
            'client_start_time': self.start_time.isoformat(),
            'capabilities': {
                'vscode_control': True,
                'ui_automation': True,
                'screenshot': True,
                'input_control': True
            },
            'system_info': {
                'platform': platform.system(),
                'hostname': platform.node(),
                'python_version': platform.python_version()
            }
        }
        
        await self.ws.send(json.dumps(registration))
        logger.info(f"Registered as user: {registration['user_session']}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.ws.send(json.dumps({'type': 'heartbeat'}))
            except:
                break
    
    async def _handle_message(self, message: str):
        """Handle incoming messages from server"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'welcome':
                self.client_id = data.get('client_id')
                logger.info(f"Assigned client ID: {self.client_id}")
                
            elif msg_type == 'command':
                await self._execute_command(data)
                
            elif msg_type == 'heartbeat_ack':
                pass  # Heartbeat acknowledged
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _execute_command(self, command_data: dict):
        """Execute command from server"""
        command_id = command_data.get('command_id')
        command = command_data.get('command')
        params = command_data.get('params', {})
        
        logger.info(f"Executing command: {command}")
        
        result = None
        error = None
        
        try:
            # Window operations
            if command == 'get_windows':
                result = self._get_windows()
                
            elif command == 'get_window_content':
                result = self.vscode_controller.get_window_content()
                
            elif command == 'activate_window':
                result = self.vscode_controller.activate_window()
                
            # Input operations
            elif command == 'send_keys':
                keys = params.get('keys', '')
                result = self.vscode_controller.send_keys_to_vscode(keys)
                
            elif command == 'send_mouse_click':
                x = params.get('x', 0)
                y = params.get('y', 0)
                pyautogui.click(x, y)
                result = True
                
            # Screen operations
            elif command == 'take_screenshot':
                result = self._take_screenshot()
                
            elif command == 'get_screen_size':
                result = {'width': pyautogui.size()[0], 'height': pyautogui.size()[1]}
                
            # System operations
            elif command == 'get_processes':
                result = self._get_processes()
                
            elif command == 'get_system_info':
                result = self._get_system_info()
                
            # VSCode specific
            elif command == 'vscode_get_content':
                result = self.vscode_controller.get_window_content()
                
            elif command == 'vscode_send_command':
                vscode_cmd = params.get('command', '')
                result = self.vscode_controller.send_command(vscode_cmd)
                
            elif command == 'vscode_type_text':
                text = params.get('text', '')
                result = self.vscode_controller.type_text(text)
                
            # Background operations (no window activation)
            elif command == 'background_input':
                element_name = params.get('element_name', '')
                text = params.get('text', '')
                
                if self.vscode_controller.vscode_window:
                    try:
                        # Try to find element by name
                        elements = self.vscode_controller.vscode_window.descendants()
                        for elem in elements:
                            if elem.window_text() == element_name:
                                elem.set_text(text)
                                result = True
                                break
                        else:
                            # If not found by exact name, try type_text without activation
                            escaped_text = text.replace('{', '{{').replace('}', '}}')
                            send_keys(escaped_text)
                            result = True
                    except Exception as e:
                        logger.error(f"Background input error: {e}")
                        result = False
                else:
                    result = False
                    
            elif command == 'background_click':
                element_name = params.get('element_name', '')
                
                if self.vscode_controller.vscode_window:
                    try:
                        elements = self.vscode_controller.vscode_window.descendants()
                        for elem in elements:
                            if elem.window_text() == element_name:
                                elem.click_input()
                                result = True
                                break
                        else:
                            result = False
                    except Exception as e:
                        logger.error(f"Background click error: {e}")
                        result = False
                else:
                    result = False
                
            else:
                error = f"Unknown command: {command}"
                
        except Exception as e:
            error = str(e)
            logger.error(f"Command execution error: {e}")
        
        # Send result back
        response = {
            'type': 'command_result',
            'command_id': command_id,
            'result': result,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.ws.send(json.dumps(response))
    
    def _get_windows(self):
        """Get list of all windows"""
        windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'class': win32gui.GetClassName(hwnd)
                    })
            return True
            
        win32gui.EnumWindows(enum_handler, None)
        return windows
    
    def _take_screenshot(self):
        """Take screenshot and return as base64"""
        try:
            screenshot = ImageGrab.grab()
            
            # Convert to base64
            import io
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'image': img_base64,
                'width': screenshot.width,
                'height': screenshot.height
            }
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    def _get_processes(self):
        """Get running processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'] or 0,
                    'memory_mb': round(pinfo['memory_info'].rss / 1024 / 1024)
                })
            except:
                pass
                
        return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:50]
    
    def _get_system_info(self):
        """Get system information"""
        return {
            'hostname': platform.node(),
            'platform': platform.platform(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
            'user': os.environ.get('USERNAME', 'unknown')
        }
    
    async def run(self):
        """Main client loop"""
        try:
            await self.connect()
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
        finally:
            self.running = False
            if self.ws:
                await self.ws.close()

if __name__ == "__main__":
    # Configure pyautogui
    pyautogui.FAILSAFE = False  # Allow control even at screen edges
    pyautogui.PAUSE = 0.1  # Small delay between actions
    
    client = CyberCorpClient()
    asyncio.run(client.run())