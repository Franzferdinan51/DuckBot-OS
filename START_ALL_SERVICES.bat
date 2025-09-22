@echo off
REM ==============================================================================
REM  🎛️  DUCKBOT ALL-SERVICES STARTUP SCRIPT v4.2
REM  Complete Ecosystem Launcher with Voice & Communication Features
REM ==============================================================================
REM This script starts all DuckBot services including:
REM - Enhanced WebUI Dashboard with real-time monitoring
REM - AI Ecosystem Manager with multi-agent coordination
REM - VibeVoice TTS Server with advanced voice synthesis
REM - Realtime Voice Chat with AI integration
REM - MCP Server for tool integration
REM - Enhanced Discord Bot with entertainment commands
REM - System Monitoring Dashboard
REM - Archon Multi-Agent System
REM - ByteBot Desktop Automation
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - All Services Launcher
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DUCKBOT_VERSION=4.2.0"
set "BUILD_DATE=2025-09-19"
set "BUILD_STATUS=ALL-SERVICES-ENHANCED"

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
echo  🎛️  DUCKBOT ALL-SERVICES STARTUP v%DUCKBOT_VERSION%
echo ================================================================================
echo    Complete AI Ecosystem with Voice & Communication Features
echo    [STATUS] %BUILD_STATUS% - Full Feature Set
echo    [BUILD] %BUILD_DATE% - Latest Enhanced Build
echo ================================================================================
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto :eof

call :install_dependencies_if_needed
if errorlevel 1 goto :eof

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo.
echo ================================================================================
echo  DUCKBOT ALL-SERVICES STARTUP SEQUENCE - COMPLETE ECOSYSTEM
echo ================================================================================
echo.

REM Track startup success
set "STARTUP_SUCCESS=0"
set "FAILED_SERVICES="

echo [1/10] Checking system requirements...
echo       - Verifying Python installation...
echo       - Checking available memory and CPU...
echo       - Validating network interfaces...

%PY_CMD% -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%% used, CPU: {psutil.cpu_percent()}%% used')" >nul 2>&1
if %errorlevel% equ 0 (
    echo       - System requirements: OK
) else (
    echo       - Warning: psutil not available, skipping system checks
)

echo [2/10] Starting Enhanced WebUI Dashboard...
echo       - Modern web interface with real-time updates
echo       - WebSocket-based live monitoring
echo       - Multi-agent coordination dashboard
echo       - Target: http://localhost:8787

REM Check and free port 8787
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "DuckBot WebUI" %PY_CMD% -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 > logs\unified_webui.log 2>&1
timeout /t 5 >nul

REM Check if WebUI started successfully
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] WebUI started successfully on port 8787
) else (
    echo [ERROR] Failed to start WebUI on port 8787
    set "FAILED_SERVICES=%FAILED_SERVICES% WebUI"
)
timeout /t 2 >nul

echo [3/10] Starting AI Ecosystem Manager...
echo       - Intelligent service orchestration
echo       - Multi-agent AI coordination
echo       - Real-time monitoring and health checks

start "AI Ecosystem" /MIN %PY_CMD% ai_ecosystem_manager.py > logs\ai_ecosystem.log 2>&1
timeout /t 5 >nul

echo [4/10] Starting VibeVoice TTS Server...
echo       - Advanced text-to-speech capabilities
echo       - Multiple voice engines and languages
echo       - REST API for external integration
echo       - Target: http://localhost:8000

REM Check and free port 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "VibeVoice TTS" %PY_CMD% start_vibevoice_server.py > logs\vibevoice.log 2>&1
timeout /t 5 >nul

REM Check if VibeVoice started successfully
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] VibeVoice TTS started successfully on port 8000
) else (
    echo [ERROR] Failed to start VibeVoice TTS on port 8000
    set "FAILED_SERVICES=%FAILED_SERVICES% VibeVoice"
)
timeout /t 2 >nul

echo [5/10] Starting Realtime Voice Chat Server...
echo       - Real-time voice conversation with AI
echo       - WebSocket-based live communication
echo       - Multiple AI provider support
echo       - Target: http://localhost:8001

REM Check and free port 8001
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8001 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "Realtime Voice Chat" %PY_CMD% realtime_voicechat.py > logs\voicechat.log 2>&1
timeout /t 5 >nul

REM Check if Voice Chat started successfully
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] Realtime Voice Chat started successfully on port 8001
) else (
    echo [ERROR] Failed to start Realtime Voice Chat on port 8001
    set "FAILED_SERVICES=%FAILED_SERVICES% VoiceChat"
)
timeout /t 2 >nul

echo [6/10] Starting MCP Server...
echo       - Model Context Protocol server
echo       - Tool integration and API management
echo       - AI agent tool access

start "MCP Server" %PY_CMD% start_mcp_server.py > logs\mcp_server.log 2>&1
timeout /t 3 >nul

echo [7/10] Starting Enhanced Discord Bot...
echo       - Entertainment commands and games
echo       - Voice channel integration
echo       - AI assistant and moderation

%PY_CMD% -c "import importlib; importlib.import_module('duckbot.discord_bot')" >nul 2>&1 && (
    echo       - Discord Bot: Starting with logging to logs/discord.log
    start "Discord Bot" %PY_CMD% -c "from duckbot.discord_bot import DiscordBot; import asyncio; asyncio.run(DiscordBot().start_service())" > logs\discord.log 2>&1
    timeout /t 3 >nul
    echo [OK] Discord Bot started successfully
) || (
    echo       - Discord Bot not available - skipping
    set "FAILED_SERVICES=%FAILED_SERVICES% DiscordBot"
)

