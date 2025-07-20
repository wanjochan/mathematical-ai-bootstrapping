"""Demo to understand OmniParser's actual output for computer-use"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from cybercorp_node.utils.vision_validator import VisionValidator
from cybercorp_node.utils.vision_model_omniparser import UIVisionModelOmniParser

def demo_omniparser_output():
    """Show what OmniParser actually outputs for computer-use"""
    print("OmniParser Computer-Use Demo")
    print("=" * 50)
    print("\nOmniParser is designed for computer-use by:")
    print("1. Detecting ALL interactable regions (not classifying types)")
    print("2. Providing functional descriptions for each region")
    print("3. Letting LLMs decide what to do based on descriptions")
    print("\n" + "=" * 50)
    
    # Create test UI
    validator = VisionValidator()
    test_image = validator.create_test_interface()
    
    # Initialize OmniParser
    try:
        print("\nInitializing OmniParser...")
        omni_model = UIVisionModelOmniParser()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return
    
    # Run detection
    print("Running detection...")
    elements = omni_model.detect_ui_elements(test_image)
    
    print(f"\nTotal interactable regions found: {len(elements)}")
    print("\nOmniParser Output (for LLM interpretation):")
    print("-" * 50)
    
    # Show what OmniParser provides to LLMs
    for i, elem in enumerate(elements):
        print(f"\nRegion {i+1}:")
        print(f"  Location: {elem.bbox}")
        print(f"  Center: {elem.center}")
        print(f"  Confidence: {elem.confidence:.2f}")
        print(f"  Type: {elem.element_type}")  # This is 'icon' for all
        if elem.description:
            print(f"  Function: {elem.description}")  # This should describe what it does
        else:
            print(f"  Function: [No caption - caption model not loaded]")
    
    print("\n" + "=" * 50)
    print("\nKey Insight:")
    print("- OmniParser doesn't classify UI elements (button/input/checkbox)")
    print("- It finds ALL clickable regions and describes their function")
    print("- LLMs use these descriptions to understand what each region does")
    print("- This is why it's perfect for computer-use scenarios!")
    
    # Save visualization
    vis_image = omni_model.visualize_detection(test_image, elements)
    cv2.imwrite("tests/omniparser_demo_output.png", vis_image)
    print("\nVisualization saved to: tests/omniparser_demo_output.png")

if __name__ == "__main__":
    demo_omniparser_output()