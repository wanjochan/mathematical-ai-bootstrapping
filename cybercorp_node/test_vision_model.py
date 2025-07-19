"""Test vision model for UI understanding"""

import cv2
import numpy as np
import time
import os
import sys
from PIL import Image, ImageGrab
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.vision_model import UIVisionModel, UIElement
from utils.ocr_backend import OCRBackend


def capture_screen_region(x=0, y=0, width=None, height=None):
    """Capture a region of the screen"""
    if width and height:
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    else:
        screenshot = ImageGrab.grab()
    
    # Convert PIL to OpenCV format
    screenshot_np = np.array(screenshot)
    # Convert RGB to BGR
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    return screenshot_bgr


def test_on_screenshot():
    """Test vision model on a screenshot"""
    print("Testing Vision Model on Screenshot")
    print("=" * 60)
    
    # Initialize vision model
    vision_model = UIVisionModel(use_yolo=False)  # Start without YOLO
    
    # Capture screen
    print("\nCapturing screen in 3 seconds...")
    time.sleep(3)
    
    image = capture_screen_region()
    print(f"Captured image size: {image.shape[1]}x{image.shape[0]}")
    
    # Detect UI elements
    print("\nDetecting UI elements...")
    elements = vision_model.detect_ui_elements(image)
    
    print(f"\nFound {len(elements)} UI elements:")
    
    # Group by type
    element_types = {}
    for elem in elements:
        if elem.element_type not in element_types:
            element_types[elem.element_type] = []
        element_types[elem.element_type].append(elem)
    
    # Print summary
    for elem_type, elems in element_types.items():
        print(f"  {elem_type}: {len(elems)} elements")
    
    # Visualize results
    vis_image = vision_model.visualize_detection(image, elements)
    cv2.imwrite("vision_test_result.png", vis_image)
    print(f"\nVisualization saved to: vision_test_result.png")
    
    # Extract UI structure
    print("\nExtracting UI structure...")
    ui_structure = vision_model.extract_ui_structure(image, include_ocr=False)
    
    # Save structure
    with open("ui_structure.json", "w", encoding="utf-8") as f:
        json.dump(ui_structure, f, indent=2)
    print("UI structure saved to: ui_structure.json")
    
    return elements, image


def test_combined_with_ocr(elements, image):
    """Test combining vision model with OCR"""
    print("\n" + "=" * 60)
    print("Testing Combined Vision + OCR")
    print("=" * 60)
    
    # Initialize OCR
    ocr = OCRBackend()
    
    # For each detected element, try OCR
    text_elements = []
    
    for elem in elements[:10]:  # Limit to first 10 for speed
        if elem.element_type in ['button', 'input', 'text', 'menu_item']:
            # Extract region
            x1, y1, x2, y2 = elem.bbox
            roi = image[y1:y2, x1:x2]
            
            # Perform OCR
            try:
                detections = ocr.detect_text(roi)
                if detections:
                    # Combine text from all detections
                    text = ' '.join(d['text'] for d in detections)
                    elem.text = text
                    text_elements.append(elem)
                    print(f"  {elem.element_type} at {elem.bbox}: '{text}'")
            except Exception as e:
                print(f"  OCR error for {elem.element_type}: {e}")
    
    print(f"\nExtracted text from {len(text_elements)} elements")
    
    return text_elements


def test_performance():
    """Test vision model performance"""
    print("\n" + "=" * 60)
    print("Performance Benchmark")
    print("=" * 60)
    
    vision_model = UIVisionModel(use_yolo=False)
    
    # Test on different image sizes
    test_sizes = [(640, 480), (1024, 768), (1920, 1080)]
    
    for width, height in test_sizes:
        # Create test image
        test_image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Add some UI elements
        # Buttons
        for i in range(5):
            cv2.rectangle(test_image, (50 + i*150, 50), (150 + i*150, 100), (200, 200, 200), -1)
            cv2.rectangle(test_image, (50 + i*150, 50), (150 + i*150, 100), (0, 0, 0), 2)
        
        # Input fields
        for i in range(3):
            cv2.rectangle(test_image, (50, 150 + i*60), (400, 190 + i*60), (240, 240, 240), -1)
            cv2.rectangle(test_image, (50, 150 + i*60), (400, 190 + i*60), (100, 100, 100), 1)
        
        # Benchmark
        print(f"\nBenchmarking on {width}x{height} image...")
        metrics = vision_model.benchmark(test_image, iterations=10)
        
        print(f"  Average time: {metrics['avg_time']:.3f}s")
        print(f"  FPS: {metrics['fps']:.1f}")
        print(f"  Elements detected: {metrics['avg_elements']:.1f}")


