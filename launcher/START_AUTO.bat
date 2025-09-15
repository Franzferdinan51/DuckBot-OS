@echo off
REM DuckBot v4.2 Automatic Startup Script
REM Starts all DuckBot services automatically without user interaction
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 Auto-Startup

REM Change to script directory
cd /d "%~dp0"

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

echo.
echo ================================================================================
echo  DUCKBOT v4.2 AUTOMATIC STARTUP
echo ================================================================================
echo Starting all DuckBot services automatically...
echo.

REM Kill existing processes
echo [1/5] Cleaning up existing processes...
taskkill //F /IM python.exe /FI "COMMANDLINE eq *duckbot*" 2>nul
timeout /t 2 >nul

REM Start Enhanced WebUI
echo [2/5] Starting Enhanced WebUI on port 8787...
start "DuckBot WebUI" /MIN cmd /c "%PY_CMD% -m duckbot.webui_enhanced --host 127.0.0.1 --port 8787"
timeout /t 3 >nul

REM Start MCP Server
echo [3/5] Starting MCP Server for external AI integration...
start "DuckBot MCP Server" /MIN cmd /c "%PY_CMD% -m duckbot.integrations.mcp_server"
timeout /t 2 >nul

REM Start Multi-Agent System
echo [4/5] Starting Multi-Agent System...
start "DuckBot Multi-Agent" /MIN cmd /c "%PY_CMD% multi_agent_activator.py"
timeout /t 2 >nul

REM Start AI Ecosystem Manager
echo [5/5] Starting AI Ecosystem Manager...
start "DuckBot AI Manager" /MIN cmd /c "%PY_CMD% ai_ecosystem_manager.py --host 127.0.0.1 --port 8789"
timeout /t 2 >nul

echo.
echo ================================================================================
echo  ALL SERVICES STARTED SUCCESSFULLY
echo ================================================================================
echo.
echo ACCESS POINTS:
echo   - Enhanced WebUI: http://localhost:8787
echo   - AI Manager:     http://localhost:8789
echo   - MCP Server:     Running in background
echo   - Multi-Agent:    Running in background
echo.
echo Logs are available in the logs/ directory
echo.
echo To stop services, run: taskkill //F /IM python.exe
echo.
pause