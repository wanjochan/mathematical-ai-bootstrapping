"""
多实例管理系统

支持多个seed实例的管理和协调，包括：
- 实例注册和发现
- 负载均衡
- 故障切换
- 状态同步
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import uuid
import aiohttp
import random

# 配置日志
logger = logging.getLogger(__name__)

class InstanceStatus(Enum):
    """实例状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class LoadBalanceStrategy(Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"

@dataclass
class InstanceInfo:
    """实例信息数据类"""
    id: str
    host: str
    port: int
    status: InstanceStatus
    last_heartbeat: datetime
    connections: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    weight: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def url(self) -> str:
        """获取实例URL"""
        return f"http://{self.host}:{self.port}"
    
    def is_healthy(self, timeout_seconds: int = 30) -> bool:
        """检查实例是否健康"""
        if self.status in [InstanceStatus.ERROR, InstanceStatus.MAINTENANCE]:
            return False
        
        time_diff = datetime.now() - self.last_heartbeat
        return time_diff.total_seconds() < timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        return data

class MultiInstanceManager:
    """多实例管理器"""
    
    def __init__(self, 
                 heartbeat_interval: int = 10,
                 instance_timeout: int = 30,
                 load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.instances: Dict[str, InstanceInfo] = {}
        self.heartbeat_interval = heartbeat_interval
        self.instance_timeout = instance_timeout
        self.load_balance_strategy = load_balance_strategy
        self._round_robin_index = 0
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self.on_instance_added: Optional[Callable[[InstanceInfo], None]] = None
        self.on_instance_removed: Optional[Callable[[str], None]] = None
        self.on_instance_status_changed: Optional[Callable[[str, InstanceStatus, InstanceStatus], None]] = None
    
    async def start(self):
        """启动管理器"""
        if self._running:
            return
        
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("多实例管理器已启动")
    
    async def stop(self):
        """停止管理器"""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("多实例管理器已停止")
    
    def register_instance(self, 
                         host: str, 
                         port: int, 
                         instance_id: str = None,
                         weight: int = 1,
                         metadata: Dict[str, Any] = None) -> str:
        """注册实例"""
        if instance_id is None:
            instance_id = str(uuid.uuid4())
        
        instance = InstanceInfo(
            id=instance_id,
            host=host,
            port=port,
            status=InstanceStatus.ACTIVE,
            last_heartbeat=datetime.now(),
            weight=weight,
            metadata=metadata or {}
        )
        
        old_instance = self.instances.get(instance_id)
        self.instances[instance_id] = instance
        
        if old_instance is None:
            logger.info(f"实例注册成功: {instance_id} ({host}:{port})")
            if self.on_instance_added:
                self.on_instance_added(instance)
        else:
            logger.info(f"实例更新成功: {instance_id} ({host}:{port})")
        
        return instance_id
    
    def unregister_instance(self, instance_id: str) -> bool:
        """注销实例"""
        if instance_id in self.instances:
            instance = self.instances.pop(instance_id)
            logger.info(f"实例注销成功: {instance_id}")
            
            if self.on_instance_removed:
                self.on_instance_removed(instance_id)
            
            return True
        
        logger.warning(f"尝试注销不存在的实例: {instance_id}")
        return False
    
    def get_instance(self, instance_id: str) -> Optional[InstanceInfo]:
        """获取指定实例信息"""
        return self.instances.get(instance_id)
    
    def get_healthy_instances(self) -> List[InstanceInfo]:
        """获取所有健康的实例"""
        return [
            instance for instance in self.instances.values()
            if instance.is_healthy(self.instance_timeout)
        ]
    
    def get_instance_for_request(self) -> Optional[InstanceInfo]:
        """根据负载均衡策略获取实例"""
        healthy_instances = self.get_healthy_instances()
        
        if not healthy_instances:
            logger.warning("没有可用的健康实例")
            return None
        
        if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            instance = healthy_instances[self._round_robin_index % len(healthy_instances)]
            self._round_robin_index += 1
            return instance
        
        elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return min(healthy_instances, key=lambda x: x.connections)
        
        elif self.load_balance_strategy == LoadBalanceStrategy.RANDOM:
            return random.choice(healthy_instances)
        
        elif self.load_balance_strategy == LoadBalanceStrategy.WEIGHTED:
            total_weight = sum(instance.weight for instance in healthy_instances)
            if total_weight == 0:
                return random.choice(healthy_instances)
            
            rand_val = random.uniform(0, total_weight)
            current_weight = 0
            
            for instance in healthy_instances:
                current_weight += instance.weight
                if rand_val <= current_weight:
                    return instance
            
            return healthy_instances[-1]  # fallback
        
        else:
            return healthy_instances[0]  # fallback
    
    def update_instance_status(self, instance_id: str, status: InstanceStatus):
        """更新实例状态"""
        if instance_id not in self.instances:
            logger.warning(f"尝试更新不存在实例的状态: {instance_id}")
            return
        
        instance = self.instances[instance_id]
        old_status = instance.status
        instance.status = status
        
        if old_status != status:
            logger.info(f"实例 {instance_id} 状态变更: {old_status.value} -> {status.value}")
            
            if self.on_instance_status_changed:
                self.on_instance_status_changed(instance_id, old_status, status)
    
    def update_instance_metrics(self, 
                               instance_id: str,
                               connections: int = None,
                               cpu_usage: float = None,
                               memory_usage: float = None):
        """更新实例指标"""
        if instance_id not in self.instances:
            return
        
        instance = self.instances[instance_id]
        
        if connections is not None:
            instance.connections = connections
        if cpu_usage is not None:
            instance.cpu_usage = cpu_usage
        if memory_usage is not None:
            instance.memory_usage = memory_usage
        
        instance.last_heartbeat = datetime.now()
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """获取集群统计信息"""
        healthy_instances = self.get_healthy_instances()
        total_instances = len(self.instances)
        
        if not healthy_instances:
            return {
                "total_instances": total_instances,
                "healthy_instances": 0,
                "unhealthy_instances": total_instances,
                "total_connections": 0,
                "avg_cpu_usage": 0.0,
                "avg_memory_usage": 0.0,
                "load_balance_strategy": self.load_balance_strategy.value
            }
        
        total_connections = sum(instance.connections for instance in healthy_instances)
        avg_cpu = sum(instance.cpu_usage for instance in healthy_instances) / len(healthy_instances)
        avg_memory = sum(instance.memory_usage for instance in healthy_instances) / len(healthy_instances)
        
        return {
            "total_instances": total_instances,
            "healthy_instances": len(healthy_instances),
            "unhealthy_instances": total_instances - len(healthy_instances),
            "total_connections": total_connections,
            "avg_cpu_usage": round(avg_cpu, 2),
            "avg_memory_usage": round(avg_memory, 2),
            "load_balance_strategy": self.load_balance_strategy.value
        }
    
    def get_all_instances_info(self) -> List[Dict[str, Any]]:
        """获取所有实例信息"""
        return [instance.to_dict() for instance in self.instances.values()]
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await self._send_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._check_instance_health()
                await asyncio.sleep(self.heartbeat_interval * 2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _send_heartbeats(self):
        """发送心跳到所有实例"""
        tasks = []
        for instance_id, instance in self.instances.items():
            if instance.status != InstanceStatus.MAINTENANCE:
                task = asyncio.create_task(self._ping_instance(instance_id, instance))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _ping_instance(self, instance_id: str, instance: InstanceInfo):
        """Ping单个实例"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{instance.url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 更新实例指标
                        self.update_instance_metrics(
                            instance_id,
                            connections=data.get("connections", 0),
                            cpu_usage=data.get("cpu_usage", 0.0),
                            memory_usage=data.get("memory_usage", 0.0)
                        )
                        
                        if instance.status == InstanceStatus.ERROR:
                            self.update_instance_status(instance_id, InstanceStatus.ACTIVE)
                    else:
                        self.update_instance_status(instance_id, InstanceStatus.ERROR)
        
        except Exception as e:
            logger.debug(f"Ping实例 {instance_id} 失败: {e}")
            self.update_instance_status(instance_id, InstanceStatus.ERROR)
    
    async def _check_instance_health(self):
        """检查实例健康状态"""
        current_time = datetime.now()
        
        for instance_id, instance in self.instances.items():
            if instance.status == InstanceStatus.MAINTENANCE:
                continue
            
            time_diff = current_time - instance.last_heartbeat
            
            if time_diff.total_seconds() > self.instance_timeout:
                if instance.status != InstanceStatus.INACTIVE:
                    logger.warning(f"实例 {instance_id} 超时，标记为非活跃")
                    self.update_instance_status(instance_id, InstanceStatus.INACTIVE)

# 全局实例管理器
instance_manager = MultiInstanceManager()

class InstanceManagerAPI:
    """实例管理器API接口"""
    
    @staticmethod
    async def start_manager():
        """启动实例管理器"""
        await instance_manager.start()
    
    @staticmethod
    async def stop_manager():
        """停止实例管理器"""
        await instance_manager.stop()
    
    @staticmethod
    def register_instance(host: str, port: int, **kwargs) -> str:
        """注册实例"""
        return instance_manager.register_instance(host, port, **kwargs)
    
    @staticmethod
    def unregister_instance(instance_id: str) -> bool:
        """注销实例"""
        return instance_manager.unregister_instance(instance_id)
    
    @staticmethod
    def get_instance_for_request() -> Optional[InstanceInfo]:
        """获取负载均衡实例"""
        return instance_manager.get_instance_for_request()
    
    @staticmethod
    def get_cluster_stats() -> Dict[str, Any]:
        """获取集群统计"""
        return instance_manager.get_cluster_stats()
    
    @staticmethod
    def get_all_instances() -> List[Dict[str, Any]]:
        """获取所有实例信息"""
        return instance_manager.get_all_instances_info()
    
    @staticmethod
    def update_instance_status(instance_id: str, status: str):
        """更新实例状态"""
        try:
            status_enum = InstanceStatus(status)
            instance_manager.update_instance_status(instance_id, status_enum)
        except ValueError:
            raise ValueError(f"无效的状态值: {status}")

if __name__ == "__main__":
    # 测试代码
    async def test_multi_instance_manager():
        """测试多实例管理器"""
        print("=== 多实例管理器测试 ===")
        
        # 启动管理器
        await instance_manager.start()
        
        # 注册实例
        id1 = instance_manager.register_instance("localhost", 8000, weight=2)
        id2 = instance_manager.register_instance("localhost", 8001, weight=1)
        id3 = instance_manager.register_instance("localhost", 8002, weight=3)
        
        print(f"注册实例: {id1}, {id2}, {id3}")
        
        # 测试负载均衡
        print("\n负载均衡测试:")
        for i in range(10):
            instance = instance_manager.get_instance_for_request()
            if instance:
                print(f"请求 {i+1}: {instance.host}:{instance.port} (权重: {instance.weight})")
        
        # 获取集群统计
        print(f"\n集群统计: {instance_manager.get_cluster_stats()}")
        
        # 模拟实例故障
        instance_manager.update_instance_status(id2, InstanceStatus.ERROR)
        print(f"\n实例 {id2} 故障后的集群统计: {instance_manager.get_cluster_stats()}")
        
        # 停止管理器
        await instance_manager.stop()
        print("\n测试完成")
    
    # 运行测试
    asyncio.run(test_multi_instance_manager()) 