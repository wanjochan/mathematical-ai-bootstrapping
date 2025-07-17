#!/usr/bin/env python3
"""
CyberCorp 虚拟智能公司中控系统
命令行工具，用于管理 AI 员工团队，实现软件开发流程自动化

根据 PRD-shortterm.md 实现的功能：
- AI 员工管理 (employee)
- 模型配置 (model)  
- 系统监控 (monitor)
- 客户端管理 (client)
"""

import sys
import json
import argparse
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 版本信息
VERSION = "1.0.0"
CYBERCORP_HOME = Path(__file__).parent / "cybercorp"

# 确保配置目录存在
def ensure_config_dir():
    """确保配置目录存在"""
    config_dir = CYBERCORP_HOME / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    instances_dir = config_dir / "instances"
    instances_dir.mkdir(exist_ok=True)
    return config_dir

def load_config() -> Dict[str, Any]:
    """加载默认配置"""
    config_dir = ensure_config_dir()
    config_file = config_dir / "default.json"
    
    default_config = {
        "version": VERSION,
        "created": datetime.now().isoformat(),
        "ai_employees": [
            {
                "id": "PM",
                "nickname": "PM",
                "role": "经理",
                "description": "负责项目规划、任务分配和进度跟踪",
                "model_type": "cursor-ide",
                "status": "active"
            },
            {
                "id": "Dev1", 
                "nickname": "Dev1",
                "role": "开发者",
                "description": "负责核心功能开发，使用 vscode+augment 插件",
                "model_type": "vscode-augment",
                "status": "active"
            },
            {
                "id": "Dev2",
                "nickname": "Dev2", 
                "role": "开发者",
                "description": "负责辅助功能开发，使用 claude-code-cli",
                "model_type": "claude-code-cli",
                "status": "active"
            }
        ],
        "models": {
            "cursor-ide": {
                "name": "Cursor IDE 模式",
                "description": "基于 Cursor IDE 的开发模式",
                "suitable_roles": ["经理", "架构师"]
            },
            "vscode-augment": {
                "name": "VSCode + Augment 模式",
                "description": "VSCode 与 Augment 插件集成",
                "suitable_roles": ["开发者", "测试员"]
            },
            "claude-code-cli": {
                "name": "Claude 命令行模式",
                "description": "Claude 命令行代码助手",
                "suitable_roles": ["开发者", "文档员"]
            }
        }
    }
    
    if not config_file.exists():
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config: Dict[str, Any]):
    """保存配置"""
    config_dir = ensure_config_dir()
    config_file = config_dir / "default.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

