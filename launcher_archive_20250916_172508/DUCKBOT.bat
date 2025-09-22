@echo off
REM ==============================================================================
REM  🦆 DUCKBOT MAIN LAUNCHER v4.2
REM  Unified entry point for all DuckBot modes and features
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - Unified AI Ecosystem
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version info
set "DUCKBOT_VERSION=4.2.0"
set "BUILD_DATE=2025-09-15"
set "BUILD_STATUS=CONSOLIDATED-ENHANCED"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

:main_menu
cls
echo.
echo ================================================================================
echo  🦆 DUCKBOT v%DUCKBOT_VERSION% UNIFIED LAUNCHER
echo ================================================================================
echo.
echo 🚀 SELECT YOUR LAUNCH MODE:
echo.
echo 1. 🌟 [ULTIMATE] Complete Ecosystem - RECOMMENDED!
echo    ▶ All integrations active: Enhanced WebUI + Multi-Agent AI
echo    ▶ Real-time monitoring + Advanced system integration
echo    ▶ Maximum capabilities with full feature set
echo.
echo 2. 🌐 [WEBUI] Enhanced Web Interface Only
echo    ▶ Modern web dashboard with real-time updates
echo    ▶ Access at: http://localhost:8787
echo.
echo 3. 🏠 [LOCAL] Privacy-First Local Mode
echo    ▶ Complete offline operation with LM Studio
echo    ▶ Zero external API calls + Full privacy
echo.
echo 4. 🤖 [HEADLESS] AI Management Only
echo    ▶ Pure AI management without WebUI overhead
echo    ▶ Server deployment optimized
echo.
echo 5. ⚡ [QUICK] Fast Start (Ultimate + Free Tier)
echo    ▶ One-click startup with optimizations
echo    ▶ Skip configuration menus
echo.
echo ⚙️  SYSTEM TOOLS:
echo.
echo I. 📦 [INSTALL] Install Missing Components
echo U. 🔧 [UPDATE] Update All Components
echo D. 🩺 [DOCTOR] System Health Check
echo S. 🔍 [STATUS] Quick System Status
echo K. 🛑 [KILL] Stop All DuckBot Processes
echo H. ❓ [HELP] Help and Documentation
echo Q. 🚪 [QUIT] Exit Launcher
echo.
set /p choice="[DUCKBOT] Enter your choice: "

REM Launch modes
if /i "%choice%"=="1" goto ultimate_mode
if /i "%choice%"=="2" goto webui_mode
if /i "%choice%"=="3" goto local_mode
if /i "%choice%"=="4" goto headless_mode
if /i "%choice%"=="5" goto quick_mode

REM System tools
if /i "%choice%"=="I" goto install_components
if /i "%choice%"=="i" goto install_components
if /i "%choice%"=="U" goto update_components
if /i "%choice%"=="u" goto update_components
if /i "%choice%"=="D" goto doctor_check
if /i "%choice%"=="d" goto doctor_check
if /i "%choice%"=="S" goto system_status
if /i "%choice%"=="s" goto system_status
if /i "%choice%"=="K" goto kill_processes
if /i "%choice%"=="k" goto kill_processes
if /i "%choice%"=="H" goto show_help
if /i "%choice%"=="h" goto show_help
if /i "%choice%"=="Q" goto exit_launcher
if /i "%choice%"=="q" goto exit_launcher

echo.
echo ❌ Invalid choice: %choice%
echo 💡 Please enter 1, 2, 3, 4, 5, I, U, D, S, K, H, or Q
echo.
timeout /t 3 >nul
goto main_menu

:ultimate_mode
cls
echo.
echo ================================================================================
echo  🌟 DUCKBOT ULTIMATE MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Complete DuckBot Ecosystem
echo.

REM Start AI ecosystem in background
start "AI Ecosystem" /MIN python start_ai_ecosystem.py

REM Wait a moment for services to start
timeout /t 5 >nul

REM Start Enhanced WebUI
echo 🌐 Starting Enhanced WebUI at http://localhost:8787
python -m duckbot.webui --host 127.0.0.1 --port 8787 --mode classic

echo.
echo ✅ Ultimate mode session ended
pause
goto main_menu

:webui_mode
cls
echo.
echo ================================================================================
echo  🌐 ENHANCED WEBUI MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Enhanced WebUI Dashboard
echo 🌐 Access at: http://localhost:8787
echo.

