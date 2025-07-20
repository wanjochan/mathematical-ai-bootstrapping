@echo off
echo CyberCorp Client - Port 9998
echo ============================
echo.
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo.
echo Connecting to server at localhost:9998...
echo.

REM Activate conda environment
call conda activate base
:st
REM Start client (will read from config.ini which specifies port 9998)
python client.py
python -c "from time import sleep;sleep(2)"
goto st