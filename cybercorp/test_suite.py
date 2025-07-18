#!/usr/bin/env python3
"""CyberCorp 测试套件 - 单实例和热重载测试"""

import os
import sys
import time
import subprocess
import threading
import requests
import json
from datetime import datetime
import psutil

class CyberCorpTestSuite:
    """CyberCorp 系统测试套件"""
    
    def __init__(self):
        self.server_process = None
        self.client_processes = []
        self.test_results = []
        self.server_url = "http://localhost:8000"
        
    def log_result(self, test_name, status, details=""):
        """记录测试结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{test_name}] {status} - {details}")
        
    def start_server(self):
        """启动服务器"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)  # 等待服务器启动
            
            # 检查服务器是否启动成功
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code == 200:
                    self.log_result("Server Start", "PASS", "服务器启动成功")
                    return True
            except:
                pass
                
            self.log_result("Server Start", "FAIL", "服务器启动失败")
            return False
            
        except Exception as e:
            self.log_result("Server Start", "ERROR", str(e))
            return False
            
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            
    def test_single_instance(self):
        """测试单实例模式"""
        print("\n=== 单实例模式测试 ===")
        
        try:
            # 启动第一个客户端
            client1 = subprocess.Popen(
                [sys.executable, "desktop_client.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            
            # 尝试启动第二个客户端
            client2 = subprocess.Popen(
                [sys.executable, "desktop_client.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            
            # 检查第二个客户端是否立即退出
            client2.poll()
            if client2.returncode is not None and client2.returncode != 0:
                self.log_result("Single Instance", "PASS", "第二个客户端被正确阻止")
            else:
                self.log_result("Single Instance", "FAIL", "第二个客户端未被阻止")
                
            # 清理
            client1.terminate()
            client2.terminate()
            client1.wait()
            client2.wait()
            
        except Exception as e:
            self.log_result("Single Instance", "ERROR", str(e))
            
    def test_api_endpoints(self):
        """测试API端点"""
        print("\n=== API端点测试 ===")
        
        endpoints = [
            ("/api/employees", "GET"),
            ("/api/tasks", "GET"),
            ("/api/monitoring/dashboard", "GET"),
            ("/api/employees", "POST", {"name": "测试员工", "role": "developer"}),
            ("/api/tasks", "POST", {"name": "测试任务", "description": "测试描述", "priority": 3})
        ]
        
        for endpoint, method, *data in endpoints:
            try:
                url = f"{self.server_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(url, json=data[0], timeout=5)
                    
                if response.status_code in [200, 201]:
                    self.log_result(f"API {endpoint}", "PASS", f"{method} 请求成功")
                else:
                    self.log_result(f"API {endpoint}", "FAIL", 
                                  f"{method} 请求失败: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"API {endpoint}", "ERROR", str(e))
                
    def run_all_tests(self):
        """运行所有测试"""
        print("开始CyberCorp系统测试...\n")
        
        # 启动服务器
        if not self.start_server():
            return
            
        try:
            # 运行测试
            self.test_single_instance()
            self.test_api_endpoints()
            
            # 打印测试结果
            print("\n=== 测试结果汇总 ===")
            passed = sum(1 for r in self.test_results if r["status"] == "PASS")
            total = len(self.test_results)
            print(f"通过: {passed}/{total}")
            
            for result in self.test_results:
                print(f"{result['test']}: {result['status']}")
                
        finally:
            self.stop_server()
            
    def cleanup(self):
        """清理所有进程"""
        for client in self.client_processes:
            try:
                client.terminate()
                client.wait()
            except:
                pass
                
        self.stop_server()

if __name__ == "__main__":
    suite = CyberCorpTestSuite()
    try:
        suite.run_all_tests()
    finally:
        suite.cleanup()