@echo off
REM CyberCorp 增强版桌面管理器启动脚本
echo 正在启动 CyberCorp 增强版桌面管理器...
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装或未添加到系统PATH
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements_enhanced.txt
)

REM 启动增强版应用
echo 启动应用程序...
python main_enhanced.py

pause