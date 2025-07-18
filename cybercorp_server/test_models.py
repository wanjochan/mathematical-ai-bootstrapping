#!/usr/bin/env python3
"""模型和服务单元测试"""

import pytest
from src.models import SystemMetrics, Employee, TaskStatus, ProcessStatus
from src.services.config_service import ConfigService
from src.services.window_service import WindowService


class TestModels:
    """测试数据模型"""
    
    def test_system_metrics(self):
        """测试系统模型"""
        metrics_data = {
            "cpu": 75.5,
            "memory": 65.2,
            "disk": 80.1,
            "uptime": 1205847
        }
        metrics = SystemMetrics(**metrics_data)
        assert metrics.cpu == 75.5
        assert metrics.memory == 65.2
        assert metrics.disk == 80.1
        assert metrics.uptime == 1205847
    
    def test_employee_creation(self):
        """测试员工模型"""
        employee_data = {
            "id": "emp-001",
            "name": "张三",
            "email": "zhangsan@company.com",
            "department": "技术部",
            "position": "软件工程师",
            "type": "remote",
            "skill_tags": ["Python", "React"]
        }
        employee = Employee(**employee_data)
        assert employee.name == "张三"
        assert employee.email == "zhangsan@company.com"
        assert "Python" in employee.skill_tags
    
    def test_task_status_values(self):
        """测试任务状态枚举"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_process_status_values(self):
        """测试进程状态枚举"""
        assert ProcessStatus.RUNNING.value == "running"
        assert ProcessStatus.SLEEPING.value == "sleeping"
        assert ProcessStatus.STOPPED.value == "stopped"


class TestServices:
    """测试服务类"""
    
    def test_config_service_init(self):
        """测试配置服务初始化"""
        config_service = ConfigService()
        assert config_service is not None
    
    def test_window_service_init(self):
        """测试窗口服务初始化"""
        window_service = WindowService()
        assert window_service is not None
    
    def test_config_service_methods(self):
        """测试配置服务方法"""
        config_service = ConfigService()
        
        # 测试获取系统信息
        config = config_service.get_system_config()
        assert isinstance(config, dict)
        
        # 测试获取应用配置
        app_config = config_service.get_app_config()
        assert isinstance(app_config, dict)


class TestAPIEndpoints:
    """API端点基础测试"""
    
    def test_import_modules(self):
        """测试模块导入"""
        try:
            from src.main import CyberCorpServer
            from src.routers import employees_router, tasks_router
            assert True
        except ImportError as e:
            pytest.fail(f"导入失败: {e}")
    
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        # 这里可以添加更详细的测试
        pass


def test_package_imports():
    """测试包导入"""
    try:
        import src.models
        import src.services
        import src.routers
        assert True
    except ImportError as e:
        pytest.fail(f"包导入失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])