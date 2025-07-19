"""
CyberCorp Control Server with Hot Reload Support
支持热修改、热替换的节点中控端
"""

import asyncio
import websockets
import json
import logging
import time
import os
import sys
import importlib
import importlib.util
import threading
import configparser
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CyberCorpServer')

# 命令处理器注册表
command_handlers = {}
plugin_modules = {}

class CommandType(Enum):
    """可动态扩展的命令类型"""
    # 基础命令
    GET_WINDOWS = "get_windows"
    GET_WINDOW_CONTENT = "get_window_content"
    RELOAD_PLUGINS = "reload_plugins"
    HOT_UPDATE = "hot_update"

def register_command(command: str, handler: Callable):
    """注册命令处理器"""
    command_handlers[command] = handler
    logger.info(f"Registered command handler: {command}")

def load_plugin(plugin_path: Path):
    """动态加载插件"""
    try:
        spec = importlib.util.spec_from_file_location(
            plugin_path.stem, 
            plugin_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找并注册命令处理器
        if hasattr(module, 'register_commands'):
            module.register_commands(register_command)
            
        plugin_modules[plugin_path.stem] = module
        logger.info(f"Loaded plugin: {plugin_path.stem}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load plugin {plugin_path}: {e}")
        return False

class PluginWatcher(FileSystemEventHandler):
    """监控插件目录变化"""
    def __init__(self, server):
        self.server = server
        
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            logger.info(f"Plugin modified: {event.src_path}")
            # 触发热重载
            asyncio.run_coroutine_threadsafe(
                self.server.reload_plugins(),
                self.server.loop
            )

@dataclass
class Client:
    """客户端信息"""
    id: str
    websocket: Any
    ip: str
    connected_at: datetime
    last_heartbeat: datetime
    user_session: Optional[str] = None
    capabilities: Dict[str, bool] = None
    hostname: Optional[str] = None
    platform: Optional[str] = None
    client_start_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None  # 可扩展的元数据
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'connected_at': self.connected_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'connection_duration': str(datetime.now() - self.connected_at),
            'user_session': self.user_session,
            'hostname': self.hostname,
            'platform': self.platform,
            'client_start_time': self.client_start_time.isoformat() if self.client_start_time else None,
            'capabilities': self.capabilities or {},
            'metadata': self.metadata or {}
        }

