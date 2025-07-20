"""Auto-detect correct chat input position in Cursor IDE"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import win32gui
import win32con
import win32api
import cv2
import numpy as np
from cybercorp_node.utils.vision_model_optimized import UIVisionModelOptimized


def capture_cursor_window():
    """Capture Cursor IDE window"""
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
        return None, None
    
    hwnd, title = windows[0]
    print(f"Found Cursor IDE: {title}")
    
    try:
        import win32ui
        from PIL import Image
        
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        print(f"Window size: {width}x{height} at ({left}, {top})")
        
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
        
        # Save screenshot for analysis
        cv2.imwrite("tests/cursor_current_screenshot.png", img_bgr)
        print("Screenshot saved to: tests/cursor_current_screenshot.png")
        
        return img_bgr, (hwnd, left, top, width, height)
        
    except Exception as e:
        print(f"Failed to capture window: {e}")
        return None, None


def find_chat_input_advanced(screenshot, window_info):
    """Advanced search for chat input box"""
    hwnd, left, top, width, height = window_info
    
    print("Searching for chat input using advanced methods...")
    
    # Use vision model
    vision_model = UIVisionModelOptimized()
    elements = vision_model.detect_ui_elements(screenshot)
    
    print(f"Vision model found {len(elements)} UI elements:")
    
    input_candidates = []
    
    for i, elem in enumerate(elements):
        print(f"  {i+1}. {elem.element_type} at {elem.center} (conf: {elem.confidence:.2f})")
        
        if elem.element_type == 'input':
            input_candidates.append(elem)
    
    # Also search for text areas that might be chat inputs
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    
    # Look for rectangular regions in the right side that could be inputs
    right_region = screenshot[:, int(width*0.6):]  # Right 40% of screen
    right_gray = cv2.cvtColor(right_region, cv2.COLOR_BGR2GRAY)
    
    # Find edges
    edges = cv2.Canny(right_gray, 30, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    text_area_candidates = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Look for larger rectangular areas that could be text input
        if w > 200 and h > 30 and w/h > 4 and h < 100:
            global_x = x + int(width*0.6)
            global_y = y
            
            roi = right_region[y:y+h, x:x+w]
            if roi.size > 0:
                mean_brightness = cv2.mean(roi)[0]
                
                text_area_candidates.append({
                    'bbox': (global_x, global_y, global_x + w, global_y + h),
                    'center': (global_x + w//2, global_y + h//2),
                    'area': w * h,
                    'brightness': mean_brightness,
                    'type': 'text_area'
                })
    
    # Sort by area (larger is more likely to be main input)
    text_area_candidates.sort(key=lambda x: x['area'], reverse=True)
    
    print(f"Found {len(text_area_candidates)} potential text areas:")
    for i, area in enumerate(text_area_candidates[:3]):  # Show top 3
        print(f"  Area {i+1}: center {area['center']}, size {area['area']}")
    
    # Create visualization
    vis_image = screenshot.copy()
    
    # Draw vision model inputs in green
    for elem in input_candidates:
        x1, y1, x2, y2 = elem.bbox
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis_image, f"Input {elem.confidence:.2f}", (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Draw text areas in blue
    for i, area in enumerate(text_area_candidates[:3]):
        x1, y1, x2, y2 = area['bbox']
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(vis_image, f"TextArea {i+1}", (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.circle(vis_image, area['center'], 5, (255, 0, 0), -1)
    
    cv2.imwrite("tests/cursor_input_detection.png", vis_image)
    print("Input detection saved to: tests/cursor_input_detection.png")
    
    # Return best candidates
    all_candidates = []
    
    # Add vision model inputs
    for elem in input_candidates:
        all_candidates.append({
            'center': elem.center,
            'screen_pos': (left + elem.center[0], top + elem.center[1]),
            'confidence': elem.confidence,
            'type': 'vision_input',
            'area': elem.area
        })
    
    # Add text areas
    for area in text_area_candidates[:2]:  # Top 2 text areas
        all_candidates.append({
            'center': area['center'],
            'screen_pos': (left + area['center'][0], top + area['center'][1]),
            'confidence': 0.8,
            'type': 'text_area',
            'area': area['area']
        })
    
    # Sort by confidence and area
    all_candidates.sort(key=lambda x: (x['confidence'], x['area']), reverse=True)
    
    return all_candidates


def test_positions(candidates, window_info):
    """Test each candidate position"""
    hwnd, left, top, width, height = window_info
    
    print(f"\nTesting {len(candidates)} candidate positions:")
    
    for i, candidate in enumerate(candidates[:3]):  # Test top 3
        print(f"\nTesting candidate {i+1}:")
        print(f"  Type: {candidate['type']}")
        print(f"  Window position: {candidate['center']}")
        print(f"  Screen position: {candidate['screen_pos']}")
        print(f"  Confidence: {candidate['confidence']:.2f}")
        
        try:
            # Bring window to foreground
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            
            # Click position
            screen_x, screen_y = candidate['screen_pos']
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.3)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            
            print(f"  Clicked position")
            time.sleep(1)
            
            # Try typing a short test
            test_text = f"test{i+1}"
            print(f"  Typing: {test_text}")
            
            for char in test_text:
                if char.isalnum():
                    vk_code = ord(char.upper())
                    win32api.keybd_event(vk_code, 0, 0, 0)
                    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            
            # Don't send Enter, just test typing
            print(f"  Test typing completed")
            
            # Clear the test text
            time.sleep(0.5)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
            win32api.keybd_event(win32con.VK_DELETE, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            print(f"  Position tested (check if text appeared in chat input)")
            
        except Exception as e:
            print(f"  Error testing position: {e}")


def main():
    print("=== Auto-detect Cursor IDE Chat Input Position ===")
    
    # Capture window
    screenshot, window_info = capture_cursor_window()
    if screenshot is None:
        return
    
    # Find chat input candidates
    candidates = find_chat_input_advanced(screenshot, window_info)
    
    if not candidates:
        print("No chat input candidates found")
        return
    
    print(f"\nFound {len(candidates)} potential chat input positions")
    
    # Test positions
    test_positions(candidates, window_info)
    
    print(f"\nTesting completed!")
    print(f"Check the following files:")
    print(f"  - tests/cursor_current_screenshot.png (full screenshot)")
    print(f"  - tests/cursor_input_detection.png (detected inputs)")
    print(f"\nObserve which position actually accepted text input in Cursor IDE")


if __name__ == "__main__":
    main()