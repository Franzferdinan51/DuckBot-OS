@echo off
REM ==============================================================================
REM  🦆 DUCKBOT CONSOLIDATED LAUNCHER v4.2
REM  Unified, Streamlined Launcher for All DuckBot Modes and Features
REM ==============================================================================
REM This single launcher replaces dozens of redundant batch files while providing:
REM - All core DuckBot functionality in one interface
REM - Enhanced WebUI with real-time monitoring
REM - Local-only privacy mode with LM Studio
REM - Multi-agent AI orchestration
REM - Service management and health monitoring
REM - System diagnostics and troubleshooting
REM - Dependency management and installation
REM - Cross-platform compatibility
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - Unified AI Ecosystem Launcher
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DUCKBOT_VERSION=4.2.0"
set "BUILD_DATE=2025-09-15"
set "BUILD_STATUS=CONSOLIDATED-ENHANCED"

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

REM Main menu loop
:main_menu
cls
echo.
echo ================================================================================
echo  🦆 DUCKBOT v%DUCKBOT_VERSION% UNIFIED LAUNCHER
echo ================================================================================
echo    Enterprise-Grade AI-Managed Ecosystem with Complete Feature Set
echo    [STATUS] %BUILD_STATUS% - Enhanced Edition
echo    [BUILD] %BUILD_DATE% - Latest Consolidated Build
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
echo 3. 🤖 [HEADLESS] AI Management Only
echo    ▶ Pure AI management without WebUI overhead
echo    ▶ Server deployment optimized
echo.
echo 4. 🏠 [LOCAL-ONLY] Complete Privacy Mode
echo    ▶ Complete offline operation with LM Studio
echo    ▶ Zero external API calls + Full privacy
echo.
echo 5. ⚡ [QUICK-START] Ultra-Fast Unified Mode
echo    ▶ One-click startup with optimizations
echo    ▶ Skip configuration menus
echo.
echo 🎯 SPECIALIZED MODES - TARGETED FUNCTIONALITY:
echo.
echo 6. 🧪 [TEST] Comprehensive System Testing
echo    ▶ All features validation + Performance benchmarks
echo    ▶ AI routing + Model detection + Health checks
echo.
echo 7. 📊 [MONITORING] System Monitoring Dashboard
echo    ▶ Real-time system metrics + Performance tracking
echo    ▶ Agent status monitoring + Resource utilization
echo.
echo 8. 💬 [CHAT] Interactive AI Assistant
echo    ▶ Direct chat with DuckBot AI Assistant
echo    ▶ Ask questions, get help, and control DuckBot
echo.
echo 🎙️  VOICE & COMMUNICATION MODES:
echo.
echo 9. 🔊 [VIBEVOICE] VibeVoice TTS Server
echo    ▶ Advanced text-to-speech with multiple voices
echo    ▶ Edge TTS, pyttsx3, and Coqui TTS support
echo    ▶ Available at: http://localhost:8000
echo.
echo 10. 🗣️  [VOICECHAT] Realtime Voice Chat
echo    ▶ Real-time voice conversation with AI
echo    ▶ WebSocket-based live communication
echo    ▶ Available at: http://localhost:8001
echo.
echo ⚙️  SYSTEM MANAGEMENT - MAINTENANCE AND TROUBLESHOOTING:
echo.
echo I. 📦 [INSTALL] Auto-Install Missing Components
echo    ▶ Install all required dependencies
echo    ▶ Python packages + System tools
echo.
echo U. 🔧 [UPDATE] Update All Components
echo    ▶ Update DuckBot + All integrations
echo    ▶ Dependency updates + Configuration migration
echo.
echo D. 🩺 [DOCTOR] System Doctor & Dependency Fixer
echo    ▶ Comprehensive health diagnostics
echo    ▶ Automatic dependency installation
echo    ▶ Performance analysis & automated repair
echo.
echo S. 🔍 [STATUS] Quick System Status
echo    ▶ Integration health checks + Service status
echo    ▶ Port availability + Process monitoring
echo.
echo K. 🛑 [KILL] Kill All DuckBot Processes
echo    ▶ Stop all running services and integrations
echo    ▶ Clean shutdown + Process cleanup
echo.
echo C. ⚙️  [CONFIG] DuckBot Settings and Configuration
echo    ▶ Configure AI providers, integrations, and system settings
echo.
echo A. 🎛️  [ALL-SERVICES] Start All Services
echo    ▶ Complete ecosystem with all voice & communication features
echo    ▶ VibeVoice + RealtimeVoiceChat + Discord + WebUI + MCP
echo.
echo H. ❓ [HELP] Help and Documentation
echo    ▶ Integration guides + Troubleshooting
echo    ▶ Feature documentation + Best practices
echo.
echo Q. 🚪 [QUIT] Exit Launcher
echo.
set /p choice="[DUCKBOT PROMPT] Enter your choice: "

