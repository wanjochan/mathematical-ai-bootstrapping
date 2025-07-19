@echo off
echo CyberCorp Server (Config: port 9998)
echo =====================================
echo.
echo Starting server with config.ini settings...
echo.

REM Activate conda environment
call conda activate base

REM Start server (will read port from config.ini)
python server.py

pause