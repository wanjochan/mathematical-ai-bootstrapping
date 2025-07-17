#!/usr/bin/env python3
"""
测试代码生成API功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_code_generation():
    """测试代码生成API"""
    print("=== CyberCorp Seed Server 代码生成 API 测试 ===\n")
    
    # 1. 测试列出可用模板
    print("1. 测试列出可用模板...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/code/templates")
        if response.status_code == 200:
            print("✓ 模板列表获取成功")
            data = response.json()
            print(f"支持语言数量: {data['total_languages']}")
            print(f"总模板数量: {data['total_templates']}")
            for lang, templates in data['templates'].items():
                print(f"  {lang}: {', '.join(templates)}")
        else:
            print(f"✗ 模板列表获取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 模板列表获取错误: {e}")
    
    # 2. 测试生成Python函数模板
    print("\n2. 测试生成Python函数模板...")
    python_function_template = {
        "template_type": "function",
        "language": "python",
        "name": "calculate_sum",
        "parameters": {
            "description": "计算两个数字的和",
            "params": "a: int, b: int",
            "return_type": "int"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/code/templates/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(python_function_template)
        )
        if response.status_code == 200:
            print("✓ Python函数模板生成成功")
            data = response.json()
            print("生成的代码:")
            print("─" * 40)
            print(data['template']['code'])
            print("─" * 40)
        else:
            print(f"✗ Python函数模板生成失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ Python函数模板生成错误: {e}")
    
    # 3. 测试生成FastAPI路由模板
    print("\n3. 测试生成FastAPI路由模板...")
    fastapi_route_template = {
        "template_type": "fastapi_route",
        "language": "python",
        "name": "get_user",
        "parameters": {
            "description": "获取用户信息",
            "method": "get",
            "path": "users/{user_id}",
            "params": "user_id: int",
            "return_type": "Dict[str, Any]"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/code/templates/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(fastapi_route_template)
        )
        if response.status_code == 200:
            print("✓ FastAPI路由模板生成成功")
            data = response.json()
            print("生成的代码:")
            print("─" * 40)
            print(data['template']['code'])
            print("─" * 40)
        else:
            print(f"✗ FastAPI路由模板生成失败: {response.status_code}")
    except Exception as e:
        print(f"✗ FastAPI路由模板生成错误: {e}")
    
    # 4. 测试生成React组件模板
    print("\n4. 测试生成React组件模板...")
    react_component_template = {
        "template_type": "react_component",
        "language": "javascript",
        "name": "UserCard",
        "parameters": {
            "description": "用户卡片组件",
            "params": "{ user, onEdit }"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/code/templates/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(react_component_template)
        )
        if response.status_code == 200:
            print("✓ React组件模板生成成功")
            data = response.json()
            print("生成的代码:")
            print("─" * 40)
            print(data['template']['code'])
            print("─" * 40)
        else:
            print(f"✗ React组件模板生成失败: {response.status_code}")
    except Exception as e:
        print(f"✗ React组件模板生成错误: {e}")
    
    # 5. 测试添加代码片段
    print("\n5. 测试添加代码片段...")
    code_snippet = {
        "language": "python",
        "snippet_type": "decorator",
        "content": "@functools.wraps(func)\ndef wrapper(*args, **kwargs):\n    return func(*args, **kwargs)",
        "description": "基础装饰器模板"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/code/snippets",
            headers={"Content-Type": "application/json"},
            data=json.dumps(code_snippet)
        )
        if response.status_code == 200:
            print("✓ 代码片段添加成功")
            data = response.json()
            print(f"片段ID: {data['snippet']['id']}")
            print(f"语言: {data['snippet']['language']}")
        else:
            print(f"✗ 代码片段添加失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 代码片段添加错误: {e}")
    
    # 6. 测试获取代码片段
    print("\n6. 测试获取代码片段...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/code/snippets/python")
        if response.status_code == 200:
            print("✓ 代码片段获取成功")
            data = response.json()
            print(f"找到 {data['total']} 个Python代码片段")
            for snippet in data['snippets'][:3]:  # 只显示前3个
                print(f"  - {snippet['type']}: {snippet['description']}")
        else:
            print(f"✗ 代码片段获取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 代码片段获取错误: {e}")
    
    # 7. 测试在项目中生成代码文件
    print("\n7. 测试在项目中生成代码文件...")
    project_code_template = {
        "template_type": "class",
        "language": "python",
        "name": "UserService",
        "parameters": {
            "description": "用户服务类",
            "init_params": ", database: Database"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/test-project-api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(project_code_template)
        )
        if response.status_code == 200:
            print("✓ 项目代码文件生成成功")
            data = response.json()
            print(f"文件路径: {data['file']['path']}")
            print(f"文件大小: {data['file']['size']} bytes")
            print(f"模板类型: {data['file']['template_type']}")
        else:
            print(f"✗ 项目代码文件生成失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ 项目代码文件生成错误: {e}")
    
    # 8. 验证生成的文件
    print("\n8. 验证生成的文件...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/test-project-api/files/UserService.py")
        if response.status_code == 200:
            print("✓ 生成的文件读取成功")
            data = response.json()
            print("文件内容:")
            print("─" * 40)
            print(data['file']['content'])
            print("─" * 40)
        else:
            print(f"✗ 生成的文件读取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 生成的文件读取错误: {e}")
    
    print("\n=== 代码生成 API 测试完成 ===")

if __name__ == "__main__":
    test_code_generation() 