"""Test the advanced vision model for 95%+ accuracy"""

import time
import numpy as np
import cv2
from cybercorp_node.utils.vision_model_advanced import UIVisionModelAdvanced

def create_test_ui():
    """Create the same test UI as before"""
    img = np.ones((600, 900, 3), dtype=np.uint8) * 250
    
    # Window title bar
    cv2.rectangle(img, (0, 0), (900, 30), (70, 130, 180), -1)
    cv2.putText(img, "Settings Window", (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Close button
    cv2.rectangle(img, (870, 5), (895, 25), (220, 60, 60), -1)
    cv2.putText(img, "X", (877, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Text inputs with white background
    cv2.putText(img, "Username:", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.rectangle(img, (150, 65), (400, 90), (255, 255, 255), -1)
    cv2.rectangle(img, (150, 65), (400, 90), (150, 150, 150), 2)
    
    cv2.putText(img, "Email:", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.rectangle(img, (150, 105), (400, 130), (255, 255, 255), -1)
    cv2.rectangle(img, (150, 105), (400, 130), (150, 150, 150), 2)
    
    # Checkboxes
    cv2.rectangle(img, (50, 160), (65, 175), (255, 255, 255), -1)
    cv2.rectangle(img, (50, 160), (65, 175), (100, 100, 100), 2)
    cv2.putText(img, "v", (52, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 0), 2)
    cv2.putText(img, "Enable notifications", (80, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    cv2.rectangle(img, (50, 190), (65, 205), (255, 255, 255), -1)
    cv2.rectangle(img, (50, 190), (65, 205), (100, 100, 100), 2)
    cv2.putText(img, "Auto-save", (80, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Radio buttons
    cv2.circle(img, (58, 240), 8, (255, 255, 255), -1)
    cv2.circle(img, (58, 240), 8, (100, 100, 100), 2)
    cv2.circle(img, (58, 240), 4, (0, 120, 200), -1)
    cv2.putText(img, "Light theme", (80, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    cv2.circle(img, (58, 270), 8, (255, 255, 255), -1)
    cv2.circle(img, (58, 270), 8, (100, 100, 100), 2)
    cv2.putText(img, "Dark theme", (80, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Dropdown with gray background
    cv2.rectangle(img, (150, 300), (300, 325), (240, 240, 240), -1)
    cv2.rectangle(img, (150, 300), (300, 325), (150, 150, 150), 2)
    cv2.putText(img, "English", (160, 318), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    # Arrow indicator
    pts = np.array([[280, 310], [285, 315], [275, 315]], np.int32)
    cv2.fillPoly(img, [pts], (100, 100, 100))
    
    # Buttons at bottom
    cv2.rectangle(img, (500, 500), (580, 530), (220, 220, 220), -1)
    cv2.rectangle(img, (500, 500), (580, 530), (150, 150, 150), 2)
    cv2.putText(img, "Cancel", (515, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    cv2.rectangle(img, (600, 500), (680, 530), (60, 140, 60), -1)
    cv2.putText(img, "Save", (625, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return img

def test_advanced_model():
    """Test the advanced vision model"""
    print("Creating test UI...")
    test_img = create_test_ui()
    
    print("Initializing advanced vision model...")
    model = UIVisionModelAdvanced()
    
    print("Running detection...")
    start_time = time.time()
    elements = model.detect_ui_elements(test_img)
    detection_time = time.time() - start_time
    
    print(f"\nDetection completed in {detection_time:.3f}s ({1/detection_time:.1f} FPS)")
    print(f"Total elements detected: {len(elements)}")
    
    # Count by type
    type_counts = {}
    for elem in elements:
        type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1
    
    print(f"Element types: {type_counts}")
    
    # Expected elements
    expected = {
        'button': 3,  # Cancel, Save, Close(X)
        'input': 2,   # Username, Email
        'checkbox': 2,
        'radio': 2,
        'dropdown': 1
    }
    
    print("\nExpected vs Detected:")
    for elem_type, expected_count in expected.items():
        detected_count = type_counts.get(elem_type, 0)
        accuracy = (min(expected_count, detected_count) / expected_count) * 100 if expected_count > 0 else 0
        print(f"  {elem_type}: expected {expected_count}, detected {detected_count} ({accuracy:.0f}% accuracy)")
    
    # Calculate overall accuracy
    total_expected = sum(expected.values())
    total_correct = sum(min(expected.get(t, 0), type_counts.get(t, 0)) for t in expected.keys())
    overall_accuracy = (total_correct / total_expected) * 100
    
    print(f"\nOverall accuracy: {overall_accuracy:.1f}%")
    print(f"Target: 95%")
    print(f"Status: {'PASS' if overall_accuracy >= 95 else 'FAIL'}")
    
    # Detailed element list
    print("\nDetailed elements:")
    for i, elem in enumerate(elements):
        print(f"{i+1}. {elem.element_type} at {elem.bbox} (confidence: {elem.confidence:.2f})")
    
    # Save annotated image
    annotated = test_img.copy()
    for elem in elements:
        x1, y1, x2, y2 = elem.bbox
        color = (0, 255, 0) if elem.clickable else (255, 0, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated, elem.element_type, (x1, y1-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite("advanced_vision_result.png", annotated)
    print("\nAnnotated result saved to: advanced_vision_result.png")

if __name__ == "__main__":
    test_advanced_model()