class CyberCorpServer:
    def __init__(self, host=None, port=None):
        # Load config.ini first
        self.ini_config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        if os.path.exists(config_path):
            self.ini_config.read(config_path)
            logger.info(f"Loaded configuration from {config_path}")
        
        self.host = host or self.ini_config.get('server', 'host', fallback='0.0.0.0')
        self.port = port or self.ini_config.getint('server', 'port', fallback=9998)
        self.clients: Dict[str, Client] = {}
        self.client_counter = 0
        self.running = True
        self.loop = None
        
        # 插件目录
        self.plugin_dir = Path(os.path.dirname(__file__)) / 'plugins'
        self.plugin_dir.mkdir(exist_ok=True)
        
        # 配置文件监控
        self.config_file = Path(os.path.dirname(__file__)) / 'server_config.json'
        
        # Load config after paths are set
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # 默认配置
        return {
            'heartbeat_interval': 30,
            'heartbeat_timeout': 60,
            'max_clients': 100,
            'enable_hot_reload': True,
            'plugin_watch_interval': 1
        }
    
    async def reload_config(self):
        """热重载配置"""
        logger.info("Reloading configuration...")
        self.config = self.load_config()
        
        # 通知所有客户端配置更新
        await self.broadcast({
            'type': 'config_update',
            'config': self.config
        })
        
    async def reload_plugins(self):
        """热重载插件"""
        logger.info("Reloading plugins...")
        
        # 清空现有命令处理器
        command_handlers.clear()
        
        # 重新加载所有插件
        plugin_files = self.plugin_dir.glob('*.py')
        for plugin_file in plugin_files:
            if plugin_file.stem != '__init__':
                load_plugin(plugin_file)
        
        # 通知客户端
        await self.broadcast({
            'type': 'plugins_reloaded',
            'available_commands': list(command_handlers.keys())
        })
    
    async def start(self):
        """启动服务器"""
        logger.info(f"Starting CyberCorp Hot-Reload Server on {self.host}:{self.port}")
        
        self.loop = asyncio.get_event_loop()
        
        # 加载插件
        await self.reload_plugins()
        
        # 启动文件监控
        if self.config.get('enable_hot_reload', True):
            self.start_file_watchers()
        
        # 启动维护任务
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._config_monitor())
        
        # 启动WebSocket服务器
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            compression=None
        ):
            logger.info(f"Server listening on {self.host}:{self.port}")
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
    
    def start_file_watchers(self):
        """启动文件监控"""
        # 监控插件目录
        plugin_observer = Observer()
        plugin_observer.schedule(
            PluginWatcher(self),
            str(self.plugin_dir),
            recursive=False
        )
        plugin_observer.start()
        
        logger.info("File watchers started")
    
    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        client_id = f"client_{self.client_counter}"
        self.client_counter += 1
        
        client = Client(
            id=client_id,
            websocket=websocket,
            ip=websocket.remote_address[0],
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
            metadata={}
        )
        
        self.clients[client_id] = client
        logger.info(f"Client {client_id} connected from {client.ip}")
        
        try:
            # 发送欢迎消息
            await self._send_message(client, {
                'type': 'welcome',
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'available_commands': list(command_handlers.keys()),
                'hot_reload_enabled': self.config.get('enable_hot_reload', True)
            })
            
            # 处理消息
            async for message in websocket:
                await self._handle_message(client, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            del self.clients[client_id]
    
    async def _handle_message(self, client: Client, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'heartbeat':
                client.last_heartbeat = datetime.now()
                await self._send_message(client, {'type': 'heartbeat_ack'})
                
            elif msg_type == 'register':
                # 客户端注册
                client.user_session = data.get('user_session')
                client.capabilities = data.get('capabilities', {})
                client.hostname = data.get('system_info', {}).get('hostname')
                client.platform = data.get('system_info', {}).get('platform')
                client.client_start_time = datetime.fromisoformat(data.get('client_start_time')) if data.get('client_start_time') else None
                client.metadata.update(data.get('metadata', {}))
                
                logger.info(f"Client {client.id} registered: user={client.user_session}, host={client.hostname}")
                
            elif msg_type == 'command_result':
                # 命令结果
                command_id = data.get('command_id')
                logger.info(f"Received result for command {command_id}")
                
                # Forward result back to management clients
                for cid, c in self.clients.items():
                    if c.capabilities and c.capabilities.get('management'):
                        result_msg = {
                            'type': 'command_result',
                            'from_client': client.id,
                            'command_id': command_id,
                            'result': data.get('result'),
                            'error': data.get('error'),
                            'timestamp': data.get('timestamp')
                        }
                        await self._send_message(c, result_msg)
                
            elif msg_type == 'request':
                # Handle client requests
                command = data.get('command')
                if command == 'list_clients':
                    # Send list of all connected clients
                    client_list = []
                    for cid, c in self.clients.items():
                        client_info = {
                            'id': c.id,
                            'ip': c.ip,
                            'connected_at': c.connected_at.isoformat(),
                            'user_session': c.user_session,
                            'hostname': c.hostname,
                            'platform': c.platform,
                            'capabilities': c.capabilities or {},
                            'client_start_time': c.client_start_time.isoformat() if c.client_start_time else None
                        }
                        client_list.append(client_info)
                    
                    await self._send_message(client, {
                        'type': 'client_list',
                        'clients': client_list
                    })
                    logger.info(f"Sent client list to {client.id}: {len(client_list)} clients")
                
            elif msg_type == 'forward_command':
                # Forward command from one client to another
                target_client_id = data.get('target_client')
                command_data = data.get('command')
                
                if target_client_id and command_data:
                    if target_client_id in self.clients:
                        target_client = self.clients[target_client_id]
                        # Add source client info
                        command_data['from_client'] = client.id
                        await self._send_message(target_client, command_data)
                        logger.info(f"Forwarded command from {client.id} to {target_client_id}")
                        
                        # Send acknowledgment
                        await self._send_message(client, {
                            'type': 'forward_ack',
                            'target_client': target_client_id,
                            'status': 'sent'
                        })
                    else:
                        await self._send_message(client, {
                            'type': 'error',
                            'message': f'Target client {target_client_id} not found'
                        })
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client.id}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _send_message(self, client: Client, message: dict):
        """发送消息给客户端"""
        try:
            await client.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to {client.id}: {e}")
    
    async def send_command(self, client_id: str, command: str, params: dict = None):
        """发送命令给客户端"""
        if client_id not in self.clients:
            logger.error(f"Client {client_id} not found")
            return None
            
        client = self.clients[client_id]
        command_id = f"cmd_{int(time.time() * 1000)}"
        
        # 检查是否有自定义处理器
        if command in command_handlers:
            # 在服务器端处理
            result = await command_handlers[command](client, params)
            return result
        else:
            # 发送给客户端处理
            message = {
                'type': 'command',
                'command_id': command_id,
                'command': command,
                'params': params or {}
            }
            
            await self._send_message(client, message)
            logger.info(f"Sent command {command} to {client_id}")
            
            return command_id
    
    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        tasks = []
        for client in self.clients.values():
            task = self._send_message(client, message)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _heartbeat_monitor(self):
        """监控客户端心跳"""
        while self.running:
            try:
                now = datetime.now()
                timeout = self.config.get('heartbeat_timeout', 60)
                disconnected = []
                
                for client_id, client in self.clients.items():
                    if (now - client.last_heartbeat).total_seconds() > timeout:
                        logger.warning(f"Client {client_id} heartbeat timeout")
                        disconnected.append(client_id)
                
                for client_id in disconnected:
                    if client_id in self.clients:
                        await self.clients[client_id].websocket.close()
                        
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
            await asyncio.sleep(30)
    
    async def _config_monitor(self):
        """监控配置文件变化"""
        last_mtime = 0
        
        while self.running:
            try:
                if self.config_file.exists():
                    mtime = self.config_file.stat().st_mtime
                    if mtime > last_mtime:
                        last_mtime = mtime
                        await self.reload_config()
                        
            except Exception as e:
                logger.error(f"Config monitor error: {e}")
                
            await asyncio.sleep(5)

# 创建示例配置文件
def create_default_config():
    config = {
        "heartbeat_interval": 30,
        "heartbeat_timeout": 60,
        "max_clients": 100,
        "enable_hot_reload": True,
        "plugin_watch_interval": 1,
        "custom_settings": {
            "allow_remote_control": True,
            "max_command_queue": 100
        }
    }
    
    config_file = Path(__file__).parent / 'server_config.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created default config: {config_file}")

# 创建示例插件
def create_example_plugin():
    plugin_dir = Path(__file__).parent / 'plugins'
    plugin_dir.mkdir(exist_ok=True)
    
    example_plugin = plugin_dir / 'example_commands.py'
    with open(example_plugin, 'w', encoding='utf-8') as f:
        f.write('''"""Example plugin for CyberCorp server"""

import logging

logger = logging.getLogger('ExamplePlugin')

async def handle_echo(client, params):
    """Echo command handler"""
    message = params.get('message', 'Hello from server!')
    logger.info(f"Echo command from {client.id}: {message}")
    return {'echo': message, 'client': client.id}

async def handle_status(client, params):
    """Get server status"""
    return {
        'status': 'online',
        'client_count': len(client.server.clients),
        'uptime': str(datetime.now() - client.server.start_time)
    }

def register_commands(register_func):
    """Register plugin commands"""
    register_func('echo', handle_echo)
    register_func('status', handle_status)
    logger.info("Example plugin commands registered")
''')
    
    logger.info(f"Created example plugin: {example_plugin}")

if __name__ == "__main__":
    # 创建默认配置和插件
    base_dir = Path(__file__).parent
    if not (base_dir / 'server_config.json').exists():
        create_default_config()
    
    if not (base_dir / 'plugins' / 'example_commands.py').exists():
        create_example_plugin()
    
    # 启动服务器
    server = CyberCorpServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        server.running = False