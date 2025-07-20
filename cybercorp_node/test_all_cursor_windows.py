"""
Find ALL windows belonging to Cursor processes
"""

import psutil
import win32gui
import win32process
import win32con

def find_all_cursor_windows():
    """Find ALL windows (visible or not) belonging to Cursor processes"""
    
    # First, get all Cursor PIDs
    cursor_pids = set()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'cursor' in proc.info['name'].lower():
                cursor_pids.add(proc.info['pid'])
        except:
            pass
    
    print(f"Found {len(cursor_pids)} Cursor processes: {cursor_pids}")
    
    cursor_windows = []
    all_windows = []
    
    def enum_handler(hwnd, ctx):
        try:
            # Get window info regardless of visibility
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Check if window belongs to Cursor
            if pid in cursor_pids:
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                # Get window state
                placement = win32gui.GetWindowPlacement(hwnd)
                show_state = placement[1]
                
                state_str = "Unknown"
                if show_state == win32con.SW_HIDE:
                    state_str = "Hidden"
                elif show_state == win32con.SW_MINIMIZE:
                    state_str = "Minimized"
                elif show_state == win32con.SW_MAXIMIZE:
                    state_str = "Maximized"
                elif show_state == win32con.SW_NORMAL:
                    state_str = "Normal"
                elif show_state == win32con.SW_SHOWMINIMIZED:
                    state_str = "Show Minimized"
                
                window_info = {
                    'hwnd': hwnd,
                    'title': title or '(No Title)',
                    'class': class_name,
                    'pid': pid,
                    'visible': is_visible,
                    'state': state_str
                }
                
                cursor_windows.append(window_info)
                
                # Show info
                if title or class_name:  # Only show windows with title or class
                    print(f"\nFound Cursor window:")
                    print(f"  HWND: {hwnd}")
                    print(f"  Title: {title or '(No Title)'}")
                    print(f"  Class: {class_name}")
                    print(f"  PID: {pid}")
                    print(f"  Visible: {is_visible}")
                    print(f"  State: {state_str}")
        except Exception as e:
            # Ignore errors for inaccessible windows
            pass
        
        return True
    
    print("\nSearching for ALL Cursor windows (including hidden)...")
    win32gui.EnumWindows(enum_handler, None)
    
    return cursor_windows

def find_main_cursor_window(windows):
    """Try to identify the main Cursor window"""
    # Priority order for window classes
    priority_classes = [
        'Chrome_WidgetWin_1',  # Electron app main window
        'Chrome_WidgetWin_0',  # Alternative Electron window
        'CursorMainWindow',    # Possible custom class
        'Cursor'               # Another possible class
    ]
    
    # First, look for visible windows with known classes
    for class_name in priority_classes:
        for window in windows:
            if window['class'] == class_name and window['visible']:
                return window
    
    # If no visible windows found, look for any window with these classes
    for class_name in priority_classes:
        for window in windows:
            if window['class'] == class_name:
                return window
    
    # Last resort: any visible window with a title
    for window in windows:
        if window['visible'] and window['title'] != '(No Title)':
            return window
    
    return None

if __name__ == '__main__':
    print("=== Comprehensive Cursor Window Detection ===\n")
    
    windows = find_all_cursor_windows()
    
    print(f"\n\nTotal Cursor windows found: {len(windows)}")
    
    # Group by window class
    classes = {}
    for w in windows:
        class_name = w['class']
        if class_name not in classes:
            classes[class_name] = []
        classes[class_name].append(w)
    
    print("\nWindows grouped by class:")
    for class_name, class_windows in classes.items():
        print(f"\n{class_name}: {len(class_windows)} windows")
        for w in class_windows[:3]:  # Show first 3 of each class
            print(f"  - {w['title'][:50]}... (Visible: {w['visible']}, State: {w['state']})")
    
    # Try to find main window
    main_window = find_main_cursor_window(windows)
    if main_window:
        print(f"\n\nLikely main Cursor window:")
        print(f"  HWND: {main_window['hwnd']}")
        print(f"  Title: {main_window['title']}")
        print(f"  Class: {main_window['class']}")
        print(f"  State: {main_window['state']}")
    
    print("\nDone.")