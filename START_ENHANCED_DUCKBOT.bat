@echo off
REM ==============================================================================
REM  DUCKBOT ENHANCED LAUNCHER v4.2
REM  Complete Feature Set with Modern WebUI and AI Management
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Enhanced Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  DUCKBOT ENHANCED MODE v4.2
echo ================================================================================
echo.
echo [ENHANCED] FEATURE SETUP:
echo   [OK] Modern WebUI with real-time monitoring
echo   [OK] Multi-agent AI coordination
echo   [OK] Complete integration suite
echo   [OK] System monitoring and health checks
echo.
echo [LAUNCHING] Enhanced Ecosystem...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [CHECK] Dependencies...
python -c "import fastapi, uvicorn, aiohttp, requests, psutil" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Required dependencies...
    python -m pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil websockets
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [OK] All dependencies are available
)

REM Check if port 8787 is available
echo [CHECK] Port availability...
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo [STARTING] Enhanced WebUI...
echo    Access URL: http://localhost:8787
echo    Press Ctrl+C to stop when done
echo.

REM Start the enhanced webui
python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start Enhanced WebUI
    echo [INFO] Trying alternative startup method...
    python duckbot/ui/unified_webui.py --host 127.0.0.1 --port 8787 --mode classic
    if errorlevel 1 (
        echo [ERROR] Alternative method also failed
        pause
    )
)

echo.
echo [OK] Enhanced WebUI session ended
pause