def test_vscode_specific():
    """Test on VSCode window specifically"""
    print("\n" + "=" * 60)
    print("VSCode-Specific Testing")
    print("=" * 60)
    
    # Try to find VSCode window
    try:
        from utils.win32_backend import Win32Backend
        win32 = Win32Backend()
        
        # Find VSCode windows
        vscode_windows = win32.find_windows_by_title("Visual Studio Code")
        
        if vscode_windows:
            print(f"Found {len(vscode_windows)} VSCode windows")
            
            # Capture first VSCode window
            hwnd = vscode_windows[0]
            window_info = win32.get_window_info(hwnd)
            print(f"Window: {window_info['title']}")
            
            # Capture window
            image = win32.capture_window(hwnd)
            
            if image is not None:
                # Detect UI elements
                vision_model = UIVisionModel(use_yolo=False)
                elements = vision_model.detect_ui_elements(image)
                
                print(f"\nDetected {len(elements)} elements in VSCode")
                
                # Look for specific VSCode elements
                vscode_elements = {
                    'sidebar': [],
                    'editor': [],
                    'terminal': [],
                    'tabs': []
                }
                
                for elem in elements:
                    bbox = elem.bbox
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    
                    # Heuristics for VSCode layout
                    if bbox[0] < 100 and height > 500:
                        vscode_elements['sidebar'].append(elem)
                    elif width > 500 and height > 300:
                        vscode_elements['editor'].append(elem)
                    elif bbox[1] > window_info['height'] - 300:
                        vscode_elements['terminal'].append(elem)
                    elif height < 50 and width > 100 and bbox[1] < 200:
                        vscode_elements['tabs'].append(elem)
                
                # Print VSCode-specific results
                for area, elems in vscode_elements.items():
                    if elems:
                        print(f"  {area}: {len(elems)} elements")
                
                # Save VSCode analysis
                cv2.imwrite("vscode_vision_analysis.png", 
                           vision_model.visualize_detection(image, elements))
                print("\nVSCode analysis saved to: vscode_vision_analysis.png")
            else:
                print("Failed to capture VSCode window")
        else:
            print("No VSCode windows found")
            
    except Exception as e:
        print(f"VSCode test error: {e}")


def interactive_test():
    """Interactive test with real-time detection"""
    print("\n" + "=" * 60)
    print("Interactive Vision Test")
    print("=" * 60)
    print("Press 'q' to quit, 's' to save current detection")
    
    vision_model = UIVisionModel(use_yolo=False)
    
    while True:
        # Capture screen
        image = capture_screen_region(0, 0, 800, 600)
        
        # Detect elements
        start_time = time.time()
        elements = vision_model.detect_ui_elements(image)
        elapsed = time.time() - start_time
        
        # Visualize
        vis_image = vision_model.visualize_detection(image, elements)
        
        # Add FPS counter
        fps = 1 / elapsed if elapsed > 0 else 0
        cv2.putText(vis_image, f"FPS: {fps:.1f} | Elements: {len(elements)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show result
        cv2.imshow("Vision Model Test", vis_image)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(f"vision_capture_{timestamp}.png", vis_image)
            print(f"Saved: vision_capture_{timestamp}.png")
    
    cv2.destroyAllWindows()


def main():
    """Main test function"""
    print("CyberCorp Vision Model Testing")
    print("=" * 60)
    
    # Test 1: Screenshot detection
    elements, image = test_on_screenshot()
    
    # Test 2: Combined with OCR
    if input("\nTest with OCR? (y/n): ").lower() == 'y':
        test_combined_with_ocr(elements, image)
    
    # Test 3: Performance benchmark
    if input("\nRun performance benchmark? (y/n): ").lower() == 'y':
        test_performance()
    
    # Test 4: VSCode specific
    if input("\nTest on VSCode window? (y/n): ").lower() == 'y':
        test_vscode_specific()
    
    # Test 5: Interactive
    if input("\nRun interactive test? (y/n): ").lower() == 'y':
        interactive_test()
    
    print("\nAll tests completed!")
    print("Check generated files for results.")


if __name__ == "__main__":
    main()