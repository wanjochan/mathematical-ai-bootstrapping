# Seed CLI工具使用指南

Seed CLI是CyberCorp Seed服务器的命令行工具，提供便捷的项目管理和开发工具功能。

## 安装

### 自动安装
```bash
python install_cli.py
```

### 手动使用
```bash
python cli.py <命令>
```

## 基本命令

### 服务器管理

#### 检查服务器健康状态
```bash
seed health
```
显示服务器运行状态和系统信息。

#### 查看服务器状态
```bash
seed status
```
显示服务器详细配置和运行时信息。

### 项目管理

#### 创建新项目
```bash
seed create <项目名> [选项]

# 选项:
# -d, --description  项目描述
# -t, --template     项目模板 (默认: basic)

# 示例:
seed create myapp -d "我的应用" -t python
```

#### 列出所有项目
```bash
seed list
```

### 依赖管理

#### 安装依赖
```bash
seed install <项目名> <包名1> [包名2] ... [选项]

# 选项:
# --dev  安装为开发依赖

# 示例:
seed install myapp requests flask
seed install myapp pytest --dev
```

#### 查看项目依赖
```bash
seed deps <项目名>

# 示例:
seed deps myapp
```

### 代码格式化

#### 格式化项目代码
```bash
seed format <项目名> [选项]

# 选项:
# --files  指定要格式化的文件

# 示例:
seed format myapp
seed format myapp --files main.py utils.py
```

## 高级选项

### 自定义服务器URL
```bash
seed --url http://192.168.1.100:8000/api/v1 health
```

### 获取帮助
```bash
seed --help
seed <命令> --help
```

## 使用示例

### 完整的项目创建和开发流程

```bash
# 1. 检查服务器状态
seed health

# 2. 创建新项目
seed create webapp -d "我的Web应用" -t python

# 3. 查看所有项目
seed list

# 4. 安装依赖
seed install webapp fastapi uvicorn requests

# 5. 安装开发依赖
seed install webapp pytest black --dev

# 6. 查看依赖列表
seed deps webapp

# 7. 格式化代码
seed format webapp
```

### 批量操作

```bash
# 为多个项目安装相同依赖
seed install project1 requests
seed install project2 requests
seed install project3 requests

# 批量格式化
seed format project1
seed format project2
seed format project3
```

## 错误处理

CLI工具提供友好的错误信息：

- **连接错误**: 如果无法连接到seed服务器，会提示启动服务器的方法
- **权限错误**: 如果没有足够权限，会建议相应的解决方案
- **参数错误**: 提供正确的命令格式和参数说明

## 配置文件

CLI工具支持环境变量配置：

```bash
# 设置默认服务器URL
export SEED_SERVER_URL=http://localhost:8000/api/v1

# 使用配置的URL
seed health
```

## 集成开发环境

### VS Code集成
可以在VS Code的任务配置中使用seed命令：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Seed: 创建项目",
            "type": "shell",
            "command": "seed",
            "args": ["create", "${input:projectName}"]
        },
        {
            "label": "Seed: 格式化代码",
            "type": "shell",
            "command": "seed",
            "args": ["format", "${workspaceFolderBasename}"]
        }
    ]
}
```

### Shell别名
在shell配置文件中添加常用别名：

```bash
# ~/.bashrc 或 ~/.zshrc
alias sc='seed create'
alias sl='seed list'
alias si='seed install'
alias sf='seed format'
alias sh='seed health'
```

## 故障排除

### 常见问题

**Q: 命令提示"seed命令未找到"**
A: 检查CLI工具是否正确安装，或使用`python cli.py`代替

**Q: 连接服务器失败**
A: 确保seed服务器正在运行：`python main.py`

**Q: 权限错误**
A: 在Windows上以管理员身份运行，在Unix系统上检查文件权限

**Q: 命令执行超时**
A: 检查网络连接，或增加超时时间

### 调试模式

启用详细输出：
```bash
python cli.py --verbose <命令>
```

## 扩展开发

CLI工具采用模块化设计，可以轻松添加新功能：

1. 在`SeedCLI`类中添加新方法
2. 在`main()`函数中添加新的子命令解析器
3. 更新帮助文档

示例添加新命令：
```python
def my_new_command(self, arg1: str):
    """新命令的实现"""
    result = self._make_request("GET", f"/my-endpoint/{arg1}")
    print(f"结果: {result}")
``` 