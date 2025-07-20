"""Test optimized vision model accuracy"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import cv2
import logging
from cybercorp_node.utils.vision_validator import VisionValidator
from cybercorp_node.utils.vision_model_optimized import UIVisionModelOptimized

# Enable debug logging
logging.basicConfig(level=logging.INFO)

def test_optimized_accuracy():
    """Test optimized model targeting 95% accuracy"""
    print("Testing Optimized Vision Model (Target: 95%)")
    print("=" * 50)
    
    # Create test UI
    validator = VisionValidator()
    test_image = validator.create_test_interface()
    
    # Initialize optimized model
    print("Initializing optimized model...")
    model = UIVisionModelOptimized()
    
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
    
    print(f"Element types detected: {type_counts}")
    
    # Expected elements
    expected = {
        'button': 3,
        'input': 2,
        'checkbox': 2,
        'radio': 2,
        'dropdown': 1,
    }
    
    print(f"Expected element counts: {expected}")
    
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
        status = "✓ PASS" if detected_count == expected_count else "✗ FAIL"
        print(f"{status} {elem_type:10} expected: {expected_count}, detected: {detected_count}, accuracy: {accuracy:.0f}%")
    
    overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\nOverall accuracy: {overall_accuracy:.1f}%")
    print(f"Target accuracy: 95%")
    status = "🎉 PASS" if overall_accuracy >= 95 else "❌ FAIL"
    print(f"Final status: {status}")
    
    # Detailed element information
    print("\nDetailed detection results:")
    for i, elem in enumerate(elements):
        print(f"{i+1}. {elem.element_type:10} at {elem.bbox} (conf: {elem.confidence:.2f})")
    
    # Save visualization
    vis_image = test_image.copy()
    for elem in elements:
        x1, y1, x2, y2 = elem.bbox
        color = (0, 255, 0) if elem.clickable else (255, 0, 0)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis_image, f"{elem.element_type} ({elem.confidence:.2f})", 
                   (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    cv2.imwrite("tests/optimized_detection_result.png", vis_image)
    print("\nVisualization saved to: tests/optimized_detection_result.png")
    
    # Performance comparison
    print("\n" + "="*50)
    print("Performance Comparison:")
    print(f"Previous model (enhanced): 70% accuracy")
    print(f"Optimized model: {overall_accuracy:.1f}% accuracy")
    improvement = overall_accuracy - 70
    print(f"Improvement: {improvement:+.1f}%")
    
    if overall_accuracy >= 95:
        print("\n🎯 SUCCESS: Achieved 95% accuracy target!")
        print("Ready for computer-use functionality!")
    else:
        print(f"\n⚠️  Need {95 - overall_accuracy:.1f}% more improvement to reach target")
    
    return overall_accuracy

if __name__ == "__main__":
    accuracy = test_optimized_accuracy()
    print(f"\nFinal result: {accuracy:.1f}% accuracy")