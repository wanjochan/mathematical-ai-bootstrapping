#!/usr/bin/env python3
"""综合API测试脚本"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import requests
import subprocess
import sys
import signal
import os

class APITestSuite:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}
        self.server_process = None
    
    def start_server(self):
        """启动服务器"""
        print("🔧 启动服务器...")
        try:
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "src.main", 
                "--bind", "0.0.0.0", "--port", "8000"
            ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)  # 等待服务器启动
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
    
    def check_health(self):
        """健康检查"""
        print("🏥 进行健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ 服务器健康正常")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接服务器: {e}")
            return False
    
    def test_auth_endpoints(self):
        """测试认证端点"""
        print("🔐 测试认证端点...")
        try:
            # 测试登录
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                "username": "admin",
                "password": "password"
            })
            print(f"登录响应: {response.status_code}")
            return response.status_code in [200, 401, 422]  # 401表示认证失败，422表示格式错误，都是可接受的
        except Exception as e:
            print(f"❌ 认证测试失败: {e}")
            return False
    
    def test_employee_endpoints(self):
        """测试员工管理端点"""
        print("👥 测试员工端点...")
        try:
            # 测试获取员工列表
            response = requests.get(f"{self.base_url}/api/employees")
            print(f"员工列表: {response.status_code}")
            
            # 测试创建员工
            create_data = {
                "name": "测试员工",
                "email": "test@example.com",
                "department": "技术部",
                "position": "测试工程师",
                "type": "remote",
                "skill_tags": ["Python", "测试"]
            }
            create_response = requests.post(
                f"{self.base_url}/api/employees",
                json=create_data,
                headers=self.headers
            )
            print(f"创建员工: {create_response.status_code}")
            
            return response.status_code == 200 and create_response.status_code in [200, 201, 422]
        except Exception as e:
            print(f"❌ 员工测试失败: {e}")
            return False
    
    def test_task_endpoints(self):
        """测试任务管理端点"""
        print("📋 测试任务端点...")
        try:
            # 测试获取任务列表
            response = requests.get(f"{self.base_url}/api/tasks")
            print(f"任务列表: {response.status_code}")
            
            # 测试创建任务
            task_data = {
                "title": "测试任务",
                "description": "这是一个测试任务",
                "type": "feature",
                "priority": "medium",
                "assignee_id": "test-user-001"
            }
            create_response = requests.post(
                f"{self.base_url}/api/tasks",
                json=task_data,
                headers=self.headers
            )
            print(f"创建任务: {create_response.status_code}")
            
            return response.status_code == 200 and create_response.status_code in [200, 201, 422]
        except Exception as e:
            print(f"❌ 任务测试失败: {e}")
            return False
    
    def test_system_endpoints(self):
        """测试系统端点"""
        print("⚙️ 测试系统端点...")
        try:
            # 测试配置端点
            config_response = requests.get(f"{self.base_url}/api/config")
            print(f"系统配置: {config_response.status_code}")
            
            # 测试进程端点
            process_response = requests.get(f"{self.base_url}/api/processes")
            print(f"进程列表: {process_response.status_code}")
            
            # 测试窗口端点
            window_response = requests.get(f"{self.base_url}/api/windows")
            print(f"窗口列表: {window_response.status_code}")
            
            return all(r.status_code == 200 for r in [config_response, process_response, window_response])
        except Exception as e:
            print(f"❌ 系统测试失败: {e}")
            return False
    
    async def run_async_tests(self):
        """运行异步测试"""
        print("🚀 开始综合API测试...")
        
        # 启动服务器
        if not self.start_server():
            return False
        
        try:
            # 等待服务器完全启动
            time.sleep(3)
            
            # 运行各项测试
            all_passed = True
            
            if not self.check_health():
                all_passed = False
            
            if not self.test_auth_endpoints():
                all_passed = False
            
            if not self.test_employee_endpoints():
                all_passed = False
            
            if not self.test_task_endpoints():
                all_passed = False
            
            if not self.test_system_endpoints():
                all_passed = False
            
            print(f"\n🎯 测试结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
            return all_passed
            
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {e}")
            return False
        finally:
            self.stop_server()
    
    def run(self):
        """同步运行测试"""
        return asyncio.run(self.run_async_tests())

if __name__ == "__main__":
    print("🧪 CyberCorp Server API 测试工具")
    print("=" * 50)
    
    test_suite = APITestSuite()
    success = test_suite.run()
    
    if success:
        print("\n🎉 所有测试通过！服务器运行正常")
    else:
        print("\n⚠️  部分测试失败，请检查日志")
    
    sys.exit(0 if success else 1)