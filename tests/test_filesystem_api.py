#!/usr/bin/env python3
"""
测试高级文件系统操作API功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_filesystem_operations():
    """测试文件系统操作API"""
    print("=== CyberCorp Seed Server 文件系统操作 API 测试 ===\n")
    
    # 确保测试项目存在
    project_name = "test-project-api"
    
    # 1. 测试文件搜索功能
    print("1. 测试文件搜索功能...")
    
    # 搜索Python文件
    search_data = {
        "pattern": "*.py",
        "file_types": [".py"],
        "include_content": True,
        "max_results": 50
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_name}/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_data)
        )
        if response.status_code == 200:
            print("✓ 文件搜索成功")
            data = response.json()
            print(f"搜索模式: {data['pattern']}")
            print(f"搜索文件数: {data['searched_files']}")
            print(f"匹配结果: {data['total_matches']}")
            
            for result in data['results'][:3]:  # 显示前3个结果
                print(f"  - {result['path']} ({result['size']} bytes, {result['match_type']} match)")
        else:
            print(f"✗ 文件搜索失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ 文件搜索错误: {e}")
    
    # 2. 测试内容搜索
    print("\n2. 测试内容搜索...")
    content_search_data = {
        "pattern": "def",
        "file_types": [".py"],
        "include_content": True,
        "max_results": 10
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_name}/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(content_search_data)
        )
        if response.status_code == 200:
            print("✓ 内容搜索成功")
            data = response.json()
            print(f"找到 {data['total_matches']} 个包含 'def' 的文件")
            
            for result in data['results'][:2]:
                if result['content_matches']:
                    print(f"  文件: {result['path']}")
                    for match in result['content_matches'][:2]:
                        print(f"    第{match['line']}行: {match['content']}")
        else:
            print(f"✗ 内容搜索失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 内容搜索错误: {e}")
    
    # 3. 测试目录操作
    print("\n3. 测试目录操作...")
    
    # 创建目录
    dir_create_data = {
        "operation": "create",
        "source_path": "test_dir/subdir"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_name}/directories",
            headers={"Content-Type": "application/json"},
            data=json.dumps(dir_create_data)
        )
        if response.status_code == 200:
            print("✓ 目录创建成功")
            data = response.json()
            print(f"创建目录: {data['message']}")
        else:
            print(f"✗ 目录创建失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 目录创建错误: {e}")
    
    # 4. 测试项目统计信息
    print("\n4. 测试项目统计信息...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/{project_name}/stats")
        if response.status_code == 200:
            print("✓ 项目统计获取成功")
            data = response.json()
            stats = data['stats']
            
            print(f"总文件数: {stats['total_files']}")
            print(f"总目录数: {stats['total_directories']}")
            print(f"总大小: {stats['total_size_formatted']}")
            print("文件类型分布:")
            for ext, count in list(stats['file_types'].items())[:5]:
                print(f"  {ext}: {count}")
            
            if stats['largest_files']:
                print("最大文件:")
                for file in stats['largest_files'][:3]:
                    size_kb = file['size'] / 1024
                    print(f"  {file['path']} ({size_kb:.1f} KB)")
                    
        else:
            print(f"✗ 项目统计获取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 项目统计获取错误: {e}")
    
    # 5. 测试批量文件操作
    print("\n5. 测试批量文件操作...")
    
    # 首先创建一些测试文件
    test_files = ["test1.txt", "test2.txt"]
    for filename in test_files:
        file_data = {
            "path": filename,
            "content": f"This is content for {filename}"
        }
        requests.post(
            f"{BASE_URL}/api/v1/projects/{project_name}/files",
            headers={"Content-Type": "application/json"},
            data=json.dumps(file_data)
        )
    
    # 批量复制文件
    batch_operation = {
        "operation": "copy",
        "files": test_files,
        "target_dir": "test_dir"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_name}/batch",
            headers={"Content-Type": "application/json"},
            data=json.dumps(batch_operation)
        )
        if response.status_code == 200:
            print("✓ 批量文件操作成功")
            data = response.json()
            print(f"操作类型: {data['operation']}")
            print(f"处理文件数: {data['processed']}")
            print(f"错误数: {data['errors']}")
            
            if data['results']:
                print("操作结果:")
                for result in data['results'][:3]:
                    print(f"  {result}")
                    
        else:
            print(f"✗ 批量文件操作失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 批量文件操作错误: {e}")
    
    # 6. 测试项目备份
    print("\n6. 测试项目备份...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/{project_name}/backup")
        if response.status_code == 200:
            print("✓ 项目备份成功")
            data = response.json()
            backup = data['backup']
            
            print(f"备份文件: {backup['name']}")
            size_kb = backup['size'] / 1024
            print(f"备份大小: {size_kb:.1f} KB")
            print(f"创建时间: {backup['created_at']}")
                    
        else:
            print(f"✗ 项目备份失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 项目备份错误: {e}")
    
    # 7. 测试文件树更新（验证所有操作结果）
    print("\n7. 验证操作结果 - 查看项目文件树...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/projects/{project_name}/tree")
        if response.status_code == 200:
            print("✓ 文件树获取成功")
            data = response.json()
            print("更新后的项目结构:")
            print_tree(data['tree'], indent=0)
        else:
            print(f"✗ 文件树获取失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 文件树获取错误: {e}")
    
    print("\n=== 文件系统操作 API 测试完成 ===")

def print_tree(node, indent=0, max_depth=3):
    """打印文件树（限制深度）"""
    if indent > max_depth:
        return
        
    prefix = "  " * indent
    if node['type'] == 'file':
        size = f" ({node.get('size', 0)} bytes)" if 'size' in node else ""
        print(f"{prefix}📄 {node['name']}{size}")
    elif node['type'] == 'dir':
        print(f"{prefix}📁 {node['name']}/")
        for child in node.get('children', [])[:5]:  # 限制显示数量
            print_tree(child, indent + 1, max_depth)
        
        if len(node.get('children', [])) > 5:
            print(f"{prefix}   ... and {len(node['children']) - 5} more items")

if __name__ == "__main__":
    test_filesystem_operations() 