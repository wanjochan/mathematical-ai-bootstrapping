@echo off
echo CyberCorp Client - Unified Port Configuration
echo ============================================
echo.
echo Current User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo.

REM Set unified port
set CYBERCORP_PORT=9998

REM Set server IP (change if server is on different machine)
set SERVER_IP=localhost

echo Connecting to server at: %SERVER_IP%:%CYBERCORP_PORT%
echo.

REM For remote server, uncomment and modify:
REM set CYBERCORP_SERVER=ws://192.168.1.100:9998

REM Start the client
python client.py

pause