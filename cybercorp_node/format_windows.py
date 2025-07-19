"""Format and display window information"""

import json
import sys

def format_windows(json_data):
    """Format window information for better display"""
    
    windows = json.loads(json_data) if isinstance(json_data, str) else json_data
    
    print(f"\nTotal Windows: {len(windows)}")
    print("=" * 80)
    
    # Group by window class
    by_class = {}
    for window in windows:
        class_name = window.get('class', 'Unknown')
        if class_name not in by_class:
            by_class[class_name] = []
        by_class[class_name].append(window)
    
    # Display grouped
    for class_name, wins in by_class.items():
        print(f"\n[{class_name}] ({len(wins)} windows)")
        print("-" * 60)
        
        for win in wins:
            hwnd = win.get('hwnd', 0)
            title = win.get('title', '').strip()
            # Clean up encoding issues
            title = title.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
            
            print(f"  HWND: {hwnd:>10} | {title}")
    
    print("\n" + "=" * 80)
    
    # Summary by type
    print("\nWindow Types Summary:")
    print("-" * 40)
    
    cmd_windows = [w for w in windows if 'cmd.exe' in w.get('title', '')]
    folder_windows = [w for w in windows if w.get('class') == 'CabinetWClass']
    
    print(f"  Command Line Windows: {len(cmd_windows)}")
    print(f"  File Explorer Windows: {len(folder_windows)}")
    print(f"  VSCode Windows: {len([w for w in windows if 'Visual Studio Code' in w.get('title', '')])}")
    print(f"  PuTTY Sessions: {len([w for w in windows if w.get('class') == 'PuTTY'])}")
    
    # Find specific important windows
    print("\nImportant Windows:")
    print("-" * 40)
    
    for win in windows:
        title = win.get('title', '')
        if 'Visual Studio Code' in title:
            print(f"  VSCode: {title}")
        elif 'client_9998.bat' in title:
            print(f"  CyberCorp Client: {title}")

# Test with sample data
sample_data = '''[
  {
    "hwnd": 12345,
    "title": "Sample Window",
    "class": "SampleClass"
  },
  {
    "hwnd": 67890,
    "title": "Another Window",
    "class": "AnotherClass"
  }
]'''

if __name__ == "__main__":
    # Use command line argument or sample data
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = f.read()
        format_windows(data)
    else:
        print("Usage: python format_windows.py <json_file>")
        print("\nUsing sample data for demonstration:")
        format_windows(sample_data)