#!/usr/bin/env python3
"""
CyberCorp Seed开发工具
提供热重载、调试增强等开发辅助功能
"""

import os
import sys
import time
import signal
import subprocess
import threading
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil

class DevServerManager:
    """开发服务器管理器"""
    
    def __init__(self, script_path: str = "main.py", host: str = "localhost", port: int = 8000):
        self.script_path = script_path
        self.host = host
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.last_restart = 0
        self.restart_delay = 2  # 重启延迟秒数
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('dev_server.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start_server(self) -> bool:
        """启动服务器"""
        try:
            if self.process and self.process.poll() is None:
                self.logger.info("服务器已经在运行中...")
                return True
            
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--reload",
                "--host", self.host,
                "--port", str(self.port),
                "--log-level", "debug"
            ]
            
            self.logger.info(f"启动服务器: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 启动日志监控线程
            log_thread = threading.Thread(target=self._monitor_logs, daemon=True)
            log_thread.start()
            
            self.restart_count += 1
            self.last_restart = time.time()
            self.logger.info(f"服务器启动成功 (重启次数: {self.restart_count})")
            return True
            
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
            return False
    
    def _monitor_logs(self):
        """监控服务器日志输出"""
        if not self.process:
            return
            
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line.strip():
                    # 过滤和增强日志
                    enhanced_line = self._enhance_log_line(line.strip())
                    print(f"[SERVER] {enhanced_line}")
                    
                    # 检查是否有错误
                    if "ERROR" in line.upper() or "EXCEPTION" in line.upper():
                        self.logger.error(f"服务器错误: {line.strip()}")
                        
        except Exception as e:
            self.logger.error(f"日志监控错误: {e}")
    
    def _enhance_log_line(self, line: str) -> str:
        """增强日志输出"""
        # 添加颜色和图标（简化版）
        if "INFO" in line:
            return f"ℹ️  {line}"
        elif "WARNING" in line or "WARN" in line:
            return f"⚠️  {line}"
        elif "ERROR" in line:
            return f"❌ {line}"
        elif "DEBUG" in line:
            return f"🔍 {line}"
        elif "started server process" in line.lower():
            return f"🚀 {line}"
        elif "uvicorn running" in line.lower():
            return f"✅ {line}"
        else:
            return line
    
    def stop_server(self):
        """停止服务器"""
        if self.process:
            self.logger.info("停止服务器...")
            try:
                # 尝试优雅关闭
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制关闭
                self.process.kill()
                self.process.wait()
            self.process = None
            self.logger.info("服务器已停止")
    
    def restart_server(self):
        """重启服务器"""
        current_time = time.time()
        if current_time - self.last_restart < self.restart_delay:
            self.logger.info(f"重启过于频繁，等待 {self.restart_delay} 秒...")
            time.sleep(self.restart_delay)
        
        self.logger.info("重启服务器...")
        self.stop_server()
        time.sleep(1)
        self.start_server()
    
    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        return self.process is not None and self.process.poll() is None

class FileWatcher(FileSystemEventHandler):
    """文件变化监控器"""
    
    def __init__(self, server_manager: DevServerManager, patterns: List[str] = None):
        self.server_manager = server_manager
        self.patterns = patterns or ['.py', '.json', '.yaml', '.yml', '.env']
        self.last_modified = {}
        self.debounce_time = 1.0  # 防抖时间
        
        self.logger = logging.getLogger(__name__)
    
    def should_trigger_reload(self, file_path: str) -> bool:
        """判断是否应该触发重载"""
        path = Path(file_path)
        
        # 检查文件扩展名
        if not any(file_path.endswith(pattern) for pattern in self.patterns):
            return False
        
        # 排除特定目录
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'node_modules', '.vscode'}
        if any(exclude_dir in path.parts for exclude_dir in exclude_dirs):
            return False
        
        # 防抖处理
        current_time = time.time()
        last_time = self.last_modified.get(file_path, 0)
        if current_time - last_time < self.debounce_time:
            return False
        
        self.last_modified[file_path] = current_time
        return True
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        if self.should_trigger_reload(event.src_path):
            self.logger.info(f"📝 检测到文件变化: {event.src_path}")
            self.server_manager.restart_server()
    
    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
        
        if self.should_trigger_reload(event.src_path):
            self.logger.info(f"📄 检测到新文件: {event.src_path}")
            self.server_manager.restart_server()

