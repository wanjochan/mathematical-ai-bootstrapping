@echo off
echo CyberCorp Hot Reload Server
echo ===========================
echo.
echo Starting server with hot reload support...
echo Plugins directory: plugins\
echo Config file: server_config.json
echo.

REM Activate conda environment
call conda activate base

REM Start hot reload server
python server_hotreload.py

pause