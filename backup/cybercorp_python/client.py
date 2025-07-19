import asyncio
import websockets
import json
import logging
import psutil
import subprocess
from datetime import datetime
from typing import Dict, Any

# Windows UI Automation imports
try:
    import pywinauto
    from pywinauto import Desktop
    import win32gui
    import win32process
    WINAUTO_AVAILABLE = True
except ImportError:
    WINAUTO_AVAILABLE = False
    logging.warning("pywinauto not available. UIA features will be limited.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CyberCorpClient:
    def __init__(self, server_url='ws://localhost:8080'):
        self.server_url = server_url
        self.client_id = None
        self.ws = None
        self.reconnect_interval = 5
        self.heartbeat_interval = 30
        
    async def connect(self):
        while True:
            try:
                logging.info(f"Connecting to {self.server_url}...")
                # Use legacy_recv for compatibility
                self.ws = await websockets.connect(
                    self.server_url,
                    compression=None  # Disable compression for compatibility
                )
                logging.info("Connected to server")
                
                # Start heartbeat
                heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                
                try:
                    async for message in self.ws:
                        await self.handle_message(message)
                except websockets.exceptions.ConnectionClosed:
                    logging.info("Connection closed")
                    
                heartbeat_task.cancel()
                
            except Exception as e:
                logging.error(f"Connection error: {e}")
                
            logging.info(f"Reconnecting in {self.reconnect_interval} seconds...")
            await asyncio.sleep(self.reconnect_interval)
            
    async def handle_message(self, message: str):
        try:
            data = json.loads(message)
            logging.info(f"Received: {data['type']}")
            
            if data['type'] == 'welcome':
                self.client_id = data['client_id']
                logging.info(f"Assigned client ID: {self.client_id}")
                
            elif data['type'] == 'command':
                await self.handle_command(data['command'], data.get('data', {}))
                
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON: {e}")
            
    async def handle_command(self, command: str, data: Dict[str, Any]):
        logging.info(f"Executing command: {command}")
        
        if command == 'get_uia_structure':
            await self.get_uia_structure()
        elif command == 'get_processes':
            await self.get_processes()
        else:
            logging.warning(f"Unknown command: {command}")
            
    async def get_uia_structure(self):
        structure_data = {}
        
        try:
            if WINAUTO_AVAILABLE:
                desktop = Desktop(backend="uia")
                all_windows = []
                
                # Find ALL windows (not just active)
                for window in desktop.windows():
                    try:
                        title = window.window_text()
                        class_name = window.class_name()
                        
                        # Check if it's VSCode or contains Roo Code dialog
                        if ('Visual Studio Code' in title or 'VSCode' in title or 
                            class_name == 'Chrome_WidgetWin_1'):
                            
                            logging.info(f"Found window: {title}")
                            
                            # Deep scan for Roo Code content
                            window_info = {
                                'title': title,
                                'class_name': class_name,
                                'is_visible': window.is_visible(),
                                'rectangle': str(window.rectangle()),
                                'roo_code_content': []
                            }
                            
                            # Extract Roo Code dialog content
                            roo_content = self._extract_roo_code_content(window)
                            if roo_content:
                                window_info['roo_code_content'] = roo_content
                            
                            all_windows.append(window_info)
                    except Exception as e:
                        logging.debug(f"Error processing window: {e}")
                        
                structure_data['windows'] = all_windows
                structure_data['total_windows'] = len(all_windows)
                
            else:
                structure_data['error'] = 'pywinauto not available'
                
        except Exception as e:
            structure_data['error'] = str(e)
            logging.error(f"Error getting UIA structure: {e}")
            
        await self.send_response('uia_structure', {
            'structure': json.dumps(structure_data, indent=2),
            'timestamp': datetime.now().isoformat()
        })
    
    def _extract_roo_code_content(self, window, depth=0, max_depth=15):
        """Extract Roo Code dialog content from window"""
        if depth > max_depth:
            return []
            
        contents = []
        
        try:
            # Check all controls
            for control in window.children():
                try:
                    control_type = control.element_info.control_type
                    control_name = control.element_info.name or ''
                    
                    # Look for Roo Code related content
                    if 'Roo Code' in control_name or 'Task:' in control_name:
                        # Found relevant section, extract all text
                        texts = self._get_all_texts(control)
                        if texts:
                            contents.append({
                                'type': control_type,
                                'content': texts
                            })
                    
                    # Recursively check children
                    child_content = self._extract_roo_code_content(control, depth + 1, max_depth)
                    if child_content:
                        contents.extend(child_content)
                        
                except:
                    pass
                    
        except:
            pass
            
        return contents
    
    def _get_all_texts(self, control):
        """Get all text content from a control and its children"""
        texts = []
        
        try:
            # Get control's own text
            control_texts = control.texts()
            for text in control_texts:
                if text and len(text) > 5 and not text.startswith('\ue'):
                    texts.append(text)
            
            # Get children's text
            for child in control.children():
                child_texts = self._get_all_texts(child)
                texts.extend(child_texts)
                
        except:
            pass
            
        return texts
        
    async def get_processes(self):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'id': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'] or 0,
                        'memory': round(pinfo['memory_info'].rss / 1024 / 1024) if pinfo['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            # Sort by memory usage and get top 20
            processes.sort(key=lambda x: x['memory'], reverse=True)
            top_processes = processes[:20]
            
            await self.send_response('processes', {
                'processes': top_processes,
                'total': len(processes),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logging.error(f"Error getting processes: {e}")
            await self.send_response('processes', {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
    async def send_response(self, response_type: str, data: Dict[str, Any]):
        if self.ws:
            message = {
                'type': 'response',
                'response_type': response_type,
                'data': data,
                'client_id': self.client_id
            }
            try:
                await self.ws.send(json.dumps(message))
                logging.info(f"Sent {response_type} response")
            except Exception as e:
                logging.error(f"Failed to send response: {e}")
                
    async def heartbeat_loop(self):
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self.ws:
                    await self.ws.send(json.dumps({'type': 'heartbeat'}))
            except:
                break

if __name__ == "__main__":
    client = CyberCorpClient()
    
    try:
        asyncio.run(client.connect())
    except KeyboardInterrupt:
        logging.info("Client stopped")