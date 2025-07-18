@echo off
echo 启动桌面窗口管理器...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH
    echo 请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

:: 检查依赖是否安装
echo 检查依赖包...
pip show pywin32 >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 安装依赖包失败
        pause
        exit /b 1
    )
)

:: 启动应用程序
echo 启动应用程序...
python main.py

if errorlevel 1 (
    echo.
    echo 程序运行出错
    pause
) 