"""List all windows to find Cursor"""

import win32gui

def enum_windows():
    """Enumerate all windows"""
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
    return windows

def main():
    windows = enum_windows()
    
    # Filter potential development tools
    dev_keywords = ['cursor', 'code', 'visual', 'studio', 'ide', 'editor', 'vscode']
    
    print(f"Total windows: {len(windows)}")
    print("\nDevelopment-related windows:")
    
    found_dev = False
    for w in windows:
        title_lower = w['title'].lower()
        if any(keyword in title_lower for keyword in dev_keywords):
            print(f"  - {w['title'][:80]} (class: {w['class']})")
            found_dev = True
    
    if not found_dev:
        print("  No development tools found")
        print("\nShowing first 20 windows:")
        for w in windows[:20]:
            print(f"  - {w['title'][:80]} (class: {w['class']})")

if __name__ == "__main__":
    main()