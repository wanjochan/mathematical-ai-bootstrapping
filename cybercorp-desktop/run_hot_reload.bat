@echo off
echo 🔥 启动热重载版桌面窗口管理器...
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
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo 正在安装热重载相关依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 安装依赖包失败
        pause
        exit /b 1
    )
)

:: 启动热重载版本的应用程序
echo 🚀 启动热重载版应用程序...
echo.
echo 功能说明:
echo • 支持实时热重载UI组件
echo • API服务器运行在 http://localhost:8888
echo • 修改 ui_components.py 文件会自动触发重载
echo • 可通过API或界面按钮手动触发重载
echo.

python main_hot_reload.py

if errorlevel 1 (
    echo.
    echo 程序运行出错
    echo 请检查日志文件查看详细错误信息
    pause
) 