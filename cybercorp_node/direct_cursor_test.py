"""Direct test for Cursor control"""

import win32gui
import win32con
import win32api
import time
import pyautogui
import pyperclip

def find_cursor_window():
    """Find Cursor IDE window"""
    windows = []
    
    def enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class': win32gui.GetClassName(hwnd)
                })
        return True
    
    win32gui.EnumWindows(enum_handler, None)
    return windows

def main():
    # Find Cursor windows
    cursor_windows = find_cursor_window()
    
    print(f"Found {len(cursor_windows)} Cursor windows:")
    for w in cursor_windows:
        print(f"  - {w['title']} (hwnd: {w['hwnd']}, class: {w['class']})")
    
    if not cursor_windows:
        print("No Cursor windows found")
        return
        
    # Use the first Cursor window
    cursor_window = cursor_windows[0]
    hwnd = cursor_window['hwnd']
    
    # Activate window
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        print(f"Activated window: {cursor_window['title']}")
    except Exception as e:
        print(f"Failed to activate window: {e}")
        return
    
    # Wait for window to be active
    time.sleep(1)
    
    # The text to send
    text = """阅读workflow.md了解工作流；
启动新job(work_id=cybercorp_dashboard)，在现有的cybercorp_web/里面加入dashboard功能，用来观察所有的受控端信息
做好之后打开网站测试看看效果"""
    
    # Use clipboard approach for multi-line text
    pyperclip.copy(text)
    time.sleep(0.5)
    
    # Press Ctrl+V to paste
    pyautogui.hotkey('ctrl', 'v')
    
    print("Text sent to Cursor")
    
    # Optional: Press Enter to send
    # time.sleep(0.5)
    # pyautogui.press('enter')

if __name__ == "__main__":
    main()