REM Primary launch modes
if /i "%choice%"=="1" goto ultimate_mode
if /i "%choice%"=="2" goto webui_mode
if /i "%choice%"=="3" goto headless_mode
if /i "%choice%"=="4" goto local_only_mode
if /i "%choice%"=="5" goto quick_start_mode

REM Specialized modes
if /i "%choice%"=="6" goto test_system
if /i "%choice%"=="7" goto monitoring_mode
if /i "%choice%"=="8" goto chat_mode
if /i "%choice%"=="9" goto vibevoice_mode
if /i "%choice%"=="10" goto voicechat_mode

REM System management
if /i "%choice%"=="I" goto install_components
if /i "%choice%"=="i" goto install_components
if /i "%choice%"=="U" goto update_components
if /i "%choice%"=="u" goto update_components
if /i "%choice%"=="D" goto doctor_mode
if /i "%choice%"=="d" goto doctor_mode
if /i "%choice%"=="S" goto system_status
if /i "%choice%"=="s" goto system_status
if /i "%choice%"=="K" goto kill_processes
if /i "%choice%"=="k" goto kill_processes
if /i "%choice%"=="C" goto config_settings
if /i "%choice%"=="c" goto config_settings
if /i "%choice%"=="A" goto all_services_mode
if /i "%choice%"=="a" goto all_services_mode
if /i "%choice%"=="H" goto show_help
if /i "%choice%"=="h" goto show_help
if /i "%choice%"=="Q" goto exit_launcher
if /i "%choice%"=="q" goto exit_launcher

echo.
echo ❌ Invalid choice: %choice%
echo 💡 Please enter a valid option: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, I, U, D, S, K, C, A, H, or Q
echo.
timeout /t 3 >nul
goto main_menu

REM =============================================================================
REM CORE LAUNCH MODES
REM =============================================================================

:ultimate_mode
cls
echo.
echo ================================================================================
echo  🌟 DUCKBOT ULTIMATE MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Complete DuckBot Ecosystem
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

echo ================================================================================
echo  DUCKBOT ULTIMATE STARTUP SEQUENCE - COMPLETE INTEGRATION EXPERIENCE
echo ================================================================================
echo.

echo [1/5] Starting Enhanced WebUI Dashboard...
echo       - Modern web interface with real-time updates
echo       - WebSocket-based live monitoring
echo       - Multi-agent coordination dashboard
echo       - Available at: http://localhost:8787
echo.
REM Check if port 8787 is already in use
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)
echo       - Unified WebUI: Starting with logging to logs/unified_webui.log
start "DuckBot WebUI" %PY_CMD% -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 > logs\unified_webui.log 2>&1
timeout /t 3 >nul
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] WebUI is running on port 8787
) else (
    echo [WARN] WebUI may still be starting, continuing anyway...
)
echo [OK] Enhanced WebUI started successfully

echo [2/5] Starting AI Ecosystem Manager...
echo       - Intelligent service orchestration
echo       - Multi-agent AI coordination
echo       - Real-time monitoring and health checks
echo.
start "AI Ecosystem" /MIN %PY_CMD% start_ai_ecosystem.py
timeout /t 3 >nul

echo [3/5] Starting Additional Services...
echo       - System monitoring dashboard
echo       - Cost tracking and analytics
echo       - Discord bot integration
echo.
REM Start monitoring dashboard
start "System Monitor" /MIN %PY_CMD% -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789 > logs\system_monitor.log 2>&1

echo [4/5] Starting Archon Multi-Agent System...
echo       - Advanced AI agent orchestration
echo       - Knowledge base management and search
echo       - Real-time agent collaboration
echo.
%PY_CMD% -c "import importlib; importlib.import_module('duckbot.archon_integration')" >nul 2>&1 && (
    echo       - Archon: Starting with logging to logs/archon.log
    start "Archon" /MIN %PY_CMD% -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())" > logs\archon.log 2>&1 &
) || (
    echo       - Archon Integration not available - skipping
)
timeout /t 2 >nul

echo [5/5] Starting ByteBot Desktop Automation...
echo       - Complete computer control and task automation
echo       - Natural language task processing
echo       - Cross-application automation capabilities
echo.
%PY_CMD% -c "import importlib; importlib.import_module('duckbot.bytebot_integration')" >nul 2>&1 && (
    echo       - ByteBot: Starting with logging to logs/bytebot.log
    start "ByteBot" /MIN %PY_CMD% -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())" > logs\bytebot.log 2>&1 &
) || (
    echo       - ByteBot Integration not available - skipping
)
timeout /t 2 >nul

echo.
echo ================================================================================
echo  DUCKBOT ULTIMATE MODE - ECOSYSTEM STATUS
echo ================================================================================
echo.
echo 🌐 ACCESS INFORMATION:
echo   Enhanced WebUI Dashboard:     http://localhost:8787
echo   System Monitoring Dashboard:  http://localhost:8789
echo.
echo ✅ Ultimate mode started successfully!
echo 💡 Press Ctrl+C in individual service windows to stop services
echo    Or use option 'K' from main menu to kill all processes
echo.
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
echo.