python -m duckbot.webui --host 127.0.0.1 --port 8787 --mode classic

echo.
echo ✅ WebUI mode session ended
pause
goto main_menu

:local_mode
cls
echo.
echo ================================================================================
echo  🏠 LOCAL PRIVACY MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Complete Local-Only Operation
echo 🔒 Zero external API calls
echo.

REM Check LM Studio
echo 🤖 Checking LM Studio availability...
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
    goto main_menu
)

echo 🏠 Starting local-only DuckBot ecosystem...
set AI_ROUTING_MODE=local_first
set FORCE_CLOUD_FOR_CHAT=0
set LM_STUDIO_URL=http://localhost:1234/v1
python start_local_ecosystem.py

echo.
echo ✅ Local mode session ended
pause
goto main_menu

:headless_mode
cls
echo.
echo ================================================================================
echo  🤖 HEADLESS AI MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: AI Management Only (No UI)
echo.

python start_ai_ecosystem.py

echo.
echo ✅ Headless mode session ended
pause
goto main_menu

:quick_mode
cls
echo.
echo ================================================================================
echo  ⚡ QUICK START MODE
echo ================================================================================
echo.
echo 🚀 ONE-CLICK STARTUP: Ultimate + Free Tier Optimized
echo.

REM Apply free tier optimizations
echo 💸 Applying free tier optimizations...
python -c "
import json
config = {
    'openrouter_budget_per_min': 3,
    'ai_confidence_min': 0.75,
    'ai_local_conf_min': 0.68,
    'ai_ttl_cache_sec': 120,
    'max_memory_threshold': 80.0,
    'enable_enhanced_caching': True,
    'free_tier_optimized': True
}
with open('.env.local', 'w') as f:
    for k, v in config.items():
        f.write(f'{k.upper()}={v}\n')
print('✅ Free tier settings applied')
"

REM Start ecosystem with optimizations
start "AI Ecosystem" /MIN python start_ai_ecosystem.py
timeout /t 5 >nul

echo 🌐 Starting WebUI...
python -m duckbot.webui --host 127.0.0.1 --port 8787 --mode classic

echo.
echo ✅ Quick start session ended
pause
goto main_menu

:install_components
cls
echo.
echo ================================================================================
echo  📦 INSTALL MISSING COMPONENTS
echo ================================================================================
echo.

echo 📦 Installing core dependencies...
pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil

echo 📦 Installing enhanced dependencies...
pip install discord.py openai anthropic torch transformers

echo 📦 Installing web dependencies...
pip install streamlit gradio flask

echo 📦 Installing system utilities...
pip install python-dotenv PyYAML watchdog neo4j SpeechRecognition pyttsx3

echo ✅ Dependencies installed successfully
pause
goto main_menu

:update_components
cls
echo.
echo ================================================================================
echo  🔧 UPDATE ALL COMPONENTS
echo ================================================================================
echo.

echo 🔧 Updating Python packages...
pip install --upgrade fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil
pip install --upgrade discord.py openai anthropic torch transformers
pip install --upgrade streamlit gradio flask
pip install --upgrade python-dotenv PyYAML watchdog neo4j SpeechRecognition pyttsx3

echo ✅ All components updated successfully
pause
goto main_menu

:doctor_check
cls
echo.
echo ================================================================================
echo  🩺 SYSTEM HEALTH CHECK
echo ================================================================================
echo.

echo 🔍 Checking system health...
python -c "
import platform, subprocess, os, sys
print(f'OS: {platform.platform()}')
print(f'Python: {sys.version.split()[0]}')
try:
    import psutil
    print(f'CPU: {psutil.cpu_percent()}%% usage')
    print(f'Memory: {psutil.virtual_memory().percent}%% used')
    print(f'Disk: {psutil.disk_usage(os.getcwd()).percent}%% used')
except ImportError:
    print('System Metrics: psutil module not found. Install with: pip install psutil')
"

echo.
echo 🔍 Checking integration status...
python -c "
import importlib
modules = [
    ('WebUI', 'duckbot.webui'),
    ('AI Router', 'duckbot.ai_router_gpt'),
    ('Server Manager', 'duckbot.server_manager'),
    ('Service Detector', 'duckbot.service_detector')
]
for name, module in modules:
    try:
        importlib.import_module(module)
        print(f'{name}: AVAILABLE')
    except ImportError as e:
        print(f'{name}: NOT AVAILABLE - {str(e)[:50]}...')
    except Exception as e:
        print(f'{name}: ERROR - {str(e)[:50]}...')
