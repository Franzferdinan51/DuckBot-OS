@echo off
REM ==============================================================================
REM  🤖 DUCKBOT HEADLESS LAUNCHER v4.2
REM  Pure AI Management Without WebUI Overhead
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
echo 🚀 LAUNCHING: Pure AI Management (No WebUI)
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo 🤖 Starting AI ecosystem manager...
echo ⏹️  Press Ctrl+C to stop
echo.

python start_ai_ecosystem.py

echo.
echo ✅ Headless mode session ended
pause