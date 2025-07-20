"""
Test _get_windows function directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import what we need
import win32gui
from utils.response_formatter import format_success, format_error

def test_get_windows():
    """Test the _get_windows function directly"""
    try:
        windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'class': win32gui.GetClassName(hwnd)
                    })
            return True
            
        win32gui.EnumWindows(enum_handler, None)
        
        result = format_success(
            data={'windows': windows, 'count': len(windows)},
            message=f"Found {len(windows)} windows"
        )
        
        print(f"Success! Found {len(windows)} windows")
        print(f"Result: {result}")
        
        # Show first 5 windows
        for window in windows[:5]:
            print(f"  - {window['title']} (Class: {window['class']})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_get_windows()