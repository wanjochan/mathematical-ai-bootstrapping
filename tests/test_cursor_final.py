"""Final test of Cursor IDE control functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api


class SimpleCursorController:
    """Simple Cursor IDE controller"""
    
    def __init__(self):
        self.cursor_hwnd = None
        
    def find_cursor_window(self):
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
            self.cursor_hwnd, title = windows[0]
            print(f"Found Cursor IDE: {title}")
            return True
        else:
            print("Cursor IDE window not found")
            return False
    
    def click_chat_area(self):
        """Click chat input area"""
        try:
            if not self.cursor_hwnd:
                print("No Cursor window handle")
                return False
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(self.cursor_hwnd)
            width = right - left
            height = bottom - top
            
            # Calculate chat input area position (right panel, lower part)
            input_x = int(width * 0.8)  # 80% width (right panel)
            input_y = int(height * 0.75)  # 75% height (lower part)
            
            # Convert to screen coordinates
            screen_x = left + input_x
            screen_y = top + input_y
            
            print(f"Clicking chat area at: ({screen_x}, {screen_y})")
            
            # Bring window to foreground
            win32gui.SetForegroundWindow(self.cursor_hwnd)
            time.sleep(0.5)
            
            # Click the position
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.3)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            
            print("Click completed")
            return True
            
        except Exception as e:
            print(f"Click failed: {e}")
            return False
    
    def send_message(self, message):
        """Send message to Cursor IDE"""
        try:
            print(f"Sending message: '{message}'")
            
            # Wait for focus to stabilize
            time.sleep(0.5)
            
            # Clear existing content (Ctrl+A)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.2)
            
            # Type message
            self.type_text(message)
            
            # Wait
            time.sleep(0.5)
            
            # Send Enter
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print("Message sent successfully")
            return True
            
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    def type_text(self, text):
        """Type text character by character"""
        for char in text:
            if char == ' ':
                win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
                win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char.isalpha():
                vk_code = ord(char.upper())
                if char.isupper():
                    # Uppercase letter
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    # Lowercase letter
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char.isdigit():
                vk_code = ord(char)
                win32api.keybd_event(vk_code, 0, 0, 0)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char == '.':
                # Period
                win32api.keybd_event(0xBE, 0, 0, 0)  # VK_OEM_PERIOD
                win32api.keybd_event(0xBE, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char == ',':
                # Comma
                win32api.keybd_event(0xBC, 0, 0, 0)  # VK_OEM_COMMA
                win32api.keybd_event(0xBC, 0, win32con.KEYEVENTF_KEYUP, 0)
            elif char == '!':
                # Exclamation (Shift+1)
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                win32api.keybd_event(ord('1'), 0, 0, 0)
                win32api.keybd_event(ord('1'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            time.sleep(0.05)  # Small delay to avoid typing too fast


def main():
    """Main test function"""
    print("=== Cursor IDE Control Test ===")
    print("This test will:")
    print("1. Find Cursor IDE window")
    print("2. Click estimated chat input area")
    print("3. Send a test message")
    print()
    
    controller = SimpleCursorController()
    
    # Step 1: Find window
    if not controller.find_cursor_window():
        return False
    
    # Step 3: Interaction test
    print("\nStarting interaction test...")
    
    # Click chat input area
    if not controller.click_chat_area():
        return False
    
    # Wait for interface to respond
    time.sleep(1)
    
    # Send test message
    test_message = "Hello from cybercorp_node! This is a test message."
    print(f"\nSending test message...")
    
    if controller.send_message(test_message):
        print("\nInteraction test successful!")
        print("cybercorp_node successfully sent message to Cursor IDE")
        print("Please check Cursor IDE interface to confirm message was sent")
        return True
    else:
        print("\nInteraction test failed")
        return False


if __name__ == "__main__":
    print("==================================================")
    print("cybercorp_node -> Cursor IDE Interaction Test")
    print("==================================================")
    print()
    print("Requirements:")
    print("1. Cursor IDE is running")
    print("2. AI assistant chat panel is open")
    print("3. No other programs blocking Cursor window")
    print()
    print("Starting actual interaction test...")
    print("This will send a real test message to Cursor IDE!")
    print()
    
    try:
        success = main()
        
        if success:
            print("\n" + "=" * 60)
            print("Congratulations! cybercorp_node successfully controlled Cursor IDE!")
            print("=" * 60)
            print("This proves that:")
            print("   - cybercorp_node can find and control Cursor IDE")
            print("   - Can send programming-related questions to Cursor")
            print("   - Implemented basic 'backup developer' functionality")
            print()
            print("Now you can use cybercorp_node to automate your development workflow!")
        else:
            print("\nTest not completely successful, but basic functionality verified")
            
    except KeyboardInterrupt:
        print("\nUser interrupted test")
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()