call :check_python
if errorlevel 1 goto main_menu

echo Starting Enhanced WebUI with complete integration suite...
echo.
echo FEATURES INCLUDED:
echo   - Modern web interface with real-time updates
echo   - WebSocket-based live monitoring and notifications
echo   - Multi-agent coordination dashboard  
echo   - Task management and knowledge base integration
echo   - Real-time system metrics and performance tracking
echo   - Multi-model AI routing and management
echo.
echo STARTUP INFORMATION:
echo   - Host: 127.0.0.1 (localhost)
echo   - Port: 8787
echo   - Local Access URL: http://127.0.0.1:8787
echo   - Tailscale Access: Check Tailscale IP from main menu status
echo   - Log files: logs/ directory
echo.
echo [LAUNCHING] Starting Enhanced WebUI server...
echo.

REM Check if port 8787 is already in use
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

%PY_CMD% -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic

echo.
echo ================================================================================
echo  ENHANCED WEBUI SESSION COMPLETED
echo ================================================================================
echo.
pause
goto main_menu

:headless_mode
cls
echo.
echo ================================================================================
echo  🤖 HEADLESS AI MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Pure AI Management (No WebUI)
echo.

call :check_python
if errorlevel 1 goto main_menu

echo.
echo 🤖 LAUNCHING AI ECOSYSTEM (headless)...
echo 📋 AI will start and manage all services automatically
echo ⏹️  Press Ctrl+C to stop
echo.

%PY_CMD% start_ai_ecosystem.py

echo.
pause
goto main_menu

:local_only_mode
cls
echo.
echo ================================================================================
echo  🏠 LOCAL PRIVACY MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Complete Offline Operation Mode
echo.

call :check_python
if errorlevel 1 goto main_menu

echo.
echo Starting Local Privacy Mode with LM Studio integration...
echo [INFO] Zero external API calls - Complete offline operation
echo [INFO] Press Ctrl+C to stop when done
echo.

REM Check LM Studio
echo [CHECK] Checking LM Studio availability (required for local-only mode)...
%PY_CMD% -c "import requests; r=requests.get('http://localhost:1234/v1/models', timeout=3); print('✅ LM Studio ready')" 2>nul
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
%PY_CMD% start_local_ecosystem.py

echo.
pause
goto main_menu

:quick_start_mode
cls
echo.
echo ================================================================================
echo  ⚡ QUICK START MODE
echo ================================================================================
echo.
echo 🚀 ONE-CLICK STARTUP: Unified + Free Tier Optimized
echo.

call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

echo.
echo 🚀 Starting unified ecosystem with optimizations...
start "AI Ecosystem" /MIN %PY_CMD% start_ai_ecosystem.py
timeout /t 3 >nul

echo 🌐 Starting WebUI...
%PY_CMD% -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic

goto main_menu

REM =============================================================================
REM SPECIALIZED MODES
REM =============================================================================

:test_system
cls
echo.
echo ================================================================================
echo  🧪 COMPREHENSIVE SYSTEM TESTING
echo ================================================================================
echo.
echo 🧪 Running comprehensive system tests...
echo.

%PY_CMD% tests\unified_test_suite.py --mode full

echo.
pause
goto main_menu

:monitoring_mode
cls
echo.
echo ================================================================================
echo  📊 MONITORING DASHBOARD
echo ================================================================================
echo.
echo 🚀 LAUNCHING: System Monitoring Dashboard
echo.

call :check_python
if errorlevel 1 goto main_menu

echo Starting System Monitoring Dashboard...
echo [INFO] Executing: %PY_CMD% -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789
echo [INFO] Local monitoring interface: http://localhost:8789
echo [INFO] Press Ctrl+C to stop the monitoring server
echo.

%PY_CMD% -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789

echo.
pause
goto main_menu

:chat_mode
cls
echo.
echo ================================================================================
echo  💬 DUCKBOT AI ASSISTANT
echo ================================================================================
echo.
echo STARTING: DuckBot AI Assistant with Chat Interface
echo.

call :check_python
if errorlevel 1 goto main_menu

echo [INFO] Initializing DuckBot AI Assistant...
echo [INFO] This will start DuckBot with full AI capabilities and chat interface
echo.

%PY_CMD% -m duckbot.ai_assistant

echo.
pause
goto main_menu

:vibevoice_mode
cls
echo.
echo ================================================================================
echo  🔊 VIBEVOICE TTS SERVER
echo ================================================================================
echo.
echo 🚀 LAUNCHING: VibeVoice TTS Server
echo.

call :check_python
if errorlevel 1 goto main_menu

