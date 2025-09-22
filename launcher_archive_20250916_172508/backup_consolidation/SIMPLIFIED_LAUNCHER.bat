@echo off
REM Simplified DuckBot Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Simplified Launcher
color 0A
cls

echo ================================================================================
echo  DUCKBOT v3.1.0+ SIMPLIFIED LAUNCHER
echo ================================================================================
echo.

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.8 or later.
    pause
    exit /b 1
)

echo Python installation found.

REM Launch the main ecosystem
echo.
echo Starting DuckBot ecosystem...
echo.
python start_ecosystem.py

echo.
echo DuckBot ecosystem has exited.
echo.
pause