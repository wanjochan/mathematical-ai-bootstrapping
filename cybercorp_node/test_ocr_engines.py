"""Test and benchmark different OCR engines"""

import os
import sys
import time
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ocr_backend import OCRBackend


def create_test_image():
    """Create a test image with various text elements"""
    # Create image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add various text elements
    texts = [
        ("CyberCorp Node System", (50, 50), font_large, 'black'),
        ("OCR Engine Test", (50, 100), font_medium, 'blue'),
        ("Hello World! 你好世界！", (50, 150), font_medium, 'black'),
        ("1234567890", (50, 200), font_medium, 'red'),
        ("test@example.com", (50, 250), font_small, 'green'),
        ("Button Text", (600, 50), font_medium, 'black'),
        ("验证码: ABC123", (50, 300), font_medium, 'black'),
        ("拖动滑块完成验证", (50, 350), font_small, 'gray'),
    ]
    
    for text, pos, font, color in texts:
        draw.text(pos, text, font=font, fill=color)
    
    # Add some UI elements
    # Button
    draw.rectangle([580, 40, 750, 80], outline='black', width=2)
    
    # Input box
    draw.rectangle([50, 400, 400, 440], outline='gray', width=1)
    draw.text((60, 410), "Type here...", font=font_small, fill='gray')
    
    return img


def test_ocr_engines():
    """Test all available OCR engines"""
    print("=" * 60)
    print("OCR Engine Testing")
    print("=" * 60)
    
    # Initialize OCR backend
    ocr = OCRBackend()
    
    if not ocr.available_engines:
        print("No OCR engines available! Please install at least one:")
        print("- pip install easyocr")
        print("- pip install pytesseract")
        print("- pip install paddlepaddle paddleocr")
        print("- For Windows OCR: pip install winsdk")
        return
    
    # Create test image
    print("\nCreating test image...")
    test_img = create_test_image()
    test_img.save("test_ocr_image.png")
    print("Test image saved as: test_ocr_image.png")
    
    # Test each engine
    print("\nTesting individual engines:")
    print("-" * 60)
    
    results = {}
    
    for engine_name in ocr.available_engines:
        print(f"\nTesting {engine_name}...")
        
        start_time = time.time()
        
        try:
            detections = ocr.detect_text(test_img, engine=engine_name)
            elapsed = time.time() - start_time
            
            print(f"✓ Success! Time: {elapsed:.2f}s")
            print(f"  Detected {len(detections)} text regions")
            
            # Show first few detections
            for i, det in enumerate(detections[:3]):
                print(f"  [{i+1}] '{det['text']}' (confidence: {det.get('confidence', 'N/A')})")
            
            if len(detections) > 3:
                print(f"  ... and {len(detections) - 3} more")
            
            results[engine_name] = {
                'success': True,
                'time': elapsed,
                'detections': detections
            }
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            results[engine_name] = {
                'success': False,
                'error': str(e)
            }
    
    # Benchmark all engines
    print("\n" + "=" * 60)
    print("Benchmarking all engines...")
    print("-" * 60)
    
    benchmark_results = ocr.benchmark(test_img)
    
    print("\nBenchmark Results:")
    print(f"{'Engine':<15} {'Status':<10} {'Time (s)':<10} {'Detections':<12} {'Characters'}")
    print("-" * 60)
    
    for engine, result in benchmark_results.items():
        if result['success']:
            print(f"{engine:<15} {'Success':<10} {result['time']:<10.3f} {result['detections']:<12} {result['total_chars']}")
        else:
            print(f"{engine:<15} {'Failed':<10} {'-':<10} {'-':<12} -")
    
    # Test merged results
    print("\n" + "=" * 60)
    print("Testing merged results from all engines...")
    print("-" * 60)
    
    merged_detections = ocr.detect_text(test_img, merge_results=True)
    print(f"Merged detections: {len(merged_detections)}")
    
    # Save results
    output_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'available_engines': list(ocr.available_engines.keys()),
        'individual_results': results,
        'benchmark': benchmark_results,
        'merged_detections': merged_detections
    }
    
    with open('ocr_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\nResults saved to: ocr_test_results.json")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("-" * 60)
    
    if benchmark_results:
        # Find fastest engine
        fastest = min(
            [(e, r['time']) for e, r in benchmark_results.items() if r['success']],
            key=lambda x: x[1],
            default=(None, None)
        )
        
        if fastest[0]:
            print(f"Fastest engine: {fastest[0]} ({fastest[1]:.3f}s)")
        
        # Find most accurate (most detections)
        most_accurate = max(
            [(e, r['detections']) for e, r in benchmark_results.items() if r['success']],
            key=lambda x: x[1],
            default=(None, None)
        )
        
        if most_accurate[0]:
            print(f"Most detections: {most_accurate[0]} ({most_accurate[1]} detections)")
    
    print("\nFor CyberCorp Node usage:")
    print("- Primary: Windows OCR (if available) - fastest for UI text")
    print("- Fallback: EasyOCR - good balance of speed and accuracy")
    print("- Chinese text: PaddleOCR - optimized for Chinese")
    print("- Complex scenes: Merge results from multiple engines")


def test_specific_scenario():
    """Test OCR on specific UI scenarios"""
    print("\n" + "=" * 60)
    print("Testing specific UI scenarios...")
    print("-" * 60)
    
    ocr = OCRBackend()
    
    # Test 1: Button detection
    print("\n1. Button text detection:")
    # Would need actual screenshot of buttons
    
    # Test 2: Chinese UI elements
    print("\n2. Chinese UI text:")
    # Would need actual Chinese UI screenshot
    
    # Test 3: Small text / status bar
    print("\n3. Small text detection:")
    # Would need actual status bar screenshot
    
    print("\n(Note: For real scenario testing, provide actual UI screenshots)")


if __name__ == "__main__":
    # Run tests
    test_ocr_engines()
    test_specific_scenario()
    
    # Cleanup
    if os.path.exists("test_ocr_image.png"):
        print("\nCleaning up test image...")
        # Keep for inspection
        # os.remove("test_ocr_image.png")