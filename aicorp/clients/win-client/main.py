#!/usr/bin/env python
"""
AI-Corp Windows客户端主入口
提供Windows桌面会话管理的命令行和图形界面
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Optional

from .session import SessionManager
from .ui.main import WinClientUI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('aicorp-win-client.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI-Corp Windows客户端')
    
    parser.add_argument('--no-gui', action='store_true', help='不启动图形界面，仅使用命令行')
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        help='日志级别')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 会话命令
    session_parser = subparsers.add_parser('session', help='会话管理')
    session_subparsers = session_parser.add_subparsers(dest='session_command', help='会话子命令')
    
    # 创建会话
    create_parser = session_subparsers.add_parser('create', help='创建会话')
    create_parser.add_argument('username', type=str, help='Windows用户名')
    
    # 列出会话
    list_parser = session_subparsers.add_parser('list', help='列出会话')
    
    # 关闭会话
    close_parser = session_subparsers.add_parser('close', help='关闭会话')
    close_parser.add_argument('session_id', type=str, help='会话ID')
    
    # 执行命令
    exec_parser = subparsers.add_parser('exec', help='执行命令')
    exec_parser.add_argument('session_id', type=str, help='会话ID')
    exec_parser.add_argument('command', type=str, help='要执行的命令')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info("Starting AI-Corp Windows client")
    
    # 创建会话管理器
    session_manager = SessionManager()
    
    # 处理命令行命令
    if args.command:
        if args.command == 'session':
            if args.session_command == 'create':
                session = session_manager.create_session(args.username)
                if session:
                    logger.info(f"Created session {session.session_id}")
                else:
                    logger.error(f"Failed to create session for {args.username}")
            elif args.session_command == 'list':
                sessions = session_manager.list_sessions()
                logger.info(f"Found {len(sessions)} sessions")
                for session in sessions:
                    print(f"Session {session['session_id']} - {session['username']} - {'Active' if session['active'] else 'Inactive'}")
            elif args.session_command == 'close':
                success = session_manager.close_session(args.session_id)
                if success:
                    logger.info(f"Closed session {args.session_id}")
                else:
                    logger.error(f"Failed to close session {args.session_id}")
        elif args.command == 'exec':
            session = session_manager.get_session(args.session_id)
            if not session:
                logger.error(f"Session {args.session_id} not found")
                return
                
            result = session.execute_command(args.command)
            if result.get('success'):
                print(result.get('output', 'Command executed successfully'))
            else:
                logger.error(f"Command execution failed: {result.get('error', 'Unknown error')}")
    
    # 如果没有指定命令或未使用--no-gui选项，启动图形界面
    if not args.command or not args.no_gui:
        ui = WinClientUI(session_manager)
        ui.setup_ui()
        ui.connect_signals()
        ui.run()
    
    logger.info("AI-Corp Windows client exiting")

if __name__ == '__main__':
    main() 