class EmployeeManager:
    """AI员工管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def list_employees(self):
        """列出所有AI员工"""
        employees = self.config.get('ai_employees', [])
        if not employees:
            print("暂无AI员工")
            return
            
        print(f"{'ID':<8} {'昵称':<10} {'角色':<10} {'模型':<15} {'状态':<8} {'描述'}")
        print("-" * 70)
        for emp in employees:
            print(f"{emp['id']:<8} {emp['nickname']:<10} {emp['role']:<10} "
                  f"{emp['model_type']:<15} {emp['status']:<8} {emp['description']}")
    
    def add_employee(self, nickname: str, role: str, description: str):
        """添加新AI员工"""
        employees = self.config.get('ai_employees', [])
        
        # 生成新ID
        employee_id = f"EMP{len(employees) + 1}"
        while any(emp['id'] == employee_id for emp in employees):
            employee_id = f"EMP{len(employees) + 1}_{datetime.now().strftime('%H%M%S')}"
        
        new_employee = {
            "id": employee_id,
            "nickname": nickname,
            "role": role,
            "description": description,
            "model_type": "claude-code-cli",  # 默认模型
            "status": "active",
            "created": datetime.now().isoformat()
        }
        
        employees.append(new_employee)
        self.config['ai_employees'] = employees
        save_config(self.config)
        
        print(f"✅ 成功添加AI员工: {nickname} (ID: {employee_id})")
    
    def update_employee(self, employee_id: str, nickname: str = None, 
                       role: str = None, description: str = None):
        """更新AI员工信息"""
        employees = self.config.get('ai_employees', [])
        
        for emp in employees:
            if emp['id'] == employee_id:
                if nickname:
                    emp['nickname'] = nickname
                if role:
                    emp['role'] = role  
                if description:
                    emp['description'] = description
                emp['updated'] = datetime.now().isoformat()
                
                save_config(self.config)
                print(f"✅ 成功更新AI员工: {employee_id}")
                return
        
        print(f"❌ 未找到ID为 {employee_id} 的AI员工")
    
    def remove_employee(self, employee_id: str):
        """移除AI员工"""
        employees = self.config.get('ai_employees', [])
        original_count = len(employees)
        
        employees = [emp for emp in employees if emp['id'] != employee_id]
        
        if len(employees) < original_count:
            self.config['ai_employees'] = employees
            save_config(self.config)
            print(f"✅ 成功移除AI员工: {employee_id}")
        else:
            print(f"❌ 未找到ID为 {employee_id} 的AI员工")
    
    def get_employee_info(self, employee_id: str):
        """查看AI员工详细信息"""
        employees = self.config.get('ai_employees', [])
        
        for emp in employees:
            if emp['id'] == employee_id:
                print(f"AI员工详细信息:")
                print(f"  ID: {emp['id']}")
                print(f"  昵称: {emp['nickname']}")
                print(f"  角色: {emp['role']}")
                print(f"  描述: {emp['description']}")
                print(f"  模型类型: {emp['model_type']}")
                print(f"  状态: {emp['status']}")
                if 'created' in emp:
                    print(f"  创建时间: {emp['created']}")
                if 'updated' in emp:
                    print(f"  更新时间: {emp['updated']}")
                return
        
        print(f"❌ 未找到ID为 {employee_id} 的AI员工")

class ModelManager:
    """模型配置管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def list_models(self):
        """列出所有可用模型配置"""
        models = self.config.get('models', {})
        
        print(f"{'模型类型':<20} {'名称':<25} {'描述'}")
        print("-" * 70)
        for model_type, info in models.items():
            print(f"{model_type:<20} {info['name']:<25} {info['description']}")
    
    def set_employee_model(self, employee_id: str, model_type: str):
        """为AI员工设置模型类型"""
        employees = self.config.get('ai_employees', [])
        models = self.config.get('models', {})
        
        if model_type not in models:
            print(f"❌ 未知的模型类型: {model_type}")
            print(f"可用模型: {', '.join(models.keys())}")
            return
        
        for emp in employees:
            if emp['id'] == employee_id:
                emp['model_type'] = model_type
                emp['model_updated'] = datetime.now().isoformat()
                save_config(self.config)
                print(f"✅ 成功为 {employee_id} 设置模型: {model_type}")
                return
        
        print(f"❌ 未找到ID为 {employee_id} 的AI员工")
    
    def get_model_status(self):
        """查看当前模型使用状态"""
        employees = self.config.get('ai_employees', [])
        models = self.config.get('models', {})
        
        model_usage = {}
        for emp in employees:
            model_type = emp.get('model_type', 'unknown')
            if model_type not in model_usage:
                model_usage[model_type] = []
            model_usage[model_type].append(emp['id'])
        
        print("模型使用状态:")
        for model_type, employee_ids in model_usage.items():
            model_name = models.get(model_type, {}).get('name', model_type)
            print(f"  {model_name}: {', '.join(employee_ids)}")

class MonitorManager:
    """系统监控管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def show_status(self):
        """显示系统整体状态"""
        employees = self.config.get('ai_employees', [])
        models = self.config.get('models', {})
        
        active_employees = [emp for emp in employees if emp.get('status') == 'active']
        
        print("CyberCorp 系统状态:")
        print(f"  版本: {self.config.get('version', VERSION)}")
        print(f"  AI员工总数: {len(employees)}")
        print(f"  活跃员工: {len(active_employees)}")
        print(f"  可用模型: {len(models)}")
        print(f"  配置文件: {CYBERCORP_HOME / 'config' / 'default.json'}")

class ClientManager:
    """客户端管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def list_clients(self):
        """列出可用客户端"""
        print("可用客户端:")
        print("  win-client: Windows桌面客户端")
    
    def launch_win_client(self, no_gui: bool = False):
        """启动Windows客户端"""
        if no_gui:
            print("启动Windows客户端 (命令行模式)...")
            print("暂未实现")
        else:
            print("启动Windows客户端 (图形界面模式)...")
            print("暂未实现")