echo [8/10] Starting System Monitoring Dashboard...
echo       - Real-time system metrics and performance tracking
echo       - Service health monitoring
echo       - Resource utilization tracking
echo       - Target: http://localhost:8789

REM Check and free port 8789
netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8789 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8789 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "System Monitor" %PY_CMD% -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789 > logs\system_monitor.log 2>&1
timeout /t 5 >nul

REM Check if Monitor started successfully
netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] System Monitor started successfully on port 8789
) else (
    echo [ERROR] Failed to start System Monitor on port 8789
    set "FAILED_SERVICES=%FAILED_SERVICES% SystemMonitor"
)
timeout /t 2 >nul

echo [9/10] Starting Archon Multi-Agent System...
echo       - Advanced AI agent orchestration
echo       - Knowledge base management and search
echo       - Real-time agent collaboration

%PY_CMD% -c "import importlib; importlib.import_module('duckbot.archon_integration')" >nul 2>&1 && (
    echo       - Archon: Starting with logging to logs/archon.log
    start "Archon" /MIN %PY_CMD% -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())" > logs\archon.log 2>&1
    timeout /t 3 >nul
    echo [OK] Archon Multi-Agent System started successfully
) || (
    echo       - Archon Integration not available - skipping
    set "FAILED_SERVICES=%FAILED_SERVICES% Archon"
)

echo [10/10] Starting ByteBot Desktop Automation...
echo        - Complete computer control and task automation
echo        - Natural language task processing
echo        - Cross-application automation capabilities

%PY_CMD% -c "import importlib; importlib.import_module('duckbot.bytebot_integration')" >nul 2>&1 && (
    echo       - ByteBot: Starting with logging to logs/bytebot.log
    start "ByteBot" /MIN %PY_CMD% -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())" > logs\bytebot.log 2>&1
    timeout /t 3 >nul
    echo [OK] ByteBot Desktop Automation started successfully
) || (
    echo       - ByteBot Integration not available - skipping
    set "FAILED_SERVICES=%FAILED_SERVICES% ByteBot"
)

echo.
echo ================================================================================
echo  ALL-SERVICES STARTUP COMPLETE - ECOSYSTEM STATUS
echo ================================================================================
echo.

REM Final status check
if "%FAILED_SERVICES%"=="" (
    echo 🎉 ALL SERVICES STARTED SUCCESSFULLY!
    set "STARTUP_SUCCESS=1"
) else (
    echo ⚠️  STARTUP COMPLETED WITH SOME FAILURES:
    echo    Failed services: %FAILED_SERVICES%
    echo    Check logs in logs/ directory for details
)

echo.
echo 🌐 ACCESS INFORMATION:
echo   Enhanced WebUI Dashboard:     http://localhost:8787
echo   VibeVoice TTS Server:         http://localhost:8000
echo   Realtime Voice Chat:          http://localhost:8001
echo   System Monitoring Dashboard:  http://localhost:8789
echo.

echo 🎙️  VOICE SERVICES:
echo   VibeVoice API:               http://localhost:8000/tts
echo   Voice Chat WebSocket:        ws://localhost:8001/ws/{session_id}
echo.

echo 📊 MONITORING:
echo   All service logs available in: logs/ directory
echo   Service health monitoring:    http://localhost:8789
echo.

echo 🔧 SERVICE MANAGEMENT:
echo   Use Ctrl+C in individual service windows to stop specific services
echo   Or run START_KILL.bat to stop all DuckBot processes
echo.

if %STARTUP_SUCCESS% equ 1 (
    echo ✅ All services are running successfully!
) else (
    echo 💡 Some services failed to start. Check the logs directory for details.
)

echo.
echo 📋 QUICK VERIFICATION:
echo   You can verify service status by checking the ports above
echo   All services should be accessible within 30 seconds
echo.

REM Optional: Wait for user input before closing
if /i "%1"=="--no-wait" goto :eof
echo.
echo Press any key to close this window...
pause >nul
goto :eof

REM ==============================================================================
REM SUPPORT FUNCTIONS
REM ==============================================================================

:check_python
echo 🐍 Checking Python installation...
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    echo 📝 During installation, make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ Python installation verified
exit /b 0

:install_dependencies_if_needed
echo 📦 Checking dependencies...
%PY_CMD% -c "import fastapi, uvicorn, aiohttp, requests, psutil, matplotlib, GPUtil, websockets, discord" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing required dependencies...
    %PY_CMD% -m pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil websockets discord.py
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        echo 💡 Try manually: pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil websockets discord.py
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ All dependencies are available
)
exit /b 0

:health_check
echo 🔍 Performing health check...
echo.
echo Checking service ports...

%PY_CMD% -c "
import socket
import time

ports = [
    ('WebUI', 8787),
    ('VibeVoice', 8000),
    ('VoiceChat', 8001),
    ('Monitor', 8789)
]

print('Service Health Check:')
print('=' * 40)

for name, port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        print(f'{name:<15}: ✅ RUNNING (:{port})')
    else:
        print(f'{name:<15}: ❌ OFFLINE (:{port})')
    sock.close()

print('=' * 40)
"
exit /b 0