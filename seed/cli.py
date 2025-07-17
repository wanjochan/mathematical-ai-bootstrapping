#!/usr/bin/env python3
"""
CyberCorp Seed CLI Tool
Command line interface for CyberCorp Seed Server
"""

import argparse
import requests
import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import time

class SeedCLI:
    """Seed服务器命令行工具"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到seed服务器 ({self.base_url})")
            print("请确保seed服务器正在运行: python main.py")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 ({timeout}s)")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP错误: {e}")
            if hasattr(e.response, 'text'):
                print(f"详细信息: {e.response.text}")
            sys.exit(1)
    
    def health(self):
        """检查服务器健康状态"""
        print("🔍 检查seed服务器状态...")
        result = self._make_request("GET", "/health")
        
        print("✅ seed服务器运行正常")
        print(f"📊 系统信息:")
        system = result.get("system", {})
        print(f"   平台: {system.get('platform')} {system.get('platform_version')}")
        print(f"   CPU: {system.get('cpu_count')}核 {system.get('cpu_percent')}%使用率")
        print(f"   内存: {system.get('memory', {}).get('percent')}%使用率")
        
    def status(self):
        """显示服务器状态"""
        print("📈 获取服务器状态...")
        result = self._make_request("GET", "/status")
        
        server = result.get("server", {})
        runtime = result.get("runtime", {})
        
        print(f"🚀 {server.get('name')} v{server.get('version')}")
        print(f"🌍 环境: {server.get('environment')}")
        print(f"🔌 地址: {server.get('host')}:{server.get('port')}")
        print(f"⏱️  运行时间: {runtime.get('uptime_seconds', 0):.1f}秒")
        
    def create_project(self, name: str, description: str = "", template: str = "basic"):
        """创建新项目"""
        print(f"📁 创建项目 '{name}'...")
        
        data = {
            "name": name,
            "description": description,
            "template": template
        }
        
        result = self._make_request("POST", "/projects", data)
        print(f"✅ 项目 '{name}' 创建成功")
        print(f"📍 项目路径: {result.get('project_path')}")
        
    def list_projects(self):
        """列出所有项目"""
        print("📂 获取项目列表...")
        result = self._make_request("GET", "/projects")
        
        projects = result.get("projects", [])
        if not projects:
            print("📭 暂无项目")
            return
            
        print(f"📚 发现 {len(projects)} 个项目:")
        for project in projects:
            print(f"   📁 {project['name']}")
            if project.get('description'):
                print(f"      📝 {project['description']}")
                
    def install_deps(self, project: str, packages: list, dev: bool = False):
        """安装项目依赖"""
        print(f"📦 为项目 '{project}' 安装依赖...")
        
        data = {
            "packages": packages,
            "dev": dev
        }
        
        result = self._make_request("POST", f"/projects/{project}/dependencies/install", data)
        print(f"✅ {result.get('message', '依赖安装完成')}")
        
        for pkg_result in result.get("results", []):
            status = "✅" if pkg_result.get("success") else "❌"
            print(f"   {status} {pkg_result.get('package')}: {pkg_result.get('message')}")
    
    def list_deps(self, project: str):
        """列出项目依赖"""
        print(f"📋 获取项目 '{project}' 的依赖列表...")
        result = self._make_request("GET", f"/projects/{project}/dependencies/list")
        
        dependencies = result.get("dependencies", {})
        
        for pkg_type, info in dependencies.items():
            packages = info.get("packages", [])
            print(f"📦 {info.get('type', pkg_type)} ({len(packages)}个包):")
            for pkg in packages[:10]:  # 只显示前10个
                print(f"   - {pkg}")
            if len(packages) > 10:
                print(f"   ... 还有 {len(packages) - 10} 个包")
                
    def format_code(self, project: str, files: Optional[list] = None):
        """格式化代码"""
        print(f"🎨 格式化项目 '{project}' 的代码...")
        
        data = {
            "files": files
        }
        
        result = self._make_request("POST", f"/projects/{project}/format", data)
        print(f"✅ 代码格式化完成")
        
        for file_result in result.get("results", []):
            status = "✅" if file_result.get("status") == "success" else "❌"
            changes = "🔄" if file_result.get("changes_made") else "📄"
            print(f"   {status}{changes} {file_result.get('file')}")

def main():
    parser = argparse.ArgumentParser(
        description="CyberCorp Seed CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  seed health                           # 检查服务器状态
  seed create myproject                 # 创建新项目
  seed list                            # 列出所有项目
  seed install myproject requests flask # 安装依赖
  seed deps myproject                   # 查看项目依赖
  seed format myproject                 # 格式化项目代码
        """
    )
    
    parser.add_argument(
        "--url", 
        default="http://localhost:8000/api/v1",
        help="Seed服务器URL (默认: http://localhost:8000/api/v1)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # health命令
    subparsers.add_parser("health", help="检查服务器健康状态")
    
    # status命令
    subparsers.add_parser("status", help="显示服务器状态")
    
    # create命令
    create_parser = subparsers.add_parser("create", help="创建新项目")
    create_parser.add_argument("name", help="项目名称")
    create_parser.add_argument("--description", "-d", default="", help="项目描述")
    create_parser.add_argument("--template", "-t", default="basic", help="项目模板")
    
    # list命令
    subparsers.add_parser("list", help="列出所有项目")
    
    # install命令
    install_parser = subparsers.add_parser("install", help="安装项目依赖")
    install_parser.add_argument("project", help="项目名称")
    install_parser.add_argument("packages", nargs="+", help="要安装的包")
    install_parser.add_argument("--dev", action="store_true", help="安装为开发依赖")
    
    # deps命令
    deps_parser = subparsers.add_parser("deps", help="查看项目依赖")
    deps_parser.add_argument("project", help="项目名称")
    
    # format命令
    format_parser = subparsers.add_parser("format", help="格式化项目代码")
    format_parser.add_argument("project", help="项目名称")
    format_parser.add_argument("--files", nargs="*", help="指定要格式化的文件")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = SeedCLI(args.url)
    
    try:
        if args.command == "health":
            cli.health()
        elif args.command == "status":
            cli.status()
        elif args.command == "create":
            cli.create_project(args.name, args.description, args.template)
        elif args.command == "list":
            cli.list_projects()
        elif args.command == "install":
            cli.install_deps(args.project, args.packages, args.dev)
        elif args.command == "deps":
            cli.list_deps(args.project)
        elif args.command == "format":
            cli.format_code(args.project, args.files)
        else:
            print(f"❌ 未知命令: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 