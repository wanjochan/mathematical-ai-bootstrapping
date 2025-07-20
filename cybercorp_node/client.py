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
    
    # Import new backends
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # Import backends on demand to avoid startup errors
    Win32Backend = None
    OCRBackend = None

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
                'mouse_drag': True,
                'ocr': True,
                'win32_api': True,
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
        global Win32Backend, OCRBackend
        command_id = command_data.get('command_id')
        command = command_data.get('command')
        params = command_data.get('params', {})
        
        # Enhanced logging with parameter info
        param_log = json.dumps(params, ensure_ascii=False) if params else "None"
        if len(param_log) > 200:
            param_log = param_log[:200] + "... (truncated)"
        logger.info(f"Executing command: {command} | Params: {param_log}")
        
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
                    
            # Mouse drag operations
            elif command == 'mouse_drag':
                start_x = params.get('start_x', 0)
                start_y = params.get('start_y', 0)
                end_x = params.get('end_x', 0)
                end_y = params.get('end_y', 0)
                duration = params.get('duration', 1.0)
                button = params.get('button', 'left')
                humanize = params.get('humanize', True)
                
                try:
                    # Import on demand
                    if Win32Backend is None:
                        from utils.win32_backend import Win32Backend
                    win32_backend = Win32Backend()
                    result = win32_backend.mouse_drag(
                        start_x, start_y, end_x, end_y,
                        duration=duration, button=button, humanize=humanize
                    )
                except Exception as e:
                    logger.error(f"Mouse drag error: {e}")
                    result = False
                    
            # OCR operations
            elif command == 'ocr_screen':
                x = params.get('x', 0)
                y = params.get('y', 0)
                width = params.get('width', 0)
                height = params.get('height', 0)
                engine = params.get('engine', None)  # None for auto-select
                
                try:
                    # Take screenshot of specified region
                    if width > 0 and height > 0:
                        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                    else:
                        screenshot = ImageGrab.grab()
                        
                    # Perform OCR
                    # Import on demand
                    if OCRBackend is None:
                        from utils.ocr_backend import OCRBackend
                    ocr_backend = OCRBackend()
                    detections = ocr_backend.detect_text(screenshot, engine=engine)
                    
                    # Format results
                    result = {
                        'success': True,
                        'detections': detections,
                        'available_engines': list(ocr_backend.available_engines.keys())
                    }
                except Exception as e:
                    logger.error(f"OCR error: {e}")
                    result = {'success': False, 'error': str(e)}
                    
            elif command == 'ocr_window':
                hwnd = params.get('hwnd', None)
                engine = params.get('engine', None)
                
                try:
                    if hwnd:
                        # Capture specific window
                        # Import on demand
                        if Win32Backend is None:
                            from utils.win32_backend import Win32Backend
                        win32_backend = Win32Backend()
                        image = win32_backend.capture_window(hwnd)
                        
                        if image is not None:
                            # Perform OCR
                            ocr_backend = OCRBackend()
                            detections = ocr_backend.detect_text(image, engine=engine)
                            
                            result = {
                                'success': True,
                                'detections': detections
                            }
                        else:
                            result = {'success': False, 'error': 'Failed to capture window'}
                    else:
                        result = {'success': False, 'error': 'No window handle provided'}
                except Exception as e:
                    logger.error(f"Window OCR error: {e}")
                    result = {'success': False, 'error': str(e)}
                    
            # Win32 API operations
            elif command == 'win32_find_window':
                class_name = params.get('class_name', None)
                window_name = params.get('window_name', None)
                
                try:
                    # Import on demand
                    if Win32Backend is None:
                        from utils.win32_backend import Win32Backend
                    win32_backend = Win32Backend()
                    hwnd = win32_backend.find_window(class_name, window_name)
                    if hwnd:
                        info = win32_backend.get_window_info(hwnd)
                        result = {'success': True, 'hwnd': hwnd, 'info': info}
                    else:
                        result = {'success': False, 'error': 'Window not found'}
                except Exception as e:
                    logger.error(f"Find window error: {e}")
                    result = {'success': False, 'error': str(e)}
                    
            elif command == 'win32_send_keys':
                keys = params.get('keys', '')
                delay = params.get('delay', 0.01)
                
                try:
                    # Import on demand
                    if Win32Backend is None:
                        from utils.win32_backend import Win32Backend
                    win32_backend = Win32Backend()
                    success = win32_backend.send_keys(keys, delay)
                    result = {'success': success}
                except Exception as e:
                    logger.error(f"Send keys error: {e}")
                    result = {'success': False, 'error': str(e)}
            
            elif command == 'screenshot':
                # Take screenshot of entire screen or specific window
                import os
                from datetime import datetime
                
                window_hwnd = params.get('hwnd')
                save_path = params.get('save_path')
                
                try:
                    if not save_path:
                        # Generate default path
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        save_path = os.path.join(os.path.dirname(__file__), f'screenshot_{timestamp}.png')
                    
                    if window_hwnd:
                        # Screenshot specific window
                        import win32gui
                        import win32ui
                        import win32con
                        from PIL import Image
                        
                        # Get window rect
                        left, top, right, bottom = win32gui.GetWindowRect(window_hwnd)
                        width = right - left
                        height = bottom - top
                        
                        # Get window DC
                        hwndDC = win32gui.GetWindowDC(window_hwnd)
                        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                        saveDC = mfcDC.CreateCompatibleDC()
                        
                        # Create bitmap
                        saveBitMap = win32ui.CreateBitmap()
                        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                        saveDC.SelectObject(saveBitMap)
                        
                        # Copy window content
                        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
                        
                        # Save bitmap
                        bmpinfo = saveBitMap.GetInfo()
                        bmpstr = saveBitMap.GetBitmapBits(True)
                        
                        # Convert to PIL Image
                        img = Image.frombuffer(
                            'RGB',
                            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                            bmpstr, 'raw', 'BGRX', 0, 1
                        )
                        
                        # Save
                        img.save(save_path)
                        
                        # Cleanup
                        win32gui.DeleteObject(saveBitMap.GetHandle())
                        saveDC.DeleteDC()
                        mfcDC.DeleteDC()
                        win32gui.ReleaseDC(window_hwnd, hwndDC)
                    else:
                        # Full screen screenshot
                        screenshot = pyautogui.screenshot()
                        screenshot.save(save_path)
                    
                    result = {
                        'success': True,
                        'path': os.path.abspath(save_path),
                        'size': os.path.getsize(save_path)
                    }
                    logger.info(f"Screenshot saved to: {save_path}")
                    
                except Exception as e:
                    logger.error(f"Screenshot error: {e}")
                    result = {'success': False, 'error': str(e)}
                    
            elif command == 'get_window_uia_structure':
                hwnd = params.get('hwnd')
                if hwnd:
                    result = self._get_window_uia_structure(hwnd)
                else:
                    error = "Missing hwnd parameter"
                
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
        
        # Enhanced logging for results
        if error:
            logger.error(f"Command '{command}' failed: {error}")
        else:
            # Sample result for logging
            result_log = str(result)
            if len(result_log) > 300:
                result_log = result_log[:300] + "... (truncated)"
            logger.info(f"Command '{command}' completed | Result: {result_log}")
        
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
    
    def _get_window_uia_structure(self, hwnd):
        """Get complete UIA structure of any window"""
        try:
            from pywinauto import Application
            
            # Connect to the window
            app = Application(backend="uia").connect(handle=hwnd)
            window = app.window(handle=hwnd)
            
            def extract_structure(element, depth=0, max_depth=15):
                """Extract complete element structure"""
                if depth > max_depth:
                    return {"error": "Max depth reached"}
                    
                try:
                    elem_info = element.element_info
                    
                    structure = {
                        'ControlType': elem_info.control_type,
                        'Name': elem_info.name or '',
                        'AutomationId': element.automation_id() if hasattr(element, 'automation_id') else '',
                        'ClassName': elem_info.class_name or '',
                        'IsEnabled': elem_info.enabled,
                        'IsVisible': elem_info.visible,
                        'Rectangle': str(elem_info.rectangle),
                        'Children': {}
                    }
                    
                    # Add value for editable controls
                    if elem_info.control_type in ['Edit', 'ComboBox']:
                        try:
                            structure['Value'] = element.get_value() if hasattr(element, 'get_value') else ''
                            structure['IsKeyboardFocusable'] = getattr(elem_info, 'keyboard_focusable', False)
                        except:
                            structure['Value'] = ''
                    
                    # Get texts
                    try:
                        texts = element.texts()
                        if texts:
                            structure['Texts'] = texts
                    except:
                        pass
                        
                    # Get children
                    try:
                        children = element.children()
                        for i, child in enumerate(children):
                            child_name = ''
                            child_type = ''
                            child_id = ''
                            
                            try:
                                child_info = child.element_info
                                child_name = child_info.name or ''
                                child_type = child_info.control_type
                                child_id = child.automation_id() if hasattr(child, 'automation_id') else ''
                            except:
                                pass
                            
                            # Create descriptive key
                            if child_id:
                                child_key = f"{child_type}_{child_id}_{i}"
                            elif child_name:
                                safe_name = ''.join(c if c.isalnum() else '_' for c in child_name[:20])
                                child_key = f"{child_type}_{safe_name}_{i}"
                            else:
                                child_key = f"{child_type}_{i}"
                                
                            structure['Children'][child_key] = extract_structure(child, depth + 1, max_depth)
                            
                    except Exception as e:
                        logger.debug(f"Error getting children: {e}")
                        
                    return structure
                    
                except Exception as e:
                    return {"error": str(e)}
            
            # Extract full structure
            return extract_structure(window)
            
        except Exception as e:
            logger.error(f"Error getting UIA structure: {e}")
            return {"error": str(e)}
    
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