echo Starting VibeVoice TTS Server with advanced voice synthesis...
echo.
echo FEATURES INCLUDED:
echo   - Microsoft Edge TTS (online voices)
echo   - pyttsx3 (offline TTS engine)
echo   - Coqui TTS (advanced neural TTS)
echo   - Multiple voice options and languages
echo   - REST API for external integration
echo.
echo STARTUP INFORMATION:
echo   - Host: 127.0.0.1 (localhost)
echo   - Port: 8000
echo   - API Endpoint: http://localhost:8000/tts
echo   - Health Check: http://localhost:8000/health
echo   - Web Interface: http://localhost:8000
echo.

REM Check if port 8000 is already in use
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

echo [LAUNCHING] Starting VibeVoice TTS Server...
echo.

%PY_CMD% start_vibevoice_server.py

echo.
echo ================================================================================
echo  VIBEVOICE TTS SERVER SESSION COMPLETED
echo ================================================================================
echo.
pause
goto main_menu

:voicechat_mode
cls
echo.
echo ================================================================================
echo  🗣️  REALTIME VOICE CHAT
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Realtime Voice Chat Server
echo.

call :check_python
if errorlevel 1 goto main_menu

echo Starting Realtime Voice Chat with AI integration...
echo.
echo FEATURES INCLUDED:
echo   - Real-time voice conversation with AI
echo   - WebSocket-based live communication
echo   - Multiple AI provider support (OpenAI, Anthropic, etc.)
echo   - Session management and conversation history
echo   - Voice activity detection and noise cancellation
echo.
echo STARTUP INFORMATION:
echo   - Host: 127.0.0.1 (localhost)
echo   - Port: 8001
echo   - Web Interface: http://localhost:8001
echo   - WebSocket: ws://localhost:8001/ws/{session_id}
echo   - API Documentation: http://localhost:8001/docs
echo.

REM Check if port 8001 is already in use
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8001 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

echo [LAUNCHING] Starting Realtime Voice Chat Server...
echo.

%PY_CMD% realtime_voicechat.py

echo.
echo ================================================================================
echo  REALTIME VOICE CHAT SESSION COMPLETED
echo ================================================================================
echo.
pause
goto main_menu

:all_services_mode
cls
echo.
echo ================================================================================
echo  🎛️  ALL SERVICES MODE
echo ================================================================================
echo.
echo 🚀 LAUNCHING: Complete DuckBot Ecosystem with All Services
echo.

call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

echo.
echo ================================================================================
echo  DUCKBOT ALL SERVICES STARTUP SEQUENCE - COMPLETE ECOSYSTEM
echo ================================================================================
echo.

echo [1/8] Starting Enhanced WebUI Dashboard...
echo       - Modern web interface with real-time updates
echo       - WebSocket-based live monitoring
echo       - Multi-agent coordination dashboard
echo       - Available at: http://localhost:8787
echo.

REM Check and free port 8787
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "DuckBot WebUI" %PY_CMD% -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 > logs\unified_webui.log 2>&1
timeout /t 3 >nul

echo [2/8] Starting AI Ecosystem Manager...
echo       - Intelligent service orchestration
echo       - Multi-agent AI coordination
echo       - Real-time monitoring and health checks
echo.

start "AI Ecosystem" /MIN %PY_CMD% start_ai_ecosystem.py
timeout /t 3 >nul

echo [3/8] Starting VibeVoice TTS Server...
echo       - Advanced text-to-speech capabilities
echo       - Multiple voice engines and languages
echo       - REST API for external integration
echo       - Available at: http://localhost:8000
echo.

REM Check and free port 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "VibeVoice TTS" %PY_CMD% start_vibevoice_server.py > logs\vibevoice.log 2>&1
timeout /t 3 >nul

echo [4/8] Starting Realtime Voice Chat Server...
echo       - Real-time voice conversation with AI
echo       - WebSocket-based live communication
echo       - Multiple AI provider support
echo       - Available at: http://localhost:8001
echo.

REM Check and free port 8001
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8001 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "Realtime Voice Chat" %PY_CMD% realtime_voicechat.py > logs\voicechat.log 2>&1
timeout /t 3 >nul

echo [5/8] Starting MCP Server...
echo       - Model Context Protocol server
echo       - Tool integration and API management
echo       - AI agent tool access
echo.

start "MCP Server" %PY_CMD% -m duckbot.mcp_server > logs\mcp_server.log 2>&1
timeout /t 2 >nul

echo [6/8] Starting Enhanced Discord Bot...
echo       - Entertainment commands and games
echo       - Voice channel integration
echo       - AI assistant and moderation
echo.

%PY_CMD% -c "import importlib; importlib.import_module('duckbot.discord_bot')" >nul 2>&1 && (
    echo       - Discord Bot: Starting with logging to logs/discord.log
    start "Discord Bot" %PY_CMD% -c "from duckbot.discord_bot import DiscordBot; import asyncio; asyncio.run(DiscordBot().start_service())" > logs\discord.log 2>&1
) || (
    echo       - Discord Bot not available - skipping
)
timeout /t 2 >nul

