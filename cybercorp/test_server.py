#!/usr/bin/env python3
"""CyberCorp Server 测试脚本"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """测试健康检查"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            data = await response.json()
            logger.info(f"Health check: {data}")
            assert response.status == 200
            assert data["status"] == "healthy"

async def test_create_employee():
    """测试创建员工"""
    async with aiohttp.ClientSession() as session:
        employee_data = {
            "name": "测试员工",
            "role": "developer",
            "skill_level": 0.8
        }
        async with session.post(
            f"{BASE_URL}/api/employees",
            json=employee_data
        ) as response:
            data = await response.json()
            logger.info(f"Created employee: {data}")
            assert response.status == 200
            assert "employee_id" in data
            return data["employee_id"]

async def test_create_task():
    """测试创建任务"""
    async with aiohttp.ClientSession() as session:
        task_data = {
            "name": "测试任务",
            "description": "这是一个测试任务",
            "priority": 3,
            "estimated_duration": 3600
        }
        async with session.post(
            f"{BASE_URL}/api/tasks",
            json=task_data
        ) as response:
            data = await response.json()
            logger.info(f"Created task: {data}")
            assert response.status == 200
            assert "task_id" in data
            return data["task_id"]

async def test_get_tasks():
    """测试获取任务列表"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/tasks") as response:
            data = await response.json()
            logger.info(f"Tasks: {len(data)} tasks found")
            assert response.status == 200
            return data

async def test_get_employees():
    """测试获取员工列表"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/employees") as response:
            data = await response.json()
            logger.info(f"Employees: {len(data)} employees found")
            assert response.status == 200
            return data

async def test_business_analysis():
    """测试业务分析"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/business-analysis") as response:
            data = await response.json()
            logger.info(f"Business analysis: {data}")
            assert response.status == 200
            return data

async def test_dashboard():
    """测试监控大屏"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/monitoring/dashboard") as response:
            data = await response.json()
            logger.info(f"Dashboard data loaded")
            assert response.status == 200
            return data

async def test_strategic_decision():
    """测试战略决策"""
    async with aiohttp.ClientSession() as session:
        decision_data = {
            "title": "扩大团队规模",
            "description": "当前任务积压，需要增加人手",
            "priority": 4,
            "estimated_impact": 0.8,
            "required_resources": ["hr_manager"],
            "timeline_hours": 24
        }
        async with session.post(
            f"{BASE_URL}/api/strategic-decisions",
            json=decision_data
        ) as response:
            data = await response.json()
            logger.info(f"Created strategic decision: {data}")
            assert response.status == 200
            return data["decision_id"]

async def test_meeting():
    """测试会议功能"""
    async with aiohttp.ClientSession() as session:
        meeting_data = {
            "title": "项目启动会议",
            "participants": ["张三", "李四", "王五"],
            "start_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration_minutes": 60,
            "agenda": "讨论项目计划和任务分配"
        }
        async with session.post(
            f"{BASE_URL}/api/meetings",
            json=meeting_data
        ) as response:
            data = await response.json()
            logger.info(f"Created meeting: {data}")
            assert response.status == 200
            return data["meeting_id"]

async def run_all_tests():
    """运行所有测试"""
    logger.info("Starting CyberCorp Server tests...")
    
    try:
        # 基础测试
        await test_health_check()
        
        # 员工管理测试
        employee_id = await test_create_employee()
        employees = await test_get_employees()
        
        # 任务管理测试
        task_id = await test_create_task()
        tasks = await test_get_tasks()
        
        # 智能助理测试
        await test_business_analysis()
        decision_id = await test_strategic_decision()
        
        # 会议测试
        meeting_id = await test_meeting()
        
        # 监控测试
        dashboard = await test_dashboard()
        
        logger.info("✅ All tests passed successfully!")
        
        return {
            "status": "success",
            "employee_id": employee_id,
            "task_id": task_id,
            "decision_id": decision_id,
            "meeting_id": meeting_id,
            "total_employees": len(employees),
            "total_tasks": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(run_all_tests())