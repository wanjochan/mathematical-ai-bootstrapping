#!/usr/bin/env python3
"""
CyberCorp Seed开发环境自动配置脚本
一键式配置开发环境，包括虚拟环境、依赖安装、配置文件生成等
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import venv
import platform

class DevEnvSetup:
    """开发环境配置管理器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.seed_dir = self.project_root / "seed"
        self.venv_dir = self.project_root / "venv"
        self.config_dir = self.seed_dir / "config"
        
        # 平台相关配置
        self.is_windows = platform.system() == "Windows"
        self.python_exe = "python" if self.is_windows else "python3"
        self.pip_exe = "pip" if self.is_windows else "pip3"
        
    def check_prerequisites(self) -> bool:
        """检查系统前置条件"""
        print("🔍 检查系统前置条件...")
        
        # 检查Python版本
        try:
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                print("❌ Python版本过低，需要Python 3.8或更高版本")
                return False
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        except Exception as e:
            print(f"❌ Python检查失败: {e}")
            return False
        
        # 检查git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Git {result.stdout.strip()}")
            else:
                print("⚠️  Git未安装，但不影响基本功能")
        except FileNotFoundError:
            print("⚠️  Git未安装，但不影响基本功能")
        
        # 检查项目结构
        if not self.seed_dir.exists():
            print("❌ 未找到seed目录，请确保在正确的项目根目录运行")
            return False
        
        print("✅ 前置条件检查通过")
        return True
    
    def create_virtual_environment(self) -> bool:
        """创建虚拟环境"""
        print("🌍 创建虚拟环境...")
        
        if self.venv_dir.exists():
            print("📁 虚拟环境目录已存在，删除旧环境...")
            shutil.rmtree(self.venv_dir)
        
        try:
            venv.create(self.venv_dir, with_pip=True)
            print(f"✅ 虚拟环境创建成功: {self.venv_dir}")
            return True
        except Exception as e:
            print(f"❌ 虚拟环境创建失败: {e}")
            return False
    
    def get_venv_python(self) -> Path:
        """获取虚拟环境中的Python可执行文件路径"""
        if self.is_windows:
            return self.venv_dir / "Scripts" / "python.exe"
        else:
            return self.venv_dir / "bin" / "python"
    
    def get_venv_pip(self) -> Path:
        """获取虚拟环境中的pip可执行文件路径"""
        if self.is_windows:
            return self.venv_dir / "Scripts" / "pip.exe"
        else:
            return self.venv_dir / "bin" / "pip"
    
    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        print("📦 安装项目依赖...")
        
        requirements_file = self.seed_dir / "requirements.txt"
        if not requirements_file.exists():
            print("⚠️  requirements.txt不存在，创建基本依赖文件...")
            self.create_requirements_file()
        
        pip_exe = self.get_venv_pip()
        
        try:
            # 升级pip
            print("🔄 升级pip...")
            result = subprocess.run([
                str(pip_exe), "install", "--upgrade", "pip"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️  pip升级警告: {result.stderr}")
            
            # 安装依赖
            print("📥 安装项目依赖...")
            result = subprocess.run([
                str(pip_exe), "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖安装完成")
                return True
            else:
                print(f"❌ 依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 安装过程出错: {e}")
            return False
    
    def create_requirements_file(self):
        """创建基本的requirements.txt文件"""
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "websockets>=12.0",
            "pydantic>=2.0.0",
            "pydantic-settings>=2.0.0",
            "requests>=2.31.0",
            "psutil>=5.9.0",
            "aiofiles>=23.0.0",
            "python-multipart>=0.0.6",
            "jinja2>=3.1.0",
            "black>=23.0.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0"
        ]
        
        requirements_file = self.seed_dir / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        
        print(f"📝 创建requirements.txt: {len(requirements)}个依赖")
    
    def create_config_files(self) -> bool:
        """创建配置文件"""
        print("⚙️  创建配置文件...")
        
        try:
            # 创建配置目录
            self.config_dir.mkdir(exist_ok=True)
            
            # 创建开发环境配置
            dev_config = {
                "app_name": "CyberCorp Seed Server",
                "app_version": "0.1.0",
                "environment": "development",
                "host": "localhost",
                "port": 8000,
                "log_level": "DEBUG",
                "reload": True,
                "cors_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "websocket": {
                    "max_connections": 100,
                    "ping_interval": 30,
                    "ping_timeout": 10
                },
                "projects": {
                    "root_dir": "projects",
                    "max_project_size": "100MB",
                    "allowed_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".yml", ".yaml"]
                },
                "computer_use": {
                    "enabled": True,
                    "screenshot_quality": 85,
                    "operation_timeout": 30
                }
            }
            
            dev_config_file = self.config_dir / "development.json"
            with open(dev_config_file, 'w', encoding='utf-8') as f:
                json.dump(dev_config, f, indent=2, ensure_ascii=False)
            
            # 创建生产环境配置模板
            prod_config = dev_config.copy()
            prod_config.update({
                "environment": "production",
                "log_level": "INFO",
                "reload": False,
                "host": "0.0.0.0"
            })
            
            prod_config_file = self.config_dir / "production.json"
            with open(prod_config_file, 'w', encoding='utf-8') as f:
                json.dump(prod_config, f, indent=2, ensure_ascii=False)
            
            # 创建.env示例文件
            env_example = """# CyberCorp Seed Environment Variables

# 应用配置
SEED_ENVIRONMENT=development
SEED_HOST=localhost
SEED_PORT=8000
SEED_LOG_LEVEL=DEBUG

# 数据库配置 (未来使用)
# DATABASE_URL=sqlite:///./seed.db

# 外部服务配置 (未来使用)
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# 安全配置
# SECRET_KEY=your_secret_key_here
# ALLOWED_HOSTS=localhost,127.0.0.1
"""
            
            env_file = self.seed_dir / ".env.example"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_example)
            
            print("✅ 配置文件创建完成")
            print(f"   - {dev_config_file}")
            print(f"   - {prod_config_file}")
            print(f"   - {env_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置文件创建失败: {e}")
            return False
    
    def create_scripts(self) -> bool:
        """创建便捷脚本"""
        print("📜 创建便捷脚本...")
        
        try:
            scripts_dir = self.seed_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            # 创建启动脚本
            if self.is_windows:
                start_script = """@echo off
echo 启动CyberCorp Seed服务器...
cd /d "%~dp0.."
call venv\\Scripts\\activate
python main.py
pause
"""
                start_file = scripts_dir / "start.bat"
            else:
                start_script = """#!/bin/bash
echo "启动CyberCorp Seed服务器..."
cd "$(dirname "$0")/.."
source venv/bin/activate
python main.py
"""
                start_file = scripts_dir / "start.sh"
                
            with open(start_file, 'w', encoding='utf-8') as f:
                f.write(start_script)
            
            if not self.is_windows:
                os.chmod(start_file, 0o755)
            
            # 创建开发脚本
            if self.is_windows:
                dev_script = """@echo off
echo 启动开发模式...
cd /d "%~dp0.."
call venv\\Scripts\\activate
uvicorn main:app --reload --host localhost --port 8000
pause
"""
                dev_file = scripts_dir / "dev.bat"
            else:
                dev_script = """#!/bin/bash
echo "启动开发模式..."
cd "$(dirname "$0")/.."
source venv/bin/activate
uvicorn main:app --reload --host localhost --port 8000
"""
                dev_file = scripts_dir / "dev.sh"
                
            with open(dev_file, 'w', encoding='utf-8') as f:
                f.write(dev_script)
            
            if not self.is_windows:
                os.chmod(dev_file, 0o755)
            
            # 创建测试脚本
            if self.is_windows:
                test_script = """@echo off
echo 运行测试...
cd /d "%~dp0.."
call venv\\Scripts\\activate
pytest -v
pause
"""
                test_file = scripts_dir / "test.bat"
            else:
                test_script = """#!/bin/bash
echo "运行测试..."
cd "$(dirname "$0")/.."
source venv/bin/activate
pytest -v
"""
                test_file = scripts_dir / "test.sh"
                
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_script)
            
            if not self.is_windows:
                os.chmod(test_file, 0o755)
            
            print("✅ 便捷脚本创建完成")
            print(f"   - {start_file}")
            print(f"   - {dev_file}")
            print(f"   - {test_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 脚本创建失败: {e}")
            return False
    
    def setup_git_hooks(self) -> bool:
        """设置Git钩子"""
        print("🪝 设置Git钩子...")
        
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            print("⚠️  不是Git仓库，跳过Git钩子设置")
            return True
        
        try:
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            
            # 创建pre-commit钩子
            pre_commit_hook = """#!/bin/sh
# Pre-commit hook for CyberCorp Seed

echo "运行pre-commit检查..."

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 代码格式化检查
echo "检查Python代码格式..."
black --check seed/ || {
    echo "代码格式不符合规范，请运行 'black seed/' 进行格式化"
    exit 1
}

# 运行测试
echo "运行快速测试..."
pytest seed/tests/ -x -q || {
    echo "测试失败，请修复后再提交"
    exit 1
}

echo "✅ pre-commit检查通过"
"""
            
            pre_commit_file = hooks_dir / "pre-commit"
            with open(pre_commit_file, 'w', encoding='utf-8') as f:
                f.write(pre_commit_hook)
            
            if not self.is_windows:
                os.chmod(pre_commit_file, 0o755)
            
            print("✅ Git钩子设置完成")
            return True
            
        except Exception as e:
            print(f"❌ Git钩子设置失败: {e}")
            return False
    
    def verify_setup(self) -> bool:
        """验证环境配置"""
        print("🔎 验证环境配置...")
        
        try:
            python_exe = self.get_venv_python()
            
            # 检查虚拟环境
            if not python_exe.exists():
                print("❌ 虚拟环境Python可执行文件不存在")
                return False
            
            # 检查核心依赖
            result = subprocess.run([
                str(python_exe), "-c", "import fastapi, uvicorn, websockets; print('核心依赖检查通过')"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ 核心依赖检查失败: {result.stderr}")
                return False
            
            print("✅ 核心依赖检查通过")
            
            # 检查配置文件
            config_files = [
                self.config_dir / "development.json",
                self.config_dir / "production.json",
                self.seed_dir / ".env.example"
            ]
            
            for config_file in config_files:
                if not config_file.exists():
                    print(f"❌ 配置文件缺失: {config_file}")
                    return False
            
            print("✅ 配置文件检查通过")
            print("✅ 环境配置验证成功")
            return True
            
        except Exception as e:
            print(f"❌ 验证过程出错: {e}")
            return False
    
    def print_usage_instructions(self):
        """打印使用说明"""
        print("\n" + "="*50)
        print("🎉 开发环境配置完成！")
        print("="*50)
        
        venv_activate = "venv\\Scripts\\activate" if self.is_windows else "source venv/bin/activate"
        
        print(f"""
📚 使用说明:

1. 激活虚拟环境:
   {venv_activate}

2. 启动开发服务器:
   python main.py
   或使用便捷脚本: scripts/{'dev.bat' if self.is_windows else 'dev.sh'}

3. 运行测试:
   pytest
   或使用便捷脚本: scripts/{'test.bat' if self.is_windows else 'test.sh'}

4. 代码格式化:
   black seed/

5. 使用CLI工具:
   python cli.py --help

📁 项目结构:
   - seed/              # 核心代码
   - venv/              # 虚拟环境
   - seed/config/       # 配置文件
   - seed/scripts/      # 便捷脚本
   - seed/.env.example  # 环境变量示例

📖 更多信息请查看 README.md 和文档
        """)

def main():
    """主函数"""
    print("🚀 CyberCorp Seed开发环境自动配置")
    print("="*50)
    
    setup = DevEnvSetup()
    
    # 执行配置步骤
    steps = [
        ("检查前置条件", setup.check_prerequisites),
        ("创建虚拟环境", setup.create_virtual_environment),
        ("安装依赖包", setup.install_dependencies),
        ("创建配置文件", setup.create_config_files),
        ("创建便捷脚本", setup.create_scripts),
        ("设置Git钩子", setup.setup_git_hooks),
        ("验证环境配置", setup.verify_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 步骤: {step_name}")
        if not step_func():
            print(f"\n❌ {step_name}失败，配置中断")
            sys.exit(1)
    
    # 打印使用说明
    setup.print_usage_instructions()

if __name__ == "__main__":
    main() 