echo [7/8] Starting System Monitoring Dashboard...
echo       - Real-time system metrics and performance tracking
echo       - Service health monitoring
echo       - Resource utilization tracking
echo       - Available at: http://localhost:8789
echo.

REM Check and free port 8789
netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8789 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8789 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

start "System Monitor" %PY_CMD% -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789 > logs\system_monitor.log 2>&1
timeout /t 3 >nul

echo [8/8] Starting Additional Services...
echo       - Archon Multi-Agent System
echo       - ByteBot Desktop Automation
echo       - Service coordination and management
echo.

REM Start Archon Multi-Agent System
%PY_CMD% -c "import importlib; importlib.import_module('duckbot.archon_integration')" >nul 2>&1 && (
    echo       - Archon: Starting with logging to logs/archon.log
    start "Archon" /MIN %PY_CMD% -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())" > logs\archon.log 2>&1
) || (
    echo       - Archon Integration not available - skipping
)
timeout /t 2 >nul

REM Start ByteBot Desktop Automation
%PY_CMD% -c "import importlib; importlib.import_module('duckbot.bytebot_integration')" >nul 2>&1 && (
    echo       - ByteBot: Starting with logging to logs/bytebot.log
    start "ByteBot" /MIN %PY_CMD% -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())" > logs\bytebot.log 2>&1
) || (
    echo       - ByteBot Integration not available - skipping
)
timeout /t 2 >nul

echo.
echo ================================================================================
echo  ALL SERVICES MODE - ECOSYSTEM STATUS
echo ================================================================================
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
echo ✅ All services started successfully!
echo 💡 Press Ctrl+C in individual service windows to stop specific services
echo    Or use option 'K' from main menu to kill all processes
echo.
pause
goto main_menu

REM =============================================================================
REM SYSTEM MANAGEMENT
REM =============================================================================

:install_components
cls
echo.
echo ================================================================================
echo  📦 INSTALL MISSING COMPONENTS
echo ================================================================================
echo.
echo 📦 Installing Python core dependencies...
%PY_CMD% -m pip install --upgrade pip
if exist requirements.txt (
    %PY_CMD% -m pip install -r requirements.txt
) else (
    echo [WARN] No requirements file found. Skipping Python deps.
)
echo.
echo 📦 Installing optional extras (if available)...
if exist requirements-extras.txt (
    %PY_CMD% -m pip install -r requirements-extras.txt
) else (
    echo [INFO] No extras file found.
)
echo.
echo 📦 Installing enhanced dependencies...
%PY_CMD% -m pip install --upgrade psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer
echo.
echo 📦 Installing system utilities...
%PY_CMD% -m pip install --upgrade streamlit gradio flask requests aiohttp
echo.
echo 📦 Installing database and serialization tools...
%PY_CMD% -m pip install --upgrade sqlite3 pyyaml jsonpickle
echo.
echo 📦 Installing AI and machine learning libraries...
%PY_CMD% -m pip install --upgrade torch transformers accelerate
echo.
echo 📦 Installing communication and networking tools...
%PY_CMD% -m pip install --upgrade discord.py websockets websocket-client
echo.
echo 📦 Verifying tools (glow/crush) in PATH...
where glow >nul 2>&1 && echo   - glow: FOUND || echo   - glow: NOT FOUND (optional)
where crush >nul 2>&1 && echo   - crush: FOUND || echo   - crush: NOT FOUND (optional)
echo.
echo Installation step completed.
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
%PY_CMD% -m pip install --upgrade pip
if exist requirements.txt (
    %PY_CMD% -m pip install --upgrade -r requirements.txt
)

echo 🔧 Updating enhanced integration dependencies...
%PY_CMD% -m pip install --upgrade psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer

echo 🔧 Updating additional components...
%PY_CMD% -m pip install --upgrade streamlit gradio flask requests aiohttp

echo 🔧 Updating AI libraries...
%PY_CMD% -m pip install --upgrade torch transformers accelerate

echo 🔧 Updating communication tools...
%PY_CMD% -m pip install --upgrade discord.py websockets websocket-client

echo 🔧 Updating database tools...
%PY_CMD% -m pip install --upgrade sqlite3 pyyaml jsonpickle

echo ✅ All components updated successfully
pause
goto main_menu

:doctor_mode
cls
echo.
echo ================================================================================
echo  🩺 SYSTEM DOCTOR
echo ================================================================================
echo.
echo 🩺 DuckBot System Doctor - Comprehensive Health Analysis
echo.

%PY_CMD% doctor_check_services.py

echo.
pause
goto main_menu

:system_status
cls
echo.
echo ================================================================================
echo  🔍 SYSTEM STATUS
echo ================================================================================
echo.
echo Checking system health...
echo.

%PY_CMD% -c "
import platform, subprocess, os, sys
print(f'OS: {platform.platform()}')
print(f'Python: {sys.version.split()[0]}')
print(f'Current Directory: {os.getcwd()}')
try:
    import psutil
    print(f'CPU: {psutil.cpu_percent()}%% usage')
    print(f'Memory: {psutil.virtual_memory().percent}%% used')
    print(f'Disk: {psutil.disk_usage(os.getcwd()).percent}%% used')
