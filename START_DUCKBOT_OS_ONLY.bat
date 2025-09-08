@echo off
title DuckBot OS - Pure Interface (No Classic WebUI)
color 0A

echo.
echo ========================================
echo  DUCKBOT OS - PURE INTERFACE
echo ========================================
echo.
echo This launcher starts ONLY the new DuckBot OS
echo The classic WebUI has been completely removed
echo.

:: Kill any existing DuckBot processes first
echo Stopping any existing DuckBot processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1
taskkill /F /IM python.exe /FI "COMMANDLINE eq *webui*" >nul 2>&1
timeout /t 2 >nul

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

:: Verify DuckBot OS file exists
if not exist "DuckBotOS-Complete.html" (
    echo ERROR: DuckBotOS-Complete.html not found!
    echo This file is required for the new interface
    pause
    exit /b 1
)

echo.
echo DuckBot OS file found: DuckBotOS-Complete.html
echo File size: 
dir DuckBotOS-Complete.html | findstr "DuckBot"
echo.

echo ========================================
echo  STARTING DUCKBOT OS SERVER
echo ========================================
echo.
echo IMPORTANT: Watch for these log messages:
echo   [DUCKBOT OS] Loading interface from: ...
echo   [DUCKBOT OS] Successfully serving new interface
echo.
echo If you see errors, they will appear below:
echo.

:: Start the server directly (no minimized mode)
python -m duckbot.webui

echo.
echo ========================================
echo  DUCKBOT OS SERVER STOPPED
echo ========================================
echo.
echo The server has been stopped.
echo To restart, run this script again.
pause