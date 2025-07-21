"""Vision model validation module using visual analysis comparison"""

import json
import time
import numpy as np
import cv2
from .vision_model_enhanced import UIVisionModelEnhanced

class VisionValidator:
    """Validates vision model output by comparing with expected UI elements"""
    
    def __init__(self):
        self.model = UIVisionModelEnhanced(use_yolo=False, enable_ocr=False)
    
    def create_test_interface(self):
        """Create standardized test UI for validation"""
        img = np.ones((600, 900, 3), dtype=np.uint8) * 250
        
        # Window title bar
        cv2.rectangle(img, (0, 0), (900, 30), (70, 130, 180), -1)
        cv2.putText(img, "Settings Window", (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Close button
        cv2.rectangle(img, (870, 5), (895, 25), (220, 60, 60), -1)
        cv2.putText(img, "×", (880, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Text inputs
        cv2.putText(img, "Username:", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(img, (150, 65), (400, 90), (255, 255, 255), -1)
        cv2.rectangle(img, (150, 65), (400, 90), (150, 150, 150), 2)
        
        cv2.putText(img, "Email:", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(img, (150, 105), (400, 130), (255, 255, 255), -1)
        cv2.rectangle(img, (150, 105), (400, 130), (150, 150, 150), 2)
        
        # Checkboxes
        cv2.rectangle(img, (50, 160), (65, 175), (255, 255, 255), -1)
        cv2.rectangle(img, (50, 160), (65, 175), (100, 100, 100), 2)
        cv2.putText(img, "✓", (54, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 2)
        cv2.putText(img, "Enable notifications", (80, 172), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        cv2.rectangle(img, (50, 190), (65, 205), (255, 255, 255), -1)
        cv2.rectangle(img, (50, 190), (65, 205), (100, 100, 100), 2)
        cv2.putText(img, "Auto-save", (80, 202), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Radio buttons
        cv2.circle(img, (70, 240), 8, (255, 255, 255), -1)
        cv2.circle(img, (70, 240), 8, (100, 100, 100), 2)
        cv2.circle(img, (70, 240), 4, (0, 120, 200), -1)
        cv2.putText(img, "Light theme", (90, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        cv2.circle(img, (70, 270), 8, (255, 255, 255), -1)
        cv2.circle(img, (70, 270), 8, (100, 100, 100), 2)
        cv2.putText(img, "Dark theme", (90, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Dropdown
        cv2.rectangle(img, (150, 300), (300, 325), (240, 240, 240), -1)
        cv2.rectangle(img, (150, 300), (300, 325), (150, 150, 150), 2)
        cv2.putText(img, "English", (160, 318), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        cv2.putText(img, "▼", (280, 318), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (100, 100, 100), 1)
        
        # Buttons
        cv2.rectangle(img, (500, 500), (580, 530), (220, 220, 220), -1)
        cv2.rectangle(img, (500, 500), (580, 530), (150, 150, 150), 2)
        cv2.putText(img, "Cancel", (515, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        cv2.rectangle(img, (600, 500), (680, 530), (60, 140, 60), -1)
        cv2.putText(img, "Save", (625, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return img
    
    def analyze_with_vision_model(self, image):
        """Analyze image with vision model"""
        start_time = time.time()
        elements = self.model.detect_ui_elements(image)
        detection_time = time.time() - start_time
        
        results = {
            'detection_time': detection_time,
            'total_elements': len(elements),
            'elements': [],
            'type_distribution': {},
            'clickable_count': 0
        }
        
        for elem in elements:
            results['elements'].append({
                'type': elem.element_type,
                'bbox': elem.bbox,
                'center': elem.center,
                'confidence': elem.confidence,
                'clickable': elem.clickable
            })
            
            # Count types
            elem_type = elem.element_type
            results['type_distribution'][elem_type] = results['type_distribution'].get(elem_type, 0) + 1
            
            if elem.clickable:
                results['clickable_count'] += 1
        
        return results, elements
    
    def get_expected_elements(self):
        """Define expected UI elements for the test interface"""
        return {
            'window_title': 1,      # Settings Window title
            'close_button': 1,      # X button
            'text_inputs': 2,       # Username, Email fields  
            'checkboxes': 2,        # Enable notifications, Auto-save
            'radio_buttons': 2,     # Light theme, Dark theme
            'dropdown': 1,          # Language dropdown
            'buttons': 2,           # Cancel, Save buttons
            'text_labels': 6,       # Various labels
            'total_interactive': 8  # Close + 2 inputs + 2 checkboxes + 2 radios + 1 dropdown + 2 buttons
        }
    
    def save_for_visual_analysis(self, image, vision_results, elements):
        """Save files for Claude visual analysis"""
        
        # Save test image
        cv2.imwrite("cybercorp_node/test_interface.png", image)
        
        # Create visualization
        vis_image = self.model.visualize_detection_enhanced(image, elements)
        cv2.imwrite("cybercorp_node/vision_detection_result.png", vis_image)
        
        # Save results
        with open("cybercorp_node/vision_analysis_results.json", "w") as f:
            json.dump(vision_results, f, indent=2)
        
        # Create analysis prompt for Claude
        expected = self.get_expected_elements()
        analysis_prompt = f"""
Vision Model Validation Analysis

Test Image: cybercorp_node/test_interface.png
Detection Result: cybercorp_node/vision_detection_result.png
Structured Results: cybercorp_node/vision_analysis_results.json

Expected UI Elements:
- Window title bar with "Settings Window" text
- Close button (red X) in top right corner
- 2 text input fields (Username, Email)
- 2 checkboxes (one checked, one unchecked)
- 2 radio buttons (one selected, one unselected)  
- 1 dropdown menu with arrow indicator
- 2 buttons at bottom (Cancel gray, Save green)
- Various text labels

Total expected interactive elements: {expected['total_interactive']}

Vision Model Detected:
- Total elements: {vision_results['total_elements']}
- Clickable elements: {vision_results['clickable_count']}
- Element types: {vision_results['type_distribution']}
- Processing time: {vision_results['detection_time']:.3f}s

Please analyze the test image and compare with the vision model results to evaluate accuracy.
"""
        
        with open("cybercorp_node/vision_validation_prompt.txt", "w") as f:
            f.write(analysis_prompt)
        
        return {
            'test_image': 'cybercorp_node/test_interface.png',
            'detection_visualization': 'cybercorp_node/vision_detection_result.png', 
            'results_json': 'cybercorp_node/vision_analysis_results.json',
            'analysis_prompt': 'cybercorp_node/vision_validation_prompt.txt'
        }

def run_validation():
    """Run vision model validation"""
    validator = VisionValidator()
    
    print("Creating test interface...")
    test_image = validator.create_test_interface()
    
    print("Running vision model analysis...")
    vision_results, elements = validator.analyze_with_vision_model(test_image)
    
    print("Saving files for visual analysis...")
    files = validator.save_for_visual_analysis(test_image, vision_results, elements)
    
    expected = validator.get_expected_elements()
    
    print(f"\nValidation Results:")
    print(f"Detection time: {vision_results['detection_time']:.3f}s")
    print(f"Expected interactive elements: {expected['total_interactive']}")
    print(f"Detected total elements: {vision_results['total_elements']}")
    print(f"Detected clickable elements: {vision_results['clickable_count']}")
    print(f"Element types found: {vision_results['type_distribution']}")
    
    print(f"\nFiles created for Claude analysis:")
    for key, path in files.items():
        print(f"- {key}: {path}")
    
    return vision_results, expected