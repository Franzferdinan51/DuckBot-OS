@echo off
REM ==============================================================================
REM  🤖 DUCKBOT HEADLESS LAUNCHER v4.2
REM  Pure AI Management without WebUI Overhead
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Headless Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🤖 DUCKBOT HEADLESS MODE v4.2
echo ================================================================================
echo.
echo 🤖 HEADLESS FEATURES:
echo   ✅ Pure AI management without WebUI overhead
echo   ✅ Server deployment optimized
echo   ✅ Minimal resource usage
echo   ✅ Background service operation
echo.
echo 🚀 LAUNCHING HEADLESS AI ECOSYSTEM...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check for required files
echo 📋 Checking required files...
if not exist "start_ai_ecosystem.py" (
    echo ❌ start_ai_ecosystem.py not found!
    echo 💡 This file is required for headless mode
    pause
    exit /b 1
)

echo 🤖 Starting AI Ecosystem (headless)...
echo 📋 AI will start and manage all services automatically
echo ⏹️  Press Ctrl+C to stop
echo.

REM Start the AI ecosystem
python start_ai_ecosystem.py

if errorlevel 1 (
    echo.
    echo ❌ Failed to start AI ecosystem
    echo 💡 Please check the error message above
    pause
)

echo.
echo ✅ Headless AI ecosystem session ended
pause