#!/usr/bin/env python3
"""
测试依赖管理API功能
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

# 添加seed模块到Python路径
sys.path.insert(0, str(Path(__file__).parent / "seed"))

# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_PROJECT = "test-dependency-project"

def test_api_endpoint(endpoint, method="GET", data=None):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"测试 {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        if response.status_code < 400:
            result = response.json()
            print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True, result
        else:
            print(f"错误: {response.text}")
            return False, response.text
    except Exception as e:
        print(f"请求失败: {e}")
        return False, str(e)

def test_dependency_workflow():
    """测试依赖管理工作流"""
    print("=" * 50)
    print("开始测试依赖管理工作流")
    print("=" * 50)
    
    # 1. 创建测试项目
    print("\n1. 创建测试项目")
    success, result = test_api_endpoint(
        "/projects",
        "POST",
        {
            "name": TEST_PROJECT,
            "description": "测试依赖管理功能",
            "template": "python"
        }
    )
    
    if not success:
        print("项目创建失败，停止测试")
        return
    
    # 2. 列出初始依赖
    print("\n2. 列出初始依赖")
    test_api_endpoint(f"/projects/{TEST_PROJECT}/dependencies/list")
    
    # 3. 安装一些测试依赖
    print("\n3. 安装测试依赖")
    test_api_endpoint(
        f"/projects/{TEST_PROJECT}/dependencies/install",
        "POST",
        {
            "packages": ["requests", "pytest"],
            "dev": False
        }
    )
    
    # 4. 再次列出依赖
    print("\n4. 列出安装后的依赖")
    test_api_endpoint(f"/projects/{TEST_PROJECT}/dependencies/list")
    
    # 5. 检查依赖更新
    print("\n5. 检查依赖更新")
    test_api_endpoint(
        f"/projects/{TEST_PROJECT}/dependencies/update",
        "POST",
        {
            "check_only": True
        }
    )
    
    # 6. 检查依赖健康状况
    print("\n6. 检查依赖健康状况")
    test_api_endpoint(f"/projects/{TEST_PROJECT}/dependencies/check")
    
    # 7. 卸载一个依赖
    print("\n7. 卸载pytest依赖")
    test_api_endpoint(
        f"/projects/{TEST_PROJECT}/dependencies/uninstall",
        "POST",
        {
            "packages": ["pytest"]
        }
    )
    
    # 8. 最终检查依赖列表
    print("\n8. 最终依赖列表")
    test_api_endpoint(f"/projects/{TEST_PROJECT}/dependencies/list")
    
    print("\n=" * 50)
    print("依赖管理工作流测试完成")
    print("=" * 50)

def test_direct_import():
    """直接导入模块测试"""
    print("=" * 50)
    print("测试直接导入seed模块")
    print("=" * 50)
    
    try:
        from seed.routers.projects import router
        print("✅ 成功导入项目路由模块")
        
        # 检查依赖管理相关路由
        routes = [route.path for route in router.routes]
        dependency_routes = [r for r in routes if '/dependencies/' in r]
        print(f"✅ 发现 {len(dependency_routes)} 个依赖管理相关路由:")
        for route in dependency_routes:
            print(f"  - {route}")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_server_health():
    """测试服务器健康状态"""
    print("=" * 50)
    print("测试服务器连接")
    print("=" * 50)
    
    # 测试健康检查
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            result = response.json()
            print(f"服务器信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def cleanup():
    """清理测试数据"""
    print("\n" + "=" * 50)
    print("清理测试数据")
    print("=" * 50)
    
    # 删除测试项目
    success, result = test_api_endpoint(f"/projects/{TEST_PROJECT}", "DELETE")
    if success:
        print("✅ 测试项目已删除")
    else:
        print("❌ 测试项目删除失败")

if __name__ == "__main__":
    print("依赖管理 API 功能测试")
    print("=" * 50)
    
    # 1. 测试模块导入
    if not test_direct_import():
        print("模块导入测试失败，退出")
        sys.exit(1)
    
    # 2. 测试服务器连接
    print(f"\n等待服务器启动...")
    time.sleep(3)
    
    if not test_server_health():
        print("服务器连接失败，仅测试模块导入")
        sys.exit(0)
    
    # 3. 测试依赖管理工作流
    try:
        test_dependency_workflow()
    finally:
        # 4. 清理
        cleanup()
    
    print("\n🎉 所有测试完成！") 