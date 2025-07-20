"""Optimized CyberCorp client with async command queue"""

import asyncio
import websockets
import json
import logging
import os
import socket
import platform
from datetime import datetime
from typing import Dict, Any, Optional, List
import concurrent.futures
import pyautogui
import pygetwindow as gw
import pyperclip
from collections import deque
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global backends (lazy loading)
Win32Backend = None
OCRBackend = None


class CommandQueue:
    """Priority command queue with async execution"""
    
    def __init__(self, max_workers: int = 3):
        self.queue = asyncio.PriorityQueue()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        self.results = {}
        
    async def add_command(self, command_id: str, command: str, params: dict, priority: int = 5):
        """Add command to queue (lower priority = higher precedence)"""
        await self.queue.put((priority, time.time(), command_id, command, params))
        
    async def process_commands(self, client):
        """Process commands from queue"""
        while self.running:
            try:
                priority, timestamp, cmd_id, command, params = await asyncio.wait_for(
                    self.queue.get(), timeout=0.1
                )
                
                # Execute command
                start_time = time.time()
                result = await client._execute_command_async(command, params)
                duration = time.time() - start_time
                
                # Store result
                self.results[cmd_id] = {
                    'result': result,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Command {command} executed in {duration:.2f}s")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
    def get_result(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get command result"""
        return self.results.pop(command_id, None)
        
    async def shutdown(self):
        """Shutdown queue"""
        self.running = False
        self.executor.shutdown(wait=True)


class OptimizedCyberCorpClient:
    """Optimized client with async operations"""
    
    def __init__(self):
        self.ws = None
        self.running = True
        self.user_session = self._get_user_session()
        self.client_id = None
        self.command_queue = CommandQueue()
        self.window_cache = {}
        self.cache_ttl = 60  # seconds
        
    def _get_user_session(self) -> str:
        """Get user session identifier"""
        return os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
        
    async def connect(self):
        """Connect to server and start processing"""
        server_url = "ws://localhost:9998"
        
        while self.running:
            try:
                logger.info(f"Connecting to {server_url}...")
                self.ws = await websockets.connect(server_url)
                
                # Register client
                await self._register()
                
                # Start command processor
                processor_task = asyncio.create_task(
                    self.command_queue.process_commands(self)
                )
                
                # Start message handler
                await self._handle_messages()
                
                # Cleanup
                processor_task.cancel()
                
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)
                
    async def _register(self):
        """Register with server"""
        register_data = {
            'type': 'register',
            'user_session': self.user_session,
            'system_info': {
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'version': platform.version()
            },
            'client_start_time': datetime.now().isoformat(),
            'capabilities': {
                'screenshot': True,
                'ocr': True,
                'win32': True,
                'uia': True,
                'async_commands': True
            }
        }
        
        await self.ws.send(json.dumps(register_data))
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get('type') == 'welcome':
            self.client_id = data.get('client_id')
            logger.info(f"Registered as {self.client_id}")
            
    async def _handle_messages(self):
        """Handle incoming messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')
                    
                    if msg_type == 'command':
                        # Add to queue with priority
                        command_id = data.get('command_id')
                        command = data.get('command')
                        params = data.get('params', {})
                        priority = data.get('priority', 5)
                        
                        await self.command_queue.add_command(
                            command_id, command, params, priority
                        )
                        
                        # Send immediate acknowledgment
                        await self.ws.send(json.dumps({
                            'type': 'command_ack',
                            'command_id': command_id,
                            'status': 'queued'
                        }))
                        
                        # Wait for result
                        asyncio.create_task(self._wait_and_send_result(command_id))
                        
                    elif msg_type == 'ping':
                        await self.ws.send(json.dumps({'type': 'pong'}))
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            
    async def _wait_and_send_result(self, command_id: str):
        """Wait for command result and send back"""
        max_wait = 30  # seconds
        check_interval = 0.1
        waited = 0
        
        while waited < max_wait:
            result_data = self.command_queue.get_result(command_id)
            if result_data:
                # Send result
                await self.ws.send(json.dumps({
                    'type': 'command_result',
                    'command_id': command_id,
                    'result': result_data['result'],
                    'duration': result_data['duration'],
                    'timestamp': result_data['timestamp']
                }))
                return
                
            await asyncio.sleep(check_interval)
            waited += check_interval
            
        # Timeout
        await self.ws.send(json.dumps({
            'type': 'command_error',
            'command_id': command_id,
            'error': 'Command timeout'
        }))
        
    async def _execute_command_async(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command asynchronously"""
        # Check if command can use cache
        if command == 'get_windows':
            cached = self._get_cached_windows()
            if cached:
                return cached
                
        # Execute in thread pool for blocking operations
        loop = asyncio.get_event_loop()
        
        if command in ['screenshot', 'ocr_screen', 'ocr_window', 'mouse_drag']:
            # CPU-intensive operations
            return await loop.run_in_executor(
                self.command_queue.executor,
                self._execute_blocking_command,
                command,
                params
            )
        else:
            # Regular commands
            return self._execute_command_sync(command, params)
            
    def _execute_blocking_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute blocking commands in thread"""
        try:
            if command == 'screenshot':
                return self._take_screenshot(params)
            elif command == 'ocr_screen':
                return self._ocr_screen(params)
            elif command == 'ocr_window':
                return self._ocr_window(params)
            elif command == 'mouse_drag':
                return self._mouse_drag(params)
            else:
                return {'success': False, 'error': 'Unknown blocking command'}
        except Exception as e:
            logger.error(f"Error in blocking command {command}: {e}")
            return {'success': False, 'error': str(e)}
            
    def _execute_command_sync(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute synchronous commands"""
        try:
            if command == 'get_windows':
                return self._get_windows()
            elif command == 'activate_window':
                return self._activate_window(params)
            elif command == 'send_mouse_click':
                return self._send_mouse_click(params)
            elif command == 'send_keys':
                return self._send_keys(params)
            elif command == 'get_window_uia_structure':
                return self._get_window_uia_structure(params.get('hwnd'))
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
        except Exception as e:
            logger.error(f"Error in command {command}: {e}")
            return {'success': False, 'error': str(e)}
            
    def _get_cached_windows(self) -> Optional[List[Dict[str, Any]]]:
        """Get windows from cache if fresh"""
        if 'windows' in self.window_cache:
            cache_time = self.window_cache['windows']['time']
            if time.time() - cache_time < self.cache_ttl:
                return self.window_cache['windows']['data']
        return None
        
    def _get_windows(self) -> List[Dict[str, Any]]:
        """Get all windows"""
        windows = []
        for window in gw.getAllWindows():
            if window.title:
                windows.append({
                    'title': window.title,
                    'hwnd': window._hWnd,
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height,
                    'is_active': window.isActive
                })
                
        # Update cache
        self.window_cache['windows'] = {
            'data': windows,
            'time': time.time()
        }
        
        return windows
        
    def _activate_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Activate window by hwnd"""
        hwnd = params.get('hwnd')
        if not hwnd:
            return {'success': False, 'error': 'Missing hwnd parameter'}
            
        try:
            import win32gui
            import win32con
            
            # Show and activate window
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _send_mouse_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send mouse click"""
        x = params.get('x')
        y = params.get('y')
        button = params.get('button', 'left')
        
        if x is None or y is None:
            return {'success': False, 'error': 'Missing x or y parameter'}
            
        try:
            pyautogui.click(x, y, button=button)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _send_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send keyboard input"""
        keys = params.get('keys', '')
        delay = params.get('delay', 0.01)
        
        try:
            # Handle special keys
            if '{' in keys:
                pyautogui.hotkey(*keys.strip('{}').split('+'))
            else:
                pyautogui.write(keys, interval=delay)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot (implemented in thread)"""
        # Implementation from original client.py
        import os
        from datetime import datetime
        
        window_hwnd = params.get('hwnd')
        save_path = params.get('save_path')
        
        try:
            if not save_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = os.path.join(os.path.dirname(__file__), f'screenshot_{timestamp}.png')
            
            if window_hwnd:
                # Window screenshot
                import win32gui
                import win32ui
                import win32con
                from PIL import Image
                
                left, top, right, bottom = win32gui.GetWindowRect(window_hwnd)
                width = right - left
                height = bottom - top
                
                hwndDC = win32gui.GetWindowDC(window_hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()
                
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                saveDC.SelectObject(saveBitMap)
                
                saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
                
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                img.save(save_path)
                
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(window_hwnd, hwndDC)
            else:
                # Full screen
                screenshot = pyautogui.screenshot()
                screenshot.save(save_path)
            
            return {
                'success': True,
                'path': os.path.abspath(save_path),
                'size': os.path.getsize(save_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _get_window_uia_structure(self, hwnd: int) -> Dict[str, Any]:
        """Get UIA structure (simplified for performance)"""
        if not hwnd:
            return {"error": "Missing hwnd parameter"}
            
        try:
            from pywinauto import Application
            
            app = Application(backend="uia").connect(handle=hwnd)
            window = app.window(handle=hwnd)
            
            # Only get top-level structure for performance
            structure = {
                "ControlType": window.element_info.control_type,
                "Name": window.element_info.name,
                "AutomationId": window.element_info.automation_id,
                "ClassName": window.element_info.class_name,
                "Rectangle": str(window.element_info.rectangle),
                "Children": {}
            }
            
            # Get only direct children
            for i, child in enumerate(window.children()[:10]):  # Limit to 10
                try:
                    child_info = {
                        "ControlType": child.element_info.control_type,
                        "Name": child.element_info.name[:50],  # Truncate long names
                        "AutomationId": child.element_info.automation_id
                    }
                    structure["Children"][f"child_{i}"] = child_info
                except:
                    pass
                    
            return structure
            
        except Exception as e:
            return {"error": str(e)}
            
    def _ocr_screen(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """OCR screen region"""
        # TODO: Implement OCR
        return {'success': False, 'error': 'OCR not implemented yet'}
        
    def _ocr_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """OCR window"""
        # TODO: Implement OCR
        return {'success': False, 'error': 'OCR not implemented yet'}
        
    def _mouse_drag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mouse drag operation"""
        start_x = params.get('start_x')
        start_y = params.get('start_y')
        end_x = params.get('end_x')
        end_y = params.get('end_y')
        duration = params.get('duration', 1.0)
        
        if None in [start_x, start_y, end_x, end_y]:
            return {'success': False, 'error': 'Missing coordinates'}
            
        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=duration)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    async def run(self):
        """Main client loop"""
        try:
            await self.connect()
        except KeyboardInterrupt:
            logger.info("Client stopped by user")
        finally:
            self.running = False
            await self.command_queue.shutdown()
            if self.ws:
                await self.ws.close()


if __name__ == "__main__":
    # Configure pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
    
    client = OptimizedCyberCorpClient()
    asyncio.run(client.run())