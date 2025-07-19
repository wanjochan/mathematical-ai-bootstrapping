@echo off
echo Starting CyberCorp Multi-Client Test
echo ===================================
echo.

echo 1. Starting Server on port 9999...
start "CyberCorp Server" cmd /k "cd cybercorp_node && set CYBERCORP_PORT=9999 && python server.py"

timeout /t 3 /nobreak >nul

echo.
echo 2. Starting Client in current user (%USERNAME%)...
start "CyberCorp Client - %USERNAME%" cmd /k "cd cybercorp_node && set CYBERCORP_PORT=9999 && python client.py"

echo.
echo ===================================
echo Server and client are now running in separate windows.
echo.
echo Please start another client in a different user session using:
echo   cd cybercorp_node
echo   set CYBERCORP_PORT=9999
echo   python client.py
echo.
echo In the server window, type 'list' to see all connected clients.
echo ===================================
pause