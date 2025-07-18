#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载API服务器稳定性测试脚本
验证所有修复和改进
"""

import requests
import time
import json
import threading
import sys
import os
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hot_reload import global_reloader, global_api
from logger import app_logger


class HotReloadAPITester:
    """热重载API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """记录测试结果"""
        result = {
            'test': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_server_startup(self) -> bool:
        """测试服务器启动"""
        print("\n=== 测试服务器启动 ===")
        
        try:
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
        """测试API端点"""
        print("\n=== 测试API端点 ===")
        all_passed = True
        
        # 测试状态端点
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
        
        # 测试健康检查端点
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
        
        # 测试指标端点
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
        """测试重载功能"""
        print("\n=== 测试重载功能 ===")
        all_passed = True
        
        # 测试重载所有组件
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
        
        # 测试重载特定组件
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
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        all_passed = True
        
        # 测试无效端点
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
        
        # 测试无效JSON
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
        """测试性能"""
        print("\n=== 测试性能 ===")
        all_passed = True
        
        # 测试响应时间
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
        """测试并发请求"""
        print("\n=== 测试并发请求 ===")
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/status", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        threads = []
        results = []
        
        # 启动10个并发请求
        for i in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
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
        """测试服务器关闭"""
        print("\n=== 测试服务器关闭 ===")
        
        try:
            start_time = time.time()
            global_api.stop_api_server()
            shutdown_time = time.time() - start_time
            
            # 验证服务器已停止
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
        """运行所有测试"""
        print("🧪 开始热重载API服务器稳定性测试")
        print("=" * 60)
        
        # 重置测试结果
        self.test_results = []
        
        # 运行测试
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
        
        # 生成测试报告
        report = {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'results': self.test_results
        }
        
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        print(f"成功率: {report['success_rate']:.1f}%")
        
        if report['success_rate'] >= 95:
            print("🎉 所有测试通过！API服务器稳定性良好")
        else:
            print("⚠️  部分测试失败，需要进一步调试")
        
        return report


def main():
    """主测试函数"""
    tester = HotReloadAPITester()
    report = tester.run_all_tests()
    
    # 保存测试报告
    try:
        with open('hot_reload_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\n📄 测试报告已保存到: hot_reload_test_report.json")
    except Exception as e:
        print(f"\n⚠️  无法保存测试报告: {e}")
    
    return report['success_rate'] >= 95


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)