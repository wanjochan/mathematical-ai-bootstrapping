"""
CyberCorp 核心入口

提供虚拟同事系统的命令行界面。
"""
import argparse
import logging
from typing import Optional
from core.colleague import Colleague, ColleagueManager, TaskPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """设置命令行参数解析"""
    parser = argparse.ArgumentParser(description='CyberCorp 虚拟同事系统')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加同事
    add_parser = subparsers.add_parser('add', help='添加新同事')
    add_parser.add_argument('--name', required=True, help='同事姓名')
    add_parser.add_argument('--role', required=True, help='角色')
    add_parser.add_argument('--skills', nargs='+', required=True, help='技能列表')
    
    # 创建任务
    task_parser = subparsers.add_parser('task', help='任务管理')
    task_parser.add_argument('--title', required=True, help='任务标题')
    task_parser.add_argument('--desc', required=True, help='任务描述')
    task_parser.add_argument('--priority', choices=['low', 'normal', 'high'], 
                           default='normal', help='任务优先级')
    task_parser.add_argument('--assign', help='分配给指定ID的同事')
    
    # 状态查看
    subparsers.add_parser('status', help='查看系统状态')
    
    return parser

def main():
    """主函数"""
    manager = ColleagueManager()
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'add':
            colleague = Colleague(
                name=args.name,
                role=args.role,
                skills=args.skills
            )
            manager.add_colleague(colleague)
            print(f"✓ 已添加同事: {colleague.name} (ID: {colleague.id})")
            
        elif args.command == 'task':
            priority_map = {
                'low': TaskPriority.LOW,
                'normal': TaskPriority.NORMAL,
                'high': TaskPriority.HIGH
            }
            task = manager.create_task(
                title=args.title,
                description=args.desc,
                priority=priority_map[args.priority]
            )
            
            if args.assign:
                if manager.assign_task(task.id, args.assign):
                    print(f"✓ 任务已分配给同事 {args.assign}")
                else:
                    print("× 分配任务失败")
            
            print(f"✓ 已创建任务: {task.title} (ID: {task.id})")
            
        elif args.command == 'status':
            status = manager.get_colleague_status()
            print("\n=== 同事状态 ===")
            for cid, info in status.items():
                print(f"\nID: {cid}")
                print(f"姓名: {info['name']}")
                print(f"角色: {info['role']}")
                print(f"状态: {info['status']}")
                if info['current_task']:
                    print(f"当前任务: {info['current_task']}")
            
    except Exception as e:
        logger.error(f"发生错误: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
