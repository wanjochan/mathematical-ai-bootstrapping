"""
CyberCorp AI中控助理服务器

FastAPI服务器，提供AI中控助理的完整API接口。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

# 导入路由
from routers.ai_orchestrator_api import router as orchestrator_router
from routers.collaboration import router as collaboration_router
from routers.api import router as api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 CyberCorp AI中控助理服务器启动中...")
    
    # 启动时的初始化逻辑
    try:
        # 这里可以添加启动时的初始化任务
        logger.info("✅ 服务器初始化完成")
        yield
    finally:
        # 关闭时的清理逻辑
        logger.info("🛑 CyberCorp AI中控助理服务器关闭")

# 创建FastAPI应用
app = FastAPI(
    title="CyberCorp AI中控助理",
    description="""
    🤖 **CyberCorp AI中控助理** - 智能任务协调和执行系统
    
    ## 核心功能
    
    - **模式化处理**: 支持Architect、Code、Debug、Orchestrator、Ask五种专业化模式
    - **智能工具调度**: 自动选择最佳的computer-use、browser-use、IDE等工具
    - **实时协作**: WebSocket支持实时任务状态更新
    - **上下文记忆**: 跨会话的任务历史和偏好学习
    
    ## 快速开始
    
    1. **简单任务**: `POST /ai-orchestrator/tasks` 提交任务描述
    2. **实时交互**: 连接 `ws://localhost:8000/ai-orchestrator/ws/{session_id}`
    3. **快捷接口**: 使用 `/ai-orchestrator/quick/*` 系列接口
    
    ## 使用示例
    
    ```python
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        task_data = {
            "description": "用Python实现一个计算器",
            "context": {"language": "python"}
        }
        async with session.post("http://localhost:8000/ai-orchestrator/tasks", json=task_data) as resp:
            result = await resp.json()
            print(f"任务完成: {result['mode']} 模式，耗时 {result['execution_time']:.2f}s")
    ```
    """,
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(orchestrator_router)
app.include_router(collaboration_router)
app.include_router(api_router)

# 首页
@app.get("/", response_class=HTMLResponse)
async def root():
    """首页 - 提供简单的Web界面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CyberCorp AI中控助理</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            .feature { background: #ecf0f1; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
            .api-link { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
            .api-link:hover { background: #2980b9; }
            .demo-box { background: #e8f5e8; padding: 15px; border: 1px solid #27ae60; border-radius: 5px; margin: 20px 0; }
            code { background: #f8f8f8; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 CyberCorp AI中控助理</h1>
            
            <p>欢迎使用CyberCorp AI中控助理！这是一个智能任务协调和执行系统，基于模式化AI工作流程。</p>
            
            <div class="feature">
                <h3>🎯 核心功能</h3>
                <ul>
                    <li><strong>模式化处理</strong>: 支持Architect、Code、Debug、Orchestrator、Ask五种专业化模式</li>
                    <li><strong>智能工具调度</strong>: 自动选择最佳的computer-use、browser-use、IDE等工具</li>
                    <li><strong>实时协作</strong>: WebSocket支持实时任务状态更新</li>
                    <li><strong>上下文记忆</strong>: 跨会话的任务历史和偏好学习</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>🚀 快速开始</h3>
                <a href="/docs" class="api-link">📚 API文档</a>
                <a href="/ai-orchestrator/status" class="api-link">📊 系统状态</a>
                <a href="/ai-orchestrator/metrics" class="api-link">📈 性能指标</a>
            </div>
            
            <div class="demo-box">
                <h3>💡 使用示例</h3>
                <p><strong>简单任务提交:</strong></p>
                <pre><code>curl -X POST "http://localhost:8000/ai-orchestrator/tasks" \\
     -H "Content-Type: application/json" \\
     -d '{"description": "用Python实现一个计算器", "context": {"language": "python"}}'</code></pre>
                
                <p><strong>快捷编程接口:</strong></p>
                <pre><code>curl -X POST "http://localhost:8000/ai-orchestrator/quick/code?description=排序算法&language=python"</code></pre>
                
                <p><strong>快速询问:</strong></p>
                <pre><code>curl -X POST "http://localhost:8000/ai-orchestrator/quick/ask?question=什么是微服务架构？"</code></pre>
            </div>
            
            <div class="feature">
                <h3>🔗 WebSocket实时连接</h3>
                <p>连接到 <code>ws://localhost:8000/ai-orchestrator/ws/{session_id}</code> 进行实时交互</p>
                <p>支持的命令: <code>execute_task</code>, <code>get_status</code>, <code>get_metrics</code></p>
            </div>
            
            <div class="feature">
                <h3>📖 更多资源</h3>
                <ul>
                    <li>运行 <code>python examples/ai_orchestrator_demo.py</code> 查看完整演示</li>
                    <li>运行 <code>python examples/ai_orchestrator_demo.py interactive</code> 进入交互模式</li>
                    <li>查看 <code>/docs</code> 获取完整API文档</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "cybercorp-ai-orchestrator",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberCorp AI中控助理服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式热重载")
    parser.add_argument("--log-level", default="info", help="日志级别")
    
    args = parser.parse_args()
    
    print(f"""
    🤖 CyberCorp AI中控助理启动中...
    
    📍 服务地址: http://{args.host}:{args.port}
    📚 API文档: http://{args.host}:{args.port}/docs  
    📊 系统状态: http://{args.host}:{args.port}/ai-orchestrator/status
    
    💡 快速测试:
    curl -X POST "http://{args.host}:{args.port}/ai-orchestrator/quick/ask?question=你好"
    """)
    
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    ) 