@echo off
echo Starting CyberCorp System...
echo.

REM Kill any existing Python processes on port 8080
echo Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

echo.
echo Starting server in new window...
start "CyberCorp Server" cmd /k "cd /d %cd%\cybercorp_python && python server.py"

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting client in new window...
start "CyberCorp Client" cmd /k "cd /d %cd%\cybercorp_python && python client.py"

echo.
echo Both server and client are running in separate windows.
echo.
echo Commands you can type in the SERVER window:
echo   list         - List connected clients
echo   uia 0        - Get window structure from client 0
echo   process 0    - Get process list from client 0
echo   help         - Show all commands
echo   exit         - Stop server
echo.
pause