"""Debug test for Cursor IDE control - verify click positions"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api


def get_cursor_info():
    """Get detailed Cursor IDE window information"""
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        print("No Cursor IDE window found")
        return None
    
    hwnd, title = windows[0]
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    print(f"Cursor IDE Window Info:")
    print(f"  Title: {title}")
    print(f"  HWND: {hwnd}")
    print(f"  Position: ({left}, {top}) to ({right}, {bottom})")
    print(f"  Size: {width}x{height}")
    
    return hwnd, left, top, width, height


def test_click_positions(hwnd, left, top, width, height):
    """Test different click positions"""
    print(f"\nTesting different click positions:")
    
    # Test positions in the right panel area
    test_positions = [
        (0.7, 0.8, "Lower right area 70%-80%"),
        (0.8, 0.7, "Right lower area 80%-70%"), 
        (0.85, 0.75, "Right panel center 85%-75%"),
        (0.9, 0.8, "Far right lower 90%-80%"),
        (0.75, 0.85, "Lower center right 75%-85%"),
    ]
    
    for x_ratio, y_ratio, description in test_positions:
        window_x = int(width * x_ratio)
        window_y = int(height * y_ratio)
        screen_x = left + window_x
        screen_y = top + window_y
        
        print(f"  {description}")
        print(f"    Window coords: ({window_x}, {window_y})")
        print(f"    Screen coords: ({screen_x}, {screen_y})")
        
        # Move cursor to position and wait for user to verify
        win32api.SetCursorPos((screen_x, screen_y))
        
        print(f"    Cursor moved to position. Check if it's over chat input!")
        response = input(f"    Is cursor over chat input area? (y/n/s to stop): ").lower()
        
        if response == 'y':
            print(f"    SUCCESS! Found correct position: {description}")
            return screen_x, screen_y, window_x, window_y
        elif response == 's':
            print(f"    Stopping test.")
            return None
        else:
            print(f"    Not correct position, trying next...")
    
    print(f"No correct position found in automated test")
    return None


def manual_click_test():
    """Manual click test - let user position cursor"""
    print(f"\nManual positioning test:")
    print(f"1. Please manually move your cursor to the Cursor IDE chat input box")
    print(f"2. Press Enter when cursor is positioned correctly")
    
    input("Press Enter when cursor is over chat input box...")
    
    # Get current cursor position
    x, y = win32api.GetCursorPos()
    print(f"Current cursor position: ({x}, {y})")
    
    # Get window info again
    cursor_info = get_cursor_info()
    if cursor_info:
        hwnd, left, top, width, height = cursor_info
        
        # Calculate relative position
        rel_x = x - left
        rel_y = y - top
        x_ratio = rel_x / width
        y_ratio = rel_y / height
        
        print(f"Relative to Cursor window:")
        print(f"  Window coords: ({rel_x}, {rel_y})")
        print(f"  Ratios: ({x_ratio:.3f}, {y_ratio:.3f})")
        
        return x, y, x_ratio, y_ratio
    
    return None


def test_actual_send(screen_x, screen_y):
    """Test actual message sending at the correct position"""
    print(f"\nTesting actual message send at position ({screen_x}, {screen_y})")
    
    cursor_info = get_cursor_info()
    if not cursor_info:
        return False
    
    hwnd = cursor_info[0]
    
    try:
        # Bring window to foreground
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Click the position
        win32api.SetCursorPos((screen_x, screen_y))
        time.sleep(0.3)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        
        print("Clicked position")
        time.sleep(1)
        
        # Send a simple test message
        test_message = "TEST from cybercorp"
        print(f"Typing: {test_message}")
        
        # Type message character by character
        for char in test_message:
            if char == ' ':
                win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
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
            time.sleep(0.05)
        
        time.sleep(0.5)
        
        # Send Enter
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        print("Message sent!")
        return True
        
    except Exception as e:
        print(f"Error during send test: {e}")
        return False


def main():
    print("=== Cursor IDE Click Position Debug Test ===")
    print()
    
    # Get window info
    cursor_info = get_cursor_info()
    if not cursor_info:
        return
    
    hwnd, left, top, width, height = cursor_info
    
    print(f"\nChoose test method:")
    print(f"1. Automated position testing")
    print(f"2. Manual position finding")
    print(f"3. Skip to manual positioning")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    correct_position = None
    
    if choice == "1":
        result = test_click_positions(hwnd, left, top, width, height)
        if result:
            screen_x, screen_y, window_x, window_y = result
            correct_position = (screen_x, screen_y)
    
    elif choice == "2":
        result = manual_click_test()
        if result:
            screen_x, screen_y, x_ratio, y_ratio = result
            correct_position = (screen_x, screen_y)
    
    elif choice == "3":
        result = manual_click_test()
        if result:
            screen_x, screen_y, x_ratio, y_ratio = result
            correct_position = (screen_x, screen_y)
    
    # Test actual sending if we found a position
    if correct_position:
        print(f"\nFound correct position: {correct_position}")
        test_send = input("Test actual message sending? (y/n): ").lower()
        
        if test_send == 'y':
            print("IMPORTANT: Check Cursor IDE to see if message appears!")
            success = test_actual_send(correct_position[0], correct_position[1])
            
            if success:
                print("Send test completed - check Cursor IDE for the message!")
            else:
                print("Send test failed")
    else:
        print("No correct position found")


if __name__ == "__main__":
    main()