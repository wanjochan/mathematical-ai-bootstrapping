# 开发工具和调试增强

本文档介绍CyberCorp Seed的开发工具和调试增强功能。

## 功能特性

- 🔥 **热重载** - 自动检测文件变化并重启服务器
- 📊 **调试增强** - 提供详细的调试信息和健康检查
- 📝 **增强日志** - 带图标和颜色的日志输出
- 🔍 **文件监控** - 智能文件变化检测，支持防抖处理
- 🚀 **开发模式** - 一键启动开发环境
- 🛠️ **调试API** - 专门的调试接口

## 使用方法

### 快速开始

启动开发模式：
```bash
cd seed
python dev_tools.py
```

### 命令行选项

```bash
python dev_tools.py [选项]

选项:
  --host HOST       服务器主机地址 (默认: localhost)
  --port PORT       服务器端口 (默认: 8000)
  --watch DIR [DIR] 监控目录列表 (默认: .)
  --script SCRIPT   启动脚本路径 (默认: main.py)
```

### 使用示例

```bash
# 基本使用
python dev_tools.py

# 自定义端口和主机
python dev_tools.py --host 0.0.0.0 --port 8080

# 监控特定目录
python dev_tools.py --watch . ../shared

# 使用不同的启动脚本
python dev_tools.py --script app.py
```

## 功能详解

### 热重载功能

开发工具会监控以下类型的文件变化：
- `.py` - Python源代码
- `.json` - JSON配置文件
- `.yaml/.yml` - YAML配置文件
- `.env` - 环境变量文件

**排除目录:**
- `.git` - Git仓库目录
- `__pycache__` - Python缓存目录
- `.pytest_cache` - pytest缓存目录
- `venv` - 虚拟环境目录
- `node_modules` - Node.js模块目录
- `.vscode` - VS Code配置目录

**防抖处理:**
文件变化检测包含1秒的防抖延迟，避免频繁重启。

### 增强日志

日志输出包含图标和增强信息：
- ℹ️ INFO - 一般信息
- ⚠️ WARNING - 警告信息  
- ❌ ERROR - 错误信息
- 🔍 DEBUG - 调试信息
- 🚀 STARTUP - 服务器启动
- ✅ SUCCESS - 成功状态

### 调试API端点

开发模式下提供额外的调试API：

#### 获取调试信息
```http
GET /debug/info
```

返回服务器、系统和进程信息：
```json
{
  "server_info": {
    "python_version": "3.10.0",
    "platform": "win32",
    "working_directory": "/path/to/project",
    "script_path": "main.py"
  },
  "system_info": {
    "cpu_count": 8,
    "cpu_percent": 15.2,
    "memory": {...},
    "disk": {...}
  },
  "process_info": {
    "pid": 12345,
    "memory_info": {...},
    "cpu_percent": 5.1,
    "num_threads": 12
  }
}
```

#### 详细健康检查
```http
GET /debug/health
```

返回详细的健康检查信息：
```json
{
  "status": "healthy",
  "timestamp": 1642123456.789,
  "checks": {
    "memory": {
      "status": "ok",
      "usage_percent": 65.2,
      "available_mb": 2048
    },
    "disk": {
      "status": "ok", 
      "usage_percent": 45.8,
      "free_gb": 120
    },
    "database": {
      "status": "ok",
      "message": "暂无数据库配置"
    },
    "external_services": {
      "status": "ok",
      "message": "暂无外部服务依赖"
    }
  }
}
```

#### 手动重载
```http
POST /debug/reload
```

手动触发服务器重载：
```json
{
  "message": "重载信号已发送"
}
```

## 开发模式特性

### 服务器管理

- **自动重启**: 检测到文件变化时自动重启服务器
- **重启保护**: 防止过于频繁的重启（2秒延迟）
- **进程监控**: 持续监控服务器进程状态
- **优雅关闭**: 支持SIGINT和SIGTERM信号处理

### 文件监控

