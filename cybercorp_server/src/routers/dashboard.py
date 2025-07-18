"""Real-time dashboard endpoints for CyberCorp System Monitor."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
from typing import Dict, Any
from datetime import datetime
import psutil
from ..models.system import SystemMetrics

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory="src/templates")


@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """系统大屏主页"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


async def system_data_generator():
    """实时系统数据生成器"""
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "network": psutil.net_io_counters()._asdict(),
            "processes": len(psutil.pids()),
            "uptime": datetime.now().timestamp() - psutil.boot_time()
        }
        
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(2)


@dashboard_router.get("/events")
async def system_events():
    """SSE端点：实时系统数据"""
    return StreamingResponse(
        system_data_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@dashboard_router.get("/metrics")
async def dashboard_metrics():
    """REST API：获取当前指标"""
    return await _generate_metrics()


async def _generate_metrics():
    """生成系统指标"""
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    return SystemMetrics(
        cpu_usage=cpu,
        memory_usage=memory.percent,
        disk_usage=psutil.disk_usage('/').percent,
        network_io=psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv,
        uptime=datetime.now().timestamp() - psutil.boot_time()
    )