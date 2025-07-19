#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hot Reload API Server Stability Test Script
Verifies all fixes and improvements
"""

import requests
import time
import json
import threading
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hot_reload import global_reloader, global_api
from logger import app_logger


class HotReloadAPITester:
    """Hot Reload API Tester"""
    
    def __init__(self, base_url: str = "http://localhost:8889"):
        self.base_url = base_url
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Record test results"""
        result = {
            'test': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_server_startup(self) -> bool:
        """Test server startup"""
        print("\n=== Testing Server Startup ===")
        
        try:
            # Use a different port to avoid conflicts
            global_api.port = 8889
            start_time = time.time()
            success = global_api.start_api_server()
            startup_time = time.time() - start_time
            
            if success and global_api.is_running:
                self.log_result("Server Startup", True, {
                    "startup_time": f"{startup_time:.3f}s",
                    "port": global_api.port,
                    "running": global_api.is_running
                })
                return True
            else:
                self.log_result("Server Startup", False, {
                    "error": "Failed to start server",
                    "running": global_api.is_running
                })
                return False
                
        except Exception as e:
            self.log_result("Server Startup", False, {"error": str(e)})
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints"""
        print("\n=== Testing API Endpoints ===")
        all_passed = True
        
        # Test status endpoint
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("GET /status", True, {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s",
                    "data": data
                })
            else:
                self.log_result("GET /status", False, {
                    "status_code": response.status_code
                })
                all_passed = False
                
        except Exception as e:
            self.log_result("GET /status", False, {"error": str(e)})
            all_passed = False
        
        # Test health check endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_result("GET /health", True, {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_result("GET /health", False, {
                    "status_code": response.status_code
                })
                all_passed = False
                
        except Exception as e:
            self.log_result("GET /health", False, {"error": str(e)})
            all_passed = False
        
        # Test metrics endpoint
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            if response.status_code == 200:
                self.log_result("GET /metrics", True, {
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.3f}s"
                })
            else:
                self.log_result("GET /metrics", False, {
                    "status_code": response.status_code
                })
                all_passed = False
                
        except Exception as e:
            self.log_result("GET /metrics", False, {"error": str(e)})
            all_passed = False
        
        return all_passed
    
    def test_reload_functionality(self) -> bool:
        """Test reload functionality"""
        print("\n=== Testing Reload Functionality ===")
        all_passed = True
        
        # Test reload all components
        try:
            response = requests.post(
                f"{self.base_url}/reload",
                json={"component": "all"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_result("POST /reload (all)", True, {
                        "status_code": response.status_code,
                        "response_time": f"{response.elapsed.total_seconds():.3f}s",
                        "result": data.get('result', {})
                    })
                else:
                    self.log_result("POST /reload (all)", False, {
                        "status_code": response.status_code,
                        "error": data
                    })
                    all_passed = False
            else:
                self.log_result("POST /reload (all)", False, {
                    "status_code": response.status_code
                })
                all_passed = False
                
        except Exception as e:
            self.log_result("POST /reload (all)", False, {"error": str(e)})
            all_passed = False
        
        # Test reload specific component
        try:
            response = requests.post(
                f"{self.base_url}/reload",
                json={"component": "nonexistent"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("POST /reload (invalid)", True, {
                    "status_code": response.status_code,
                    "response": data
                })
            else:
                self.log_result("POST /reload (invalid)", False, {
                    "status_code": response.status_code
                })
                
        except Exception as e:
            self.log_result("POST /reload (invalid)", False, {"error": str(e)})
        
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        print("\n=== Testing Error Handling ===")
        all_passed = True
        
        # Test invalid endpoint
        try:
            response = requests.get(f"{self.base_url}/invalid_endpoint", timeout=5)
            if response.status_code == 404:
                self.log_result("GET /invalid_endpoint", True, {
                    "status_code": response.status_code,
                    "expected": 404
                })
            else:
                self.log_result("GET /invalid_endpoint", False, {
                    "status_code": response.status_code,
                    "expected": 404
                })
                all_passed = False
                
        except Exception as e:
            self.log_result("GET /invalid_endpoint", False, {"error": str(e)})
            all_passed = False
        
        # Test invalid JSON
        try:
            response = requests.post(
                f"{self.base_url}/reload",
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 400:
                self.log_result("POST /reload (invalid JSON)", True, {
                    "status_code": response.status_code,
                    "expected": 400
                })
            else:
                self.log_result("POST /reload (invalid JSON)", False, {
                    "status_code": response.status_code,
                    "expected": 400
                })
                
        except Exception as e:
            self.log_result("POST /reload (invalid JSON)", False, {"error": str(e)})
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test performance"""
        print("\n=== Testing Performance ===")
        all_passed = True
        
        # Test response time
        response_times = []
        
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/status", timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    
            except Exception as e:
                self.log_result(f"Performance test {i+1}", False, {"error": str(e)})
                all_passed = False
                break
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            self.log_result("Response Time", avg_time < 0.5, {
                "average": f"{avg_time:.3f}s",
                "max": f"{max_time:.3f}s",
                "target": "< 0.5s"
            })
            
            if max_time > 0.5:
                all_passed = False
        
        return all_passed
    
    def test_concurrent_requests(self) -> bool:
        """Test concurrent requests"""
        print("\n=== Testing Concurrent Requests ===")
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/status", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        threads = []
        results = []
        
        # Start 10 concurrent requests
        for i in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        success_count = sum(results)
        success_rate = success_count / len(results) * 100
        
        self.log_result("Concurrent Requests", success_rate >= 95, {
            "success_rate": f"{success_rate:.1f}%",
            "target": ">= 95%"
        })
        
        return success_rate >= 95
    
    def test_server_shutdown(self) -> bool:
        """Test server shutdown"""
        print("\n=== Testing Server Shutdown ===")
        
        try:
            start_time = time.time()
            global_api.stop_api_server()
            shutdown_time = time.time() - start_time
            
            # Verify server has stopped
            try:
                response = requests.get(f"{self.base_url}/status", timeout=2)
                self.log_result("Server Shutdown", False, {
                    "error": "Server still responding",
                    "shutdown_time": f"{shutdown_time:.3f}s"
                })
                return False
            except requests.exceptions.ConnectionError:
                self.log_result("Server Shutdown", True, {
                    "shutdown_time": f"{shutdown_time:.3f}s"
                })
                return True
                
        except Exception as e:
            self.log_result("Server Shutdown", False, {"error": str(e)})
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        print("Starting Hot Reload API Server Stability Tests")
        print("=" * 60)
        
        # Reset test results
        self.test_results = []
        
        # Run tests
        tests = [
            ("Server Startup", self.test_server_startup),
            ("API Endpoints", self.test_api_endpoints),
            ("Reload Functionality", self.test_reload_functionality),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
            ("Concurrent Requests", self.test_concurrent_requests),
            ("Server Shutdown", self.test_server_shutdown)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_result(test_name, False, {"error": str(e)})
        
        # Generate test report
        report = {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'results': self.test_results
        }
        
        print("\n" + "=" * 60)
        print("Test Report")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        
        if report['success_rate'] >= 95:
            print("All tests passed! API server stability is good")
        else:
            print("Some tests failed, further debugging needed")
        
        return report


def main():
    """Main test function"""
    tester = HotReloadAPITester("http://localhost:8889")
    report = tester.run_all_tests()
    
    # Save test report
    try:
        with open('hot_reload_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\nTest report saved to: hot_reload_test_report.json")
    except Exception as e:
        print(f"\nCannot save test report: {e}")
    
    return report['success_rate'] >= 95


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)