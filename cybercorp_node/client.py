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

# Setup logging with enhanced log manager
from utils.log_manager import setup_logging, get_log_manager
from utils.response_formatter import ResponseFormatter, format_success, format_error

# Initialize enhanced logging
log_manager = setup_logging(app_name='CyberCorpClient')
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
                return format_error("VSCode window not found", error_code='WINDOW_NOT_FOUND')
                
        try:
            content = {
                'window_title': self.vscode_window.window_text(),
                'is_active': self.vscode_window.has_keyboard_focus(),
                'rectangle': str(self.vscode_window.rectangle()),
                'content_areas': []
            }
            
            # Deep scan for content
            self._extract_content(self.vscode_window, content['content_areas'])
            
            return format_success(
                data=content,
                message=f"Window content retrieved: {content['window_title']}"
            )
            
        except Exception as e:
            logger.error(f"Error getting window content: {e}")
            return format_error(e, error_code='GET_CONTENT_FAILED')
    
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
        """Bring VSCode window to foreground with improved reliability"""
        if not self.vscode_window:
            if not self.find_vscode_window():
                return False
                
        try:
            hwnd = self.vscode_window.handle
            
            # Use Win32 API for more reliable activation
            # First, check if window is minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
            
            # Set foreground window using multiple methods for reliability
            # Method 1: SetForegroundWindow
            win32gui.SetForegroundWindow(hwnd)
            
            # Method 2: Use pywinauto's set_focus
            self.vscode_window.set_focus()
            
            # Method 3: Simulate alt key to ensure we can set foreground
            # This is a Windows trick to bypass foreground window restrictions
            import ctypes
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt key down
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt key up
            
            # Try SetForegroundWindow again
            win32gui.SetForegroundWindow(hwnd)
            
            # Wait for window to be active
            time.sleep(0.2)
            
            # Verify activation
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd == hwnd:
                logger.info("Window activated successfully")
                return True
            else:
                logger.warning(f"Window activation may have failed. Expected {hwnd}, got {foreground_hwnd}")
                # Try one more time with BringWindowToTop
                win32gui.BringWindowToTop(hwnd)
                time.sleep(0.1)
                return True
                
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False
    
    def send_keys_to_vscode(self, keys: str):
        """Send keystrokes to VSCode with improved reliability"""
        if not self.activate_window():
            return False
            
        try:
            # Additional delay to ensure window is ready
            time.sleep(0.3)
            
            # Verify window still has focus before sending keys
            hwnd = self.vscode_window.handle
            if win32gui.GetForegroundWindow() != hwnd:
                logger.warning("Window lost focus, reactivating...")
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
            
            # Clear any pending input
            import ctypes
            ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)  # ESC key down
            ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)  # ESC key up
            time.sleep(0.05)
            
            # Send keys with small delays for reliability
            send_keys(keys, pause=0.01, with_spaces=True)
            
            # Small delay after sending keys
            time.sleep(0.05)
            
            return True
        except Exception as e:
            logger.error(f"Error sending keys: {e}")
            return False
    
    def type_text(self, text: str):
        """Type text in VSCode with proper escaping"""
        # More comprehensive escaping for pywinauto
        escaped_text = text
        # Escape special characters used by pywinauto
        special_chars = {
            '{': '{{',
            '}': '}}',
            '+': '{+}',
            '^': '{^}',
            '%': '{%}',
            '~': '{~}',
            '(': '{(}',
            ')': '{)}',
            '[': '{[}',
            ']': '{]}'
        }
        
        for char, escaped in special_chars.items():
            escaped_text = escaped_text.replace(char, escaped)
        
        return self.send_keys_to_vscode(escaped_text)
    
    def send_command(self, command: str):
        """Send command to VSCode (Ctrl+Shift+P) with improved reliability"""
        if not self.activate_window():
            return False
            
        try:
            # Ensure window has focus
            hwnd = self.vscode_window.handle
            if win32gui.GetForegroundWindow() != hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
            
            # Open command palette with explicit key codes
            import ctypes
            user32 = ctypes.windll.user32
            
            # Press Ctrl+Shift+P
            user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            user32.keybd_event(0x10, 0, 0, 0)  # Shift down
            user32.keybd_event(0x50, 0, 0, 0)  # P down
            time.sleep(0.05)
            user32.keybd_event(0x50, 0, 2, 0)  # P up
            user32.keybd_event(0x10, 0, 2, 0)  # Shift up
            user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            
            # Wait for command palette to open
            time.sleep(0.7)
            
            # Clear any existing text
            send_keys('^a')
            time.sleep(0.05)
            
            # Type command
            self.type_text(command)
            time.sleep(0.2)
            
            # Execute with Enter
            user32.keybd_event(0x0D, 0, 0, 0)  # Enter down
            user32.keybd_event(0x0D, 0, 2, 0)  # Enter up
            
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
        self.start_time = datetime.now()
        
        # Reconnection parameters
        self.max_reconnect_delay = 60
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = -1  # -1 means infinite
        
        # Hot reload support
        self.hot_reload = None
        self.enable_hot_reload = self.config.getboolean('client', 'enable_hot_reload', fallback=True)
        
        # Health monitoring
        self.health_monitor = None
        self.enable_health_monitor = self.config.getboolean('client', 'enable_health_monitor', fallback=True)
        
    async def connect(self):
        """Connect to control server with auto-reconnect and exponential backoff"""
        while self.running:
            try:
                self.reconnect_attempts += 1
                logger.info(f"Connection attempt #{self.reconnect_attempts} to {self.server_url}...")
                
                # Check max attempts
                if self.max_reconnect_attempts > 0 and self.reconnect_attempts > self.max_reconnect_attempts:
                    logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
                    break
                
                self.ws = await websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                logger.info("Connected to control server")
                
                # Reset reconnection parameters on successful connection
                self.reconnect_attempts = 0
                current_delay = self.reconnect_delay
                
                # Register with server
                await self._register()
                
                # Start hot reload if enabled
                if self.enable_hot_reload and self.hot_reload is None:
                    await self._start_hot_reload()
                
                # Start health monitor if enabled
                if self.enable_health_monitor and self.health_monitor is None:
                    await self._start_health_monitor()
                
                # Start heartbeat
                heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                try:
                    # Handle messages
                    async for message in self.ws:
                        await self._handle_message(message)
                        
                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"Connection closed: {e}")
                except websockets.exceptions.ConnectionClosedError as e:
                    logger.error(f"Connection error: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error in message handling: {e}")
                    
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
                
            except asyncio.TimeoutError:
                logger.error("Connection timeout")
            except Exception as e:
                logger.error(f"Connection error: {e}")
                
            if self.running:
                # Calculate exponential backoff with jitter
                current_delay = min(
                    self.reconnect_delay * (2 ** min(self.reconnect_attempts - 1, 5)),
                    self.max_reconnect_delay
                )
                # Add jitter to prevent thundering herd
                import random
                jitter = current_delay * 0.1 * random.random()
                current_delay = current_delay + jitter
                
                logger.info(f"Reconnecting in {current_delay:.1f} seconds (attempt #{self.reconnect_attempts})...")
                await asyncio.sleep(current_delay)
    
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
                'input_control': True,
                'hot_reload': self.enable_hot_reload
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
                
                # Record heartbeat time for latency measurement
                heartbeat_time = time.time()
                await self.ws.send(json.dumps({
                    'type': 'heartbeat',
                    'timestamp': heartbeat_time
                }))
                
                # Update health monitor
                if self.health_monitor:
                    self.health_monitor.update_heartbeat()
                    
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
                # Calculate heartbeat latency
                if 'timestamp' in data and self.health_monitor:
                    latency = time.time() - data['timestamp']
                    self.health_monitor.update_heartbeat(latency)
                
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
        
        # Get timeout from params or use default
        timeout = params.get('timeout', 30.0)  # Default 30 seconds
        start_time = time.time()
        
        # Track command start in health monitor
        if self.health_monitor and command_id:
            self.health_monitor.track_command_start(command_id, command)
        
        try:
            # Create a task for the actual command execution
            exec_task = asyncio.create_task(self._execute_command_impl(command, params))
            
            # Wait for completion with timeout
            try:
                result = await asyncio.wait_for(exec_task, timeout=timeout)
            except asyncio.TimeoutError:
                # Command timed out
                error = f"Command '{command}' timed out after {timeout} seconds"
                logger.error(error)
                
                # Try to cancel the task
                exec_task.cancel()
                try:
                    await exec_task
                except asyncio.CancelledError:
                    pass
                
        except Exception as e:
            error = str(e)
            logger.error(f"Command execution error: {e}")
        
        # Calculate execution time
        exec_time = time.time() - start_time
        
        # Format response using unified formatter
        if error:
            # Command failed
            formatted_result = format_error(
                error,
                error_code='COMMAND_EXECUTION_ERROR',
                details={
                    'command': command,
                    'command_id': command_id,
                    'execution_time': exec_time,
                    'params': params
                }
            )
        else:
            # Command succeeded - normalize result
            if isinstance(result, dict) and ResponseFormatter.validate_response(result):
                # Result is already in unified format
                formatted_result = result
            else:
                # Convert to unified format
                formatted_result = ResponseFormatter.normalize_legacy_response(result, command)
                # Add execution metadata
                formatted_result['metadata'] = {
                    'command': command,
                    'command_id': command_id,
                    'execution_time': exec_time
                }
        
        # Create final response for server
        response = {
            'type': 'command_result',
            'command_id': command_id,
            'result': formatted_result
        }
        
        # Track command end in health monitor
        if self.health_monitor and command_id:
            self.health_monitor.track_command_end(command_id, not error, error)
        
        # Enhanced logging for results
        if error:
            logger.error(f"Command '{command}' failed: {error}")
        else:
            # Sample result for logging
            result_log = json.dumps(formatted_result.get('data', formatted_result))
            if len(result_log) > 300:
                result_log = result_log[:300] + "... (truncated)"
            logger.info(f"Command '{command}' completed in {exec_time:.2f}s | Result: {result_log}")
        
        await self.ws.send(json.dumps(response))
    
    async def _execute_command_impl(self, command: str, params: dict):
        """Actual command implementation (separated for timeout handling)"""
        global Win32Backend, OCRBackend
        
        # Make synchronous operations async-friendly
        loop = asyncio.get_event_loop()
        
        try:
            # Window operations
            if command == 'get_windows':
                return await loop.run_in_executor(None, self._get_windows)
                
            elif command == 'find_cursor_windows':
                return await loop.run_in_executor(None, self._find_cursor_windows)
                
            elif command == 'get_window_content':
                return await loop.run_in_executor(None, self.vscode_controller.get_window_content)
                
            elif command == 'activate_window':
                return await loop.run_in_executor(None, self.vscode_controller.activate_window)
                
            # Input operations
            elif command == 'send_keys':
                keys = params.get('keys', '')
                return await loop.run_in_executor(None, self.vscode_controller.send_keys_to_vscode, keys)
                
            elif command == 'send_mouse_click':
                x = params.get('x', 0)
                y = params.get('y', 0)
                await loop.run_in_executor(None, pyautogui.click, x, y)
                return True
                
            # Screen operations
            elif command == 'take_screenshot':
                return await loop.run_in_executor(None, self._take_screenshot)
                
            elif command == 'get_screen_size':
                size = await loop.run_in_executor(None, pyautogui.size)
                return {'width': size[0], 'height': size[1]}
                
            # System operations
            elif command == 'get_processes':
                return await loop.run_in_executor(None, self._get_processes)
                
            elif command == 'get_system_info':
                return await loop.run_in_executor(None, self._get_system_info)
                
            # VSCode specific
            elif command == 'vscode_get_content':
                return await loop.run_in_executor(None, self.vscode_controller.get_window_content)
                
            elif command == 'vscode_send_command':
                vscode_cmd = params.get('command', '')
                return await loop.run_in_executor(None, self.vscode_controller.send_command, vscode_cmd)
                
            elif command == 'vscode_type_text':
                text = params.get('text', '')
                return await loop.run_in_executor(None, self.vscode_controller.type_text, text)
                
            # Background operations (no window activation)
            elif command == 'background_input':
                element_name = params.get('element_name', '')
                text = params.get('text', '')
                return await loop.run_in_executor(None, self._handle_background_input, element_name, text)
                    
            elif command == 'background_click':
                element_name = params.get('element_name', '')
                return await loop.run_in_executor(None, self._handle_background_click, element_name)
                    
            # Mouse drag operations
            elif command == 'mouse_drag':
                return await loop.run_in_executor(None, self._handle_mouse_drag, params)
                    
            # OCR operations
            elif command == 'ocr_screen':
                return await loop.run_in_executor(None, self._handle_ocr_screen, params)
                    
            elif command == 'ocr_window':
                return await loop.run_in_executor(None, self._handle_ocr_window, params)
                    
            # Win32 API operations
            elif command == 'win32_find_window':
                return await loop.run_in_executor(None, self._handle_win32_find_window, params)
                    
            elif command == 'win32_send_keys':
                return await loop.run_in_executor(None, self._handle_win32_send_keys, params)
            
            elif command == 'screenshot':
                return await loop.run_in_executor(None, self._handle_screenshot, params)
                    
            elif command == 'get_window_uia_structure':
                hwnd = params.get('hwnd')
                if hwnd:
                    return await loop.run_in_executor(None, self._get_window_uia_structure, hwnd)
                else:
                    raise ValueError("Missing hwnd parameter")
                
            # Hot reload commands
            elif command == 'hot_reload':
                return await self._handle_hot_reload_command(params)
                
            # Health monitoring commands
            elif command == 'health_status':
                return self._get_health_status()
                
            # Logging commands
            elif command == 'get_logs':
                return self._handle_get_logs(params)
                
            elif command == 'set_log_level':
                return self._handle_set_log_level(params)
                
            elif command == 'get_log_stats':
                return self._handle_get_log_stats()
                
            # System control commands
            elif command == 'restart_client':
                return await self._handle_restart_client(params)
                
            elif command == 'execute_program':
                return await self._handle_execute_program(params)
                
            else:
                raise ValueError(f"Unknown command: {command}")
                
        except Exception as e:
            raise
    
    def _get_windows(self):
        """Get list of all windows"""
        try:
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
            
            return format_success(
                data={'windows': windows, 'count': len(windows)},
                message=f"Found {len(windows)} windows"
            )
        except Exception as e:
            return format_error(e, error_code='ENUM_WINDOWS_FAILED')
    
    def _find_cursor_windows(self):
        """Find Cursor IDE windows specifically"""
        try:
            import psutil
            import win32process
            
            cursor_windows = []
            all_windows = []
            
            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        class_name = win32gui.GetClassName(hwnd)
                        
                        # Get process info
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            process_name = process.name()
                        except:
                            process_name = "Unknown"
                            pid = 0
                        
                        window_info = {
                            'hwnd': hwnd,
                            'title': title,
                            'class': class_name,
                            'process_name': process_name,
                            'pid': pid
                        }
                        
                        all_windows.append(window_info)
                        
                        # Check if this is a Cursor window
                        # Cursor uses Chrome_WidgetWin_1 class and "Cursor.exe" process
                        if (class_name == 'Chrome_WidgetWin_1' and 
                            'cursor' in process_name.lower()):
                            cursor_windows.append(window_info)
                            logger.info(f"Found Cursor window: {title} (process: {process_name})")
                        
                return True
                
            win32gui.EnumWindows(enum_handler, None)
            
            # If no Cursor windows found, show Chrome_WidgetWin_1 windows for debugging
            if not cursor_windows:
                chrome_windows = [w for w in all_windows if w['class'] == 'Chrome_WidgetWin_1']
                logger.info(f"No Cursor windows found. Chrome_WidgetWin_1 windows: {len(chrome_windows)}")
                for w in chrome_windows[:5]:
                    logger.info(f"  - {w['title']} (process: {w['process_name']})")
            
            return format_success(
                data={
                    'cursor_windows': cursor_windows, 
                    'count': len(cursor_windows),
                    'all_chrome_windows': [w for w in all_windows if w['class'] == 'Chrome_WidgetWin_1']
                },
                message=f"Found {len(cursor_windows)} Cursor windows"
            )
        except Exception as e:
            logger.error(f"Error finding Cursor windows: {e}")
            return format_error(str(e))
    
    def _take_screenshot(self):
        """Take screenshot and return as base64"""
        try:
            screenshot = ImageGrab.grab()
            
            # Convert to base64
            import io
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return format_success(
                data={
                    'image': img_base64,
                    'width': screenshot.width,
                    'height': screenshot.height,
                    'format': 'PNG',
                    'encoding': 'base64'
                },
                message="Screenshot captured successfully"
            )
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return format_error(e, error_code='SCREENSHOT_FAILED')
    
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
    
    def _handle_background_input(self, element_name: str, text: str):
        """Handle background input operation"""
        if self.vscode_controller.vscode_window:
            try:
                # Try to find element by name
                elements = self.vscode_controller.vscode_window.descendants()
                for elem in elements:
                    if elem.window_text() == element_name:
                        elem.set_text(text)
                        return True
                else:
                    # If not found by exact name, try type_text without activation
                    escaped_text = text.replace('{', '{{').replace('}', '}}')
                    send_keys(escaped_text)
                    return True
            except Exception as e:
                logger.error(f"Background input error: {e}")
                return False
        else:
            return False
    
    def _handle_background_click(self, element_name: str):
        """Handle background click operation"""
        if self.vscode_controller.vscode_window:
            try:
                elements = self.vscode_controller.vscode_window.descendants()
                for elem in elements:
                    if elem.window_text() == element_name:
                        elem.click_input()
                        return True
                return False
            except Exception as e:
                logger.error(f"Background click error: {e}")
                return False
        else:
            return False
    
    def _handle_mouse_drag(self, params: dict):
        """Handle mouse drag operation"""
        global Win32Backend
        
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
            return win32_backend.mouse_drag(
                start_x, start_y, end_x, end_y,
                duration=duration, button=button, humanize=humanize
            )
        except Exception as e:
            logger.error(f"Mouse drag error: {e}")
            return False
    
    def _handle_ocr_screen(self, params: dict):
        """Handle OCR screen operation"""
        global OCRBackend
        
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
            return {
                'success': True,
                'detections': detections,
                'available_engines': list(ocr_backend.available_engines.keys())
            }
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_ocr_window(self, params: dict):
        """Handle OCR window operation"""
        global Win32Backend, OCRBackend
        
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
                    if OCRBackend is None:
                        from utils.ocr_backend import OCRBackend
                    ocr_backend = OCRBackend()
                    detections = ocr_backend.detect_text(image, engine=engine)
                    
                    return {
                        'success': True,
                        'detections': detections
                    }
                else:
                    return {'success': False, 'error': 'Failed to capture window'}
            else:
                return {'success': False, 'error': 'No window handle provided'}
        except Exception as e:
            logger.error(f"Window OCR error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_win32_find_window(self, params: dict):
        """Handle Win32 find window operation"""
        global Win32Backend
        
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
                return {'success': True, 'hwnd': hwnd, 'info': info}
            else:
                return {'success': False, 'error': 'Window not found'}
        except Exception as e:
            logger.error(f"Find window error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_win32_send_keys(self, params: dict):
        """Handle Win32 send keys operation"""
        global Win32Backend
        
        keys = params.get('keys', '')
        delay = params.get('delay', 0.01)
        
        try:
            # Import on demand
            if Win32Backend is None:
                from utils.win32_backend import Win32Backend
            win32_backend = Win32Backend()
            success = win32_backend.send_keys(keys, delay)
            return {'success': success}
        except Exception as e:
            logger.error(f"Send keys error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_screenshot(self, params: dict):
        """Handle screenshot operation"""
        import os
        # Use the module-level datetime import instead of local import
        global datetime
        
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
            
            return {
                'success': True,
                'path': os.path.abspath(save_path),
                'size': os.path.getsize(save_path)
            }
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run(self):
        """Main client loop"""
        try:
            await self.connect()
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in client: {e}")
        finally:
            await self.shutdown()
    
    async def _start_hot_reload(self):
        """Start hot reload manager"""
        try:
            from utils.hot_reload_manager import HotReloadManager
            
            self.hot_reload = HotReloadManager()
            
            # Add reload callback
            async def on_reload(reload_type: str, data: Any):
                logger.info(f"Hot reload: {reload_type} - {data}")
                
                if reload_type == 'config':
                    # Update configuration values
                    self.heartbeat_interval = self.hot_reload.get_config('main', 'client.heartbeat_interval', self.heartbeat_interval)
                    self.reconnect_delay = self.hot_reload.get_config('main', 'client.reconnect_interval', self.reconnect_delay)
                    logger.info(f"Updated config: heartbeat={self.heartbeat_interval}s, reconnect={self.reconnect_delay}s")
            
            self.hot_reload.add_reload_callback(on_reload)
            await self.hot_reload.start()
            
            logger.info("Hot reload manager started")
            
        except Exception as e:
            logger.error(f"Failed to start hot reload: {e}")
            self.hot_reload = None
    
    async def _start_health_monitor(self):
        """Start health monitor"""
        try:
            from utils.health_monitor import HealthMonitor
            
            self.health_monitor = HealthMonitor()
            
            # Add health change callback
            def on_health_change(old_status: str, new_status: str, full_status: dict):
                logger.warning(f"Health status changed: {old_status} -> {new_status}")
                if new_status == 'critical':
                    logger.error(f"Critical health issues: {full_status}")
            
            self.health_monitor.add_health_callback(on_health_change)
            await self.health_monitor.start()
            
            logger.info("Health monitor started")
            
        except Exception as e:
            logger.error(f"Failed to start health monitor: {e}")
            self.health_monitor = None
    
    def _get_health_status(self) -> dict:
        """Get current health status"""
        if not self.health_monitor:
            return format_error('Health monitor not enabled', error_code='HEALTH_MONITOR_DISABLED')
        
        try:
            health_status = self.health_monitor.get_health_status()
            metrics = self.health_monitor.get_metrics_summary()
            
            return format_success(
                data={
                    'health': health_status,
                    'metrics': metrics
                },
                message=f"Health status: {health_status.get('overall', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return format_error(e, error_code='HEALTH_STATUS_ERROR')
    
    async def _handle_hot_reload_command(self, params: dict):
        """Handle hot reload commands from server"""
        action = params.get('action', 'status')
        
        if not self.hot_reload:
            return format_error('Hot reload not enabled', error_code='HOT_RELOAD_DISABLED')
        
        try:
            if action == 'status':
                stats = self.hot_reload.get_stats()
                return format_success(
                    data={'stats': stats},
                    message="Hot reload status retrieved"
                )
                
            elif action == 'reload_module':
                module_name = params.get('module_name')
                if module_name:
                    success = self.hot_reload.reload_module(module_name)
                    if success:
                        return format_success(
                            data={'module': module_name},
                            message=f"Module '{module_name}' reloaded successfully"
                        )
                    else:
                        return format_error(
                            f"Failed to reload module '{module_name}'",
                            error_code='MODULE_RELOAD_FAILED'
                        )
                else:
                    return format_error('Module name not provided', error_code='MISSING_PARAMETER')
                    
            elif action == 'reload_config':
                config_name = params.get('config_name')
                reloaded = self.hot_reload.reload_config(config_name)
                if reloaded:
                    return format_success(
                        data={'reloaded': reloaded},
                        message=f"Reloaded {len(reloaded)} config files"
                    )
                else:
                    return format_error('No configs reloaded', error_code='NO_CONFIGS_RELOADED')
                
            else:
                return format_error(f'Unknown action: {action}', error_code='UNKNOWN_ACTION')
                
        except Exception as e:
            logger.error(f"Hot reload command error: {e}")
            return format_error(e, error_code='HOT_RELOAD_ERROR')
    
    def _handle_get_logs(self, params: dict) -> dict:
        """Handle get logs command"""
        try:
            count = params.get('count', 100)
            level = params.get('level', None)
            search = params.get('search', None)
            
            if search:
                logs = log_manager.search_logs(search, max_results=count)
                message = f"Found {len(logs)} logs matching '{search}'"
            else:
                logs = log_manager.get_recent_logs(count=count, level=level)
                message = f"Retrieved {len(logs)} recent logs"
                if level:
                    message += f" at {level} level"
            
            return format_success(
                data={
                    'logs': logs,
                    'count': len(logs),
                    'filter': {'count': count, 'level': level, 'search': search}
                },
                message=message
            )
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return format_error(e, error_code='GET_LOGS_ERROR')
    
    def _handle_set_log_level(self, params: dict) -> dict:
        """Handle set log level command"""
        try:
            logger_name = params.get('logger_name', None)
            level = params.get('level', 'INFO')
            
            log_manager.set_log_level(logger_name, level)
            
            return format_success(
                data={
                    'logger': logger_name or 'root',
                    'level': level
                },
                message=f"Log level set to {level} for {logger_name or 'root'}"
            )
        except Exception as e:
            logger.error(f"Error setting log level: {e}")
            return format_error(e, error_code='SET_LOG_LEVEL_ERROR')
    
    def _handle_get_log_stats(self) -> dict:
        """Handle get log stats command"""
        try:
            stats = log_manager.get_log_stats()
            return format_success(
                data={'stats': stats},
                message=f"Log statistics: {stats.get('total_entries', 0)} total entries"
            )
        except Exception as e:
            logger.error(f"Error getting log stats: {e}")
            return format_error(e, error_code='GET_LOG_STATS_ERROR')
    
    async def _handle_restart_client(self, params: dict) -> dict:
        """Handle client restart request"""
        try:
            delay = params.get('delay', 3)  # Delay before restart (seconds)
            use_watchdog = params.get('use_watchdog', True)  # Use watchdog for restart
            reason = params.get('reason', 'Remote restart requested')
            
            logger.warning(f"Client restart requested: {reason}")
            
            # Schedule restart
            async def delayed_restart():
                await asyncio.sleep(delay)
                logger.info("Initiating client restart...")
                
                if use_watchdog:
                    # Use watchdog for clean restart
                    import sys
                    import subprocess
                    
                    # Start watchdog if not already running
                    watchdog_path = os.path.join(os.path.dirname(__file__), 'client_watchdog.py')
                    if os.path.exists(watchdog_path):
                        # Start watchdog with current client path
                        subprocess.Popen([
                            sys.executable,
                            watchdog_path,
                            '--client-path', __file__
                        ])
                        logger.info("Watchdog started, exiting client...")
                    else:
                        logger.warning("Watchdog not found, performing direct restart")
                        # Direct restart
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    # Direct restart without watchdog
                    import sys
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                
                # Exit current process
                sys.exit(0)
            
            # Start restart task
            asyncio.create_task(delayed_restart())
            
            return format_success(
                data={
                    'delay': delay,
                    'use_watchdog': use_watchdog,
                    'reason': reason
                },
                message=f"Client will restart in {delay} seconds"
            )
            
        except Exception as e:
            logger.error(f"Error handling restart: {e}")
            return format_error(e, error_code='RESTART_ERROR')
    
    async def _handle_execute_program(self, params: dict):
        """Execute a program or command"""
        try:
            program = params.get('program')
            args = params.get('args', [])
            wait = params.get('wait', False)
            shell = params.get('shell', False)
            
            if not program:
                return format_error("No program specified", error_code='INVALID_PARAMS')
            
            logger.info(f"Executing program: {program} {' '.join(args) if isinstance(args, list) else args}")
            
            # Build command
            if isinstance(args, list):
                cmd = [program] + args
            else:
                cmd = f"{program} {args}" if args else program
            
            if wait:
                # Execute and wait for completion
                result = subprocess.run(
                    cmd,
                    shell=shell,
                    capture_output=True,
                    text=True
                )
                
                return format_success(
                    data={
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'executed': program
                    },
                    message=f"Program executed with return code {result.returncode}"
                )
            else:
                # Execute without waiting
                process = subprocess.Popen(
                    cmd,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return format_success(
                    data={
                        'pid': process.pid,
                        'executed': program
                    },
                    message=f"Program launched with PID {process.pid}"
                )
                
        except Exception as e:
            logger.error(f"Error executing program: {e}")
            return format_error(str(e), error_code='EXECUTION_FAILED')
    
    async def shutdown(self):
        """Gracefully shutdown the client"""
        logger.info("Shutting down client...")
        self.running = False
        
        # Stop hot reload
        if self.hot_reload:
            try:
                await self.hot_reload.stop()
                logger.info("Hot reload manager stopped")
            except Exception as e:
                logger.error(f"Error stopping hot reload: {e}")
        
        # Stop health monitor
        if self.health_monitor:
            try:
                await self.health_monitor.stop()
                logger.info("Health monitor stopped")
            except Exception as e:
                logger.error(f"Error stopping health monitor: {e}")
        
        # Close WebSocket connection
        if self.ws and not self.ws.closed:
            try:
                await self.ws.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        # Cleanup resources
        logger.info("Client shutdown complete")

if __name__ == "__main__":
    # Configure pyautogui
    pyautogui.FAILSAFE = False  # Allow control even at screen edges
    pyautogui.PAUSE = 0.1  # Small delay between actions
    
    client = CyberCorpClient()
    asyncio.run(client.run())