- **递归监控**: 监控指定目录及其子目录
- **智能过滤**: 只监控相关文件类型
- **事件处理**: 支持文件修改和创建事件
- **实时反馈**: 显示检测到的文件变化

### 日志管理

- **双重输出**: 同时输出到控制台和日志文件
- **日志文件**: `dev_server.log`
- **日志级别**: INFO级别，包含所有重要信息
- **时间戳**: 每条日志都包含详细时间戳

## 配置和自定义

### 环境变量

```bash
# 设置开发模式端口
export DEV_PORT=8080

# 设置日志级别
export DEV_LOG_LEVEL=DEBUG

# 设置监控目录
export DEV_WATCH_DIRS=".,../shared"
```

### 自定义监控文件类型

修改`FileWatcher`类的`patterns`属性：
```python
file_watcher = FileWatcher(server_manager, patterns=['.py', '.json', '.txt'])
```

### 自定义排除目录

修改`FileWatcher`类的`exclude_dirs`集合：
```python
exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'custom_dir'}
```

## 集成到主应用

### 添加调试路由

在主应用中集成调试功能：
```python
from dev_tools import DebugEnhancer

app = FastAPI()
debug_enhancer = DebugEnhancer()

# 只在开发环境启用调试路由
if settings.environment == "development":
    debug_enhancer.setup_debug_routes(app)
```

### 条件化调试功能

```python
import os
from dev_tools import DevTools

if os.getenv("DEV_MODE", "false").lower() == "true":
    # 启用开发工具
    dev_tools = DevTools()
    dev_tools.start_dev_mode()
```

## 性能考虑

### 监控性能

- 文件监控使用系统原生API（inotify/ReadDirectoryChangesW）
- 防抖机制避免过度CPU使用
- 排除目录减少监控负载

### 内存使用

- 日志输出使用缓冲处理
- 进程监控定期清理
- 避免内存泄漏

### 启动时间

- 并行启动服务器和文件监控
- 快速故障检测和恢复
- 最小化重启时间

## 故障排除

### 常见问题

**Q: 文件变化未触发重载**
A: 检查文件是否在监控目录中，文件类型是否被支持

**Q: 重启过于频繁**
A: 增加防抖延迟时间，检查是否有工具频繁修改文件

**Q: 服务器启动失败**
A: 检查端口是否被占用，依赖是否安装完整

**Q: 监控目录不存在**
A: 确保指定的监控目录存在且可访问

### 调试开发工具

启用详细日志：
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

检查监控状态：
```python
# 检查文件监控线程
import threading
print([t.name for t in threading.enumerate()])

# 检查进程状态
import psutil
print(psutil.Process().children())
```

### 手动测试

测试文件监控：
```bash
# 创建测试文件
echo "test" > test.py

# 修改测试文件
echo "modified" >> test.py

# 删除测试文件
rm test.py
```

测试调试API：
```bash
# 测试调试信息
curl http://localhost:8000/debug/info

# 测试健康检查
curl http://localhost:8000/debug/health

# 测试手动重载
curl -X POST http://localhost:8000/debug/reload
```

## 最佳实践

1. **开发环境**: 始终在开发环境使用开发工具
2. **生产禁用**: 生产环境禁用所有调试功能
3. **监控范围**: 只监控必要的目录，避免过度监控
4. **日志管理**: 定期清理开发日志文件
5. **性能监控**: 注意开发工具对系统性能的影响

## 扩展开发

### 添加新的监控类型

```python
class CustomFileWatcher(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
    
    def on_modified(self, event):
        if event.src_path.endswith('.custom'):
            self.callback(event.src_path)
```

### 添加新的调试检查

```python
def check_custom_service(self) -> Dict[str, Any]:
    """检查自定义服务"""
    try:
        # 实现检查逻辑
        return {"status": "ok", "message": "服务正常"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### 自定义日志格式

```python
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # 自定义日志格式
        return super().format(record)
``` 