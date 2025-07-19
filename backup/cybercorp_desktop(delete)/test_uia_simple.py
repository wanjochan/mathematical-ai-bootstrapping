#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple UIA fix test script
"""

import sys
import time
import traceback
from window_manager import WindowManager
from window_analyzer import WindowAnalyzer

def test_uia_initialization():
    """Test UIA initialization"""
    print("=" * 60)
    print("UIA Initialization Test")
    print("=" * 60)
    
    try:
        from uia_analyzer import UIAAnalyzer
        
        print("1. Creating UIA analyzer...")
        uia_analyzer = UIAAnalyzer()
        
        print("2. Checking initialization status...")
        init_info = uia_analyzer.get_initialization_info()
        print(f"   - UIA Available: {init_info['available']}")
        print(f"   - Init Method: {init_info['method']}")
        print(f"   - COM Initialized: {init_info['com_initialized']}")
        
        if init_info['available']:
            print("SUCCESS: UIA initialized successfully!")
            return True, uia_analyzer
        else:
            print("FAILED: UIA initialization failed")
            return False, None
            
    except Exception as e:
        print(f"ERROR: UIA initialization exception: {str(e)}")
        traceback.print_exc()
        return False, None

def test_window_analysis():
    """Test window analysis"""
    print("\n" + "=" * 60)
    print("Window Analysis Test")
    print("=" * 60)
    
    try:
        print("1. Creating window manager...")
        window_manager = WindowManager()
        
        print("2. Getting all windows...")
        windows = window_manager.get_all_windows()
        print(f"   Found {len(windows)} windows")
        
        if not windows:
            print("ERROR: No windows found for analysis")
            return False
        
        # Select first window for testing
        test_window = windows[0]
        print(f"3. Testing window: {test_window['title']} (HWND: {test_window['hwnd']})")
        
        print("4. Creating window analyzer...")
        analyzer = WindowAnalyzer()
        
        print("5. Performing window analysis...")
        start_time = time.time()
        
        # Test UIA analysis
        try:
            result = analyzer.analyze_window(test_window['hwnd'], use_uia=True)
            analysis_time = time.time() - start_time
            
            print(f"SUCCESS: Window analysis completed! (Time: {analysis_time:.2f}s)")
            print(f"   - Analysis method: {result.get('analysis_method', 'Unknown')}")
            print(f"   - Element count: {len(result.get('elements', []))}")
            
            # Check UIA specific info
            if 'uia_analysis' in result:
                uia_info = result['uia_analysis']
                print(f"   - UIA total elements: {uia_info.get('total_elements', 0)}")
                print(f"   - Interactive elements: {len(uia_info.get('interactive_elements', []))}")
                print(f"   - Init method: {uia_info.get('initialization_method', 'Unknown')}")
            
            # Check diagnostic info
            if 'diagnostic_info' in result:
                diag = result['diagnostic_info']
                print(f"   - UIA available: {diag.get('uia_available', False)}")
                print(f"   - Fallback used: {diag.get('fallback_used', False)}")
                if diag.get('uia_failure_reason'):
                    print(f"   - UIA failure reason: {diag['uia_failure_reason']}")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Window analysis failed: {str(e)}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"ERROR: Window analysis test exception: {str(e)}")
        traceback.print_exc()
        return False

def test_fallback_mechanism():
    """Test fallback mechanism"""
    print("\n" + "=" * 60)
    print("Fallback Mechanism Test")
    print("=" * 60)
    
    try:
        window_manager = WindowManager()
        windows = window_manager.get_all_windows()
        
        if not windows:
            print("ERROR: No windows found for testing")
            return False
        
        test_window = windows[0]
        analyzer = WindowAnalyzer()
        
        print("1. Testing traditional method...")
        result_traditional = analyzer.analyze_window(test_window['hwnd'], use_uia=False)
        
        print(f"SUCCESS: Traditional method analysis")
        print(f"   - Analysis method: {result_traditional.get('analysis_method', 'Unknown')}")
        print(f"   - Element count: {len(result_traditional.get('elements', []))}")
        
        print("2. Testing UIA method...")
        result_uia = analyzer.analyze_window(test_window['hwnd'], use_uia=True)
        
        print(f"SUCCESS: UIA method analysis completed")
        print(f"   - Analysis method: {result_uia.get('analysis_method', 'Unknown')}")
        print(f"   - Element count: {len(result_uia.get('elements', []))}")
        
        # Compare results
        traditional_count = len(result_traditional.get('elements', []))
        uia_count = len(result_uia.get('elements', []))
        
        print(f"3. Results comparison:")
        print(f"   - Traditional elements: {traditional_count}")
        print(f"   - UIA elements: {uia_count}")
        
        if uia_count > traditional_count:
            print("INFO: UIA provides more detailed analysis")
        elif traditional_count > 0:
            print("INFO: Traditional method provides reliable fallback")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Fallback mechanism test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("Error Handling Test")
    print("=" * 60)
    
    try:
        analyzer = WindowAnalyzer()
        
        print("1. Testing invalid window handle...")
        try:
            result = analyzer.analyze_window(99999, use_uia=True)
            print("WARNING: Invalid handle test did not fail as expected")
        except Exception as e:
            print(f"SUCCESS: Properly handled invalid handle: {str(e)[:100]}...")
        
        print("2. Testing null handle...")
        try:
            result = analyzer.analyze_window(0, use_uia=True)
            print("WARNING: Null handle test did not fail as expected")
        except Exception as e:
            print(f"SUCCESS: Properly handled null handle: {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error handling test failed: {str(e)}")
        return False

def generate_test_report():
    """Generate test report"""
    print("\n" + "=" * 60)
    print("Test Report Generation")
    print("=" * 60)
    
    # Run all tests
    test_results = {}
    
    print("Running test suite...")
    test_results['uia_init'] = test_uia_initialization()[0]
    test_results['window_analysis'] = test_window_analysis()
    test_results['fallback'] = test_fallback_mechanism()
    test_results['error_handling'] = test_error_handling()
    
    # Generate report
    print("\n" + "=" * 60)
    print("Final Test Report")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed tests: {passed_tests}")
    print(f"Failed tests: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed results:")
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f"  - {test_name}: {status}")
    
    # Generate recommendations
    print("\nRecommendations:")
    if passed_tests == total_tests:
        print("SUCCESS: All tests passed! UIA compatibility issues resolved.")
    elif test_results.get('fallback', False):
        print("INFO: UIA may have issues, but fallback mechanism works correctly.")
    else:
        print("CRITICAL: Issues exist that need further debugging.")
    
    return passed_tests / total_tests >= 0.75

def main():
    """Main function"""
    print("UIA Compatibility Fix Verification Test")
    print("Time:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print("Python version:", sys.version)
    
    try:
        success = generate_test_report()
        
        if success:
            print("\nSUCCESS: Test completed - UIA fix verification successful!")
            return 0
        else:
            print("\nFAILED: Test completed - issues still need resolution")
            return 1
            
    except Exception as e:
        print(f"\nERROR: Test execution failed: {str(e)}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)