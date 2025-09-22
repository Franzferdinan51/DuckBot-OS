@echo off
REM ==============================================================================
REM  DUCKBOT ULTIMATE LAUNCHER v4.2
REM  One-Click Complete AI Ecosystem Startup
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Ultimate Launcher
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🚀 DUCKBOT ULTIMATE LAUNCHER v4.2
echo ================================================================================
echo.
echo Welcome to the DuckBot AI Ecosystem!
echo.
echo Features:
echo   [AI] Complete AI integration with local and cloud models
echo   [WEB] Modern WebUI with real-time monitoring
echo   [CHAT] Discord bot with voice capabilities
echo   [AUTO] Desktop automation with ByteBot
echo   [AGENT] Multi-agent system with Archon
echo   [VOICE] VibeVoice TTS and real-time voice chat
echo   [MON] System monitoring and health checks
echo.
echo Choose your startup mode:
echo.
echo 1. 🌟 Ultimate Mode (All Features)
echo 2. 🌐 WebUI Only Mode
echo 3. 🏠 Local-Only Privacy Mode
echo 4. 🤖 Discord Bot + Voice Mode
echo 5. 🧠 AI Ecosystem Manager Only
echo 6. 🎯 ByteBot Desktop Automation
echo 7. 🧪 Diagnostic and Test Mode
echo 8. ⚡ Quick Start (Minimal Services)
echo.
echo Q. Quit
echo.

set /p choice="Enter your choice (1-8, Q): "

if /i "%choice%"=="1" goto ultimate
if /i "%choice%"=="2" goto webui
if /i "%choice%"=="3" goto local
if /i "%choice%"=="4" goto discord
if /i "%choice%"=="5" goto ai
if /i "%choice%"=="6" goto bytebot
if /i "%choice%"=="7" goto diagnostic
if /i "%choice%"=="8" goto quick
if /i "%choice%"=="q" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto start

:ultimate
echo.
echo 🌟 Starting Ultimate Mode - Complete AI Ecosystem...
echo.
call START_ALL_SERVICES.bat --no-wait
goto end

:webui
echo.
echo 🌐 Starting WebUI Only Mode...
echo.
REM Free port 8787 if in use
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill /F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)
python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
goto end

:local
echo.
echo 🏠 Starting Local-Only Privacy Mode...
echo.
python core_ai/start_local_ecosystem.py
goto end

:discord
echo.
echo 🤖 Starting Discord Bot + Voice Mode...
echo.
REM Start VibeVoice TTS server
start "VibeVoice TTS" python start_vibevoice_server.py > logs\vibevoice.log 2>&1
timeout /t 3 >nul

REM Start Discord bot
python -c "from duckbot.discord_bot import DiscordBot; import asyncio; asyncio.run(DiscordBot().start_service())"
goto end

:ai
echo.
echo 🧠 Starting AI Ecosystem Manager Only...
echo.
python ai_ecosystem_manager.py
goto end

:bytebot
echo.
echo 🎯 Starting ByteBot Desktop Automation...
echo.
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())"
goto end

:diagnostic
echo.
echo 🧪 Starting Diagnostic and Test Mode...
echo.
echo Available diagnostic tools:
echo 1. System Health Check
echo 2. Port Status
echo 3. Dependency Verification
echo 4. Service Status
echo 5. Performance Profiling
echo.
set /p diag_choice="Select diagnostic tool (1-5): "

if /i "%diag_choice%"=="1" goto health_check
if /i "%diag_choice%"=="2" goto port_check
if /i "%diag_choice%"=="3" goto dep_check
if /i "%diag_choice%"=="4" goto service_check
if /i "%diag_choice%"=="5" goto perf_check

echo Invalid choice.
goto end

:health_check
python -c "
import psutil
import time

print('System Health Check:')
print('=' * 40)
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
print(f'Disk Usage: {psutil.disk_usage(\"/\").percent}%')
print('=' * 40)
"
pause
goto end

:port_check
python -c "
import socket

ports = [8787, 8789, 8000, 8001, 1234]
print('Port Status Check:')
print('=' * 40)

for port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    status = 'OPEN' if result == 0 else 'CLOSED'
    print(f'Port {port}: {status}')
    sock.close()

print('=' * 40)
"
pause
goto end

:dep_check
python -c "
required_packages = [
    'fastapi', 'uvicorn', 'aiohttp', 'requests', 'psutil',
    'websockets', 'discord', 'matplotlib', 'GPUtil'
]

print('Dependency Verification:')
print('=' * 40)

for package in required_packages:
    try:
        __import__(package)
        print(f'{package:<15}: ✅ Available')
    except ImportError:
        print(f'{package:<15}: ❌ Missing')

print('=' * 40)
"
pause
goto end

:service_check
echo Service status check not implemented yet.
pause
goto end

:perf_check
echo Performance profiling not implemented yet.
pause
goto end

:quick
echo.
echo ⚡ Starting Quick Mode - Minimal Services...
echo.
REM Start only essential services
start "WebUI" python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode minimal > logs\webui_minimal.log 2>&1
timeout /t 3 >nul
echo WebUI started on http://localhost:8787
echo.
echo Press Ctrl+C to stop services...
pause >nul
goto end

:end
echo.
echo Thank you for using DuckBot! 🦆
echo.
pause