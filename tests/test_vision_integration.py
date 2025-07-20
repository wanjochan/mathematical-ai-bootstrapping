"""Test vision integration with cybercorp_node"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import cv2
import numpy as np
from cybercorp_node.utils.vision_integration import VisionWindowAnalyzer
from cybercorp_node.utils.vision_validator import VisionValidator

async def test_vision_integration():
    """Test integrated vision system accuracy"""
    print("Testing Vision Integration with cybercorp_node")
    print("=" * 50)
    
    # Create test UI
    validator = VisionValidator()
    test_image = validator.create_test_interface()
    
    # Create analyzer without controller (for testing)
    analyzer = VisionWindowAnalyzer(controller=None)
    
    # Test direct vision model
    print("Testing optimized vision model...")
    elements = analyzer.vision_model.detect_ui_elements(test_image)
    
    print(f"Detected {len(elements)} elements:")
    
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
    
    print("\nAccuracy verification:")
    for elem_type in expected:
        expected_count = expected[elem_type]
        detected_count = type_counts.get(elem_type, 0)
        correct = min(expected_count, detected_count)
        total_correct += correct
        accuracy = (correct / expected_count * 100) if expected_count > 0 else 0
        status = "✓ PASS" if detected_count == expected_count else "✗ FAIL"
        print(f"{status} {elem_type:10} expected: {expected_count}, detected: {detected_count}")
    
    overall_accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
    print(f"\nOverall accuracy: {overall_accuracy:.1f}%")
    
    # Test conversion to dict format
    print("\nTesting element conversion...")
    dict_elements = [analyzer._convert_element_to_dict(elem) for elem in elements]
    print(f"Successfully converted {len(dict_elements)} elements to dict format")
    
    # Test visualization
    print("\nTesting visualization...")
    vis_image = analyzer._create_visualization(test_image, elements)
    cv2.imwrite("tests/vision_integration_test.png", vis_image)
    print("Visualization saved to: tests/vision_integration_test.png")
    
    # Test analysis structure
    print("\nTesting UI structure creation...")
    ui_structure = {
        'elements': dict_elements
    }
    
    result = analyzer._build_analysis_result(12345, ui_structure, test_image)
    print(f"Analysis result created for window {result.window_hwnd}")
    print(f"Content summary: {result.content_summary}")
    print(f"Interaction points: {len(result.interaction_points)}")
    
    # Final result
    success = overall_accuracy >= 95
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Integration test {'passed' if success else 'failed'}")
    print(f"Accuracy: {overall_accuracy:.1f}% (target: ≥95%)")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(test_vision_integration())
    sys.exit(0 if success else 1)