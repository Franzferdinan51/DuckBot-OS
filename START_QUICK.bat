@echo off
REM ==============================================================================
REM  ⚡ DUCKBOT QUICK START LAUNCHER v4.2
REM  Ultra-Fast Unified Mode with Optimizations
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Quick Start Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  ⚡ DUCKBOT QUICK START MODE v4.2
echo ================================================================================
echo.
echo ⚡ QUICK START FEATURES:
echo   ✅ One-click startup with optimizations
echo   ✅ Skip configuration menus
echo   ✅ Automatic dependency management
echo   ✅ Fast deployment to production
echo.
echo 🚀 LAUNCHING QUICK START ECOSYSTEM...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Quick dependency check
echo 📦 Quick dependency check...
python -c "import sys; print('Python version:', sys.version)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Python environment issue detected
    pause
    exit /b 1
)

echo ✅ Python environment OK
echo ⚡ Starting unified ecosystem with optimizations...

REM Start AI ecosystem in background
echo 🤖 Starting AI ecosystem (background)...
start "AI Ecosystem" /MIN python start_ai_ecosystem.py
timeout /t 3 >nul

REM Start WebUI
echo 🌐 Starting WebUI...
python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic

if errorlevel 1 (
    echo.
    echo ❌ Failed to start quick start mode
    echo 💡 Trying fallback method...
    python -m duckbot.webui --host 127.0.0.1 --port 8787
    if errorlevel 1 (
        echo ❌ Fallback method also failed
        pause
    )
)

echo.
echo ✅ Quick start session ended
echo 💡 Use launcher/K option to kill all processes if needed
pause