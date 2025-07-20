"""Send cleanup message to Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32clipboard
import pyautogui

# Disable pyautogui safety
pyautogui.FAILSAFE = False


def find_cursor_window():
    """Find and activate Cursor IDE window"""
    print("Finding Cursor IDE window...")
    
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
    print(f"Found Cursor window: {title}")
    
    # Activate window
    try:
        win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(1)
        print("Window activated")
        return hwnd
    except Exception as e:
        print(f"Failed to activate window: {e}")
        return None


def set_clipboard(text):
    """Set clipboard content"""
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"Failed to set clipboard: {e}")
        return False


def send_cleanup_request():
    """Send backup cleanup request to Cursor"""
    print("Cursor IDE Cleanup Test")
    print("=" * 40)
    
    # Find Cursor window
    hwnd = find_cursor_window()
    if not hwnd:
        return False
    
    # Prepare cleanup message
    cleanup_message = """Please help me clean up the backup/ directory:

1. Delete backup files older than 7 days
2. Keep only the latest 3 backups  
3. Remove temporary files and logs
4. Show before/after directory size comparison

Generate a script to accomplish this task."""
    
    print("Message to send:")
    print(cleanup_message)
    print("\nEnsure Cursor IDE AI panel is open and ready...")
    
    input("Press Enter to send the message...")
    
    # Try to open AI assistant with Ctrl+L
    print("Opening AI assistant (Ctrl+L)...")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(2)
    
    # Use clipboard to input message
    print("Sending message via clipboard...")
    if set_clipboard(cleanup_message):
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        # Send message
        print("Sending message (Enter)...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print("Message sent successfully!")
        print("Check Cursor IDE for the response...")
        return True
    
    return False


if __name__ == "__main__":
    try:
        success = send_cleanup_request()
        if success:
            print("\nTest completed! Cursor should now process the backup cleanup request.")
        else:
            print("\nTest failed. Please manually send the cleanup request to Cursor.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()