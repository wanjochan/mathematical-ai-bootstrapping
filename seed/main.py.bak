"""
CyberCorp Seed Server Main Application

FastAPI application with WebSocket support and hot-reload capability.
Serves as the foundation for CyberCorp system development.

Enhanced with:
- Robust error handling
- Dependency validation
- Comprehensive logging
- Graceful shutdown
- Health monitoring
"""

import sys
import os
import logging
import asyncio
import traceback
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# 导入配置和核心模块（带错误处理）
try:
    from config import settings
    from core.logging_config import setup_logging
except ImportError as e:
    print(f"❌ 核心配置导入失败: {e}")
    sys.exit(1)

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 系统依赖检查
def check_system_dependencies() -> Dict[str, Any]:
    """检查系统依赖"""
    dependencies = {
        "python_version": sys.version,
        "platform": sys.platform,
        "required_modules": {}
    }
    
    # 检查必需模块
    required_modules = [
        ("fastapi", "FastAPI框架"),
        ("uvicorn", "ASGI服务器"),
        ("pydantic", "数据验证"),
        ("asyncio", "异步支持")
    ]
    
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            dependencies["required_modules"][module_name] = {"status": "ok", "description": description}
            logger.debug(f"✅ {module_name} 模块检查通过")
        except ImportError as e:
            dependencies["required_modules"][module_name] = {"status": "missing", "error": str(e), "description": description}
            logger.error(f"❌ {module_name} 模块缺失: {e}")
    
    return dependencies

# 可选依赖检查
def check_optional_dependencies() -> Dict[str, Any]:
    """检查可选依赖"""
    optional_deps = {}
    
    optional_modules = [
        ("win32gui", "Windows GUI支持", "UI-TARS功能需要"),
        ("PIL", "图像处理", "截图功能需要"),
        ("ui_tars", "字节跳动UI自动化", "Computer-Use功能需要"),
        ("pyautogui", "自动化操作", "Computer-Use操作需要"),
        ("websockets", "WebSocket客户端", "实时通信需要")
    ]
    
    for module_name, description, usage in optional_modules:
        try:
            __import__(module_name)
            optional_deps[module_name] = {"status": "available", "description": description, "usage": usage}
            logger.debug(f"✅ 可选模块 {module_name} 可用")
        except ImportError:
            optional_deps[module_name] = {"status": "unavailable", "description": description, "usage": usage}
            logger.warning(f"⚠️  可选模块 {module_name} 不可用 - {usage}")
    
    return optional_deps

# 路由器导入（带错误处理）
def import_routers() -> Dict[str, Any]:
    """安全导入路由器"""
    routers_status = {}
    
    router_configs = [
        ("api", "基础API", True),
        ("websocket", "WebSocket通信", True),
        ("projects", "项目管理", True),
        ("multi_instance", "多实例管理", False),  # 新增组件
        ("collaboration", "协作通信协议", False),  # 新增组件
        ("ui_tars", "UI-TARS组件", False),  # 可选组件
        ("computer_use", "Computer-Use操作接口", False)  # 可选组件
    ]
    
    imported_routers = {}
    
    for router_name, description, required in router_configs:
        try:
            module = __import__(f"routers.{router_name}", fromlist=[router_name])
            imported_routers[router_name] = module
            routers_status[router_name] = {"status": "loaded", "description": description, "required": required}
            logger.info(f"✅ 路由器 {router_name} 加载成功")
        except ImportError as e:
            routers_status[router_name] = {"status": "failed", "error": str(e), "description": description, "required": required}
            if required:
                logger.error(f"❌ 必需路由器 {router_name} 加载失败: {e}")
                raise
            else:
                logger.warning(f"⚠️  可选路由器 {router_name} 加载失败: {e}")
    
    return imported_routers, routers_status

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动阶段
    logger.info("🚀 CyberCorp Seed Server 启动中...")
    
    try:
        # 系统检查
        deps = check_system_dependencies()
        logger.info(f"Python版本: {deps['python_version']}")
        logger.info(f"运行平台: {deps['platform']}")
        
        # 检查必需依赖
        missing_deps = [name for name, info in deps["required_modules"].items() if info["status"] != "ok"]
        if missing_deps:
            logger.error(f"❌ 缺失必需依赖: {missing_deps}")
            raise SystemExit("缺失必需依赖，无法启动服务器")
        
        # 检查可选依赖
        optional_deps = check_optional_dependencies()
        available_features = [name for name, info in optional_deps.items() if info["status"] == "available"]
        logger.info(f"✅ 可用功能模块: {available_features}")
        
        # 应用启动信息
        logger.info(f"📝 环境: {settings.environment}")
        logger.info(f"🌐 监听地址: {settings.host}:{settings.port}")
        logger.info(f"📊 日志级别: {settings.log_level}")
        
        # 启动完成
        logger.info("✅ CyberCorp Seed Server 启动成功")
        
        yield  # 应用运行阶段
        
    except Exception as e:
        logger.error(f"❌ 启动过程中出现错误: {e}")
        logger.error(traceback.format_exc())
        raise
    
    finally:
        # 关闭阶段
        logger.info("🛑 CyberCorp Seed Server 关闭中...")
        logger.info("✅ CyberCorp Seed Server 已安全关闭")

