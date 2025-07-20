#!/usr/bin/env python3
"""Comprehensive analysis of vision model performance and information richness"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cybercorp_node'))

import json
import time
import numpy as np
import cv2
from utils.vision_model import UIVisionModel

def create_test_scenarios():
    """Create various test scenarios to evaluate comprehensively"""
    scenarios = []
    
    # Scenario 1: Simple form interface
    img1 = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img1, (50, 50), (550, 100), (240, 240, 240), -1)  # Header
    cv2.rectangle(img1, (100, 150), (400, 180), (255, 255, 255), -1)  # Input 1
    cv2.rectangle(img1, (100, 150), (400, 180), (100, 100, 100), 2)
    cv2.rectangle(img1, (100, 200), (400, 230), (255, 255, 255), -1)  # Input 2
    cv2.rectangle(img1, (100, 200), (400, 230), (100, 100, 100), 2)
    cv2.rectangle(img1, (200, 280), (300, 310), (100, 200, 100), -1)  # Button
    cv2.putText(img1, "Login Form", (220, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img1, "Username", (110, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    cv2.putText(img1, "Password", (110, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    cv2.putText(img1, "Login", (220, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    scenarios.append(("Simple Form", img1))
    
    # Scenario 2: Complex dashboard
    img2 = np.ones((800, 1200, 3), dtype=np.uint8) * 245
    
    # Top toolbar
    cv2.rectangle(img2, (0, 0), (1200, 60), (200, 200, 200), -1)
    for i in range(6):
        cv2.rectangle(img2, (20 + i*80, 15), (80 + i*80, 45), (180, 180, 180), -1)
        cv2.putText(img2, f"Tab{i+1}", (35 + i*80, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Left sidebar
    cv2.rectangle(img2, (0, 60), (250, 800), (230, 230, 230), -1)
    for i in range(8):
        cv2.rectangle(img2, (20, 80 + i*60), (230, 120 + i*60), (210, 210, 210), -1)
        cv2.putText(img2, f"Item {i+1}", (30, 105 + i*60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Main content grid
    for row in range(3):
        for col in range(3):
            x = 280 + col * 300
            y = 100 + row * 220
            cv2.rectangle(img2, (x, y), (x + 280, y + 200), (255, 255, 255), -1)
            cv2.rectangle(img2, (x, y), (x + 280, y + 200), (200, 200, 200), 2)
            cv2.putText(img2, f"Widget {row*3+col+1}", (x + 20, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
            # Add some buttons in widgets
            cv2.rectangle(img2, (x + 20, y + 150), (x + 100, y + 180), (100, 150, 200), -1)
            cv2.putText(img2, "Action", (x + 35, y + 170), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    scenarios.append(("Complex Dashboard", img2))
    
    # Scenario 3: Text-heavy document
    img3 = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    
    # Document header
    cv2.rectangle(img3, (50, 50), (750, 120), (250, 250, 250), -1)
    cv2.putText(img3, "Document Title", (60, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    # Menu bar
    cv2.rectangle(img3, (50, 130), (750, 160), (240, 240, 240), -1)
    menu_items = ["File", "Edit", "View", "Insert", "Format", "Tools"]
    for i, item in enumerate(menu_items):
        x = 70 + i * 80
        cv2.putText(img3, item, (x, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Toolbar
    cv2.rectangle(img3, (50, 170), (750, 210), (230, 230, 230), -1)
    for i in range(12):
        cv2.rectangle(img3, (70 + i*50, 180), (110 + i*50, 200), (200, 200, 200), -1)
    
    # Main text area
    cv2.rectangle(img3, (50, 220), (750, 950), (255, 255, 255), -1)
    cv2.rectangle(img3, (50, 220), (750, 950), (180, 180, 180), 2)
    
    # Simulate text content
    for i in range(25):
        y = 250 + i * 25
        cv2.line(img3, (70, y), (730, y), (200, 200, 200), 1)
    
    scenarios.append(("Text Document", img3))
    
    return scenarios

def analyze_performance_comprehensive():
    """Comprehensive performance analysis"""
    print("Vision Model Performance Analysis")
    print("=" * 50)
    
    model = UIVisionModel(use_yolo=False)
    scenarios = create_test_scenarios()
    
    overall_results = {
        "scenarios": [],
        "summary": {}
    }
    
    total_time = 0
    total_elements = 0
    
    for name, image in scenarios:
        print(f"\nAnalyzing scenario: {name}")
        print(f"Image size: {image.shape}")
        
        # Performance test
        times = []
        element_counts = []
        
        for i in range(5):  # 5 iterations per scenario
            start = time.time()
            elements = model.detect_ui_elements(image)
            elapsed = time.time() - start
            times.append(elapsed)
            element_counts.append(len(elements))
        
        avg_time = np.mean(times)
        std_time = np.std(times)
        avg_elements = np.mean(element_counts)
        
        print(f"  Average time: {avg_time:.3f}s (±{std_time:.3f}s)")
        print(f"  Average FPS: {1/avg_time:.1f}")
        print(f"  Elements detected: {avg_elements:.1f}")
        
        # Structure analysis
        ui_structure = model.extract_ui_structure(image, include_ocr=False)
        
        # Element type distribution
        type_counts = {}
        for elem in ui_structure['elements']:
            elem_type = elem['type']
            type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
        
        print(f"  Element types: {type_counts}")
        
        # Save visualization
        vis_image = model.visualize_detection(image, elements)
        filename = f"analysis_{name.lower().replace(' ', '_')}.png"
        cv2.imwrite(filename, vis_image)
        print(f"  Saved visualization: {filename}")
        
        scenario_result = {
            "name": name,
            "image_size": image.shape,
            "performance": {
                "avg_time": avg_time,
                "std_time": std_time,
                "fps": 1/avg_time,
                "avg_elements": avg_elements
            },
            "structure": {
                "total_elements": len(ui_structure['elements']),
                "element_types": type_counts,
                "hierarchy_depth": len(ui_structure.get('hierarchy', []))
            }
        }
        
        overall_results["scenarios"].append(scenario_result)
        total_time += avg_time
        total_elements += avg_elements
    
    # Overall summary
    overall_results["summary"] = {
        "total_scenarios": len(scenarios),
        "avg_time_across_scenarios": total_time / len(scenarios),
        "avg_elements_across_scenarios": total_elements / len(scenarios),
        "overall_fps": len(scenarios) / total_time
    }
    
    return overall_results

def evaluate_information_richness():
    """Evaluate the richness and usefulness of extracted information"""
    print("\n" + "=" * 50)
    print("Information Richness Analysis")
    print("=" * 50)
    
    model = UIVisionModel(use_yolo=False)
    
    # Create a feature-rich test image
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 240
    
    # Complex UI with various elements
    elements_added = []
    
    # Title bar
    cv2.rectangle(test_image, (0, 0), (800, 40), (100, 150, 200), -1)
    cv2.putText(test_image, "Application Window", (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    elements_added.append("title_bar")
    
    # Menu bar
    cv2.rectangle(test_image, (0, 40), (800, 70), (220, 220, 220), -1)
    menus = ["File", "Edit", "View", "Tools", "Help"]
    for i, menu in enumerate(menus):
        cv2.putText(test_image, menu, (20 + i*80, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        elements_added.append(f"menu_{menu.lower()}")
    
    # Toolbar with buttons
    cv2.rectangle(test_image, (0, 70), (800, 110), (200, 200, 200), -1)
    for i in range(10):
        x = 20 + i * 60
        cv2.rectangle(test_image, (x, 80), (x + 40, 100), (180, 180, 180), -1)
        elements_added.append(f"toolbar_button_{i}")
    
    # Left sidebar with tree structure
    cv2.rectangle(test_image, (0, 110), (200, 600), (230, 230, 230), -1)
    for i in range(12):
        y = 130 + i * 35
        indent = 20 if i % 3 == 0 else 40  # Create hierarchy
        cv2.rectangle(test_image, (indent, y), (180, y + 25), (210, 210, 210), -1)
        cv2.putText(test_image, f"Item {i+1}", (indent + 5, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        elements_added.append(f"sidebar_item_{i}")
    
    # Main content area with form
    cv2.rectangle(test_image, (220, 110), (780, 500), (255, 255, 255), -1)
    cv2.rectangle(test_image, (220, 110), (780, 500), (150, 150, 150), 2)
    
    # Form fields
    form_fields = [
        ("Name:", 250, 150),
        ("Email:", 250, 200),
        ("Phone:", 250, 250),
        ("Message:", 250, 300)
    ]
    
    for label, x, y in form_fields:
        cv2.putText(test_image, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.rectangle(test_image, (x + 80, y - 15), (x + 400, y + 10), (255, 255, 255), -1)
        cv2.rectangle(test_image, (x + 80, y - 15), (x + 400, y + 10), (100, 100, 100), 1)
        elements_added.append(f"input_{label[:-1].lower()}")
    
    # Buttons
    cv2.rectangle(test_image, (400, 420), (500, 450), (100, 200, 100), -1)
    cv2.putText(test_image, "Submit", (420, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    elements_added.append("submit_button")
    
    cv2.rectangle(test_image, (520, 420), (620, 450), (200, 100, 100), -1)
    cv2.putText(test_image, "Cancel", (540, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    elements_added.append("cancel_button")
    
    # Status bar
    cv2.rectangle(test_image, (0, 500), (800, 600), (180, 180, 180), -1)
    cv2.putText(test_image, "Status: Ready | Elements: 15 | Memory: 45MB", (20, 555), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    elements_added.append("status_bar")
    
    print(f"Created test image with {len(elements_added)} intentional UI elements")
    
    # Analyze with vision model
    ui_structure = model.extract_ui_structure(test_image, include_ocr=False)
    detected_elements = ui_structure['elements']
    
    print(f"Vision model detected: {len(detected_elements)} elements")
    print(f"Detection ratio: {len(detected_elements)/len(elements_added)*100:.1f}%")
    
    # Analyze element types
    detected_types = {}
    for elem in detected_elements:
        elem_type = elem['type']
        detected_types[elem_type] = detected_types.get(elem_type, 0) + 1
    
    print(f"Detected element types: {detected_types}")
    
    # Check for actionable elements
    actionable = [e for e in detected_elements if e['type'] in ['button', 'input', 'menu_item']]
    print(f"Actionable elements detected: {len(actionable)}")
    
    # Evaluate spatial understanding
    regions = ui_structure.get('layout_structure', {}).get('regions', [])
    print(f"Spatial regions identified: {len(regions)}")
    for region in regions:
        print(f"  - {region['type']}: {region['element_count']} elements")
    
    # Save detailed analysis
    cv2.imwrite("information_richness_test.png", test_image)
    
    # Create visualization
    elements = model.detect_ui_elements(test_image)
    vis_image = model.visualize_detection(test_image, elements)
    cv2.imwrite("information_richness_analysis.png", vis_image)
    
    return {
        "intended_elements": len(elements_added),
        "detected_elements": len(detected_elements),
        "detection_ratio": len(detected_elements)/len(elements_added),
        "element_types": detected_types,
        "actionable_elements": len(actionable),
        "spatial_regions": len(regions)
    }

def main():
    """Main analysis function"""
    print("Comprehensive Vision Model Analysis")
    print("=" * 60)
    
    # Performance analysis
    perf_results = analyze_performance_comprehensive()
    
    # Information richness analysis
    info_results = evaluate_information_richness()
    
    # Combined analysis
    print("\n" + "=" * 60)
    print("FINAL ASSESSMENT")
    print("=" * 60)
    
    print("\nPERFORMACE METRICS:")
    summary = perf_results["summary"]
    print(f"  Average processing time: {summary['avg_time_across_scenarios']:.3f}s")
    print(f"  Average FPS: {summary['overall_fps']:.1f}")
    print(f"  Average elements per scenario: {summary['avg_elements_across_scenarios']:.1f}")
    
    print("\nINFORMATION RICHNESS:")
    print(f"  Detection accuracy: {info_results['detection_ratio']*100:.1f}%")
    print(f"  Element type diversity: {len(info_results['element_types'])} types")
    print(f"  Actionable elements ratio: {info_results['actionable_elements']/info_results['detected_elements']*100:.1f}%")
    print(f"  Spatial understanding: {info_results['spatial_regions']} regions")
    
    print("\nASSESSMENT CONCLUSION:")
    
    # Performance assessment
    avg_fps = summary['overall_fps']
    if avg_fps > 30:
        perf_grade = "EXCELLENT"
    elif avg_fps > 10:
        perf_grade = "GOOD"
    elif avg_fps > 5:
        perf_grade = "FAIR"
    else:
        perf_grade = "POOR"
    
    # Information richness assessment
    detection_ratio = info_results['detection_ratio']
    type_diversity = len(info_results['element_types'])
    
    if detection_ratio > 0.7 and type_diversity >= 5:
        info_grade = "EXCELLENT"
    elif detection_ratio > 0.5 and type_diversity >= 4:
        info_grade = "GOOD"
    elif detection_ratio > 0.3 and type_diversity >= 3:
        info_grade = "FAIR"
    else:
        info_grade = "POOR"
    
    print(f"  Performance Grade: {perf_grade}")
    print(f"  Information Grade: {info_grade}")
    
    # Save full results
    full_results = {
        "performance": perf_results,
        "information_richness": info_results,
        "assessment": {
            "performance_grade": perf_grade,
            "information_grade": info_grade,
            "overall_ready": perf_grade in ["EXCELLENT", "GOOD"] and info_grade in ["EXCELLENT", "GOOD"]
        }
    }
    
    with open("vision_analysis_full_results.json", "w") as f:
        json.dump(full_results, f, indent=2)
    
    print(f"\nGenerated files:")
    print(f"  - vision_analysis_full_results.json (complete analysis)")
    print(f"  - information_richness_test.png (test image)")
    print(f"  - information_richness_analysis.png (detection visualization)")
    
    for scenario in perf_results["scenarios"]:
        name = scenario["name"].lower().replace(" ", "_")
        print(f"  - analysis_{name}.png (scenario visualization)")

if __name__ == "__main__":
    main()