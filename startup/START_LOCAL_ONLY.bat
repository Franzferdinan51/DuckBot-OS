@echo off
REM DuckBot Local-Only Quick Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Local-Only Launcher
color 0A
cls

cd /d "%~dp0"

echo.
echo ===============================================
echo  🏠 DUCKBOT LOCAL-ONLY QUICK LAUNCHER
echo ===============================================
echo.
echo 🔒 PRIVACY-FIRST SETUP:
echo   ✅ All processing stays on your machine
echo   ✅ No cloud API dependencies
echo   ✅ LM Studio + ComfyUI + WebUI
echo   ✅ Complete offline operation
echo.
echo 🚀 LAUNCHING LOCAL ECOSYSTEM...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check LM Studio
echo 🤖 Checking LM Studio...
python -c "import requests; r=requests.get('http://localhost:1234/v1/models', timeout=3); print('✅ LM Studio ready')" 2>nul
if errorlevel 1 (
    echo ❌ LM Studio not running!
    echo.
    echo 🔧 PLEASE START LM STUDIO FIRST:
    echo   1. Open LM Studio
    echo   2. Load a chat model
    echo   3. Make sure local server is running
    echo.
    pause
    exit /b 1
)

REM Start local ecosystem
echo.
echo 🏠 Starting local-only DuckBot ecosystem...
set AI_ROUTING_MODE=local_first
set FORCE_CLOUD_FOR_CHAT=0
set LM_STUDIO_URL=http://localhost:1234/v1
python start_local_ecosystem.py

if errorlevel 1 (
    echo.
    echo ❌ Failed to start local ecosystem
    pause
)

echo.
echo ✅ Local ecosystem session ended
pause
