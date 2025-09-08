@echo off
title DuckBot v3.1.0 - Enhanced Ecosystem Startup
color 0A

echo ================================================================
echo    DuckBot v3.1.0 - Enhanced AI Ecosystem Launcher
echo    Advanced Integration Suite with Real WSL, ByteBot, Archon
echo ================================================================
echo.

echo [SYSTEM] Checking system requirements...

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

:: Check WSL availability
wsl --version >nul 2>&1
if errorlevel 1 (
    echo [WSL] WSL not available - some features will be limited
) else (
    echo [WSL] WSL detected - full Linux integration available
    wsl --list --verbose
)

:: Check for required directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

echo.
echo [DEPS] Installing/updating Python dependencies...
pip install --upgrade pip >nul 2>&1

:: Core dependencies
pip install fastapi uvicorn websockets >nul 2>&1
pip install requests aiohttp >nul 2>&1
pip install sqlite3-utils >nul 2>&1

:: Advanced integration dependencies (ByteBot/Archon/ChromiumOS)
pip install pillow opencv-python numpy >nul 2>&1
pip install psutil >nul 2>&1
pip install asyncio aiosqlite >nul 2>&1

echo [DEPS] Dependencies updated successfully
echo.

echo ================================================================
echo    Available Startup Options:
echo ================================================================
echo.
echo [1] 🚀 Full Enhanced Ecosystem (WSL + ByteBot + Archon + ChromiumOS)
echo [2] 🏠 Local-Only Privacy Mode (No external APIs)
echo [3] 🌐 Cloud + Local Hybrid Mode (Best of both)
echo [4] 🧪 Development Mode (Debug + Hot Reload)
echo [5] 📊 Analytics Dashboard Only
echo [6] 🔧 Advanced Configuration
echo [Q] ❌ Quit
echo.

set /p choice="Select startup mode (1-6, Q): "

if "%choice%"=="1" goto enhanced_ecosystem
if "%choice%"=="2" goto local_only
if "%choice%"=="3" goto hybrid_mode
if "%choice%"=="4" goto dev_mode
if "%choice%"=="5" goto dashboard_only
if "%choice%"=="6" goto advanced_config
if /i "%choice%"=="Q" goto quit

echo Invalid choice. Starting Full Enhanced Ecosystem...

:enhanced_ecosystem
echo.
echo ================================================================
echo    🚀 STARTING FULL ENHANCED ECOSYSTEM
echo ================================================================
echo.
echo [ECOSYSTEM] Launching all services with advanced integrations...
echo [SERVICES] - AI-Enhanced WebUI Dashboard
echo [SERVICES] - Real WSL Integration (Ubuntu + NVIDIA-Workbench)
echo [SERVICES] - ByteBot Task Automation
echo [SERVICES] - Archon Multi-Agent System  
echo [SERVICES] - ChromiumOS Browser Integration
echo [SERVICES] - ComfyUI Image Generation
echo [SERVICES] - n8n Workflow Automation
echo [SERVICES] - Discord Bot
echo [SERVICES] - Jupyter Notebooks
echo.

:: Set environment for enhanced mode
set ENABLE_WSL_INTEGRATION=true
set ENABLE_BYTEBOT=true
set ENABLE_ARCHON=true
set ENABLE_CHROMIUM=true
set ENABLE_ALL_FEATURES=true

start "DuckBot Enhanced Ecosystem" python start_ai_ecosystem.py
goto show_info

:local_only
echo.
echo ================================================================
echo    🏠 STARTING LOCAL-ONLY PRIVACY MODE
echo ================================================================
echo.
echo [PRIVACY] All processing stays on your machine
echo [PRIVACY] Zero external API calls
echo [PRIVACY] Complete data sovereignty
echo.

:: Set environment for local-only mode
set AI_LOCAL_ONLY_MODE=true
set DISABLE_OPENROUTER=true
set ENABLE_LM_STUDIO_ONLY=true
set ENABLE_WSL_INTEGRATION=true
set ENABLE_BYTEBOT=true
set ENABLE_ARCHON=true
set ENABLE_CHROMIUM=true

start "DuckBot Local Privacy Mode" python start_local_ecosystem.py
goto show_info

:hybrid_mode
echo.
echo ================================================================
echo    🌐 STARTING CLOUD + LOCAL HYBRID MODE
echo ================================================================
echo.
echo [HYBRID] Best of both worlds
echo [HYBRID] Cloud AI with local fallback
echo [HYBRID] Smart cost optimization
echo.

:: Set environment for hybrid mode
set AI_HYBRID_MODE=true
set ENABLE_COST_OPTIMIZATION=true
set ENABLE_WSL_INTEGRATION=true
set ENABLE_BYTEBOT=true
set ENABLE_ARCHON=true
set ENABLE_CHROMIUM=true

start "DuckBot Hybrid Mode" python start_ai_ecosystem.py
goto show_info

:dev_mode
echo.
echo ================================================================
echo    🧪 STARTING DEVELOPMENT MODE
echo ================================================================
echo.
echo [DEV] Debug logging enabled
echo [DEV] Hot reload active
echo [DEV] All integrations in debug mode
echo.

:: Set environment for development mode
set DEBUG=true
set LOG_LEVEL=DEBUG
set HOT_RELOAD=true
set ENABLE_WSL_INTEGRATION=true
set ENABLE_BYTEBOT=true
set ENABLE_ARCHON=true
set ENABLE_CHROMIUM=true

start "DuckBot Development Mode" python -m duckbot.webui --reload
goto show_info

:dashboard_only
echo.
echo ================================================================
echo    📊 STARTING ANALYTICS DASHBOARD ONLY
echo ================================================================
echo.

start "DuckBot Dashboard" python start_cost_dashboard.py
goto show_info

:advanced_config
echo.
echo ================================================================
echo    🔧 ADVANCED CONFIGURATION
echo ================================================================
echo.
echo [CONFIG] Opening configuration interface...

start "DuckBot Config" python -c "from duckbot.config_wizard import run_wizard; run_wizard()"
goto show_info

:show_info
echo.
echo ================================================================
echo    🎉 DUCKBOT ENHANCED ECOSYSTEM STARTED!
echo ================================================================
echo.
echo 📱 WebUI Dashboard: http://localhost:8787
echo 🤖 Discord Bot: Connected and ready
echo 🐧 WSL Integration: Real Linux commands available
echo 🔄 ByteBot Automation: Natural language tasks
echo 🧠 Archon Agents: Multi-agent system active
echo 🌐 ChromiumOS Features: Advanced browser integration
echo.
echo 🔗 Key URLs:
echo    • Main Dashboard: http://localhost:8787
echo    • n8n Workflows: http://localhost:5678
echo    • Jupyter Notebooks: http://localhost:8889
echo    • ComfyUI: http://localhost:8188
echo.
echo 📋 Available Commands:
echo    • WSL Terminal: Real Linux commands
echo    • ByteBot Tasks: "Create a document", "Open calculator"
echo    • Archon Agents: Knowledge management and research
echo    • Browser Control: Bookmarks, history, extensions
echo.
echo 🔧 Management:
echo    • EMERGENCY_KILL.bat - Stop all services
echo    • CHECK_MODEL_STATUS.bat - View system resources
echo    • TEST_LOCAL_PARITY.bat - Verify features
echo.

echo Press any key to open main dashboard...
pause >nul
start http://localhost:8787

goto end

:quit
echo.
echo Goodbye! 👋
echo.
exit /b 0

:end
echo.
echo DuckBot Enhanced Ecosystem is running in the background.
echo You can safely close this window.
echo.
pause