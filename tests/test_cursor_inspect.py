"""Inspect Cursor IDE UI more carefully"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api
import cv2
import numpy as np


def capture_and_analyze():
    """Capture and analyze current Cursor state"""
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        print("Cursor IDE not found")
        return
    
    hwnd, title = windows[0]
    print(f"Analyzing: {title}")
    
    try:
        import win32ui
        from PIL import Image
        
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        print(f"Window: {width}x{height} at ({left}, {top})")
        
        # Capture screenshot
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)
        
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        
        bmp_info = save_bitmap.GetInfo()
        bmp_str = save_bitmap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_str, 'raw', 'BGRX', 0, 1
        )
        
        img_array = np.array(img)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Clean up
        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        
        # Analyze the right panel specifically
        right_panel = img_bgr[:, int(width*0.6):]  # Right 40%
        
        print(f"Analyzing right panel: {right_panel.shape}")
        
        # Look for text patterns that might indicate input areas
        gray = cv2.cvtColor(right_panel, cv2.COLOR_BGR2GRAY)
        
        # Find text regions using different methods
        
        # Method 1: Find horizontal lines (input box borders)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Method 2: Find rectangular regions
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create visualization
        vis_image = img_bgr.copy()
        
        # Mark the test positions we tried
        test_positions = [
            (0.75, 0.85, "Bottom test"),
            (0.75, 0.80, "Lower test"),
            (0.75, 0.12, "Top test"),
        ]
        
        for x_ratio, y_ratio, label in test_positions:
            x = int(width * x_ratio)
            y = int(height * y_ratio)
            cv2.circle(vis_image, (x, y), 10, (0, 0, 255), -1)  # Red circles
            cv2.putText(vis_image, label, (x+15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Mark interesting contours in the right panel
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Look for potentially interesting rectangles
            if w > 50 and h > 10 and w/h > 2:
                global_x = x + int(width*0.6)
                global_y = y
                
                cv2.rectangle(vis_image, (global_x, global_y), (global_x + w, global_y + h), (0, 255, 0), 2)
                cv2.putText(vis_image, f"Rect {w}x{h}", (global_x, global_y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Save analysis
        cv2.imwrite("tests/cursor_detailed_analysis.png", vis_image)
        print("Analysis saved to: tests/cursor_detailed_analysis.png")
        
        # Print what we observe
        print(f"\nObservations:")
        print(f"1. Window dimensions: {width}x{height}")
        print(f"2. Right panel starts at x={int(width*0.6)}")
        print(f"3. Found {len(contours)} contours in right panel")
        print(f"4. Red circles show where we tested clicking")
        print(f"5. Green rectangles show potential input areas")
        
        # Check if there are any obvious text input characteristics
        # Look for areas with certain brightness patterns typical of input fields
        
        # Sample some areas to see brightness patterns
        sample_areas = [
            (int(width*0.75), int(height*0.15), "Top area"),
            (int(width*0.75), int(height*0.50), "Middle area"), 
            (int(width*0.75), int(height*0.85), "Bottom area"),
        ]
        
        print(f"\nBrightness analysis:")
        for x, y, desc in sample_areas:
            if 0 <= x < width and 0 <= y < height:
                # Sample 20x20 area around the point
                sample = img_bgr[max(0,y-10):y+10, max(0,x-10):x+10]
                if sample.size > 0:
                    mean_brightness = cv2.mean(sample)[0]
                    print(f"  {desc}: brightness = {mean_brightness:.1f}")
        
        return img_bgr
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_special_interactions():
    """Test special interaction methods"""
    print(f"\n=== Testing Special Interactions ===")
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and 'cursor' in title.lower():
                windows.append((hwnd, title))
        return True
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    
    if not windows:
        return
    
    hwnd, title = windows[0]
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    # Test 1: Try Tab key to navigate to input
    print("Test 1: Using Tab key to find input focus")
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Press Tab multiple times to cycle through focusable elements
        for i in range(5):
            print(f"  Tab {i+1}")
            win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
            win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.3)
            
            # Try typing a character to see if we're in an input
            win32api.keybd_event(ord('X'), 0, 0, 0)
            win32api.keybd_event(ord('X'), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.2)
        
        print("  Check if any 'X' characters appeared in input fields")
        
    except Exception as e:
        print(f"  Tab test error: {e}")
    
    # Test 2: Try Ctrl+L (common for focus on input)
    print(f"\nTest 2: Using Ctrl+L shortcut")
    try:
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('L'), 0, 0, 0)
        win32api.keybd_event(ord('L'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        
        # Try typing
        test_msg = "CTRL_L_TEST"
        for char in test_msg:
            win32api.keybd_event(ord(char), 0, 0, 0)
            win32api.keybd_event(ord(char), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)
        
        print(f"  Typed '{test_msg}' after Ctrl+L")
        
    except Exception as e:
        print(f"  Ctrl+L test error: {e}")
    
    # Test 3: Try typing without clicking (maybe focus is already there)
    print(f"\nTest 3: Direct typing (no clicking)")
    try:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(1)
        
        test_msg = "DIRECT_TYPE_TEST"
        for char in test_msg:
            win32api.keybd_event(ord(char), 0, 0, 0)
            win32api.keybd_event(ord(char), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)
        
        print(f"  Typed '{test_msg}' directly")
        
    except Exception as e:
        print(f"  Direct type error: {e}")


def main():
    print("=== Detailed Cursor IDE Inspection ===")
    print()
    
    # Analyze current state
    capture_and_analyze()
    
    # Test special interaction methods
    test_special_interactions()
    
    print(f"\n=== Summary ===")
    print(f"1. Check 'tests/cursor_detailed_analysis.png' for visual analysis")
    print(f"2. Look for any test text that appeared: 'X', 'CTRL_L_TEST', 'DIRECT_TYPE_TEST'")
    print(f"3. If any text appeared, that method found the input!")


if __name__ == "__main__":
    main()