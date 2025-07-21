"""Test script for vision integration system"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

from utils.vision_integration import VisionWindowAnalyzer, analyze_window_quick, find_ui_element
from utils.remote_control import RemoteController


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_vision_integration():
    """Test the vision integration system"""
    logger.info("Starting vision integration test")
    
    try:
        # Initialize controller
        controller = RemoteController('ws://localhost:9998')
        await controller.connect('vision_test')
        
        # Find a client to test with
        client_id = await controller.find_client('main')
        if not client_id:
            logger.error("No 'main' client found. Looking for any available client...")
            # List all clients for debugging
            await controller.execute_command('list_clients')
            return
            
        logger.info(f"Using client: {client_id}")
        
        # Initialize vision analyzer
        analyzer = VisionWindowAnalyzer(controller)
        
        # Test 1: Analyze active window
        logger.info("=== Test 1: Analyzing active window ===")
        result = await analyzer.analyze_active_window()
        
        if result:
            print(f"Active window: {result.window_title}")
            print(f"Total elements found: {result.content_summary['total_elements']}")
            print(f"Layout type: {result.content_summary['layout_type']}")
            print(f"Interaction points: {len(result.interaction_points)}")
            
            # Save analysis result
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_file = f"vision_analysis_{timestamp}.json"
            with open(result_file, 'w') as f:
                json.dump(analyzer.export_analysis(result, 'json'), f, indent=2)
            logger.info(f"Analysis saved to: {result_file}")
            
        else:
            logger.warning("No active window found or analysis failed")
            
        # Test 2: Find all windows and analyze specific one
        logger.info("=== Test 2: Analyzing specific windows ===")
        windows = await controller.get_windows()
        logger.info(f"Found {len(windows)} windows")
        
        for window in windows[:3]:  # Test first 3 windows
            logger.info(f"Analyzing window: {window.get('title', 'Unknown')}")
            
            analysis = await analyzer.analyze_window(window['hwnd'], save_visualization=True)
            if analysis:
                summary = analyzer.export_analysis(analysis, 'summary')
                print(summary)
                print("-" * 50)
                
        # Test 3: Find clickable elements
        logger.info("=== Test 3: Finding clickable elements ===")
        if windows:
            test_window = windows[0]
            clickable = await analyzer.find_clickable_elements(test_window['hwnd'])
            
            print(f"Found {len(clickable)} clickable elements in {test_window.get('title', 'Unknown')}")
            for i, elem in enumerate(clickable[:5]):  # Show first 5
                print(f"  {i+1}. {elem['type']} at ({elem['center'][0]}, {elem['center'][1]})")
                
        # Test 4: Find text regions
        logger.info("=== Test 4: Finding text regions ===")
        if windows:
            text_regions = await analyzer.find_text_regions(test_window['hwnd'])
            print(f"Found {len(text_regions)} text regions")
            
        # Test 5: Get layout structure
        logger.info("=== Test 5: Getting layout structure ===")
        if windows:
            layout = await analyzer.get_window_layout(test_window['hwnd'])
            print(f"Layout structure: {json.dumps(layout, indent=2)}")
            
        # Test 6: Quick analysis function
        logger.info("=== Test 6: Quick analysis function ===")
        if windows:
            quick_result = await analyze_window_quick(test_window['hwnd'], controller)
            if quick_result:
                print(f"Quick analysis completed for {quick_result['window_title']}")
                
        # Test 7: Find specific UI element
        logger.info("=== Test 7: Finding specific UI elements ===")
        if windows:
            button = await find_ui_element(test_window['hwnd'], 'button', controller)
            if button:
                print(f"Found button at: {button['center']}")
            else:
                print("No button found in this window")
                
        logger.info("Vision integration test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        if 'controller' in locals():
            await controller.close()


async def test_vision_model_only():
    """Test vision model without remote controller"""
    logger.info("Testing vision model standalone")
    
    from utils.vision_model import UIVisionModel
    import cv2
    import numpy as np
    
    # Create test model
    model = UIVisionModel(use_yolo=False)
    
    # Create a synthetic test image
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw some UI elements
    cv2.rectangle(test_image, (100, 100), (200, 130), (200, 200, 200), -1)  # Button
    cv2.rectangle(test_image, (250, 100), (450, 130), (240, 240, 240), 2)   # Input
    cv2.rectangle(test_image, (100, 200), (700, 500), (220, 220, 220), 2)   # Panel
    
    # Add text
    cv2.putText(test_image, "Button", (120, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(test_image, "Text Input", (260, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Test detection
    elements = model.detect_ui_elements(test_image)
    logger.info(f"Detected {len(elements)} elements in synthetic image")
    
    # Test UI structure extraction
    ui_structure = model.extract_ui_structure(test_image)
    logger.info(f"UI structure: {json.dumps(ui_structure, indent=2)}")
    
    # Test visualization
    vis_image = model.visualize_detection(test_image, elements)
    cv2.imwrite("test_vision_model_output.png", vis_image)
    logger.info("Test visualization saved as test_vision_model_output.png")
    
    # Test benchmark
    benchmark = model.benchmark(test_image, iterations=5)
    logger.info(f"Benchmark results: {benchmark}")


async def main():
    """Main test function"""
    print("Vision Integration Test Suite")
    print("=" * 40)
    
    choice = input("Choose test:\n1. Full integration test (requires server)\n2. Vision model only\n3. Both\nChoice (1/2/3): ")
    
    if choice in ['1', '3']:
        print("\nRunning full integration test...")
        await test_vision_integration()
        
    if choice in ['2', '3']:
        print("\nRunning vision model standalone test...")
        await test_vision_model_only()
        
    print("\nTest suite completed!")


if __name__ == "__main__":
    asyncio.run(main())