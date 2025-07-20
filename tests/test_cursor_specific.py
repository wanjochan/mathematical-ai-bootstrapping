"""Test specific to current Cursor IDE UI layout"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api


def find_cursor_window():
    """Find Cursor IDE window"""
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if windows:
        return windows[0]
    return None, None


def test_chat_area_click():
    """Test clicking the chat area based on current UI"""
    hwnd, title = find_cursor_window()
    if not hwnd:
        print("Cursor IDE not found")
        return False
    
    print(f"Found: {title}")
    
    # Get window position
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    print(f"Window: {width}x{height} at ({left}, {top})")
    
    # Based on the screenshot, the chat area with "Plan, search, build anything" 
    # is in the right panel. Let's try clicking where that text should be
    
    # The right panel starts around 60% of width
    # The "Plan, search, build anything" text appears to be around 15% down from top
    
    target_x = int(width * 0.75)  # Center of right panel
    target_y = int(height * 0.15)  # Where the placeholder text is
    
    screen_x = left + target_x
    screen_y = top + target_y
    
    print(f"Targeting placeholder text area: ({target_x}, {target_y}) -> ({screen_x}, {screen_y})")
    
    try:
        # Bring to foreground
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Click the placeholder text area
        win32api.SetCursorPos((screen_x, screen_y))
        time.sleep(0.3)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        
        print("Clicked placeholder area")
        time.sleep(1)
        
        # Now try typing a message
        message = "Hello from cybercorp_node - testing chat functionality"
        print(f"Typing: {message}")
        
        # Type the message
        for char in message:
            if char == ' ':
                win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char == '-':
                win32api.keybd_event(0xBD, 0, 0, 0)  # VK_OEM_MINUS
                win32api.keybd_event(0xBD, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char.isalnum():
                vk_code = ord(char.upper())
                if char.isupper():
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)
        
        # Wait a moment
        time.sleep(1)
        
        # Send Enter
        print("Sending Enter key...")
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        print("Message sent!")
        print("Check Cursor IDE to see if message was received")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("=== Cursor IDE Specific UI Test ===")
    print("Based on current screenshot analysis")
    print("Targeting the 'Plan, search, build anything' area")
    print()
    
    success = test_chat_area_click()
    
    if success:
        print("\nTest completed successfully!")
        print("If you see the message in Cursor IDE, cybercorp_node is working!")
    else:
        print("\nTest failed")
    
    return success


if __name__ == "__main__":
    main()