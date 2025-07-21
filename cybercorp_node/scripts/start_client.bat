@echo off
REM Start CyberCorp Client with auto-restart

echo Starting CyberCorp Client with auto-restart...
echo Press Ctrl+C to stop

python "%~dp0start_client.py"

if errorlevel 1 (
    echo.
    echo Client exited with error
    pause
)
