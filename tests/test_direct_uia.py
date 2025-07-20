"""Direct test to capture VSCode window structure using Windows UI Automation"""

import json
import win32gui
import win32process
import psutil

try:
    import pywinauto
    from pywinauto import Desktop
    from pywinauto.application import Application
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    print("pywinauto not installed!")

def get_vscode_windows():
    """Find and analyze VSCode windows"""
    print("Searching for VSCode windows...")
    
    if not PYWINAUTO_AVAILABLE:
        return
    
    desktop = Desktop(backend="uia")
    vscode_windows = []
    
    # Find all windows
    for window in desktop.windows():
        try:
            title = window.window_text()
            class_name = window.class_name()
            
            # Check if it's a VSCode window
            if ('Visual Studio Code' in title or 'VSCode' in title or 
                'mathematical-ai-bootstrapping' in title or
                class_name == 'Chrome_WidgetWin_1'):
                
                print(f"\nFound window: {title}")
                print(f"Class: {class_name}")
                
                # Get window info
                window_info = {
                    'title': title,
                    'class_name': class_name,
                    'is_visible': window.is_visible(),
                    'is_enabled': window.is_enabled(),
                    'rectangle': str(window.rectangle()),
                    'handle': window.handle,
                    'controls': []
                }
                
                # Get process info
                try:
                    _, pid = win32process.GetWindowThreadProcessId(window.handle)
                    proc = psutil.Process(pid)
                    window_info['process'] = {
                        'name': proc.name(),
                        'pid': pid,
                        'exe': proc.exe()
                    }
                except:
                    pass
                
                # Get top-level controls
                print("  Analyzing controls...")
                try:
                    for i, control in enumerate(window.children()):
                        if i >= 15:  # Limit to first 15 controls
                            break
                        try:
                            control_type = control.element_info.control_type
                            control_name = control.element_info.name or ''
                            control_class = control.element_info.class_name or ''
                            control_id = control.element_info.automation_id or ''
                            
                            control_info = {
                                'index': i,
                                'type': control_type,
                                'name': control_name[:100],  # Limit name length
                                'class_name': control_class,
                                'automation_id': control_id,
                                'is_visible': control.is_visible(),
                                'is_enabled': control.is_enabled()
                            }
                            
                            # Special handling for certain control types
                            if control_type in ['Edit', 'Document']:
                                control_info['has_keyboard_focus'] = control.has_keyboard_focus()
                                try:
                                    # Try to get text content (limited)
                                    texts = control.texts()
                                    if texts:
                                        control_info['text_preview'] = texts[0][:50] + '...' if len(texts[0]) > 50 else texts[0]
                                except:
                                    pass
                            
                            window_info['controls'].append(control_info)
                            print(f"    [{i}] {control_type}: {control_name[:50]}")
                            
                        except Exception as e:
                            print(f"    Error reading control {i}: {e}")
                            
                except Exception as e:
                    print(f"  Error reading controls: {e}")
                
                vscode_windows.append(window_info)
                
        except Exception as e:
            pass
    
    return vscode_windows

def get_active_window():
    """Get information about the currently active window"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        
        print(f"\nActive window: {title}")
        
        if PYWINAUTO_AVAILABLE:
            try:
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                
                print(f"  Class: {window.class_name()}")
                print(f"  Control count: {len(window.children())}")
                
                return {
                    'title': title,
                    'handle': hwnd,
                    'class_name': window.class_name(),
                    'control_count': len(window.children())
                }
            except:
                pass
                
        return {'title': title, 'handle': hwnd}
        
    except Exception as e:
        print(f"Error getting active window: {e}")
        return None

def main():
    print("VSCode Window Structure Analyzer")
    print("=" * 60)
    
    # Get active window
    print("\n1. Active Window Information:")
    active = get_active_window()
    
    # Find VSCode windows
    print("\n2. VSCode Windows:")
    vscode_windows = get_vscode_windows()
    
    if vscode_windows:
        print(f"\nFound {len(vscode_windows)} VSCode window(s)")
        
        # Save to file
        output_file = "vscode_window_structure.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'active_window': active,
                'vscode_windows': vscode_windows
            }, f, indent=2, default=str)
        
        print(f"\nWindow structure saved to: {output_file}")
        
        # Print summary
        for i, window in enumerate(vscode_windows):
            print(f"\nWindow {i+1}: {window['title']}")
            print(f"  Controls found: {len(window['controls'])}")
            if 'process' in window:
                print(f"  Process: {window['process']['name']} (PID: {window['process']['pid']})")
    else:
        print("\nNo VSCode windows found!")
        print("Make sure VSCode is running and visible.")

if __name__ == "__main__":
    main()