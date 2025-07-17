# 开发环境自动配置脚本

本文档介绍如何使用`setup_dev_env.py`脚本快速配置CyberCorp Seed开发环境。

## 功能特性

- ✅ **虚拟环境管理** - 自动创建和配置Python虚拟环境
- ✅ **依赖管理** - 自动安装所有必需的依赖包
- ✅ **配置文件生成** - 创建开发和生产环境配置
- ✅ **便捷脚本** - 生成启动、开发、测试脚本
- ✅ **Git钩子设置** - 配置pre-commit代码检查
- ✅ **跨平台支持** - 支持Windows、Linux、macOS

## 使用方法

### 快速开始

在项目根目录运行：

```bash
cd seed
python setup_dev_env.py
```

### 执行步骤

脚本将自动执行以下步骤：

1. **检查前置条件**
   - Python 3.8+ 版本检查
   - Git 可用性检查
   - 项目结构验证

2. **创建虚拟环境**
   - 在项目根目录创建`venv/`目录
   - 配置独立的Python环境

3. **安装依赖包**
   - 升级pip到最新版本
   - 安装requirements.txt中的所有依赖

4. **创建配置文件**
   - `config/development.json` - 开发环境配置
   - `config/production.json` - 生产环境配置
   - `.env.example` - 环境变量示例

5. **创建便捷脚本**
   - `scripts/start.bat/.sh` - 启动服务器
   - `scripts/dev.bat/.sh` - 开发模式
   - `scripts/test.bat/.sh` - 运行测试

6. **设置Git钩子**
   - pre-commit钩子用于代码质量检查
   - 自动格式化检查和测试

7. **验证环境配置**
   - 确认虚拟环境正常工作
   - 验证核心依赖可用性

## 生成的文件结构

```
seed/
├── config/
│   ├── development.json    # 开发环境配置
│   └── production.json     # 生产环境配置
├── scripts/
│   ├── start.bat/.sh      # 启动脚本
│   ├── dev.bat/.sh        # 开发脚本
│   └── test.bat/.sh       # 测试脚本
├── .env.example           # 环境变量示例
└── requirements.txt       # Python依赖(如不存在会创建)

venv/                      # 虚拟环境(在项目根目录)
└── ...

.git/hooks/                # Git钩子
└── pre-commit            # 预提交检查
```

## 配置说明

### 开发环境配置 (development.json)

```json
{
  "app_name": "CyberCorp Seed Server",
  "environment": "development",
  "host": "localhost",
  "port": 8000,
  "log_level": "DEBUG",
  "reload": true,
  "cors_origins": ["http://localhost:3000"],
  "websocket": {
    "max_connections": 100,
    "ping_interval": 30
  },
  "projects": {
    "root_dir": "projects",
    "max_project_size": "100MB"
  }
}
```

### 环境变量 (.env.example)

```bash
SEED_ENVIRONMENT=development
SEED_HOST=localhost
SEED_PORT=8000
SEED_LOG_LEVEL=DEBUG
```

## 使用配置后的环境

### 激活虚拟环境

Windows:
```cmd
venv\Scripts\activate
```

Unix/Linux/macOS:
```bash
source venv/bin/activate
```

### 启动服务器

使用便捷脚本：
```bash
# Windows
scripts\start.bat

# Unix/Linux/macOS
scripts/start.sh
```

或手动启动：
```bash
# 激活虚拟环境后
python main.py
```

### 开发模式

使用便捷脚本：
```bash
# Windows
scripts\dev.bat

# Unix/Linux/macOS
scripts/dev.sh
```

或手动启动：
```bash
# 激活虚拟环境后
uvicorn main:app --reload --host localhost --port 8000
```

### 运行测试

使用便捷脚本：
```bash
# Windows
scripts\test.bat

# Unix/Linux/macOS
scripts/test.sh
```

或手动运行：
```bash
# 激活虚拟环境后
pytest -v
```

## 故障排除

### 常见问题

**Q: Python版本检查失败**
A: 确保安装了Python 3.8或更高版本

**Q: 虚拟环境创建失败**
A: 检查磁盘空间和权限，确保Python venv模块可用

**Q: 依赖安装失败**
A: 检查网络连接，或使用国内镜像源

**Q: 权限错误**
A: 在Windows上以管理员身份运行，或检查文件夹权限

### 重置环境

如果环境配置出现问题，可以重置：

1. 删除虚拟环境目录：`rm -rf venv/`
2. 删除配置文件：`rm -rf seed/config/`
3. 重新运行配置脚本

### 手动验证

检查环境是否正确配置：

```bash
# 激活虚拟环境
source venv/bin/activate  # Unix
# 或
venv\Scripts\activate     # Windows

# 检查Python版本
python --version

# 检查依赖
python -c "import fastapi, uvicorn, websockets; print('依赖正常')"

# 测试服务器启动
python seed/main.py
```

## 扩展配置

### 自定义配置

如需修改配置，可以编辑：
- `seed/config/development.json` - 开发环境配置
- `seed/config/production.json` - 生产环境配置

### 添加依赖

在`requirements.txt`中添加新依赖后，重新运行：
```bash
pip install -r requirements.txt
```

### 环境变量

复制并修改环境变量文件：
```bash
cp seed/.env.example seed/.env
# 编辑 .env 文件设置实际值
```

## 开发建议

1. **使用虚拟环境** - 始终在虚拟环境中开发
2. **代码格式化** - 提交前运行`black seed/`
3. **运行测试** - 提交前确保所有测试通过
4. **配置管理** - 使用环境变量管理敏感配置
5. **日志记录** - 开发时使用DEBUG级别日志

## 支持的Python版本

- Python 3.8+
- 推荐使用Python 3.10或3.11

## 支持的操作系统

- Windows 10/11
- macOS 10.15+
- Ubuntu 18.04+
- 其他主流Linux发行版 