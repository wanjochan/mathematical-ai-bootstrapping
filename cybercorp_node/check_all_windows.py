"""
Check all windows and find which process owns them
"""

import psutil
import win32gui
import win32process

def check_all_windows():
    """Check all windows and their processes"""
    
    # Get Cursor process paths
    cursor_info = {}
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            if 'cursor' in proc.info['name'].lower():
                cursor_info[proc.info['pid']] = {
                    'name': proc.info['name'],
                    'exe': proc.info['exe'],
                    'cmdline': proc.info['cmdline']
                }
        except:
            pass
    
    print("Cursor processes:")
    for pid, info in cursor_info.items():
        print(f"  PID {pid}: {info['name']}")
        if info['cmdline']:
            print(f"    Command: {' '.join(info['cmdline'][:3])}...")
    
    # Find windows that might be Cursor
    potential_cursor_windows = []
    
    def enum_handler(hwnd, ctx):
        try:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    class_name = win32gui.GetClassName(hwnd)
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                        process_exe = process.exe()
                    except:
                        process_name = "Unknown"
                        process_exe = "Unknown"
                    
                    # Check various indicators
                    is_cursor = False
                    reason = ""
                    
                    # Check by process name
                    if 'cursor' in process_name.lower():
                        is_cursor = True
                        reason = "Process name contains 'cursor'"
                    
                    # Check by window title
                    elif 'cursor' in title.lower():
                        is_cursor = True
                        reason = "Window title contains 'cursor'"
                    
                    # Check by executable path
                    elif 'cursor' in str(process_exe).lower():
                        is_cursor = True
                        reason = "Executable path contains 'cursor'"
                    
                    # Check for Electron apps that might be Cursor
                    elif (class_name == 'Chrome_WidgetWin_1' and 
                          process_name not in ['chrome.exe', 'msedge.exe', 'brave.exe', 'TencentDocs.exe']):
                        potential_cursor_windows.append({
                            'hwnd': hwnd,
                            'title': title[:80],
                            'class': class_name,
                            'process': process_name,
                            'exe': str(process_exe)[:80],
                            'pid': pid
                        })
                    
                    if is_cursor:
                        print(f"\n✓ Found Cursor window! ({reason})")
                        print(f"  HWND: {hwnd}")
                        print(f"  Title: {title}")
                        print(f"  Class: {class_name}")
                        print(f"  Process: {process_name} (PID: {pid})")
                        print(f"  Exe: {process_exe}")
        except:
            pass
        
        return True
    
    print("\n\nSearching all visible windows...")
    win32gui.EnumWindows(enum_handler, None)
    
    if potential_cursor_windows:
        print(f"\n\nPotential Cursor windows (Electron apps):")
        for w in potential_cursor_windows:
            print(f"\n  Window: {w['title']}")
            print(f"    Process: {w['process']} (PID: {w['pid']})")
            print(f"    Exe: {w['exe']}")
            
            # Check if any Cursor process matches this PID
            if w['pid'] in cursor_info:
                print(f"    ✓ MATCHES Cursor PID!")
    
    # Check if Cursor might be running as a different process
    print("\n\nChecking for renamed or embedded Cursor...")
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe_path = str(proc.info['exe'] or '').lower()
            if 'cursor' in exe_path and proc.info['name'] not in ['Cursor.exe']:
                print(f"  Found: {proc.info['name']} at {proc.info['exe']}")
        except:
            pass

if __name__ == '__main__':
    check_all_windows()