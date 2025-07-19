@echo off
echo CyberCorp Client (Config: port 9998)
echo ====================================
echo.
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo.
echo Connecting to server via config.ini settings...
echo.

REM Activate conda environment
call conda activate base

REM Start client (will read server address from config.ini)
python client.py

pause