except ImportError:
    print('System Metrics: psutil module not found. Install with: pip install psutil')
"

echo.
echo Integration Status:
%PY_CMD% -c "
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
echo Port Status:
%PY_CMD% -c "
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
pause
goto main_menu

:kill_processes
cls
echo.
echo ================================================================================
echo  🛑 KILL ALL DUCKBOT PROCESSES
echo ================================================================================
echo.
echo Stopping all running DuckBot services and integrations...
echo.

echo [1/3] Killing Python processes related to DuckBot...
taskkill //F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul
taskkill //F /IM pythonw.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul

echo [2/3] Stopping web servers on common ports...
for %%p in (8787 8788 8789) do (
    echo Checking port %%p...
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if not errorlevel 1 (
        echo Stopping service on port %%p
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do taskkill //F /PID %%i 2>nul
    )
)

echo [3/3] Clean shutdown completed!
echo.
echo All DuckBot processes have been stopped.
pause
goto main_menu

:config_settings
cls
echo.
echo ================================================================================
echo  ⚙️  DUCKBOT SETTINGS AND CONFIGURATION
echo ================================================================================
echo.
echo DUCKBOT CONFIGURATION MENU
echo.
echo 1. [AI-PROVIDERS] Configure AI Providers and Models
echo    Set up OpenAI, Anthropic, LM Studio, Ollama, Claude Code, etc.
echo.
echo 2. [INTEGRATIONS] Integration Settings
echo    Configure UI-TARS, ByteBot, Memento, Archon, MCP settings
echo.
echo 3. [WEBUI] WebUI Configuration
echo    Set themes, ports, authentication, and interface options
echo.
echo 4. [SYSTEM] System Settings
echo    Configure paths, logging, performance, and hardware options
echo.
echo 5. [NETWORK] Network and Security
echo    Set up Tailscale, ports, firewall, and access controls
echo.
echo 6. [BACKUP] Backup and Restore
echo    Backup configurations, databases, and restore settings
echo.
echo 7. [ADVANCED] Advanced Settings
echo    Developer options, debugging, and experimental features
echo.
echo 8. [VIEW-CONFIG] View Current Configuration
echo    Show all current settings and configuration files
echo.
echo 9. [RESET] Reset to Defaults
echo    Reset all settings to default values
echo.
echo B. [BACK] Return to Main Menu
echo.
set /p config_choice="[CONFIG PROMPT] Enter your configuration choice: "

if /i "%config_choice%"=="1" goto config_ai_providers
if /i "%config_choice%"=="2" goto config_integrations
if /i "%config_choice%"=="3" goto config_webui
if /i "%config_choice%"=="4" goto config_system
if /i "%config_choice%"=="5" goto config_network
if /i "%config_choice%"=="6" goto config_backup
if /i "%config_choice%"=="7" goto config_advanced
if /i "%config_choice%"=="8" goto view_config
if /i "%config_choice%"=="9" goto reset_config
if /i "%config_choice%"=="B" goto main_menu
if /i "%config_choice%"=="b" goto main_menu

echo.
echo ❌ Invalid configuration choice: %config_choice%
echo Press any key to try again...
pause
goto config_settings

:show_help
cls
echo.
echo ================================================================================
echo  ❓ HELP AND DOCUMENTATION
echo ================================================================================
echo.
echo DuckBot Ultimate Enhanced - Integration Guides and Troubleshooting
echo.
echo QUICK START:
echo   1. Use option 1 (ULTIMATE) for full experience
echo   2. Access web interface at http://127.0.0.1:8787
echo   3. Use Ctrl+C to stop any running service
echo.
echo INTEGRATION MODES:
echo   - ULTIMATE: All integrations active simultaneously
echo   - ENHANCED-WEBUI: Modern web dashboard with real-time updates
echo   - MONITORING: System metrics and performance tracking
echo   - HEADLESS: Pure AI management without UI
echo   - LOCAL-ONLY: Complete offline operation with LM Studio
echo   - QUICK-START: One-click startup with optimizations
echo.
echo SPECIALIZED MODES:
echo   - TEST: Comprehensive system testing
echo   - CHAT: Interactive AI assistant
echo   - VIBEVOICE: Advanced text-to-speech server
echo   - VOICECHAT: Real-time voice conversation with AI
echo   - ALL-SERVICES: Complete ecosystem with all voice & communication features
echo   - DOCTOR: System health diagnostics
echo.
echo UTILITIES:
echo   - I: Install missing dependencies automatically
echo   - U: Update all components to latest versions
echo   - D: System doctor for health diagnostics
echo   - S: Quick system status check
echo   - K: Kill all DuckBot processes (emergency stop)
echo   - C: Configure DuckBot settings
echo   - H: Help and documentation
echo.
echo TROUBLESHOOTING:
echo   - If ports are in use, use K option to kill processes
echo   - For Python errors, use I option to install dependencies
echo   - Check logs/ directory for detailed error information
echo   - Use S option to verify integration status
echo.
echo SUPPORT:
echo   - All logs saved to logs/ directory
echo   - Configuration files in duckbot/ directory
echo   - Web interfaces use localhost (127.0.0.1) only for security
echo.
pause
goto main_menu

