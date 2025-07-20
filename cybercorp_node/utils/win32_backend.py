"""Windows API backend for enhanced system control"""

import ctypes
import ctypes.wintypes
import win32api
import win32con
import win32gui
import win32process
import win32clipboard
import pywintypes
from typing import Optional, List, Tuple, Dict, Any
import time
import random


class Win32Backend:
    """Windows API backend for system-level operations"""
    
    def __init__(self):
        """Initialize Win32 backend"""
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.gdi32 = ctypes.windll.gdi32
        
    # Window Management Functions
    
    def find_window(self, class_name: Optional[str] = None, 
                   window_name: Optional[str] = None) -> Optional[int]:
        """Find window by class name or window title
        
        Args:
            class_name: Window class name
            window_name: Window title
            
        Returns:
            Window handle (HWND) or None
        """
        try:
            hwnd = win32gui.FindWindow(class_name, window_name)
            return hwnd if hwnd else None
        except Exception:
            return None
            
    def find_windows_by_title(self, title_pattern: str) -> List[int]:
        """Find all windows matching title pattern
        
        Args:
            title_pattern: Pattern to match in window title
            
        Returns:
            List of window handles
        """
        windows = []
        
        def enum_callback(hwnd, pattern):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if pattern.lower() in window_text.lower():
                        windows.append(hwnd)
            except Exception:
                pass
            return True
            
        win32gui.EnumWindows(enum_callback, title_pattern)
        return windows
        
    def get_window_info(self, hwnd: int) -> Dict[str, Any]:
        """Get comprehensive window information
        
        Args:
            hwnd: Window handle
            
        Returns:
            Dictionary with window information
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Get process info
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            return {
                'hwnd': hwnd,
                'title': title,
                'class_name': class_name,
                'rect': rect,
                'client_rect': client_rect,
                'width': rect[2] - rect[0],
                'height': rect[3] - rect[1],
                'process_id': process_id,
                'thread_id': thread_id,
                'is_visible': win32gui.IsWindowVisible(hwnd),
                'is_enabled': win32gui.IsWindowEnabled(hwnd),
                'is_minimized': win32gui.IsIconic(hwnd)
            }
        except Exception as e:
            return {'error': str(e)}
            
    def set_window_position(self, hwnd: int, x: int, y: int, 
                          width: int, height: int) -> bool:
        """Set window position and size
        
        Args:
            hwnd: Window handle
            x, y: Top-left position
            width, height: Window size
            
        Returns:
            Success status
        """
        try:
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return True
        except Exception:
            return False
            
    def bring_window_to_front(self, hwnd: int) -> bool:
        """Bring window to foreground
        
        Args:
            hwnd: Window handle
            
        Returns:
            Success status
        """
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
            # Bring to front
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            # Alternative method using hotkey trick
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shell.SendKeys('%')
                win32gui.SetForegroundWindow(hwnd)
                return True
            except:
                return False
                
    # Mouse Control Functions
    
    def get_cursor_pos(self) -> Tuple[int, int]:
        """Get current cursor position
        
        Returns:
            (x, y) tuple
        """
        return win32gui.GetCursorPos()
        
    def set_cursor_pos(self, x: int, y: int) -> bool:
        """Set cursor position
        
        Args:
            x, y: Screen coordinates
            
        Returns:
            Success status
        """
        try:
            win32api.SetCursorPos((x, y))
            return True
        except Exception:
            return False
            
    def mouse_click(self, x: int, y: int, button: str = 'left',
                   clicks: int = 1, interval: float = 0.0) -> bool:
        """Perform mouse click
        
        Args:
            x, y: Click position
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks
            interval: Interval between clicks
            
        Returns:
            Success status
        """
        try:
            # Move cursor
            self.set_cursor_pos(x, y)
            time.sleep(0.01)
            
            # Determine button flags
            if button == 'left':
                down_flag = win32con.MOUSEEVENTF_LEFTDOWN
                up_flag = win32con.MOUSEEVENTF_LEFTUP
            elif button == 'right':
                down_flag = win32con.MOUSEEVENTF_RIGHTDOWN
                up_flag = win32con.MOUSEEVENTF_RIGHTUP
            elif button == 'middle':
                down_flag = win32con.MOUSEEVENTF_MIDDLEDOWN
                up_flag = win32con.MOUSEEVENTF_MIDDLEUP
            else:
                return False
                
            # Perform clicks
            for _ in range(clicks):
                win32api.mouse_event(down_flag, x, y, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(up_flag, x, y, 0, 0)
                
                if interval > 0 and _ < clicks - 1:
                    time.sleep(interval)
                    
            return True
        except Exception:
            return False
            
    def mouse_drag(self, start_x: int, start_y: int, 
                  end_x: int, end_y: int, duration: float = 1.0,
                  button: str = 'left', humanize: bool = True) -> bool:
        """Perform mouse drag operation
        
        Args:
            start_x, start_y: Start position
            end_x, end_y: End position
            duration: Duration of drag in seconds
            button: Mouse button to use
            humanize: Add human-like movement
            
        Returns:
            Success status
        """
        try:
            # Determine button flags
            if button == 'left':
                down_flag = win32con.MOUSEEVENTF_LEFTDOWN
                up_flag = win32con.MOUSEEVENTF_LEFTUP
            elif button == 'right':
                down_flag = win32con.MOUSEEVENTF_RIGHTDOWN
                up_flag = win32con.MOUSEEVENTF_RIGHTUP
            else:
                return False
                
            # Move to start position
            self.set_cursor_pos(start_x, start_y)
            time.sleep(0.1)
            
            # Press button
            win32api.mouse_event(down_flag, start_x, start_y, 0, 0)
            time.sleep(0.05)
            
            if humanize:
                # Generate bezier curve path
                points = self._generate_bezier_curve(
                    (start_x, start_y), (end_x, end_y), duration
                )
                
                # Move along path
                for x, y in points:
                    self.set_cursor_pos(int(x), int(y))
                    time.sleep(duration / len(points))
            else:
                # Direct movement
                steps = max(int(duration * 60), 10)  # 60 FPS
                for i in range(steps + 1):
                    progress = i / steps
                    x = int(start_x + (end_x - start_x) * progress)
                    y = int(start_y + (end_y - start_y) * progress)
                    self.set_cursor_pos(x, y)
                    time.sleep(duration / steps)
                    
            # Release button
            win32api.mouse_event(up_flag, end_x, end_y, 0, 0)
            return True
            
        except Exception:
            return False
            
    def _generate_bezier_curve(self, start: Tuple[int, int], 
                              end: Tuple[int, int], 
                              duration: float) -> List[Tuple[float, float]]:
        """Generate bezier curve points for humanized movement
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            duration: Duration for movement
            
        Returns:
            List of points along curve
        """
        # Generate control points with some randomness
        mid_x = (start[0] + end[0]) / 2 + random.randint(-50, 50)
        mid_y = (start[1] + end[1]) / 2 + random.randint(-50, 50)
        
        # Number of points based on duration
        num_points = max(int(duration * 60), 20)
        
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            # Quadratic bezier curve
            x = (1-t)**2 * start[0] + 2*(1-t)*t * mid_x + t**2 * end[0]
            y = (1-t)**2 * start[1] + 2*(1-t)*t * mid_y + t**2 * end[1]
            
            # Add small random jitter
            if 0.1 < t < 0.9:  # Not at start or end
                x += random.randint(-2, 3)
                y += random.randint(-2, 3)
                
            points.append((x, y))
            
        return points
        
    # Keyboard Control Functions
    
    def send_keys(self, keys: str, delay: float = 0.01) -> bool:
        """Send keyboard input
        
        Args:
            keys: Keys to send (supports special keys)
            delay: Delay between keys
            
        Returns:
            Success status
        """
        try:
            # Parse special keys
            special_keys = {
                '{ENTER}': win32con.VK_RETURN,
                '{TAB}': win32con.VK_TAB,
                '{ESC}': win32con.VK_ESCAPE,
                '{BACKSPACE}': win32con.VK_BACK,
                '{DELETE}': win32con.VK_DELETE,
                '{UP}': win32con.VK_UP,
                '{DOWN}': win32con.VK_DOWN,
                '{LEFT}': win32con.VK_LEFT,
                '{RIGHT}': win32con.VK_RIGHT,
                '{HOME}': win32con.VK_HOME,
                '{END}': win32con.VK_END,
                '{PAGEUP}': win32con.VK_PRIOR,
                '{PAGEDOWN}': win32con.VK_NEXT,
                '{F1}': win32con.VK_F1,
                '{F2}': win32con.VK_F2,
                '{F3}': win32con.VK_F3,
                '{F4}': win32con.VK_F4,
                '{F5}': win32con.VK_F5,
            }
            
            i = 0
            while i < len(keys):
                # Check for special key
                special_found = False
                for special, vk_code in special_keys.items():
                    if keys[i:].startswith(special):
                        self._send_vk_key(vk_code)
                        i += len(special)
                        special_found = True
                        break
                        
                if not special_found:
                    # Regular character
                    if keys[i:].startswith('^'):  # Ctrl
                        i += 1
                        if i < len(keys):
                            self._send_key_combo(win32con.VK_CONTROL, ord(keys[i].upper()))
                            i += 1
                    elif keys[i:].startswith('+'):  # Shift
                        i += 1
                        if i < len(keys):
                            self._send_key_combo(win32con.VK_SHIFT, ord(keys[i].upper()))
                            i += 1
                    elif keys[i:].startswith('%'):  # Alt
                        i += 1
                        if i < len(keys):
                            self._send_key_combo(win32con.VK_MENU, ord(keys[i].upper()))
                            i += 1
                    else:
                        # Normal character
                        self._send_char(keys[i])
                        i += 1
                        
                if delay > 0:
                    time.sleep(delay)
                    
            return True
        except Exception:
            return False
            
    def _send_vk_key(self, vk_code: int):
        """Send virtual key"""
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        
    def _send_key_combo(self, modifier_vk: int, key_vk: int):
        """Send key combination"""
        win32api.keybd_event(modifier_vk, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(key_vk, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(key_vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(modifier_vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        
    def _send_char(self, char: str):
        """Send single character"""
        # Use SendInput for better Unicode support
        inputs = []
        for ch in char:
            # Key down
            ki = ctypes.wintypes.KEYBDINPUT(
                wVk=0,
                wScan=ord(ch),
                dwFlags=win32con.KEYEVENTF_UNICODE,
                time=0,
                dwExtraInfo=0
            )
            inputs.append(ctypes.wintypes.INPUT(type=win32con.INPUT_KEYBOARD, ki=ki))
            
            # Key up
            ki = ctypes.wintypes.KEYBDINPUT(
                wVk=0,
                wScan=ord(ch),
                dwFlags=win32con.KEYEVENTF_UNICODE | win32con.KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=0
            )
            inputs.append(ctypes.wintypes.INPUT(type=win32con.INPUT_KEYBOARD, ki=ki))
            
        # Send input
        ctypes.windll.user32.SendInput(
            len(inputs),
            ctypes.byref(inputs),
            ctypes.sizeof(ctypes.wintypes.INPUT)
        )
        
    # Screen Capture Functions
    
    def capture_window(self, hwnd: int) -> Optional[bytes]:
        """Capture window content as numpy array
        
        Args:
            hwnd: Window handle
            
        Returns:
            Image as numpy array or None
        """
        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Get device contexts
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Copy window content
            result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
            
            if result:
                # Convert to numpy array
                bmpinfo = save_bitmap.GetInfo()
                bmpstr = save_bitmap.GetBitmapBits(True)
                
                # Cleanup
                win32gui.DeleteObject(save_bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwnd_dc)
                
                # Return raw bitmap data
                return bmpstr
            else:
                return None
                
        except Exception:
            return None
            
    # Clipboard Functions
    
    def get_clipboard_text(self) -> Optional[str]:
        """Get text from clipboard
        
        Returns:
            Clipboard text or None
        """
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    return data.decode('utf-8', errors='ignore')
                elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    return data
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass
        return None
        
    def set_clipboard_text(self, text: str) -> bool:
        """Set clipboard text
        
        Args:
            text: Text to set
            
        Returns:
            Success status
        """
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                return True
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return False