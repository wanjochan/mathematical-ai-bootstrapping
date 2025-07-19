@echo off
echo CyberCorp Stable - Service Setup
echo ================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo 1. Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo 2. Creating service directories...
if not exist "C:\CyberCorp" mkdir "C:\CyberCorp"
if not exist "C:\CyberCorp\logs" mkdir "C:\CyberCorp\logs"
if not exist "C:\CyberCorp\config" mkdir "C:\CyberCorp\config"

echo.
echo 3. Copying files...
copy /Y server.py "C:\CyberCorp\server.py"
copy /Y client.py "C:\CyberCorp\client.py"
copy /Y requirements.txt "C:\CyberCorp\requirements.txt"

echo.
echo 4. Creating start scripts...

REM Create server start script
echo @echo off > "C:\CyberCorp\start_server.bat"
echo cd /d C:\CyberCorp >> "C:\CyberCorp\start_server.bat"
echo python server.py >> "C:\CyberCorp\start_server.bat"

REM Create client start script
echo @echo off > "C:\CyberCorp\start_client.bat"
echo cd /d C:\CyberCorp >> "C:\CyberCorp\start_client.bat"
echo python client.py >> "C:\CyberCorp\start_client.bat"

echo.
echo 5. Setting up firewall rule for port 8888...
netsh advfirewall firewall add rule name="CyberCorp Control Server" dir=in action=allow protocol=TCP localport=8888

echo.
echo ================================
echo Setup completed successfully!
echo.
echo To use CyberCorp:
echo.
echo 1. On the CONTROL machine:
echo    Run: C:\CyberCorp\start_server.bat
echo.
echo 2. On the TARGET machine (with VSCode):
echo    Run: C:\CyberCorp\start_client.bat
echo.
echo The client will automatically connect to the server.
echo.
pause