"

echo.
echo 🔍 Checking port status...
python -c "
import socket
ports = [('WebUI', 8787), ('Monitor', 8789)]
for name, port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    status = 'IN USE (DuckBot Running)' if result == 0 else 'AVAILABLE'
    print(f'{name} (:{port}): {status}')
    sock.close()
"

echo.
echo ✅ Health check completed
pause
goto main_menu

:system_status
cls
echo.
echo ================================================================================
echo  🔍 QUICK SYSTEM STATUS
echo ================================================================================
echo.

echo 🔍 Checking running services...
tasklist /fi "imagename eq python.exe" | findstr DuckBot >nul
if %errorlevel% equ 0 (
    echo ✅ DuckBot services are running
) else (
    echo ⚠️  No DuckBot services detected
)

echo 🔍 Checking port usage...
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo ✅ WebUI is running on port 8787
) else (
    echo ⚠️  WebUI not running (port 8787 available)
)

netstat -ano | findstr :1234 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo ✅ LM Studio is running on port 1234
) else (
    echo ⚠️  LM Studio not detected (port 1234)
)

echo.
echo 📊 System resources:
python -c "
import psutil
print(f'  CPU Usage: {psutil.cpu_percent()}%%')
print(f'  Memory Usage: {psutil.virtual_memory().percent}%%')
print(f'  Disk Usage: {psutil.disk_usage(\".\").percent}%%')
"

echo.
pause
goto main_menu

:kill_processes
cls
echo.
echo ================================================================================
echo  🛑 STOPPING ALL DUCKBOT PROCESSES
echo ================================================================================
echo.

echo 🛑 Stopping all DuckBot processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1

echo 🧹 Cleaning up ports...
for %%p in (8787 8788 8789 1234) do (
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if not errorlevel 1 (
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do (
            taskkill /F /PID %%i >nul 2>&1
        )
    )
)

echo ✅ All DuckBot processes stopped
pause
goto main_menu

:show_help
cls
echo.
echo ================================================================================
echo  ❓ HELP AND DOCUMENTATION
echo ================================================================================
echo.
echo 📚 QUICK START GUIDE:
echo.
echo 1. 🌟 ULTIMATE MODE (Recommended):
echo    ▶ Starts complete ecosystem with WebUI
echo    ▶ Access WebUI at: http://localhost:8787
echo    ▶ All features enabled
echo.
echo 2. 🌐 WEBUI MODE:
echo    ▶ Starts only the web interface
echo    ▶ Access at: http://localhost:8787
echo    ▶ Perfect for UI-focused work
echo.
echo 3. 🏠 LOCAL MODE:
echo    ▶ Complete offline operation
echo    ▶ Requires LM Studio with local model
echo    ▶ Zero external API calls
echo.
echo 4. 🤖 HEADLESS MODE:
echo    ▶ Pure AI management without UI
echo    ▶ Optimized for server deployment
echo    ▶ Background operation
echo.
echo 5. ⚡ QUICK START MODE:
echo    ▶ One-click startup with optimizations
echo    ▶ Skip configuration menus
echo.
echo ⚙️  SYSTEM TOOLS:
echo.
echo I. 📦 INSTALL - Install missing dependencies
echo U. 🔧 UPDATE - Update all components
echo D. 🩺 DOCTOR - System health diagnostics
echo S. 🔍 STATUS - Quick system status check
echo K. 🛑 KILL - Stop all DuckBot processes
echo H. ❓ HELP - Help and documentation
echo.
echo 💡 TIPS:
echo   • Use K option if ports are in use
echo   • Use I option for import errors
echo   • Check logs/ directory for detailed logs
echo   • Edit .env file for configuration
echo.
pause
goto main_menu

:exit_launcher
cls
echo.
echo ================================================================================
echo  🦆 THANK YOU FOR USING DUCKBOT v%DUCKBOT_VERSION%!
echo ================================================================================
echo.
echo 🚀 Your professional AI-managed ecosystem
echo 📝 Production-ready with enterprise features
echo 🌟 Enjoy your enhanced AI experience!
echo.
echo 💡 Quick restart: Run this script again
echo 📚 Documentation: Check README.md
echo.
timeout /t 3 >nul
exit /b 0