# 创建FastAPI应用
try:
    app = FastAPI(
        title="CyberCorp Seed Server",
        description="增强版种子服务器：为CyberCorp提供基础开发工具和Computer-Use技术支持",
        version="1.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    logger.info("✅ FastAPI应用创建成功")
except Exception as e:
    logger.error(f"❌ FastAPI应用创建失败: {e}")
    sys.exit(1)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入并注册路由器
try:
    imported_routers, routers_status = import_routers()
    
    # 注册成功导入的路由器
    for router_name, module in imported_routers.items():
        try:
            if router_name == "websocket":
                app.include_router(module.router, prefix="/ws", tags=["websocket"])
            else:
                app.include_router(module.router, prefix="/api/v1", tags=[router_name])
            logger.info(f"✅ 路由器 {router_name} 注册成功")
        except Exception as e:
            logger.error(f"❌ 路由器 {router_name} 注册失败: {e}")

except Exception as e:
    logger.error(f"❌ 路由器导入失败: {e}")
    # 在开发环境下可以继续运行，生产环境下应该退出
    if settings.environment == "production":
        sys.exit(1)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"❌ 未处理的异常: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "服务器遇到意外错误，请稍后重试",
            "request_id": getattr(request, "request_id", None),
            "timestamp": asyncio.get_event_loop().time()
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "request_id": getattr(request, "request_id", None)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """请求验证异常处理器"""
    logger.warning(f"请求验证失败: {exc}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "请求验证失败",
            "message": "请求参数不符合要求",
            "details": exc.errors(),
            "request_id": getattr(request, "request_id", None)
        }
    )

# 根路径
@app.get("/")
async def root():
    """根端点 - 服务器状态信息"""
    try:
        # 收集系统状态
        deps = check_system_dependencies()
        optional_deps = check_optional_dependencies()
        
        # 统计路由器状态
        _, router_status = import_routers()
        loaded_routers = [name for name, info in router_status.items() if info["status"] == "loaded"]
        failed_routers = [name for name, info in router_status.items() if info["status"] == "failed"]
        
        return {
            "service": "CyberCorp Seed Server",
            "version": "1.1.0",
            "status": "healthy",
            "environment": settings.environment,
            "features": {
                "loaded_routers": loaded_routers,
                "failed_routers": failed_routers,
                "available_modules": [name for name, info in optional_deps.items() if info["status"] == "available"],
                "missing_modules": [name for name, info in optional_deps.items() if info["status"] == "unavailable"]
            },
            "system": {
                "python_version": deps["python_version"],
                "platform": deps["platform"]
            },
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "api": "/api/v1",
                "websocket": "/ws"
            }
        }
    except Exception as e:
        logger.error(f"根端点错误: {e}")
        raise HTTPException(status_code=500, detail="服务器状态检查失败")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 基础健康检查
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "server": "CyberCorp Seed Server",
            "version": "1.1.0"
        }
        
        # 检查关键组件
        components = {}
        
        # 检查路由器状态
        try:
            _, router_status = import_routers()
            components["routers"] = {
                "status": "ok",
                "loaded": len([r for r in router_status.values() if r["status"] == "loaded"]),
                "failed": len([r for r in router_status.values() if r["status"] == "failed"])
            }
        except Exception as e:
            components["routers"] = {"status": "error", "error": str(e)}
        
        # 检查可选依赖
        try:
            optional_deps = check_optional_dependencies()
            components["optional_features"] = {
                "available": len([d for d in optional_deps.values() if d["status"] == "available"]),
                "total": len(optional_deps)
            }
        except Exception as e:
            components["optional_features"] = {"status": "error", "error": str(e)}
        
        health_status["components"] = components
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "error": str(e)
        }

# 服务器信息端点
@app.get("/info")
async def server_info():
    """服务器详细信息"""
    try:
        deps = check_system_dependencies()
        optional_deps = check_optional_dependencies()
        _, router_status = import_routers()
        
        return {
            "server": {
                "name": "CyberCorp Seed Server",
                "version": "1.1.0",
                "environment": settings.environment,
                "host": settings.host,
                "port": settings.port
            },
            "system": deps,
            "optional_dependencies": optional_deps,
            "routers": router_status,
            "features": {
                "cors_enabled": True,
                "websocket_support": True,
                "hot_reload": settings.environment == "development",
                "ui_tars_enabled": "ui_tars" in [r for r, s in router_status.items() if s["status"] == "loaded"]
            }
        }
    except Exception as e:
        logger.error(f"服务器信息获取失败: {e}")
        raise HTTPException(status_code=500, detail="无法获取服务器信息")

if __name__ == "__main__":
    try:
        logger.info("🎯 直接启动模式")
        
        # 检查基础依赖
        deps = check_system_dependencies()
        missing = [name for name, info in deps["required_modules"].items() if info["status"] != "ok"]
        if missing:
            logger.error(f"❌ 缺失必需依赖: {missing}")
            sys.exit(1)
        
        # 启动服务器
        uvicorn.run(
            "seed.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.environment == "development",
            log_level=settings.log_level.lower(),
            access_log=True,
            use_colors=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 服务器被用户中断")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 