class DebugEnhancer:
    """调试增强器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def setup_debug_routes(self, app):
        """设置调试路由"""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            
            @app.get("/debug/info")
            async def debug_info():
                """获取调试信息"""
                return {
                    "server_info": self.get_server_info(),
                    "system_info": self.get_system_info(),
                    "process_info": self.get_process_info()
                }
            
            @app.get("/debug/health")
            async def debug_health():
                """详细健康检查"""
                health_data = {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "checks": {
                        "memory": self.check_memory(),
                        "disk": self.check_disk(),
                        "database": self.check_database(),
                        "external_services": self.check_external_services()
                    }
                }
                return health_data
            
            @app.post("/debug/reload")
            async def debug_reload():
                """手动触发重载"""
                # 这个端点可以用于手动触发服务器重载
                return {"message": "重载信号已发送"}
            
            self.logger.info("调试路由设置完成")
            
        except Exception as e:
            self.logger.error(f"调试路由设置失败: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "script_path": sys.argv[0] if sys.argv else "unknown"
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": dict(psutil.virtual_memory()._asdict()),
                "disk": dict(psutil.disk_usage('/')._asdict())
            }
        except Exception:
            return {"error": "无法获取系统信息"}
    
    def get_process_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        try:
            process = psutil.Process()
            return {
                "pid": process.pid,
                "memory_info": dict(process.memory_info()._asdict()),
                "cpu_percent": process.cpu_percent(),
                "create_time": process.create_time(),
                "num_threads": process.num_threads()
            }
        except Exception:
            return {"error": "无法获取进程信息"}
    
    def check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": "ok" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent,
                "available_mb": memory.available // (1024 * 1024)
            }
        except Exception:
            return {"status": "error", "message": "无法检查内存"}
    
    def check_disk(self) -> Dict[str, Any]:
        """检查磁盘使用"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            return {
                "status": "ok" if usage_percent < 90 else "warning",
                "usage_percent": usage_percent,
                "free_gb": disk.free // (1024 * 1024 * 1024)
            }
        except Exception:
            return {"status": "error", "message": "无法检查磁盘"}
    
    def check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        # 简化版检查，实际项目中可以添加真实的数据库检查
        return {"status": "ok", "message": "暂无数据库配置"}
    
    def check_external_services(self) -> Dict[str, Any]:
        """检查外部服务"""
        # 简化版检查，实际项目中可以添加外部服务检查
        return {"status": "ok", "message": "暂无外部服务依赖"}

class DevTools:
    """开发工具主类"""
    
    def __init__(self, watch_dirs: List[str] = None):
        self.watch_dirs = watch_dirs or ['.']
        self.server_manager = DevServerManager()
        self.observer = Observer()
        self.debug_enhancer = DebugEnhancer()
        self.logger = logging.getLogger(__name__)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info("收到终止信号，正在清理...")
        self.stop()
        sys.exit(0)
    
    def start_dev_mode(self):
        """启动开发模式"""
        self.logger.info("🚀 启动开发模式...")
        
        # 启动服务器
        if not self.server_manager.start_server():
            self.logger.error("服务器启动失败")
            return False
        
        # 设置文件监控
        file_watcher = FileWatcher(self.server_manager)
        
        for watch_dir in self.watch_dirs:
            watch_path = Path(watch_dir).resolve()
            if watch_path.exists():
                self.observer.schedule(file_watcher, str(watch_path), recursive=True)
                self.logger.info(f"📁 监控目录: {watch_path}")
        
        self.observer.start()
        self.logger.info("📋 文件监控已启动")
        self.logger.info("🎯 开发模式运行中... (Ctrl+C 退出)")
        
        try:
            while True:
                time.sleep(1)
                # 检查服务器状态
                if not self.server_manager.is_running():
                    self.logger.warning("服务器意外停止，尝试重启...")
                    self.server_manager.start_server()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止开发工具"""
        self.logger.info("🛑 停止开发工具...")
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            
        self.server_manager.stop_server()
        self.logger.info("✅ 开发工具已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberCorp Seed开发工具")
    parser.add_argument("--host", default="localhost", help="服务器主机")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--watch", nargs="+", default=["."], help="监控目录")
    parser.add_argument("--script", default="main.py", help="启动脚本")
    
    args = parser.parse_args()
    
    # 创建开发工具实例
    dev_tools = DevTools(watch_dirs=args.watch)
    dev_tools.server_manager.script_path = args.script
    dev_tools.server_manager.host = args.host
    dev_tools.server_manager.port = args.port
    
    # 启动开发模式
    dev_tools.start_dev_mode()

if __name__ == "__main__":
    main() 