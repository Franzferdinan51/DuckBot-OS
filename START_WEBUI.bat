@echo off
REM ==============================================================================
REM  🌐 DUCKBOT WEBUI LAUNCHER v4.2
REM  Modern Web Interface with Real-time Monitoring
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot WebUI Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🌐 DUCKBOT WEBUI MODE v4.2
echo ================================================================================
echo.
echo 🌐 WEBUI FEATURES:
echo   ✅ Modern web interface with real-time updates
echo   ✅ WebSocket-based live monitoring
echo   ✅ Multi-agent coordination dashboard
echo   ✅ Task management and knowledge base integration
echo.
echo 🚀 LAUNCHING WEBUI...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if port 8787 is available
echo 🔍 Checking port 8787 availability...
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

echo 🌐 Starting WebUI server...
echo    Access URL: http://localhost:8787
echo    Log files: logs/webui.log
echo    Press Ctrl+C to stop when done
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Start the webui with logging
python -m duckbot.webui --host 127.0.0.1 --port 8787 > logs\webui.log 2>&1

if errorlevel 1 (
    echo.
    echo ❌ Failed to start WebUI
    echo 💡 Trying alternative startup method...
    python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
    if errorlevel 1 (
        echo ❌ Alternative method also failed
        echo 💡 Please check logs/webui.log for details
        pause
    )
)

echo.
echo ✅ WebUI session ended
pause