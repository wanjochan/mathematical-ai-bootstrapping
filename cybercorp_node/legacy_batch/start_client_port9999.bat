@echo off
echo Starting CyberCorp Client (Port 9999)
echo ====================================
echo.
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo.
set CYBERCORP_PORT=9999
python client.py
pause