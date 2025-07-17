#!/usr/bin/env python3
"""
测试项目管理API功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """测试项目管理API"""
    print("=== CyberCorp Seed Server API 测试 ===\n")
    
    # 1. 测试服务器状态
    print("1. 测试服务器状态...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ 服务器运行正常")
            print(f"响应: {response.json()}")
        else:
            print(f"✗ 服务器状态异常: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器，请确保服务器已启动")
        return
    
    # 2. 测试健康检查
    print("\n2. 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print("✓ 健康检查通过")
            data = response.json()
            print(f"CPU使用率: {data['system']['cpu_percent']}%")
            print(f"内存使用率: {data['system']['memory']['percent']}%")
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 健康检查错误: {e}")
    
    # 3. 测试项目列表
    print("\n3. 测试项目列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects")
        if response.status_code == 200:
            print("✓ 项目列表API正常")
            data = response.json()
            print(f"当前项目数量: {data['total']}")
        else:
            print(f"✗ 项目列表API失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 项目列表API错误: {e}")
    
    # 4. 测试创建项目
    print("\n4. 测试创建项目...")
    project_data = {
        "name": "test-project-api",
        "description": "API测试项目",
        "template": "python"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects",
            headers={"Content-Type": "application/json"},
            data=json.dumps(project_data)
        )
        if response.status_code == 200:
            print("✓ 项目创建成功")
            data = response.json()
            print(f"项目名称: {data['project']['name']}")
            print(f"项目路径: {data['project']['path']}")
        else:
            print(f"✗ 项目创建失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ 项目创建错误: {e}")
    
    # 5. 测试文件创建
    print("\n5. 测试文件创建...")
    file_data = {
        "path": "test_file.py",
        "content": "#!/usr/bin/env python3\n\ndef hello():\n    print('Hello from API test!')\n\nif __name__ == '__main__':\n    hello()\n"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/test-project-api/files",
            headers={"Content-Type": "application/json"},
            data=json.dumps(file_data)
        )
        if response.status_code == 200:
            print("✓ 文件创建成功")
            data = response.json()
            print(f"文件路径: {data['file']['path']}")
            print(f"文件大小: {data['file']['size']} bytes")
        else:
            print(f"✗ 文件创建失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ 文件创建错误: {e}")
    
    # 6. 测试文件读取
    print("\n6. 测试文件读取...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/test-project-api/files/test_file.py")
        if response.status_code == 200:
            print("✓ 文件读取成功")
            data = response.json()
            print(f"文件内容预览:")
            print(data['file']['content'][:100] + "..." if len(data['file']['content']) > 100 else data['file']['content'])
        else:
            print(f"✗ 文件读取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 文件读取错误: {e}")
    
    # 7. 测试文件树
    print("\n7. 测试文件树...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/test-project-api/tree")
        if response.status_code == 200:
            print("✓ 文件树获取成功")
            data = response.json()
            print(f"项目文件结构:")
            print_tree(data['tree'], indent=0)
        else:
            print(f"✗ 文件树获取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 文件树获取错误: {e}")
    
    print("\n=== API 测试完成 ===")

def print_tree(node, indent=0):
    """打印文件树"""
    prefix = "  " * indent
    if node['type'] == 'file':
        size = f" ({node.get('size', 0)} bytes)" if 'size' in node else ""
        print(f"{prefix}📄 {node['name']}{size}")
    elif node['type'] == 'dir':
        print(f"{prefix}📁 {node['name']}/")
        for child in node.get('children', []):
            print_tree(child, indent + 1)

if __name__ == "__main__":
    test_api() 