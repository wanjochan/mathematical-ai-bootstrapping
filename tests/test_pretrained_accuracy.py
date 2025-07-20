"""Test pre-trained model accuracy"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import cv2
from cybercorp_node.utils.vision_validator import VisionValidator
from cybercorp_node.utils.vision_model_pretrained import UIVisionModelPretrained

def test_pretrained_accuracy():
    """Test pre-trained model on the standard test UI"""
    print("Testing Pre-trained Vision Model")
    print("=" * 50)
    
    # Create test UI
    validator = VisionValidator()
    test_image = validator.create_test_interface()
    
    # Initialize pre-trained model
    try:
        print("Initializing pre-trained model...")
        model = UIVisionModelPretrained()
        print(f"Using model: {model.model_name}")
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return None
    
    # Run detection
    print("Running detection...")
    start_time = time.time()
    elements = model.detect_ui_elements(test_image)
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
        'button': 3,
        'input': 2,
        'checkbox': 2,
        'radio': 2,
        'dropdown': 1,
    }
    
    # Calculate accuracy
    total_expected = sum(expected.values())
    total_correct = 0
    
    print("\nPer-element analysis:")
    for elem_type in expected:
        expected_count = expected[elem_type]
        detected_count = type_counts.get(elem_type, 0)
        correct = min(expected_count, detected_count)
        total_correct += correct
        accuracy = (correct / expected_count * 100) if expected_count > 0 else 0
        status = "OK" if detected_count == expected_count else "FAIL"
        print(f"{status} {elem_type:10} expected: {expected_count}, detected: {detected_count}, accuracy: {accuracy:.0f}%")
    
    overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\nOverall accuracy: {overall_accuracy:.1f}%")
    print(f"Target: 95%")
    print(f"Status: {'PASS' if overall_accuracy >= 95 else 'FAIL'}")
    
    # Save visualization
    vis_image = test_image.copy()
    for elem in elements:
        x1, y1, x2, y2 = elem.bbox
        color = (0, 255, 0) if elem.clickable else (255, 0, 0)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis_image, f"{elem.element_type} ({elem.confidence:.2f})", 
                   (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite("tests/pretrained_detection_result.png", vis_image)
    print("\nVisualization saved to: tests/pretrained_detection_result.png")
    
    return overall_accuracy

if __name__ == "__main__":
    accuracy = test_pretrained_accuracy()
    print(f"\nFinal accuracy: {accuracy:.1f}%" if accuracy else "Test failed")