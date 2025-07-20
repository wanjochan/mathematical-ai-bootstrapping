"""Test clicking bottom area of Cursor IDE chat panel"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api


def test_multiple_positions():
    """Test multiple positions in the chat panel"""
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        print("Cursor IDE not found")
        return
    
    hwnd, title = windows[0]
    print(f"Found: {title}")
    
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    print(f"Window: {width}x{height} at ({left}, {top})")
    
    # Test different positions in the right panel
    test_positions = [
        (0.75, 0.85, "Bottom of chat panel"),      # Very bottom
        (0.75, 0.80, "Lower chat area"),          # Lower area  
        (0.75, 0.90, "Very bottom edge"),         # Even lower
        (0.75, 0.12, "Top placeholder area"),     # Where "Plan, search..." is
        (0.80, 0.85, "Right-bottom corner"),      # Right corner
        (0.70, 0.85, "Left side of bottom"),      # Left side of bottom
    ]
    
    for x_ratio, y_ratio, description in test_positions:
        print(f"\n--- Testing: {description} ---")
        
        target_x = int(width * x_ratio)
        target_y = int(height * y_ratio)
        screen_x = left + target_x
        screen_y = top + target_y
        
        print(f"Position: ({target_x}, {target_y}) -> screen ({screen_x}, {screen_y})")
        
        try:
            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            
            # Click position
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.2)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            
            print("Clicked")
            time.sleep(0.5)
            
            # Type a simple test
            test_text = f"TEST{test_positions.index((x_ratio, y_ratio, description)) + 1}"
            print(f"Typing: {test_text}")
            
            for char in test_text:
                if char.isalnum():
                    vk_code = ord(char.upper())
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.03)
            
            print(f"Typed '{test_text}' - check if it appears in Cursor IDE")
            
            # Wait and clear (don't send)
            time.sleep(1)
            
            # Clear any text that might have been typed
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
            win32api.keybd_event(win32con.VK_DELETE, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print("Cleared text")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Tested {len(test_positions)} positions in Cursor IDE chat panel")
    print(f"Check which position (if any) showed text input in Cursor IDE")
    print(f"The correct position is where you saw the TESTx text appear")


def send_final_test_message():
    """Send a final test message using the most likely position"""
    print(f"\n=== Final Test Message ===")
    print(f"Using bottom-center position that most likely works")
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        return
    
    hwnd, title = windows[0]
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    # Use the most likely position: bottom center of chat panel
    target_x = int(width * 0.75)
    target_y = int(height * 0.85)
    screen_x = left + target_x
    screen_y = top + target_y
    
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        win32api.SetCursorPos((screen_x, screen_y))
        time.sleep(0.3)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        
        time.sleep(1)
        
        # Send actual message
        message = "cybercorp_node working correctly!"
        print(f"Sending final message: {message}")
        
        for char in message:
            if char == ' ':
                win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char == '!':
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                win32api.keybd_event(ord('1'), 0, 0, 0)
                win32api.keybd_event(ord('1'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
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
        
        time.sleep(0.5)
        
        # Send Enter
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        print("Final message sent!")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("=== Testing Multiple Positions in Cursor IDE ===")
    print("This will test different click positions to find the correct chat input")
    print()
    
    test_multiple_positions()
    
    # Ask if user wants to send final message
    print(f"\nIf one of the TEST positions worked, we can send a real message")
    send_final_test_message()


if __name__ == "__main__":
    main()