:exit_launcher
cls
echo.
echo ================================================================================
echo  🦆 GOODBYE FROM DUCKBOT v%DUCKBOT_VERSION%!
echo ================================================================================
echo.
echo 🚀 Thanks for using DuckBot Unified AI Ecosystem!
echo 📝 Your professional AI-managed system
echo 🌟 Production-ready with enterprise-grade reliability
echo.
echo 💡 Quick restart: Just run this script again
echo 📚 Documentation: Check README.md for full features
echo 🤖 AI Support: python chat_with_ai.py anytime
echo.
echo Have a great day! 👋
timeout /t 3 >nul
exit /b 0

REM =============================================================================
REM SUPPORT FUNCTIONS
REM =============================================================================

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
%PY_CMD% -c "import fastapi, uvicorn, aiohttp, requests, matplotlib, GPUtil" >nul 2>&1
if %errorlevel% 1 (
    echo 📥 Installing required dependencies...
    %PY_CMD% -m pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil
    if %errorlevel% 1 (
        echo ❌ Failed to install dependencies
        echo 💡 Try manually: pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ All dependencies are available
)
exit /b 0

REM =============================================================================
REM CONFIGURATION SUB-MENUS
REM =============================================================================

:config_ai_providers
cls
echo.
echo ================================================================================
echo  ⚙️  AI PROVIDERS CONFIGURATION
echo ================================================================================
echo.
echo CONFIGURE AI PROVIDERS - DUCKBOT SUPPORTS MULTIPLE PROVIDERS
echo.
echo 1. [OPENAI] Configure OpenAI (GPT-4, GPT-3.5, etc.)
echo    Set API key, model selection, and parameters
echo.
echo 2. [ANTHROPIC] Configure Anthropic Claude
echo    Set API key, model selection (Claude 3, Claude Code, etc.)
echo.
echo 3. [LM-STUDIO] Configure LM Studio (Local Models)
echo    Set up local API endpoint and model selection
echo.
echo 4. [OLLAMA] Configure Ollama (Local Models)
echo    Set up Ollama endpoint and local model management
echo.
echo 5. [ROUTING] Configure AI Routing Rules
echo    Set cost limits, fallback providers, and routing logic
echo.
echo 6. [CLAUDE-CODE] Configure Claude Code Integration
echo    Set up Claude Code as AI provider with DuckBot integration
echo.
echo B. [BACK] Return to Settings Menu
echo.
set /p ai_choice="[AI PROVIDERS PROMPT] Enter your choice: "

if /i "%ai_choice%"=="1" goto config_openai
if /i "%ai_choice%"=="2" goto config_anthropic
if /i "%ai_choice%"=="3" goto config_lm_studio
if /i "%ai_choice%"=="4" goto config_ollama
if /i "%ai_choice%"=="5" goto config_routing
if /i "%ai_choice%"=="6" goto config_claude_code
if /i "%ai_choice%"=="B" goto config_settings
if /i "%ai_choice%"=="b" goto config_settings

echo.
echo ❌ Invalid AI provider choice: %ai_choice%
echo Press any key to try again...
pause
goto config_ai_providers

:config_integrations
cls
echo.
echo ================================================================================
echo  ⚙️  INTEGRATIONS CONFIGURATION
echo ================================================================================
echo.
echo CONFIGURE DUCKBOT INTEGRATIONS
echo.
echo 1. [WEBUI] Configure WebUI Integration
echo    Set up WebUI, themes, and interface options
echo.
echo 2. [DISCORD] Configure Discord Bot
echo    Set up Discord token and bot settings
echo.
echo 3. [MCP] Configure MCP Server
echo    Set up Model Context Protocol server and tools
echo.
echo 4. [ARCHON] Configure Archon Multi-Agent System
echo    Set up agents, collaboration, and knowledge management
echo.
echo B. [BACK] Return to Settings Menu
echo.
set /p int_choice="[INTEGRATIONS PROMPT] Enter your choice: "

if /i "%int_choice%"=="1" goto config_webui_integration
if /i "%int_choice%"=="2" goto config_discord_integration
if /i "%int_choice%"=="3" goto config_mcp_integration
if /i "%int_choice%"=="4" goto config_archon_integration
if /i "%int_choice%"=="B" goto config_settings
if /i "%int_choice%"=="b" goto config_settings

echo.
echo ❌ Invalid integration choice: %int_choice%
echo Press any key to try again...
pause
goto config_integrations

:view_config
cls
echo.
echo ================================================================================
echo  📋 CURRENT CONFIGURATION
echo ================================================================================
echo.
echo Displaying current DuckBot configuration...
echo.

if exist ".env" (
    echo === .env Configuration ===
    type .env
    echo.
)

if exist "ai_config.json" (
    echo === AI Configuration ===
    type ai_config.json
    echo.
)

if exist "ecosystem_config.yaml" (
    echo === Ecosystem Configuration ===
    type ecosystem_config.yaml
    echo.
)

echo.
pause
goto config_settings

:reset_config
cls
echo.
echo ================================================================================
echo  🔄 RESET CONFIGURATION
echo ================================================================================
echo.
echo ⚠️  This will reset all configuration files to default values.
echo.
set /p reset_confirm="Continue with reset? (y/N): "
if /i not "%reset_confirm%"=="y" goto config_settings

echo.
echo 🔄 Resetting configuration files...
echo.

REM Reset .env file
echo # DuckBot v4.2 Configuration > .env
echo # AI Provider Configuration >> .env
echo OPENROUTER_API_KEY=your_openrouter_api_key_here >> .env
echo DISCORD_TOKEN=your_discord_token_here >> .env
echo # System Configuration >> .env
echo DUCKBOT_WEBUI_HOST=127.0.0.1 >> .env
echo DUCKBOT_WEBUI_PORT=8787 >> .env
echo AI_CONFIDENCE_MIN=0.75 >> .env
echo AI_LOCAL_CONF_MIN=0.68 >> .env
echo MAX_MEMORY_THRESHOLD=85.0 >> .env

echo.
echo ✅ Configuration reset to defaults
echo 📝 Edit .env file to configure your settings
echo.
pause
goto config_settings

REM =============================================================================
REM PLACEHOLDER FUNCTIONS FOR FUTURE EXPANSION
REM =============================================================================

:config_openai
echo.
echo 🔄 Configuring OpenAI integration...
echo.
echo Please edit .env file to set your OpenAI API key:
echo OPENAI_API_KEY=your_openai_api_key_here
echo.
pause
goto config_ai_providers

:config_anthropic
echo.
echo 🔄 Configuring Anthropic integration...
echo.
echo Please edit .env file to set your Anthropic API key:
echo ANTHROPIC_API_KEY=your_anthropic_api_key_here
echo.
pause
goto config_ai_providers

:config_lm_studio
echo.
echo 🔄 Configuring LM Studio integration...
echo.
echo Please ensure LM Studio is running with local server enabled.
echo Default URL: http://localhost:1234/v1
echo.
pause
goto config_ai_providers

:config_ollama
echo.
echo 🔄 Configuring Ollama integration...
echo.
echo Please ensure Ollama is installed and running.
echo Default URL: http://localhost:11434
echo.
pause
goto config_ai_providers

:config_routing
echo.
echo 🔄 Configuring AI routing rules...
echo.
echo Please edit ai_config.json to customize routing rules.
echo.
pause
goto config_ai_providers

:config_claude_code
echo.
echo 🔄 Configuring Claude Code integration...
echo.
echo Please edit .env file to set Claude Code API key:
echo CLAUDE_CODE_API_KEY=your_claude_code_api_key_here
echo.
pause
goto config_ai_providers

:config_webui_integration
echo.
echo 🔄 Configuring WebUI integration...
echo.
echo Please edit ecosystem_config.yaml to customize WebUI settings.
echo.
pause
goto config_integrations

:config_discord_integration
echo.
echo 🔄 Configuring Discord integration...
echo.
echo Please edit .env file to set your Discord bot token:
echo DISCORD_TOKEN=your_discord_token_here
echo.
pause
goto config_integrations

:config_mcp_integration
echo.
echo 🔄 Configuring MCP integration...
echo.
echo Please edit .env file to set MCP server settings.
echo.
pause
goto config_integrations

:config_archon_integration
echo.
echo 🔄 Configuring Archon integration...
echo.
echo Please edit ecosystem_config.yaml to customize Archon settings.
echo.
pause
goto config_integrations

:config_webui
echo.
echo 🔄 Configuring WebUI settings...
echo.
echo Please edit ecosystem_config.yaml to customize WebUI settings.
echo.
pause
goto config_settings

:config_system
echo.
echo 🔄 Configuring system settings...
echo.
echo Please edit .env file to customize system settings.
echo.
pause
goto config_settings

:config_network
echo.
echo 🔄 Configuring network settings...
echo.
echo Please edit .env file to customize network settings.
echo.
pause
goto config_settings

:config_backup
echo.
echo 🔄 Configuring backup settings...
echo.
echo Please edit ecosystem_config.yaml to customize backup settings.
echo.
pause
goto config_settings

:config_advanced
echo.
echo 🔄 Configuring advanced settings...
echo.
echo Please edit ecosystem_config.yaml to customize advanced settings.
echo.
pause
goto config_settings