def main():
    """主函数"""
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="CyberCorp 虚拟智能公司中控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'CyberCorp {VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # employee 子命令
    employee_parser = subparsers.add_parser('employee', help='AI员工管理')
    employee_subparsers = employee_parser.add_subparsers(dest='employee_action')
    
    employee_subparsers.add_parser('list', help='列出所有AI员工')
    
    add_parser = employee_subparsers.add_parser('add', help='添加新AI员工')
    add_parser.add_argument('nickname', help='员工昵称')
    add_parser.add_argument('role', help='员工角色')
    add_parser.add_argument('description', help='员工描述')
    
    update_parser = employee_subparsers.add_parser('update', help='更新AI员工信息')
    update_parser.add_argument('employee_id', help='员工ID')
    update_parser.add_argument('--nickname', help='新昵称')
    update_parser.add_argument('--role', help='新角色')
    update_parser.add_argument('--description', help='新描述')
    
    remove_parser = employee_subparsers.add_parser('remove', help='移除AI员工')
    remove_parser.add_argument('employee_id', help='员工ID')
    
    info_parser = employee_subparsers.add_parser('info', help='查看AI员工详细信息')
    info_parser.add_argument('employee_id', help='员工ID')
    
    # model 子命令
    model_parser = subparsers.add_parser('model', help='模型配置管理')
    model_subparsers = model_parser.add_subparsers(dest='model_action')
    
    model_subparsers.add_parser('list', help='列出所有可用模型配置')
    
    set_parser = model_subparsers.add_parser('set', help='为AI员工设置模型类型')
    set_parser.add_argument('employee_id', help='员工ID')
    set_parser.add_argument('model_type', help='模型类型')
    
    model_subparsers.add_parser('status', help='查看当前模型使用状态')
    
    # monitor 子命令
    monitor_parser = subparsers.add_parser('monitor', help='系统监控')
    monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action')
    
    monitor_subparsers.add_parser('status', help='显示系统整体状态')
    
    # client 子命令
    client_parser = subparsers.add_parser('client', help='客户端管理')
    client_subparsers = client_parser.add_subparsers(dest='client_action')
    
    client_subparsers.add_parser('list', help='列出可用客户端')
    
    win_client_parser = client_subparsers.add_parser('win-client', help='Windows客户端')
    win_client_parser.add_argument('--no-gui', action='store_true', help='命令行模式')
    
    # help 子命令
    help_parser = subparsers.add_parser('help', help='显示帮助信息')
    help_parser.add_argument('command', nargs='?', help='要查看帮助的命令')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return
    
    # 加载配置
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # 执行命令
    try:
        if args.command == 'employee':
            manager = EmployeeManager(config)
            
            if args.employee_action == 'list':
                manager.list_employees()
            elif args.employee_action == 'add':
                manager.add_employee(args.nickname, args.role, args.description)
            elif args.employee_action == 'update':
                manager.update_employee(args.employee_id, args.nickname, 
                                      args.role, args.description)
            elif args.employee_action == 'remove':
                manager.remove_employee(args.employee_id)
            elif args.employee_action == 'info':
                manager.get_employee_info(args.employee_id)
            else:
                employee_parser.print_help()
        
        elif args.command == 'model':
            manager = ModelManager(config)
            
            if args.model_action == 'list':
                manager.list_models()
            elif args.model_action == 'set':
                manager.set_employee_model(args.employee_id, args.model_type)
            elif args.model_action == 'status':
                manager.get_model_status()
            else:
                model_parser.print_help()
        
        elif args.command == 'monitor':
            manager = MonitorManager(config)
            
            if args.monitor_action == 'status':
                manager.show_status()
            else:
                monitor_parser.print_help()
        
        elif args.command == 'client':
            manager = ClientManager(config)
            
            if args.client_action == 'list':
                manager.list_clients()
            elif args.client_action == 'win-client':
                manager.launch_win_client(args.no_gui)
            else:
                client_parser.print_help()
        
        elif args.command == 'help':
            if args.command:
                # 显示特定命令的帮助
                if args.command in ['employee', 'model', 'monitor', 'client']:
                    subparser = next(p for p in subparsers.choices.values() 
                                   if p.prog.endswith(args.command))
                    subparser.print_help()
                else:
                    print(f"未知命令: {args.command}")
            else:
                parser.print_help()
        
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 