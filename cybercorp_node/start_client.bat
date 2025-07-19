@echo off
echo CyberCorp Node - Client Startup for Other User
echo ==============================================
echo.

@echo whoami:
whoami

REM Set server IP (change this to your control machine IP)
set SERVER_IP=localhost

REM If running from another machine, change localhost to actual IP
REM Example: set SERVER_IP=192.168.1.100

echo Connecting to server at: %SERVER_IP%:8888
echo.

REM Set Python path if needed (uncomment and modify if Python is not in PATH)
REM set PATH=C:\Python39;%PATH%

REM Start the client
python client.py

pause
