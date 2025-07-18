#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载模块
支持界面组件的动态重新加载，无需重启程序
"""

import os
import sys
import time
import importlib
import threading
import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger import app_logger
import tkinter as tk
from typing import Dict, Callable, Any, Optional


class ComponentReloader:
    """组件重载器"""
    
    def __init__(self):
        self.components = {}  # 组件注册表
        self.reload_callbacks = {}  # 重载回调函数
        self.observer = None
        self.watching = False
        self.start_time = time.time()
        
    def register_component(self, name: str, module_name: str, class_name: str, 
                          reload_callback: Callable = None):
        """注册可重载的组件"""
        self.components[name] = {
            'module_name': module_name,
            'class_name': class_name,
            'reload_callback': reload_callback,
            'instance': None,
            'last_reload': None,
            'reload_count': 0
        }
        app_logger.info(f"注册组件: {name} -> {module_name}.{class_name}")
    
    def start_watching(self, watch_paths=None):
        """开始监控文件变化"""
        if self.watching:
            return
            
        if watch_paths is None:
            watch_paths = ['.']  # 当前目录
            
        self.observer = Observer()
        handler = FileChangeHandler(self)
        
        for path in watch_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)
                app_logger.info(f"开始监控路径: {path}")
        
        self.observer.start()
        self.watching = True
        app_logger.info("文件监控已启动")
    
    def stop_watching(self):
        """停止监控"""
        if self.observer and self.watching:
            self.observer.stop()
            self.observer.join()
            self.watching = False
            app_logger.info("文件监控已停止")
    
    def reload_component(self, name: str, context: Dict = None):
        """重载指定组件"""
        if name not in self.components:
            app_logger.warning(f"组件 {name} 未注册")
            return False
            
        component_info = self.components[name]
        
        try:
            start_time = time.time()
            app_logger.info(f"开始重载组件: {name}")
            
            # 重新导入模块
            module_name = component_info['module_name']
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
            
            # 获取新的类
            module = sys.modules[module_name]
            component_class = getattr(module, component_info['class_name'])
            
            # 执行重载回调
            if component_info['reload_callback']:
                result = component_info['reload_callback'](component_class, context)
                if result:
                    component_info['instance'] = result
            
            # 更新统计信息
            component_info['last_reload'] = time.time()
            component_info['reload_count'] += 1
            
            reload_time = time.time() - start_time
            app_logger.info(f"组件 {name} 重载成功 (耗时: {reload_time:.3f}s)")
            return {
                'success': True,
                'component': name,
                'reload_time': reload_time,
                'reload_count': component_info['reload_count']
            }
            
        except Exception as e:
            app_logger.exception(f"重载组件 {name} 失败: {str(e)}")
            return {
                'success': False,
                'component': name,
                'error': str(e)
            }
    
    def reload_all_components(self, context: Dict = None):
        """重载所有组件"""
        results = []
        success_count = 0
        
        for name in self.components:
            result = self.reload_component(name, context)
            results.append(result)
            if result.get('success', False):
                success_count += 1
        
        app_logger.info(f"批量重载完成: {success_count}/{len(self.components)} 个组件成功")
        return {
            'total': len(self.components),
            'success': success_count,
            'failed': len(self.components) - success_count,
            'results': results
        }
    
    def get_status(self):
        """获取重载器状态"""
        return {
            'registered_components': list(self.components.keys()),
            'component_details': {
                name: {
                    'module': info['module_name'],
                    'class': info['class_name'],
                    'reload_count': info['reload_count'],
                    'last_reload': info['last_reload']
                }
                for name, info in self.components.items()
            },
            'watching': self.watching,
            'uptime': time.time() - self.start_time
        }


class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""
    
    def __init__(self, reloader: ComponentReloader):
        self.reloader = reloader
        self.last_reload_time = {}
        self.reload_delay = 1.0  # 防抖延迟
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # 只处理Python文件
        if not file_path.endswith('.py'):
            return
            
        # 防抖处理
        current_time = time.time()
        if file_path in self.last_reload_time:
            if current_time - self.last_reload_time[file_path] < self.reload_delay:
                return
        
        self.last_reload_time[file_path] = current_time
        
        app_logger.info(f"检测到文件变化: {file_path}")
        
        # 延迟重载，避免文件写入过程中重载
        threading.Timer(0.5, self._delayed_reload, args=[file_path]).start()
    
    def _delayed_reload(self, file_path):
        """延迟重载"""
        try:
            # 根据文件路径判断需要重载的组件
            filename = os.path.basename(file_path)
            module_name = filename[:-3]  # 去掉.py扩展名
            
            # 查找相关组件
            for name, info in self.reloader.components.items():
                if info['module_name'] == module_name:
                    self.reloader.reload_component(name)
                    break
                    
        except Exception as e:
            app_logger.exception(f"延迟重载失败: {str(e)}")


class HotReloadAPI:
    """热重载API接口 - 增强版"""
    
    def __init__(self, reloader: ComponentReloader, port: int = 8888):
        self.reloader = reloader
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.start_time = None
        
    def start_api_server(self):
        """启动API服务器 - 增强版"""
        if self.is_running:
            app_logger.warning("API服务器已在运行中")
            return
            
        try:
            # 检查端口是否可用
            if not self._check_port_available(self.port):
                app_logger.error(f"端口 {self.port} 已被占用")
                return False
            
            # 创建HTTP服务器
            self.server = HTTPServer(('localhost', self.port), self._create_handler())
            self.start_time = time.time()
            
            # 在后台线程中启动服务器
            self.server_thread = threading.Thread(
                target=self._run_server,
                name='HotReloadAPIServer',
                daemon=True
            )
            self.server_thread.start()
            
            # 等待服务器启动
            if self._wait_for_server_ready(timeout=5):
                self.is_running = True
                app_logger.info(f"API服务器启动成功: http://localhost:{self.port}")
                return True
            else:
                app_logger.error("API服务器启动超时")
                return False
                
        except Exception as e:
            app_logger.exception(f"API服务器启动失败: {str(e)}")
            return False
    
    def stop_api_server(self):
        """停止API服务器"""
        if not self.is_running or not self.server:
            return
            
        try:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join(timeout=2)
            self.is_running = False
            self.server = None
            self.server_thread = None
            app_logger.info("API服务器已停止")
        except Exception as e:
            app_logger.exception(f"API服务器停止失败: {str(e)}")
    
    def _check_port_available(self, port):
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False
    
    def _wait_for_server_ready(self, timeout=5):
        """等待服务器准备就绪"""
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', self.port))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.1)
        return False
    
    def _run_server(self):
        """运行服务器"""
        try:
            self.server.serve_forever()
        except Exception as e:
            app_logger.exception(f"API服务器运行错误: {str(e)}")
    
    def _create_handler(self):
        """创建请求处理器"""
        reloader = self.reloader
        
        class ReloadHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
            
            def log_message(self, format, *args):
                """重写日志方法，使用我们的logger"""
                app_logger.info(f"API: {format % args}")
            
            def do_GET(self):
                """处理GET请求"""
                start_time = time.time()
                
                try:
                    if self.path == '/status' or self.path == '/health':
                        self._handle_status()
                    elif self.path == '/metrics':
                        self._handle_metrics()
                    else:
                        self._send_json(404, {'error': 'Not found'})
                        
                except Exception as e:
                    app_logger.exception(f"GET请求处理错误: {str(e)}")
                    self._send_json(500, {'error': 'Internal server error'})
                
                finally:
                    response_time = time.time() - start_time
                    if response_time > 0.5:
                        app_logger.warning(f"API响应时间过长: {response_time:.3f}s")
            
            def do_POST(self):
                """处理POST请求"""
                start_time = time.time()
                
                try:
                    if self.path == '/reload':
                        self._handle_reload()
                    else:
                        self._send_json(404, {'error': 'Not found'})
                        
                except Exception as e:
                    app_logger.exception(f"POST请求处理错误: {str(e)}")
                    self._send_json(500, {'error': 'Internal server error'})
                
                finally:
                    response_time = time.time() - start_time
                    if response_time > 0.5:
                        app_logger.warning(f"API响应时间过长: {response_time:.3f}s")
            
            def _handle_status(self):
                """处理状态检查请求"""
                status = {
                    'status': 'healthy',
                    'timestamp': time.time(),
                    'uptime': time.time() - reloader.start_time if hasattr(reloader, 'start_time') else 0,
                    'components': len(reloader.components),
                    'watching': hasattr(reloader, 'watching') and reloader.watching,
                    'server': {
                        'port': self.server.server_address[1],
                        'address': self.server.server_address[0]
                    }
                }
                self._send_json(200, status)
            
            def _handle_metrics(self):
                """处理性能指标请求"""
                metrics = reloader.get_status()
                metrics.update({
                    'server_uptime': time.time() - reloader.start_time if hasattr(reloader, 'start_time') else 0,
                    'active_threads': threading.active_count()
                })
                self._send_json(200, metrics)
            
            def _handle_reload(self):
                """处理重载请求"""
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    if content_length > 0:
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode('utf-8'))
                    else:
                        data = {}
                    
                    component = data.get('component', 'all')
                    context = data.get('context', {})
                    
                    if component == 'all':
                        result = reloader.reload_all_components(context)
                    else:
                        result = reloader.reload_component(component, context)
                    
                    if isinstance(result, dict) and result.get('success', False):
                        self._send_json(200, {
                            'status': 'success',
                            'result': result
                        })
                    else:
                        self._send_json(200, {
                            'status': 'error',
                            'result': result
                        })
                        
                except json.JSONDecodeError:
                    self._send_json(400, {'error': 'Invalid JSON'})
                except Exception as e:
                    app_logger.exception(f"重载处理错误: {str(e)}")
                    self._send_json(500, {'error': str(e)})
            
            def _send_json(self, status_code, data):
                """发送JSON响应"""
                response = json.dumps(data, ensure_ascii=False, indent=2)
                self.send_response(status_code)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
            
            def do_OPTIONS(self):
                """处理CORS预检请求"""
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
        
        return ReloadHandler
    
    def get_status(self):
        """获取API服务器状态"""
        return {
            'running': self.is_running,
            'port': self.port,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'server_thread_alive': self.server_thread.is_alive() if self.server_thread else False
        }


# 全局实例
global_reloader = ComponentReloader()
global_api = HotReloadAPI(global_reloader)