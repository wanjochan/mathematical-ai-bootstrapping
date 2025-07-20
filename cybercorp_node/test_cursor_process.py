"""
Test looking for Cursor process on Windows
"""

import psutil
import win32gui
import win32process

def find_cursor_processes():
    """Find Cursor processes locally"""
    cursor_processes = []
    
    print("Searching for Cursor processes...")
    
    # Check all processes
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'cursor' in proc.info['name'].lower():
                cursor_processes.append(proc.info)
                print(f"Found Cursor process: {proc.info['name']} (PID: {proc.info['pid']})")
                print(f"  Executable: {proc.info['exe']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return cursor_processes

def find_cursor_windows():
    """Find windows belonging to Cursor"""
    cursor_windows = []
    
    def enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                class_name = win32gui.GetClassName(hwnd)
                
                # Get process info
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                    
                    # Check if it's a Cursor window
                    if 'cursor' in process_name.lower():
                        cursor_windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'class': class_name,
                            'process': process_name,
                            'pid': pid
                        })
                        print(f"\nFound Cursor window:")
                        print(f"  Title: {title}")
                        print(f"  Class: {class_name}")
                        print(f"  Process: {process_name} (PID: {pid})")
                except:
                    pass
        return True
    
    print("\nSearching for Cursor windows...")
    win32gui.EnumWindows(enum_handler, None)
    
    return cursor_windows

def find_chrome_widget_windows():
    """Find all Chrome_WidgetWin_1 windows"""
    chrome_windows = []
    
    def enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                class_name = win32gui.GetClassName(hwnd)
                
                if class_name == 'Chrome_WidgetWin_1':
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name()
                        
                        chrome_windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'process': process_name,
                            'pid': pid
                        })
                    except:
                        chrome_windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'process': 'Unknown',
                            'pid': 0
                        })
        return True
    
    print("\nSearching for Chrome_WidgetWin_1 windows...")
    win32gui.EnumWindows(enum_handler, None)
    
    return chrome_windows

if __name__ == '__main__':
    print("=== Cursor Process and Window Detection ===\n")
    
    # Find Cursor processes
    processes = find_cursor_processes()
    
    if not processes:
        print("\nNo Cursor processes found!")
        print("Make sure Cursor IDE is running.")
    
    # Find Cursor windows
    windows = find_cursor_windows()
    
    if not windows:
        print("\nNo Cursor windows found!")
        
        # Show Chrome_WidgetWin_1 windows for debugging
        chrome_windows = find_chrome_widget_windows()
        
        print(f"\nFound {len(chrome_windows)} Chrome_WidgetWin_1 windows:")
        for w in chrome_windows[:10]:
            print(f"  - {w['title'][:60]}... (Process: {w['process']})")
    
    print("\nDone.")