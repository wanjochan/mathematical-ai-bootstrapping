"""
Cursor IDE Controller - Specialized controller for Cursor IDE
"""

import logging
import time
import win32gui
import win32process
import win32con
import psutil
from pywinauto import Desktop, Application
from pywinauto.keyboard import send_keys
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CursorController:
    """Controls Cursor IDE window interactions"""
    
    def __init__(self):
        self.cursor_window = None
        self.app = None
        self.hwnd = None
        
    def find_cursor_window(self) -> bool:
        """Find Cursor IDE window in current session"""
        try:
            desktop = Desktop(backend="uia")
            
            for window in desktop.windows():
                try:
                    title = window.window_text()
                    class_name = window.class_name()
                    
                    # Cursor uses Chrome_WidgetWin_1 like VSCode but has "Cursor" in title
                    if class_name == 'Chrome_WidgetWin_1':
                        # Check if it's Cursor by title
                        if 'cursor' in title.lower():
                            # Verify by process name
                            hwnd = window.handle
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            
                            # Cursor process name is usually "Cursor.exe"
                            if 'cursor' in process.name().lower():
                                self.cursor_window = window
                                self.app = Application(backend="uia").connect(handle=hwnd)
                                self.hwnd = hwnd
                                logger.info(f"Found Cursor IDE: {title}")
                                return True
                            
                except Exception as e:
                    logger.debug(f"Error checking window: {e}")
                    
            logger.warning("Cursor IDE window not found")
            return False
            
        except Exception as e:
            logger.error(f"Error finding Cursor: {e}")
            return False
    
    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """Get Cursor window information"""
        if not self.cursor_window:
            if not self.find_cursor_window():
                return None
                
        try:
            info = {
                'title': self.cursor_window.window_text(),
                'class': self.cursor_window.class_name(),
                'hwnd': self.hwnd,
                'is_active': self.cursor_window.has_keyboard_focus(),
                'rectangle': str(self.cursor_window.rectangle()),
                'process_name': None
            }
            
            # Get process info
            try:
                _, pid = win32process.GetWindowThreadProcessId(self.hwnd)
                process = psutil.Process(pid)
                info['process_name'] = process.name()
                info['process_id'] = pid
            except:
                pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return None
    
    def activate_window(self) -> bool:
        """Bring Cursor window to foreground with improved reliability"""
        if not self.cursor_window:
            if not self.find_cursor_window():
                return False
                
        try:
            # Use Win32 API for reliable activation
            hwnd = self.hwnd
            
            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
            
            # Set foreground window
            win32gui.SetForegroundWindow(hwnd)
            
            # Use pywinauto's set_focus as backup
            self.cursor_window.set_focus()
            
            # Alt key trick for foreground window restrictions
            import ctypes
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt down
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt up
            
            # Try SetForegroundWindow again
            win32gui.SetForegroundWindow(hwnd)
            
            # Wait for activation
            time.sleep(0.2)
            
            # Verify activation
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd == hwnd:
                logger.info("Cursor window activated successfully")
                return True
            else:
                logger.warning(f"Cursor activation may have failed. Expected {hwnd}, got {foreground_hwnd}")
                win32gui.BringWindowToTop(hwnd)
                time.sleep(0.1)
                return True
                
        except Exception as e:
            logger.error(f"Error activating Cursor window: {e}")
            return False
    
    def send_keys_to_cursor(self, keys: str) -> bool:
        """Send keystrokes to Cursor IDE"""
        if not self.activate_window():
            return False
            
        try:
            # Additional delay for window readiness
            time.sleep(0.3)
            
            # Verify window still has focus
            if win32gui.GetForegroundWindow() != self.hwnd:
                logger.warning("Cursor window lost focus, reactivating...")
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.2)
            
            # Clear pending input with ESC
            import ctypes
            ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)  # ESC down
            ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)  # ESC up
            time.sleep(0.05)
            
            # Send keys
            send_keys(keys, pause=0.01, with_spaces=True)
            time.sleep(0.05)
            
            return True
        except Exception as e:
            logger.error(f"Error sending keys to Cursor: {e}")
            return False
    
    def type_text(self, text: str) -> bool:
        """Type text in Cursor IDE with proper escaping"""
        # Escape special characters for pywinauto
        escaped_text = text
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
        
        return self.send_keys_to_cursor(escaped_text)
    
    def open_command_palette(self) -> bool:
        """Open Cursor command palette (Ctrl+Shift+P)"""
        if not self.activate_window():
            return False
            
        try:
            # Ensure window has focus
            if win32gui.GetForegroundWindow() != self.hwnd:
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.2)
            
            # Use explicit key codes for Ctrl+Shift+P
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
            
            # Wait for command palette
            time.sleep(0.7)
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening command palette: {e}")
            return False
    
    def execute_command(self, command: str) -> bool:
        """Execute a command via Cursor's command palette"""
        if not self.open_command_palette():
            return False
            
        try:
            # Clear any existing text
            send_keys('^a')
            time.sleep(0.05)
            
            # Type command
            self.type_text(command)
            time.sleep(0.2)
            
            # Execute with Enter
            import ctypes
            user32 = ctypes.windll.user32
            user32.keybd_event(0x0D, 0, 0, 0)  # Enter down
            user32.keybd_event(0x0D, 0, 2, 0)  # Enter up
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False
    
    def open_ai_chat(self) -> bool:
        """Open Cursor's AI chat panel (Ctrl+K)"""
        if not self.activate_window():
            return False
            
        try:
            import ctypes
            user32 = ctypes.windll.user32
            
            # Press Ctrl+K (Cursor's AI chat shortcut)
            user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            user32.keybd_event(0x4B, 0, 0, 0)  # K down
            time.sleep(0.05)
            user32.keybd_event(0x4B, 0, 2, 0)  # K up
            user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            
            # Wait for AI panel
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening AI chat: {e}")
            return False
    
    def send_ai_prompt(self, prompt: str) -> bool:
        """Send a prompt to Cursor's AI chat"""
        if not self.open_ai_chat():
            return False
            
        try:
            # Type the prompt
            self.type_text(prompt)
            time.sleep(0.1)
            
            # Send with Enter
            import ctypes
            user32 = ctypes.windll.user32
            user32.keybd_event(0x0D, 0, 0, 0)  # Enter down
            user32.keybd_event(0x0D, 0, 2, 0)  # Enter up
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending AI prompt: {e}")
            return False