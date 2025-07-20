#!/usr/bin/env python3
"""Simple test script for vision integration without server dependencies"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cybercorp_node'))

import cv2
import numpy as np
import json
from utils.vision_model import UIVisionModel, UIElement

def test_vision_model():
    """Test the vision model with synthetic images"""
    print("Testing vision model...")
    
    # Create test model
    model = UIVisionModel(use_yolo=False)
    print(f"Created vision model (YOLO: {model.use_yolo})")
    
    # Create synthetic test image
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw UI elements
    cv2.rectangle(test_image, (100, 100), (250, 140), (200, 200, 200), -1)  # Button
    cv2.rectangle(test_image, (300, 100), (550, 130), (240, 240, 240), 2)   # Input
    cv2.rectangle(test_image, (100, 200), (700, 500), (220, 220, 220), 2)   # Panel
    cv2.rectangle(test_image, (120, 250), (200, 280), (180, 180, 180), -1)  # Small button
    
    # Add text labels
    cv2.putText(test_image, "Save", (150, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(test_image, "Enter text here", (320, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    cv2.putText(test_image, "Panel Content", (150, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
    cv2.putText(test_image, "OK", (145, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    print(f"Created synthetic test image: {test_image.shape}")
    
    # Test element detection
    print("Running UI element detection...")
    elements = model.detect_ui_elements(test_image)
    print(f"Detected {len(elements)} UI elements")
    
    # Print element details
    for i, elem in enumerate(elements):
        x1, y1, x2, y2 = elem.bbox
        w, h = x2 - x1, y2 - y1
        print(f"  {i+1}. {elem.element_type}: ({x1},{y1}) {w}x{h} conf={elem.confidence:.2f}")
    
    # Test UI structure extraction
    print("\nExtracting UI structure...")
    ui_structure = model.extract_ui_structure(test_image, include_ocr=False)
    print(f"UI structure has {len(ui_structure['elements'])} elements")
    print(f"Image size: {ui_structure['image_size']}")
    
    # Test visualization
    print("\nCreating visualization...")
    vis_image = model.visualize_detection(test_image, elements)
    cv2.imwrite("test_vision_output.png", vis_image)
    print("Saved visualization as: test_vision_output.png")
    
    # Test benchmark
    print("\nRunning benchmark...")
    benchmark = model.benchmark(test_image, iterations=5)
    print("Benchmark results:")
    print(f"  Average time: {benchmark['avg_time']:.3f}s")
    print(f"  FPS: {benchmark['fps']:.1f}")
    print(f"  Elements detected: {benchmark['avg_elements']:.1f}")
    
    # Test element classification
    print("\nTesting element classification...")
    element_types = {}
    for elem in elements:
        elem_type = elem.element_type
        if elem_type in element_types:
            element_types[elem_type] += 1
        else:
            element_types[elem_type] = 1
    
    print("Element type distribution:")
    for elem_type, count in element_types.items():
        print(f"  {elem_type}: {count}")
    
    # Export structure as JSON
    print("\nExporting structure...")
    with open("test_ui_structure.json", "w") as f:
        json.dump(ui_structure, f, indent=2)
    print("Saved UI structure as: test_ui_structure.json")
    
    return True

def test_real_screenshot():
    """Test with a real screenshot if available"""
    print("\nTesting with real screenshot...")
    
    # Try to load a screenshot
    screenshot_files = ["screenshot.png", "test.png", "sample.png"]
    test_image = None
    
    for filename in screenshot_files:
        if os.path.exists(filename):
            test_image = cv2.imread(filename)
            if test_image is not None:
                print(f"Loaded screenshot: {filename}")
                break
    
    if test_image is None:
        print("No screenshot files found. Creating a more complex synthetic image...")
        
        # Create a more complex synthetic UI
        test_image = np.ones((800, 1200, 3), dtype=np.uint8) * 240
        
        # Title bar
        cv2.rectangle(test_image, (0, 0), (1200, 40), (100, 150, 200), -1)
        cv2.putText(test_image, "Application Window", (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Menu bar
        cv2.rectangle(test_image, (0, 40), (1200, 70), (220, 220, 220), -1)
        cv2.putText(test_image, "File", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(test_image, "Edit", (80, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(test_image, "View", (140, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Toolbar
        cv2.rectangle(test_image, (0, 70), (1200, 110), (200, 200, 200), -1)
        for i in range(8):
            x = 20 + i * 60
            cv2.rectangle(test_image, (x, 80), (x + 40, 100), (180, 180, 180), -1)
        
        # Main content area
        cv2.rectangle(test_image, (20, 130), (800, 700), (255, 255, 255), -1)
        cv2.rectangle(test_image, (20, 130), (800, 700), (150, 150, 150), 2)
        
        # Sidebar
        cv2.rectangle(test_image, (820, 130), (1180, 700), (230, 230, 230), -1)
        cv2.rectangle(test_image, (820, 130), (1180, 700), (150, 150, 150), 2)
        
        # Form elements in sidebar
        cv2.rectangle(test_image, (840, 160), (1160, 190), (255, 255, 255), -1)
        cv2.rectangle(test_image, (840, 160), (1160, 190), (100, 100, 100), 1)
        cv2.putText(test_image, "Text Input", (850, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        cv2.rectangle(test_image, (900, 210), (1000, 240), (100, 200, 100), -1)
        cv2.putText(test_image, "Submit", (920, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.rectangle(test_image, (1020, 210), (1120, 240), (200, 100, 100), -1)
        cv2.putText(test_image, "Cancel", (1040, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Status bar
        cv2.rectangle(test_image, (0, 720), (1200, 800), (180, 180, 180), -1)
        cv2.putText(test_image, "Status: Ready", (20, 765), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Test with this image
    model = UIVisionModel(use_yolo=False)
    elements = model.detect_ui_elements(test_image)
    
    print(f"Detected {len(elements)} elements in complex image")
    
    # Group by type
    by_type = {}
    for elem in elements:
        if elem.element_type not in by_type:
            by_type[elem.element_type] = []
        by_type[elem.element_type].append(elem)
    
    for elem_type, elems in by_type.items():
        print(f"  {elem_type}: {len(elems)} elements")
    
    # Save visualization
    vis_image = model.visualize_detection(test_image, elements)
    cv2.imwrite("test_complex_vision.png", vis_image)
    print("Saved complex visualization as: test_complex_vision.png")
    
    return True

if __name__ == "__main__":
    print("Vision Integration Simple Test")
    print("=" * 40)
    
    try:
        # Test 1: Basic synthetic image
        test_vision_model()
        
        # Test 2: Complex synthetic or real image
        test_real_screenshot()
        
        print("\n" + "=" * 40)
        print("All tests completed successfully!")
        print("\nGenerated files:")
        print("- test_vision_output.png (basic visualization)")
        print("- test_complex_vision.png (complex visualization)")
        print("- test_ui_structure.json (UI structure data)")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()