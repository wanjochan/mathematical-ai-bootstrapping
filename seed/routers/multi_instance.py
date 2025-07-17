"""
多实例管理API路由

提供多实例管理的REST API端点：
- 实例注册和注销
- 负载均衡查询
- 集群状态监控
- 实例状态管理
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..multi_instance_manager import (
    InstanceManagerAPI, 
    InstanceStatus, 
    LoadBalanceStrategy,
    instance_manager
)

router = APIRouter(prefix="/multi-instance", tags=["multi-instance"])

# Pydantic模型定义
class InstanceRegistration(BaseModel):
    """实例注册请求模型"""
    host: str = Field(..., description="实例主机地址")
    port: int = Field(..., ge=1, le=65535, description="实例端口")
    instance_id: Optional[str] = Field(None, description="实例ID（可选，自动生成）")
    weight: int = Field(1, ge=1, le=100, description="负载均衡权重")
    metadata: Optional[Dict[str, Any]] = Field(None, description="实例元数据")

class InstanceStatusUpdate(BaseModel):
    """实例状态更新请求模型"""
    status: str = Field(..., description="新状态（active/inactive/maintenance/error）")

class InstanceMetricsUpdate(BaseModel):
    """实例指标更新请求模型"""
    connections: Optional[int] = Field(None, ge=0, description="当前连接数")
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="内存使用率")

class LoadBalanceConfig(BaseModel):
    """负载均衡配置模型"""
    strategy: str = Field(..., description="负载均衡策略")
    heartbeat_interval: Optional[int] = Field(None, ge=5, le=300, description="心跳间隔（秒）")
    instance_timeout: Optional[int] = Field(None, ge=10, le=600, description="实例超时时间（秒）")

# API端点定义

@router.post("/instances", summary="注册实例")
async def register_instance(registration: InstanceRegistration):
    """
    注册新的seed实例到集群中
    
    - **host**: 实例主机地址
    - **port**: 实例端口
    - **instance_id**: 可选的实例ID，未提供时自动生成
    - **weight**: 负载均衡权重，默认为1
    - **metadata**: 实例元数据，可包含版本、功能等信息
    """
    try:
        instance_id = InstanceManagerAPI.register_instance(
            host=registration.host,
            port=registration.port,
            instance_id=registration.instance_id,
            weight=registration.weight,
            metadata=registration.metadata
        )
        
        return {
            "success": True,
            "instance_id": instance_id,
            "message": "实例注册成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实例注册失败: {str(e)}")

@router.delete("/instances/{instance_id}", summary="注销实例")
async def unregister_instance(instance_id: str):
    """
    从集群中注销指定实例
    
    - **instance_id**: 要注销的实例ID
    """
    success = InstanceManagerAPI.unregister_instance(instance_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="实例不存在")
    
    return {
        "success": True,
        "message": "实例注销成功"
    }

@router.get("/instances", summary="获取所有实例")
async def get_all_instances():
    """
    获取集群中所有实例的信息
    
    返回包含实例详细信息的列表，包括状态、指标等
    """
    try:
        instances = InstanceManagerAPI.get_all_instances()
        return {
            "success": True,
            "instances": instances,
            "count": len(instances)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实例列表失败: {str(e)}")

@router.get("/instances/loadbalance", summary="获取负载均衡实例")
async def get_load_balanced_instance():
    """
    根据当前负载均衡策略获取最佳实例
    
    返回推荐的实例信息，用于路由请求
    """
    try:
        instance = InstanceManagerAPI.get_instance_for_request()
        
        if not instance:
            raise HTTPException(status_code=503, detail="当前没有可用的健康实例")
        
        return {
            "success": True,
            "instance": instance.to_dict(),
            "url": instance.url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取负载均衡实例失败: {str(e)}")

@router.put("/instances/{instance_id}/status", summary="更新实例状态")
async def update_instance_status(instance_id: str, status_update: InstanceStatusUpdate):
    """
    更新指定实例的状态
    
    - **instance_id**: 实例ID
    - **status**: 新状态（active/inactive/maintenance/error）
    """
    try:
        InstanceManagerAPI.update_instance_status(instance_id, status_update.status)
        
        return {
            "success": True,
            "message": f"实例 {instance_id} 状态已更新为 {status_update.status}"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实例状态失败: {str(e)}")

@router.put("/instances/{instance_id}/metrics", summary="更新实例指标")
async def update_instance_metrics(instance_id: str, metrics: InstanceMetricsUpdate):
    """
    更新指定实例的性能指标
    
    - **instance_id**: 实例ID
    - **connections**: 当前连接数
    - **cpu_usage**: CPU使用率（0-100）
    - **memory_usage**: 内存使用率（0-100）
    """
    try:
        instance_manager.update_instance_metrics(
            instance_id,
            connections=metrics.connections,
            cpu_usage=metrics.cpu_usage,
            memory_usage=metrics.memory_usage
        )
        
        return {
            "success": True,
            "message": f"实例 {instance_id} 指标已更新"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实例指标失败: {str(e)}")

@router.get("/cluster/stats", summary="获取集群统计")
async def get_cluster_stats():
    """
    获取集群整体统计信息
    
    包括实例数量、健康状态、平均负载等指标
    """
    try:
        stats = InstanceManagerAPI.get_cluster_stats()
        
        return {
            "success": True,
            "cluster_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集群统计失败: {str(e)}")

@router.get("/cluster/health", summary="集群健康检查")
async def cluster_health_check():
    """
    集群整体健康检查
    
    返回集群健康状态和可用性信息
    """
    try:
        stats = InstanceManagerAPI.get_cluster_stats()
        healthy_instances = stats["healthy_instances"]
        total_instances = stats["total_instances"]
        
        if healthy_instances == 0:
            health_status = "critical"
            health_message = "没有可用的健康实例"
        elif healthy_instances < total_instances * 0.5:
            health_status = "warning"
            health_message = f"健康实例数量较少: {healthy_instances}/{total_instances}"
        else:
            health_status = "healthy"
            health_message = f"集群运行正常: {healthy_instances}/{total_instances} 实例健康"
        
        return {
            "success": True,
            "health_status": health_status,
            "message": health_message,
            "healthy_instances": healthy_instances,
            "total_instances": total_instances,
            "availability_percentage": round((healthy_instances / max(total_instances, 1)) * 100, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"集群健康检查失败: {str(e)}")

@router.post("/manager/start", summary="启动实例管理器")
async def start_instance_manager(background_tasks: BackgroundTasks):
    """
    启动多实例管理器服务
    
    开始心跳检测和健康监控
    """
    try:
        background_tasks.add_task(InstanceManagerAPI.start_manager)
        
        return {
            "success": True,
            "message": "实例管理器启动中"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动实例管理器失败: {str(e)}")

@router.post("/manager/stop", summary="停止实例管理器")
async def stop_instance_manager(background_tasks: BackgroundTasks):
    """
    停止多实例管理器服务
    
    停止心跳检测和健康监控
    """
    try:
        background_tasks.add_task(InstanceManagerAPI.stop_manager)
        
        return {
            "success": True,
            "message": "实例管理器停止中"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止实例管理器失败: {str(e)}")

@router.get("/config", summary="获取管理器配置")
async def get_manager_config():
    """
    获取当前实例管理器配置
    
    返回心跳间隔、超时设置、负载均衡策略等配置信息
    """
    try:
        return {
            "success": True,
            "config": {
                "heartbeat_interval": instance_manager.heartbeat_interval,
                "instance_timeout": instance_manager.instance_timeout,
                "load_balance_strategy": instance_manager.load_balance_strategy.value,
                "manager_running": instance_manager._running
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.put("/config", summary="更新管理器配置")
async def update_manager_config(config: LoadBalanceConfig):
    """
    更新实例管理器配置
    
    - **strategy**: 负载均衡策略
    - **heartbeat_interval**: 心跳间隔（可选）
    - **instance_timeout**: 实例超时时间（可选）
    """
    try:
        # 更新负载均衡策略
        try:
            strategy_enum = LoadBalanceStrategy(config.strategy)
            instance_manager.load_balance_strategy = strategy_enum
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的负载均衡策略: {config.strategy}")
        
        # 更新心跳间隔
        if config.heartbeat_interval is not None:
            instance_manager.heartbeat_interval = config.heartbeat_interval
        
        # 更新实例超时
        if config.instance_timeout is not None:
            instance_manager.instance_timeout = config.instance_timeout
        
        return {
            "success": True,
            "message": "管理器配置已更新",
            "config": {
                "heartbeat_interval": instance_manager.heartbeat_interval,
                "instance_timeout": instance_manager.instance_timeout,
                "load_balance_strategy": instance_manager.load_balance_strategy.value
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

# 添加WebSocket端点用于实时监控
@router.websocket("/monitor")
async def websocket_monitor(websocket):
    """
    WebSocket端点，用于实时监控集群状态
    
    客户端可以通过此端点实时接收集群状态变化
    """
    await websocket.accept()
    
    try:
        while True:
            # 获取集群状态
            stats = InstanceManagerAPI.get_cluster_stats()
            instances = InstanceManagerAPI.get_all_instances()
            
            # 发送状态更新
            message = {
                "type": "cluster_update",
                "timestamp": datetime.now().isoformat(),
                "cluster_stats": stats,
                "instances": instances
            }
            
            await websocket.send_json(message)
            await asyncio.sleep(5)  # 每5秒发送一次更新
    
    except Exception as e:
        print(f"WebSocket监控错误: {e}")
    finally:
        await websocket.close() 