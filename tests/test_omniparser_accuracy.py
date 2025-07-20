"""Test OmniParser accuracy on the standard test UI"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import cv2
from cybercorp_node.utils.vision_validator import VisionValidator
from cybercorp_node.utils.vision_model_omniparser import UIVisionModelOmniParser

def test_omniparser_accuracy():
    """Test OmniParser on the same UI used for traditional CV testing"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing OmniParser Accuracy")
    print("=" * 50)
    
    # Create test UI
    validator = VisionValidator()
    test_image = validator.create_test_interface()
    
    # Initialize OmniParser
    try:
        print("Initializing OmniParser...")
        omni_model = UIVisionModelOmniParser()
    except Exception as e:
        print(f"Failed to initialize OmniParser: {e}")
        print("\nPlease run: python scripts/setup_omniparser.py")
        return
    
    # Run detection
    print("Running detection...")
    start_time = time.time()
    elements = omni_model.detect_ui_elements(test_image)
    detection_time = time.time() - start_time
    
    print(f"\nDetection completed in {detection_time:.3f}s ({1/detection_time:.1f} FPS)")
    print(f"Total elements detected: {len(elements)}")
    
    # Count by type
    type_counts = {}
    for elem in elements:
        type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1
    
    print(f"Element types: {type_counts}")
    
    # Expected elements (ground truth)
    expected = {
        'button': 3,      # Cancel, Save, Close(X)
        'input': 2,       # Username, Email
        'checkbox': 2,    # Enable notifications, Auto-save
        'radio': 2,       # Light theme, Dark theme
        'dropdown': 1,    # Language dropdown
    }
    
    # Calculate accuracy
    total_expected = sum(expected.values())
    total_correct = 0
    
    print("\nPer-element analysis:")
    for elem_type in expected:
        expected_count = expected[elem_type]
        detected_count = type_counts.get(elem_type, 0)
        
        # Calculate per-type accuracy
        correct = min(expected_count, detected_count)
        total_correct += correct
        
        accuracy = (correct / expected_count * 100) if expected_count > 0 else 0
        status = "✓" if detected_count == expected_count else "✗"
        
        print(f"{status} {elem_type:10} expected: {expected_count}, detected: {detected_count}, accuracy: {accuracy:.0f}%")
    
    # Overall accuracy
    overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\nOverall accuracy: {overall_accuracy:.1f}%")
    print(f"Target: 95%")
    print(f"Status: {'PASS' if overall_accuracy >= 95 else 'FAIL'}")
    
    # Detailed element list
    print("\nDetailed elements:")
    for i, elem in enumerate(elements[:10]):  # Show first 10
        desc = f" - {elem.description}" if elem.description else ""
        print(f"{i+1}. {elem.element_type} at {elem.bbox} (conf: {elem.confidence:.2f}){desc}")
    
    # Save visualization
    vis_image = omni_model.visualize_detection(test_image, elements)
    cv2.imwrite("tests/omniparser_detection_result.png", vis_image)
    print("\nVisualization saved to: tests/omniparser_detection_result.png")
    
    # Compare with traditional CV
    print("\n" + "="*50)
    print("Comparison with Traditional CV:")
    print(f"Traditional CV accuracy: 70%")
    print(f"OmniParser accuracy: {overall_accuracy:.1f}%")
    print(f"Improvement: {overall_accuracy - 70:.1f}%")
    
    return overall_accuracy

if __name__ == "__main__":
    accuracy = test_omniparser_accuracy()
    
    if accuracy and accuracy >= 95:
        print("\n✓ OmniParser meets the 95% accuracy requirement!")
        print("Ready to replace traditional CV implementation.")
    else:
        print("\n✗ OmniParser does not meet requirements yet.")
        print("May need model fine-tuning or configuration adjustments.")