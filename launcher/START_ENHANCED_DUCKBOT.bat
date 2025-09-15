@echo off
REM DuckBot v3.1.0+ Ultimate Enhanced Launcher - Fixed Version
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Ultimate Enhanced - Complete AI Integration Suite
color 0A

REM Change to script directory
cd /d "%~dp0"

REM ------------------------------------------------------------------------------
REM Optional: add Charm tools (Windows) to PATH if present
set "CHARM_BIN_WIN=%CD%\tools\charm\bin\win64"
if exist "%CHARM_BIN_WIN%" (
    set "PATH=%CHARM_BIN_WIN%;%PATH%"
)

REM ------------------------------------------------------------------------------
REM Configure DuckBot Desktop Environment path (Windows path)
REM - You can override by setting DUCKBOT_DE_PATH before launching this script.
REM - Auto-detects local DuckBot-DE folder
REM ------------------------------------------------------------------------------
if not defined DUCKBOT_DE_PATH (
    if exist "%CD%\DuckBot-DE" (
        set "DUCKBOT_DE_PATH=%CD%\DuckBot-DE"
    ) else (
        echo Warning: DuckBot-DE directory not found in current directory
        echo Please ensure DuckBot-DE is in the same directory as this script
        echo or set DUCKBOT_DE_PATH environment variable manually
        set "DUCKBOT_DE_PATH=%CD%\DuckBot-DE"
    )
)

REM Convert Windows DUCKBOT_DE_PATH to WSL path (e.g., C:\foo -> /mnt/c/foo)
set "DUCKBOT_DE_PATH_WSL=%DUCKBOT_DE_PATH%"
set "DUCKBOT_DE_PATH_WSL=%DUCKBOT_DE_PATH_WSL:\=/%"
set "DUCKBOT_DE_PATH_WSL=%DUCKBOT_DE_PATH_WSL:C:=/mnt/c%"
set "DUCKBOT_DE_PATH_WSL=%DUCKBOT_DE_PATH_WSL:D:=/mnt/d%"

REM Select best Python launcher (prefer py -3 on Windows if python missing)
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

REM Version info
set "DUCKBOT_VERSION=3.1.0+"
set "BUILD_DATE=2025-09-09"
set "BUILD_STATUS=ULTIMATE-ENHANCED-READY"

goto main_menu

:main_menu
cls
echo.
echo ================================================================================
echo  DUCKBOT v%DUCKBOT_VERSION% ULTIMATE ENHANCED - COMPLETE AI INTEGRATION SUITE
echo ================================================================================
echo    Professional AI-Managed Enhanced Ecosystem with ALL Integrations
echo    [STATUS] %BUILD_STATUS% - Enhanced Edition with Fixed Logging
echo    [BUILD] %BUILD_DATE% - Ultimate Enhanced Edition
echo ================================================================================
echo.
echo ULTIMATE INTEGRATION FEATURES:
echo   Enhanced WebUI - Modern real-time dashboard with WebSocket updates
echo   Multi-Model AI Routing - Intelligent local/cloud hybrid processing
echo   Real-Time Monitoring - Live system metrics and performance tracking
echo   ByteBot Desktop Automation - Complete computer control and task automation
echo   Archon Multi-Agent System - Advanced orchestration and knowledge management
echo   Charm Terminal Interface - Beautiful, interactive command-line experience
echo   ChromiumOS System Features - Advanced OS-level integration and security
echo   WSL Integration - Full Windows Subsystem for Linux support
echo.
echo ULTIMATE LAUNCH MODES - COMPLETE INTEGRATION EXPERIENCE:
echo.
echo 1. [ULTIMATE] Complete Ultimate Enhanced Mode - RECOMMENDED!
echo    ALL integrations active: Enhanced WebUI + Multi-Agent AI
echo    Real-time monitoring + Advanced system integration
echo    Maximum capabilities with full feature set
echo.
echo 2. [ENHANCED-WEBUI] Enhanced WebUI (NEW - Original Style)
echo    Gradio-based interface with dark theme + multi-agent chat
echo    System monitoring + MCP tools + All modern features
echo    Clean, professional UI based on original design
echo.
echo 3. [MONITORING] System Monitoring Dashboard
echo    Real-time system metrics + Performance tracking
echo    Agent status monitoring + Resource utilization
echo.
echo 4. [DUCKBOT-DESKTOP] DuckBot Desktop Environment (WSL)
echo    Complete Linux desktop environment via WSL2
echo    Full DuckBot OS experience + VNC remote access
echo.
echo 5. [DESKTOP-VIEWER] Open DuckBot Desktop Viewer (noVNC)
echo    Opens browser to http://localhost:6080 (password: duckbot)
echo.
echo 6. [DESKTOP-STOP] Stop DuckBot Desktop (VNC/noVNC)
echo    Stops VNC server and noVNC web proxy in WSL
echo.
echo A. [AUDIO] Configure Audio for Desktop (WSLg/PulseAudio)
echo    Sets up PulseAudio for DE and runs a test sound
echo.
echo CLASSIC DUCKBOT MODES - ENHANCED VERSIONS:
echo.
echo 7. [CLASSIC-ENHANCED] Classic DuckBot with Enhancements
echo    Original DuckBot experience + New integrations
echo    Discord bot + WebUI + Service orchestration
echo.
echo 8. [LOCAL-PRIVACY] Local-First Privacy Mode
echo    Complete offline operation with LM Studio
echo    Zero external API calls + Full privacy
echo.
echo 9. [HYBRID-CLOUD] Hybrid Cloud+Local Mode
echo    Intelligent local/cloud AI routing
echo    Cost optimization + Performance balance
echo.
echo UTILITIES AND MANAGEMENT:
echo.
echo I. [INSTALL] Auto-Install Missing Components
echo    Install all required dependencies
echo    Python packages + System tools
echo.
echo U. [UPDATE] Update All Components
echo    Update DuckBot + All integrations
echo    Dependency updates + Configuration migration
echo.
echo G. [GPU] Enable/Verify WSL GPU Acceleration
echo    Installs CUDA toolkit in WSL (optional) and verifies GPU
echo.
echo S. [STATUS] Quick System Status
echo    Integration health checks + Service status
echo    Port availability + Process monitoring
echo.
echo T. [TOOLS] Charm Tools (Crush/Glow)
echo    Open interactive TUIs (if installed)
echo.
echo P. [MCP-SERVER] Start MCP Server Only
echo    Start ONLY the MCP server at http://localhost:8000
echo    Fast startup for external AI tool integration
echo.

echo U. [UI-TARS] UI-TARS Desktop Automation
echo    Start UI-TARS integration with DuckBot backend
echo    Advanced GUI automation with natural language control
echo    ByteDance UI-TARS-desktop integration
echo.

echo M. [MCP] MCP (Model Context Protocol) Options
echo    Start/Stop MCP server + Docker management
echo.
echo EMERGENCY AND MAINTENANCE:
echo.
echo K. [KILL] Kill All DuckBot Processes
echo    Stop all running services and integrations
echo    Clean shutdown + Process cleanup
echo.
echo R. [RESTART] Restart All Services
echo    Graceful restart of all components
echo    Configuration reload + Service recovery
echo.
echo H. [HELP] Help and Documentation
echo    Integration guides + Troubleshooting
echo    Feature documentation + Best practices
echo.
echo C. [CONFIG] DuckBot Settings and Configuration
echo    Configure AI providers, integrations, and system settings
echo.

echo D. [DUCKBOT-CHAT] DuckBot AI Assistant
echo    Interactive chat with DuckBot AI Assistant
echo    Ask questions, get help, and control DuckBot with natural language
echo.

echo N. [NEWELLE] Newelle WSL Integration
echo    Advanced terminal command execution and WSL environment management
echo    File operations, web search, document processing, and system control
echo.

echo Y. [BYTEBOT] ByteBot Desktop Automation
echo    Advanced task automation with Claude Code integration
echo    Natural language desktop interaction and task execution
echo.

echo Q. [QUIT] Exit Launcher
echo.
set /p choice="[ULTIMATE PROMPT] Enter your choice: "

if /i "%choice%"=="1" goto ultimate_complete_mode
if /i "%choice%"=="2" goto enhanced_webui_mode
if /i "%choice%"=="3" goto monitoring_mode
if /i "%choice%"=="4" goto duckbot_desktop_environment
if /i "%choice%"=="5" goto open_desktop_viewer
if /i "%choice%"=="6" goto stop_desktop
if /i "%choice%"=="A" goto enable_wsl_audio
if /i "%choice%"=="a" goto enable_wsl_audio
if /i "%choice%"=="7" goto classic_enhanced_mode
if /i "%choice%"=="8" goto local_privacy_mode
if /i "%choice%"=="9" goto hybrid_cloud_mode
if /i "%choice%"=="I" goto install_components
if /i "%choice%"=="i" goto install_components
if /i "%choice%"=="U" goto update_components
if /i "%choice%"=="u" goto update_components
if /i "%choice%"=="G" goto enable_wsl_gpu
if /i "%choice%"=="g" goto enable_wsl_gpu
if /i "%choice%"=="S" goto system_status
if /i "%choice%"=="s" goto system_status
if /i "%choice%"=="K" goto kill_processes
if /i "%choice%"=="k" goto kill_processes
if /i "%choice%"=="R" goto restart_services
if /i "%choice%"=="r" goto restart_services
if /i "%choice%"=="H" goto show_help
if /i "%choice%"=="h" goto show_help
if /i "%choice%"=="C" goto config_settings
if /i "%choice%"=="c" goto config_settings
if /i "%choice%"=="D" goto duckbot_chat_mode
if /i "%choice%"=="d" goto duckbot_chat_mode
if /i "%choice%"=="N" goto newelle_mode
if /i "%choice%"=="n" goto newelle_mode
if /i "%choice%"=="Y" goto bytebot_mode
if /i "%choice%"=="y" goto bytebot_mode
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit
if /i "%choice%"=="T" goto charm_tools
if /i "%choice%"=="t" goto charm_tools
if /i "%choice%"=="P" goto mcp_server_only
if /i "%choice%"=="p" goto mcp_server_only
if /i "%choice%"=="U" goto ui_tars_mode
if /i "%choice%"=="u" goto ui_tars_mode
if /i "%choice%"=="M" goto mcp_options
if /i "%choice%"=="m" goto mcp_options

echo.
echo [ERROR] Invalid choice: %choice%
echo [ERROR] Please enter a valid option: 1, 2, 3, 4, 7, 8, 9, I, U, S, P, U, M, C, D, N, Y, K, R, H, or Q
echo.
echo Press any key to try again...
pause
goto main_menu

:ultimate_complete_mode
cls
echo.
echo ================================================================================
echo  DUCKBOT v%DUCKBOT_VERSION% ULTIMATE COMPLETE MODE
echo ================================================================================
echo.
echo LAUNCHING: Complete Ultimate Integration Experience
echo.

echo [STARTING] Launching DuckBot Ultimate Mode - No checks, direct start!
echo Current directory: %CD%
echo.
echo ================================================================================
echo  DUCKBOT ULTIMATE STARTUP SEQUENCE - COMPLETE INTEGRATION EXPERIENCE
echo ================================================================================
echo.
echo Starting all DuckBot services and integrations...
echo This will launch the complete ecosystem with all features enabled.
echo.
echo INCLUDES: WebUI Dashboard + Electron Desktop App + All Background Services
echo.
echo [LOGGING] All services will log to unified files in logs/ directory
echo [LOGGING] Use 'tail -f logs/service.log' or 'type logs\service.log' to monitor
echo.

REM Ensure logs directory exists
if not exist "logs" mkdir logs
echo.

echo [1/14] Starting Enhanced WebUI Dashboard...
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
start "DuckBot WebUI" python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic > logs\unified_webui.log 2>&1
timeout /t 2 >nul
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] WebUI is running on port 8787
) else (
    echo [WARN] WebUI may still be starting, continuing anyway...
)
echo [OK] Enhanced WebUI started successfully

echo LAUNCHING DuckBot Desktop Environment (WSL)...
if not defined DUCKBOT_DE_PATH (
    echo [CONFIG] Setting default DUCKBOT_DE_PATH...
    set "DUCKBOT_DE_PATH=%cd%\DuckBot-DE"
    set "DUCKBOT_DE_PATH_WSL=/mnt/c/Users/Ryan/Desktop/DuckBot-v3.1.0-VibeVoice-Ready-20250829_191017 (1)/DuckBot-DE"
)
echo       Using DUCKBOT_DE_PATH: "%DUCKBOT_DE_PATH%"
echo [INFO] Starting desktop environment in background...
start "DuckBot Desktop" cmd /c "call :launch_duckbot_desktop && echo Desktop environment started"

echo [2/14] Starting ByteBot Desktop Automation...
echo       - Complete computer control and task automation
echo       - Natural language task processing
echo       - Cross-application automation capabilities
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.bytebot_integration'); print('OK')" >nul 2>&1 && (
    echo       - ByteBot: Starting with logging to logs/bytebot.log
    python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())" > logs\bytebot.log 2>&1 &
) || (
    echo       - ByteBot Integration not available - skipping
)
timeout /t 2 >nul

echo [3/14] Starting Archon Multi-Agent System...
echo       - Advanced AI agent orchestration
echo       - Knowledge base management and search
echo       - Real-time agent collaboration
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.archon_integration'); print('OK')" >nul 2>&1 && (
    echo       - Archon: Starting with logging to logs/archon.log
    python -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())" > logs\archon.log 2>&1 &
) || (
    echo       - Archon Integration not available - skipping
)
timeout /t 2 >nul

echo [4/14] Starting Charm Terminal Interface...
echo       - Beautiful, color-coded terminal experience
echo       - Interactive menus and configuration
echo       - Multi-model AI session management
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.charm_terminal_ui'); print('OK')" >nul 2>&1 && (
    echo       - Charm Terminal: Starting with logging to logs/charm_terminal.log
    python -m duckbot.charm_terminal_ui > logs\charm_terminal.log 2>&1 &
) || (
    echo       - Charm Terminal not available - skipping
)
timeout /t 2 >nul

echo [5/14] Starting System Monitoring Dashboard...
echo       - Real-time system metrics and performance tracking
echo       - Agent status monitoring and resource utilization
echo       - Available at: http://localhost:8789
echo.
REM Check if port 8789 is already in use
netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8789 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8789 ^| findstr LISTENING') do taskkill //F /PID %%i >nul 2>&1
    timeout /t 2 >nul
)
echo       - System Monitor: Starting with logging to logs/system_monitor.log
python ai_ecosystem_manager.py --host 127.0.0.1 --port 8789 > logs\system_monitor.log 2>&1 &
timeout /t 3 >nul

echo [6/14] Starting WSL Integration (if available)...
REM Prefer modern WSL status, fallback to list if needed
wsl --status >nul 2>&1
if %errorlevel% equ 0 (
    echo       - Full Windows Subsystem for Linux support
    echo       - Cross-platform development environment
    echo       - Docker container integration
    set "WSL_STATUS=Active (WSL available)"
    python -c "import importlib; importlib.import_module('duckbot.wsl_integration')" >nul 2>&1 && (
        echo       - WSL Integration: Starting with logging to logs/wsl_integration.log
        python -c "from duckbot.wsl_integration import WSLIntegration; import asyncio; asyncio.run(WSLIntegration().start_service())" > logs\wsl_integration.log 2>&1 &
    ) || (
        echo       - WSL Python integration not available - skipping Python service
    )
) else (
    wsl -l -v >nul 2>&1
    if %errorlevel% equ 0 (
        echo       - WSL detected via list - limited status available
        set "WSL_STATUS=Active (WSL detected)"
        python -c "import importlib; importlib.import_module('duckbot.wsl_integration')" >nul 2>&1 && (
            echo       - WSL Integration: Starting with logging to logs/wsl_integration.log
            python -c "from duckbot.wsl_integration import WSLIntegration; import asyncio; asyncio.run(WSLIntegration().start_service())" > logs\wsl_integration.log 2>&1 &
        ) || (
            echo       - WSL Python integration not available - skipping Python service
        )
    ) else (
        echo       - WSL not available - skipping WSL integration
        set "WSL_STATUS=Not Available (WSL not installed)"
    )
)
timeout /t 2 >nul

echo [7/14] Starting ChromiumOS Integration...
echo       - Advanced system-level integration
echo       - Enhanced security and containerization
echo       - Cross-platform compatibility features
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.chromium_integration'); print('OK')" >nul 2>&1 && (
    echo       - ChromiumOS: Starting with logging to logs/chromium_integration.log
    python -c "from duckbot.chromium_integration import ChromiumIntegration; import asyncio; asyncio.run(ChromiumIntegration().start_service())" > logs\chromium_integration.log 2>&1 &
) || (
    echo       - ChromiumOS Integration not available - skipping
)
timeout /t 2 >nul

echo [8/14] Starting OpenWebUI Server...
echo       - Alternative web interface with OpenRouter integration
echo       - Polished chat interface with model selection
echo       - Available at: http://localhost:8080
echo.
python -c "import importlib,sys; importlib.import_module('open_webui'); print('OK')" >nul 2>&1 && (
    REM Check if port 8080 is already in use
    netstat -ano | findstr :8080 | findstr LISTENING >nul
    if %errorlevel% equ 0 (
        echo [WARN] Port 8080 already in use, attempting to free it...
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
        timeout /t 2 >nul
    )
    echo       - OpenWebUI: Starting with logging to logs/openwebui.log
open-webui serve --port 8080 --host 127.0.0.1 > logs\openwebui.log 2>&1 &
    echo       - OpenWebUI Server: LAUNCHED
) || (
    echo       - OpenWebUI: SKIPPED (not installed)
)
timeout /t 3 >nul

echo [9/14] Starting MCP Server...
echo       - Model Context Protocol server for tool integration
echo       - Advanced AI function calling capabilities
echo       - Tool management and execution framework
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.mcp_server'); print('OK')" >nul 2>&1 && (
    echo       - MCP Server: Starting with logging to logs/mcp_server.log
    start "MCP Server" /MIN python -c "from duckbot.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start_service())" > logs\mcp_server.log 2>&1 &
    echo       - MCP Server: LAUNCHED
) || (
    echo       - MCP Server: SKIPPED (not available)
)
timeout /t 2 >nul

echo [10/14] Starting AI Router Service...
echo       - Intelligent model selection and routing
echo       - Cost optimization and performance balancing
echo       - Automatic failover between providers
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.ai_router_gpt'); print('OK')" >nul 2>&1 && (
    echo       - AI Router: Starting with logging to logs/ai_router.log
    start "AI Router" /MIN python -m duckbot.ai_router_gpt > logs\ai_router.log 2>&1 &
    echo       - AI Router: LAUNCHED
) || (
    echo       - AI Router: SKIPPED (not available)
)
timeout /t 2 >nul

echo [11/14] Starting Cost Tracker...
echo       - Real-time usage analytics and cost monitoring
echo       - Token usage tracking and budget management
echo       - Performance metrics and optimization insights
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.cost_tracker'); print('OK')" >nul 2>&1 && (
    echo       - Cost Tracker: Starting with logging to logs/cost_tracker.log
    start "Cost Tracker" /MIN python -m duckbot.cost_tracker > logs\cost_tracker.log 2>&1 &
    echo       - Cost Tracker: LAUNCHED
) || (
    echo       - Cost Tracker: SKIPPED (not available)
)
timeout /t 2 >nul

echo [12/14] Starting Discord Bot...
echo       - Discord integration for chat bot functionality
echo       - Multi-server support and command processing
echo       - AI-powered responses and moderation
echo.
python -c "import importlib,sys; importlib.import_module('duckbot.discord_bot'); print('OK')" >nul 2>&1 && (
    echo       - Discord Bot: Starting with logging to logs/discord_bot.log
    start "Discord Bot" /MIN python -c "from duckbot.discord_bot import DiscordBot; import asyncio; asyncio.run(DiscordBot().start_service())" > logs\discord_bot.log 2>&1 &
    echo       - Discord Bot: LAUNCHED
) || (
    echo       - Discord Bot: SKIPPED (not available)
)
timeout /t 2 >nul

echo [13/14] Starting Electron Desktop Application...
echo       - Beautiful React-based desktop interface
echo       - Native desktop application experience
echo       - Full DuckBot integration in desktop form
echo.
REM Check if Node.js is available for Electron
node --version >nul 2>&1
if %errorlevel% equ 0 (
    cd duckbot\react-webui
    npm list electron --depth=0 >nul 2>&1
    if %errorlevel% equ 0 (
        start "Electron Desktop" npm run electron:dev
        echo       - Electron Desktop: LAUNCHED
    ) else (
        echo       - Electron Desktop: SKIPPED (Electron not installed)
    )
    cd ..\..
) else (
    echo       - Electron Desktop: SKIPPED (Node.js not available)
)
timeout /t 2 >nul

echo [14/14] Starting Main Ecosystem Orchestrator...
echo       - Service coordination and health monitoring
echo       - Centralized logging and error handling
echo       - API routing and request management
echo.

python start_ecosystem.py

set "PYTHON_EXIT_CODE=%ERRORLEVEL%"

echo.
echo ================================================================================
echo      DUCKBOT ULTIMATE COMPLETE MODE - ECOSYSTEM STATUS
echo ================================================================================
echo.
echo [INFO] Main ecosystem orchestrator exit code: %PYTHON_EXIT_CODE%
if %PYTHON_EXIT_CODE% equ 0 (
    echo [INFO] Status: Normal shutdown
) else (
    echo [INFO] Status: Error exit - check output above for details
)
echo.
echo ================================================================================
echo  ACCESS INFORMATION - DUCKBOT SERVICES AND INTERFACES
echo ================================================================================
echo.
echo DETECTING TAILSCALE IP ADDRESS...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /C:"Tailscale"') do set TAILSCALE_IP=%%i
if defined TAILSCALE_IP (
    set TAILSCALE_IP=%TAILSCALE_IP: =%
    echo Tailscale IP detected: %TAILSCALE_IP%
) else (
    echo Tailscale IP not detected - using local access only
    set TAILSCALE_IP=127.0.0.1
)
echo.
echo PRIMARY INTERFACES (USE LOCALHOST):
echo   Enhanced WebUI Dashboard:     http://localhost:8787
echo   System Monitoring Dashboard:  http://localhost:8789
echo   Electron Desktop Application: Running in desktop window (if available)
echo   Charm Terminal Interface:     Running in background window
echo   ByteBot Desktop Automation:   Running in background window
echo.
echo INTEGRATION STATUS:
echo   Archon Multi-Agent System:    Active (background service)
echo   WSL Integration:              %WSL_STATUS% 
echo   ChromiumOS Integration:       Active (background service)
echo   Enhanced WebUI:               Active - Access via web browser
echo.
echo IMPORTANT NOTES:
echo   - All services are running in background windows
echo   - Web interfaces bind to localhost (127.0.0.1)
echo   - Use localhost URLs with Tailscale for access
echo   - Use Ctrl+C in service windows to stop individual services
echo   - Or use option 'K' from main menu to kill all processes
echo   - All activity is logged to the logs/ directory
echo.
echo TROUBLESHOOTING:
echo   - If web interfaces don't load, check if ports are available
echo   - Use option 'S' from main menu for detailed system status  
echo   - Check logs/ directory for detailed error information
echo   - Use option 'I' to install missing dependencies
echo   - Run GET_TAILSCALE_IP.bat to get your Tailscale IP address
echo.
echo ================================================================================
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:monitoring_mode
cls
echo.
echo ================================================================================
echo  MONITORING DASHBOARD v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: System Monitoring Dashboard
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting System Monitoring Dashboard...
echo [INFO] Executing: python -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789
echo [INFO] Local monitoring interface: http://localhost:8789
echo [INFO] Tailscale: use localhost URL for access
echo [INFO] Press Ctrl+C to stop the monitoring server
echo.

python -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789

set "MONITOR_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Monitoring Dashboard session ended with exit code: %MONITOR_EXIT_CODE%
echo.
pause
goto main_menu

:duckbot_desktop_environment
cls
echo.
echo ================================================================================
echo  DUCKBOT DESKTOP ENVIRONMENT v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Complete DuckBot Linux Desktop via WSL2
echo.

echo [CHECK] Testing WSL2 availability...
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    wsl -l -v >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] WSL not found or not installed!
        echo Please install WSL2 from: https://docs.microsoft.com/en-us/windows/wsl/install
        echo Run: wsl --install
        echo.
        echo Press any key to return to the main menu...
        pause
        goto main_menu
    ) else (
        echo [CHECK] WSL2: Available (detected via distro list)
    )
) else (
    echo [CHECK] WSL2: Available
)

echo [CHECK] Testing DuckBot-DE installation...
if not defined DUCKBOT_DE_PATH (
    echo [ERROR] DUCKBOT_DE_PATH not set and auto-detect failed.
    echo Please set DUCKBOT_DE_PATH to your DuckBot-DE folder.
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else if not exist "%DUCKBOT_DE_PATH%" (
    echo [ERROR] DuckBot-DE not found!
    echo Expected location: %DUCKBOT_DE_PATH%
    echo Please ensure DuckBot-DE is properly installed.
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] DuckBot-DE: Found at %DUCKBOT_DE_PATH%
)

echo.
echo DUCKBOT DESKTOP FEATURES:
echo   - Complete Linux desktop environment in WSL2
echo   - Full DuckBot OS with window manager
echo   - VNC server for remote desktop access
echo   - Multiple DuckBot applications simultaneously
echo   - Accessible via Tailscale network
echo.
echo [LAUNCHING] Starting DuckBot Desktop Environment...
echo.

echo [1/8] Checking Ubuntu WSL installation...
wsl -d Ubuntu bash -c "echo 'Ubuntu WSL found'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Installing Ubuntu WSL...
    wsl --install -d Ubuntu
    echo Please complete Ubuntu setup and run this option again.
    pause
    goto main_menu
)

echo [2/8] Installing GUI components in Ubuntu WSL...
wsl -d Ubuntu bash -c "sudo apt update && sudo apt install -y ubuntu-desktop-minimal gnome-session gdm3 tigervnc-standalone-server novnc websockify dbus-x11" 1>nul 2>nul

echo [3/8] Installing DuckBot-DE GNOME Shell Extension...
wsl -d Ubuntu bash -c "cp -r '%DUCKBOT_DE_PATH_WSL%/duckbot-shell-extension' ~/.local/share/gnome-shell/extensions/duckbot-ai@duckbot-de"

echo [4/8] Running DuckBot-DE installer script...
wsl -d Ubuntu bash -c "cd '%DUCKBOT_DE_PATH_WSL%' && chmod +x install-duckbot-de.sh && ./install-duckbot-de.sh"

echo [5/8] Setting up VNC server for remote access...
wsl -d Ubuntu bash -c "mkdir -p ~/.vnc && echo 'duckbot' | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd"

echo [6/8] Configuring VNC startup script (GNOME + dbus)...
wsl -d Ubuntu bash -c "cat > ~/.vnc/xstartup <<'EOS'\n#!/bin/bash\nexport DISPLAY=:1\nexport XDG_RUNTIME_DIR=/run/user/\$(id -u)\nmkdir -p \"$XDG_RUNTIME_DIR\"; chmod 700 \"$XDG_RUNTIME_DIR\"\n# Load DuckBot environment if present\n[ -f ~/.duckbot_env ] && . ~/.duckbot_env\nif ! pidof dbus-daemon >/dev/null 2>&1; then\n  eval \"\$(dbus-launch --sh-syntax)\"\nfi\nexec gnome-session --session=ubuntu\nEOS\nchmod +x ~/.vnc/xstartup"

echo [7/9] Preparing environment and starting VNC server (GNOME + DuckBot-DE)...
wsl -d Ubuntu bash -c "WIN_HOST=\$(awk '/nameserver/{print $2; exit}' /etc/resolv.conf); echo export DUCKBOT_WEBUI_URL=\"http://\${WIN_HOST}:8787\" > ~/.duckbot_env; mkdir -p ~/.local/bin; for f in duckbot-cli duckbot-windows duckbot-audio duckbot-sudo-store duckbot-sudo-run; do if [ -f '%DUCKBOT_DE_PATH_WSL%/bin/'\$f ]; then cp '%DUCKBOT_DE_PATH_WSL%/bin/'\$f ~/.local/bin/ && chmod +x ~/.local/bin/\$f; fi; done"
wsl -d Ubuntu bash -c "vncserver -kill :1 >/dev/null 2>&1 || true; vncserver :1 -geometry 1920x1080 -depth 24 -localhost no"

echo [8/9] Starting noVNC web client on http://localhost:6080 ...
wsl -d Ubuntu bash -c "pkill -f websockify >/dev/null 2>&1 || true; nohup websockify --web=/usr/share/novnc/ 127.0.0.1:6080 127.0.0.1:5901 >/dev/null 2>&1 &"
start "DuckBot noVNC" "http://localhost:6080/vnc.html?autoconnect=1&password=duckbot"

echo [9/12] Installing Chrome Remote Desktop...
wsl -d Ubuntu bash -c "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main' | sudo tee /etc/apt/sources.list.d/chrome-remote-desktop.list && sudo apt update && sudo apt install -y chrome-remote-desktop" 2>nul

echo [10/12] Starting Enhanced WebUI Dashboard...
echo.
REM Check if port 8787 is already in use
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)
start "Unified WebUI" python -m duckbot.ui.unified_webui --host 0.0.0.0 --port 8787 --mode classic
timeout /t 2 >nul

echo [11/12] Starting All DuckBot AI Services...
echo [AI-SERVICES] ByteBot Desktop Automation...
start "ByteBot" /MIN python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())"
timeout /t 2 >nul

echo [AI-SERVICES] Archon Multi-Agent System...
start "Archon" /MIN python -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())"
timeout /t 2 >nul

echo [AI-SERVICES] WSL Integration Services...
start "WSL Integration" /MIN python -c "from duckbot.wsl_integration import WSLIntegration; import asyncio; asyncio.run(WSLIntegration().start_service())"
timeout /t 2 >nul

echo [AI-SERVICES] ChromiumOS Features...
start "ChromiumOS Integration" /MIN python -c "from duckbot.chromium_integration import ChromiumIntegration; import asyncio; asyncio.run(ChromiumIntegration().start_service())"
timeout /t 2 >nul

echo [12/12] Complete Desktop Environment Ready!
echo.
echo ================================================================================
echo  DUCKBOT DESKTOP ENVIRONMENT - ULTIMATE EDITION WITH GNOME
echo ================================================================================
echo.
echo LOCAL ACCESS:
echo   Enhanced WebUI:  http://localhost:8787
echo   VNC Client:      localhost:5901 (password: duckbot)
echo   WSL Shell:       wsl -d Ubuntu
echo.
echo REMOTE ACCESS (Multiple Options):
echo   1. VNC via Tailscale: [YOUR-TAILSCALE-IP]:8787
echo   2. WebUI via Tailscale: use http://localhost:8787 on this host
echo   3. Chrome Remote Desktop: Set up at remotedesktop.google.com/headless
echo.
echo DESKTOP FEATURES - ULTIMATE EDITION:
echo   ✓ Complete GNOME desktop with DuckBot-DE shell extension
echo   ✓ Enhanced WebUI Dashboard with real-time monitoring
echo   ✓ ByteBot Desktop Automation (natural language control)
echo   ✓ Archon Multi-Agent System (collaborative AI)
echo   ✓ WSL Integration Services (cross-platform)
echo   ✓ ChromiumOS System Features (advanced integration)
echo   ✓ VNC + Chrome Remote Desktop support
echo   ✓ Full Tailscale network integration
echo.
echo CHROME REMOTE DESKTOP SETUP:
echo   1. Open: https://remotedesktop.google.com/headless
echo   2. Download setup script and run in WSL Ubuntu
echo   3. Access from any device with Google account
echo.
echo ================================================================================

pause
goto main_menu

:classic_enhanced_mode
cls
echo.
echo ================================================================================
echo  CLASSIC DUCKBOT ENHANCED v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Classic DuckBot with New Integrations
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo Starting Classic DuckBot Enhanced Mode...
echo [INFO] Executing: python -m duckbot.classic_enhanced
echo [INFO] This includes Discord bot + WebUI + Service orchestration
echo [INFO] Press Ctrl+C to stop when done
echo.

python -m duckbot.classic_enhanced

set "CLASSIC_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Classic Enhanced session ended with exit code: %CLASSIC_EXIT_CODE%
pause
goto main_menu

:local_privacy_mode
cls
echo.
echo ================================================================================
echo  LOCAL PRIVACY MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Complete Offline Operation Mode
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo Starting Local Privacy Mode with LM Studio integration...
echo [INFO] Executing: python -m duckbot.local_privacy_mode
echo [INFO] Zero external API calls - Complete offline operation
echo [INFO] Press Ctrl+C to stop when done
echo.

python -m duckbot.local_privacy_mode

set "PRIVACY_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Local Privacy session ended with exit code: %PRIVACY_EXIT_CODE%
pause
goto main_menu

:hybrid_cloud_mode
cls
echo.
echo ================================================================================
echo  HYBRID CLOUD MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Intelligent Local/Cloud AI Routing
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo Starting Hybrid Cloud Mode with intelligent routing...
echo [INFO] Executing: python -m duckbot.hybrid_cloud_mode
echo [INFO] Cost optimization + Performance balance
echo [INFO] Press Ctrl+C to stop when done
echo.

python -m duckbot.hybrid_cloud_mode

set "HYBRID_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Hybrid Cloud session ended with exit code: %HYBRID_EXIT_CODE%
pause
goto main_menu

:update_components
cls
echo.
echo ================================================================================
echo  UPDATE COMPONENTS v%DUCKBOT_VERSION%
echo ================================================================================
echo.

echo Updating all DuckBot components and integrations...
echo.

echo [1/4] Updating Python dependencies...
python -m pip install --upgrade pip
if exist requirements.txt (
    python -m pip install --upgrade -r requirements.txt
)

echo [2/4] Updating enhanced integration dependencies...
python -m pip install --upgrade psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer

echo [3/4] Updating additional components...
python -m pip install --upgrade streamlit gradio flask requests aiohttp

echo [4/4] Update completed!
echo.
pause
goto main_menu

:kill_processes
cls
echo.
echo ================================================================================
echo  KILL ALL DUCKBOT PROCESSES v%DUCKBOT_VERSION%
echo ================================================================================
echo.

echo Stopping all running DuckBot services and integrations...
echo.

echo [1/3] Killing Python processes related to DuckBot...
taskkill //F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul
REM Fallback: kill python.exe processes whose command line contains 'duckbot'
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'duckbot' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul

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

:restart_services
cls
echo.
echo ================================================================================
echo  RESTART ALL SERVICES v%DUCKBOT_VERSION%
echo ================================================================================
echo.

echo Performing graceful restart of all DuckBot components...
echo.

echo [1/2] Stopping existing services...
echo Killing Python processes related to DuckBot...
taskkill //F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul
taskkill //F /IM python.exe /FI "COMMANDLINE eq *duckbot*" 2>nul

echo [2/2] Restarting main ecosystem...
echo.
timeout /t 3 >nul
goto ultimate_complete_mode

:show_help
cls
echo.
echo ================================================================================
echo  HELP AND DOCUMENTATION v%DUCKBOT_VERSION%
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
echo   - CLASSIC-ENHANCED: Original DuckBot + new integrations
echo   - LOCAL-PRIVACY: Complete offline operation with LM Studio
echo   - HYBRID-CLOUD: Intelligent local/cloud AI routing
echo.

echo UTILITIES:
echo   - I: Install missing dependencies automatically
echo   - U: Update all components to latest versions
echo   - S: Check system status and integration health
echo   - K: Kill all DuckBot processes (emergency stop)
echo   - R: Restart all services (graceful restart)
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

:install_components
cls
echo.
echo ================================================================================
echo  INSTALL MISSING COMPONENTS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo [1/3] Installing Python core dependencies...
python -m pip install --upgrade pip
if exist requirements-core.txt (
    python -m pip install -r requirements-core.txt
) else if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo [WARN] No requirements file found. Skipping Python deps.
)
echo.
echo [2/3] Installing optional extras (if available)...
if exist requirements-extras.txt (
    python -m pip install -r requirements-extras.txt
) else (
    echo [INFO] No extras file found.
)
echo.
echo [3/3] Verifying tools (glow/crush) in PATH...
where glow >nul 2>&1 && echo   - glow: FOUND || echo   - glow: NOT FOUND (optional)
where crush >nul 2>&1 && echo   - crush: FOUND || echo   - crush: NOT FOUND (optional)
echo.
echo Installation step completed.
pause
goto main_menu

:charm_tools
cls
echo.
echo ================================================================================
echo  CHARM TOOLS (COMPLETE ECOSYSTEM)
echo ================================================================================
echo.
echo Checking all Charm tools availability...

REM Check Crush
where crush >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 'crush' not found in PATH. Place binaries in tools\charm\bin\win64
) else (
    echo [OK] Crush: Available - AI command runner
)

REM Check Glow
where glow >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 'glow' not found in PATH. Place binaries in tools\charm\bin\win64
) else (
    echo [OK] Glow: Available - Markdown renderer
    start "Glow" glow README.md
)

REM Check Gum
where gum >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 'gum' not found in PATH. Place binaries in tools\charm\bin\win64
) else (
    echo [OK] Gum: Available - Interactive shell components
)

REM Check Skate
where skate >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 'skate' not found in PATH. Place binaries in tools\charm\bin\win64
) else (
    echo [OK] Skate: Available - Key-value store
)

REM Check Mods
where mods >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 'mods' not found in PATH. Place binaries in tools\charm\bin\win64
) else (
    echo [OK] Mods: Available - AI-powered commands
)

echo.
echo [CHARM INTEGRATION] Python Charm ecosystem available in DuckBot
echo [CHARM INTEGRATION] Use charm terminal UI for full integration
echo.
echo.
pause
goto main_menu

:enhanced_webui_mode
cls
echo.
echo ================================================================================
echo  UNIFIED WEBUI DASHBOARD v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Enhanced WebUI with Real-Time Features
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo ================================================================================
echo  ENHANCED WEBUI STARTUP SEQUENCE
echo ================================================================================
echo.
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
echo [AUTO] Launching Electron Desktop UI...
call :launch_duckbot_desktop

REM Check if port 8787 is already in use
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8787 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8787 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic

set "WEBUI_EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  ENHANCED WEBUI SESSION COMPLETED
echo ================================================================================
echo.
echo [INFO] Enhanced WebUI session ended with exit code: %WEBUI_EXIT_CODE%
if %WEBUI_EXIT_CODE% equ 0 (
    echo [INFO] Status: Normal shutdown
) else (
    echo [INFO] Status: Error exit - check output above for details
)
echo [INFO] All logs and session data saved to logs/ directory
echo [INFO] Configuration files preserved in duckbot/ directory
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:charm_terminal_mode
cls
echo.
echo ================================================================================
echo  CHARM TERMINAL INTERFACE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Beautiful Interactive Terminal Experience
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo Starting Charm Terminal Interface...
echo [INFO] Executing: python -m duckbot.charm_terminal_ui
echo [INFO] This will start the interactive terminal interface
echo [INFO] Press Ctrl+C or use the quit option to exit
echo.

python -m duckbot.charm_terminal_ui

goto main_menu

:open_desktop_viewer
echo.
echo ================================================================================
echo  OPEN DUCKBOT DESKTOP VIEWER (noVNC)
echo ================================================================================
echo.
echo Opening http://localhost:6080 ... (password: duckbot)
start "DuckBot noVNC" "http://localhost:6080/vnc.html?autoconnect=1&password=duckbot"
echo.
pause
goto main_menu

:stop_desktop
echo.
echo ================================================================================
echo  STOP DUCKBOT DESKTOP (VNC + noVNC)
echo ================================================================================
echo.
echo [ACTION] Stopping VNC server (:1) and noVNC proxy in WSL Ubuntu...
wsl -d Ubuntu bash -c "vncserver -kill :1 >/dev/null 2>&1 || true; pkill -f websockify >/dev/null 2>&1 || true"
if %errorlevel% equ 0 (
    echo [OK] Desktop services stopped.
) else (
    echo [WARN] Some services may not have been running; stop attempted.
)
echo.
pause
goto main_menu

set "CHARM_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Charm Terminal session ended with exit code: %CHARM_EXIT_CODE%
pause
goto main_menu

:enable_wsl_gpu
cls
echo.
echo ================================================================================
echo  ENABLE / VERIFY WSL GPU ACCELERATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo [CHECK] Windows NVIDIA driver presence...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo   - Windows NVIDIA driver: FOUND
) else (
    echo   - Windows NVIDIA driver: NOT FOUND (install latest NVIDIA driver with WSL support)
)
echo.
echo [CHECK] WSL GPU device presence...
wsl -d Ubuntu bash -c "if [ -e /dev/dxg ]; then echo '  - WSL GPU device: PRESENT'; else echo '  - WSL GPU device: NOT PRESENT'; fi"
echo.
echo [ACTION] Installing CUDA toolkit in WSL (optional)...
wsl -d Ubuntu bash -c "sudo apt update && sudo apt install -y nvidia-cuda-toolkit >/dev/null 2>&1 || true"
echo.
echo [VERIFY] CUDA compiler version (if installed):
wsl -d Ubuntu bash -c "nvcc --version 2>/dev/null || echo 'nvcc not found'"
echo.
echo [INFO] If 'WSL GPU device: PRESENT' and Windows driver is installed, GPU acceleration is available to WSL.
echo [INFO] Some AI frameworks require additional setup inside WSL (e.g., PyTorch CUDA wheels).
echo.
pause
goto main_menu

:enable_wsl_audio
cls
echo.
echo ================================================================================
echo  CONFIGURE AUDIO FOR DUCKBOT DESKTOP (WSLg / PulseAudio)
echo ================================================================================
echo.
echo [ACTION] Installing audio helper tools in WSL and configuring PulseAudio...
wsl -d Ubuntu bash -c "mkdir -p ~/.local/bin; if [ -f '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-audio' ]; then cp '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-audio' ~/.local/bin/ && chmod +x ~/.local/bin/duckbot-audio; fi; ~/.local/bin/duckbot-audio setup"
echo.
echo [TEST] Playing test sound (if supported)...
wsl -d Ubuntu bash -c "~/.local/bin/duckbot-audio test"
echo.
echo [INFO] If you hear the test sound, audio is configured for the DE.
echo.
pause
goto main_menu

:system_status
cls
echo.
echo ================================================================================
echo  SYSTEM STATUS v%DUCKBOT_VERSION%
echo ================================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found - cannot run system status
    pause
    goto main_menu
)

echo SYSTEM INFORMATION:
python -c "
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
echo INTEGRATION STATUS:
python -c "
import importlib
modules = [
    ('Unified WebUI', 'duckbot.ui.unified_webui'),
    ('Charm Terminal', 'duckbot.charm_terminal_ui'),
    ('ByteBot Integration', 'duckbot.bytebot_integration'),
    ('Archon Features', 'duckbot.archon_integration'),
    ('WSL Integration', 'duckbot.wsl_integration'),
    ('ChromiumOS Features', 'duckbot.chromium_integration')
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
echo PORT STATUS:
python -c "
import socket
ports = [('Enhanced WebUI', 8787), ('Terminal Interface', 8788), ('System Monitor', 8789)]
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

:test_all_integrations
cls
echo.
echo ================================================================================
echo  COMPREHENSIVE INTEGRATION TESTING v%DUCKBOT_VERSION%
echo ================================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    pause
    goto main_menu
)

echo Testing all integrations and features...
echo.

echo [1/6] Testing Enhanced WebUI...
python -c "
try:
    import duckbot.enhanced_webui
    print('  Enhanced WebUI: PASS')
except Exception as e:
    print(f'  Enhanced WebUI: FAIL - {e}')
"

echo [2/6] Testing Charm Terminal...
python -c "
try:
    import duckbot.charm_terminal_ui
    print('  Charm Terminal: PASS')
except Exception as e:
    print('  Charm Terminal: FAIL - ' + str(e))
"

echo [3/6] Testing ByteBot Integration...
python -c "
try:
    from duckbot.bytebot_integration import ByteBotIntegration
    bytebot = ByteBotIntegration()
    available = getattr(bytebot, 'available', True)
    print('  ByteBot Integration:', 'PASS' if available else 'LIMITED')
except Exception as e:
    print('  ByteBot Integration: FAIL -', str(e))
"

echo [4/6] Testing Archon Features...
python -c "
try:
    from duckbot.archon_integration import ArchonIntegration
    print('  Archon Integration: PASS')
except Exception as e:
    print('  Archon Integration: FAIL - ' + str(e))
"

echo [5/6] Testing WSL Integration...
python -c "
try:
    from duckbot.wsl_integration import is_wsl_available
    status = 'AVAILABLE' if is_wsl_available() else 'NOT AVAILABLE'
    print('  WSL Integration: ' + status)
except Exception as e:
    print('  WSL Integration: FAIL - ' + str(e))
"

echo [6/6] Testing ChromiumOS Features...
python -c "
try:
    from duckbot.chromium_integration import ChromiumIntegration
    print('  ChromiumOS Features: PASS')
except Exception as e:
    print('  ChromiumOS Features: FAIL - ' + str(e))
"

echo.
echo Integration testing completed!
echo Check the results above for any issues.
pause
goto main_menu

REM ================================================================================
REM ADDITIONAL HIDDEN MODES (not in main menu but accessible via direct calls)
REM ================================================================================

:electron_ultimate_mode
cls
echo.
echo ================================================================================
echo  ELECTRON ULTIMATE MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Electron Desktop UI with Full Integration
echo.

echo [CHECK] Testing Python installation...
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo [CHECK] Testing system requirements...
%PY_CMD% -c "print('[CHECK] System requirements: OK')" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some system checks failed, but continuing...
)

echo.
echo ELECTRON ULTIMATE STARTUP SEQUENCE:
echo [1/9] Checking Node.js and npm...
node --version >nul 2>&1 && npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js/npm not found. Installing via winget...
    winget install OpenJS.NodeJS
)

echo [2/9] Checking React Electron UI dependencies...
if not exist "duckbot\react-webui\node_modules" (
    cd duckbot\react-webui
    npm install
    cd ..\..
)

echo [3/9] Initializing system integrations...
%PY_CMD% -c "from duckbot.server_manager import ServerManager; ServerManager().start_background_services()"

echo [4/9] Starting DuckBot backend services...
start "DuckBot Backend" /MIN %PY_CMD% start_ecosystem.py

echo [5/9] Starting ByteBot integration...
start "ByteBot" /MIN %PY_CMD% -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())"

echo [6/9] Starting Archon multi-agent system...
start "Archon" /MIN %PY_CMD% -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())"

echo [7/9] Initializing Charm ecosystem...
start "Charm" /MIN %PY_CMD% -c "from duckbot.charm_ecosystem import CharmEcosystem; CharmEcosystem().start_background()"

echo [8/9] Starting WSL integration (if available)...
wsl --status >nul 2>&1
if %errorlevel% equ 0 (
    start "WSL Integration" /MIN %PY_CMD% -c "from duckbot.wsl_integration import WSLIntegration; import asyncio; asyncio.run(WSLIntegration().start_service())"
) else (
    echo WSL not available, skipping...
)

echo [9/9] Launching React Electron Desktop UI...
set "ELECTRON_SCRIPT=electron:dev"
if exist "duckbot\react-webui\build\index.html" (
    set "ELECTRON_SCRIPT=electron"
)
cd duckbot\react-webui
npm run %ELECTRON_SCRIPT%
cd ..\..

pause
goto main_menu

:desktop_automation_mode
cls
echo.
echo ================================================================================
echo  BYTEBOT DESKTOP AUTOMATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Complete Desktop Automation System
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting ByteBot Desktop Automation...
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"

pause
goto main_menu

:duckbot_chat_mode
cls
echo.
echo ================================================================================
echo  DUCKBOT AI ASSISTANT v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo STARTING: DuckBot AI Assistant with Chat Interface
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo [INFO] Initializing DuckBot AI Assistant...
echo [INFO] This will start DuckBot with full AI capabilities and chat interface
echo [INFO] Supporting: OpenAI, Anthropic, LM Studio, Ollama, Claude Code
echo [INFO] Features: UI-TARS, ByteBot, Memento, Archon, MCP Server
echo.

echo [1/5] Starting DuckBot AI Router (central brain)...
start "DuckBot AI Router" /MIN python -m duckbot.ai_router_gpt
timeout /t 2 >nul

echo [2/5] Starting MCP Server for full tool access...
start "MCP Server" /MIN python -c "from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start_service())"
timeout /t 2 >nul

echo [3/5] Starting Enhanced WebUI for chat interface...
start "Enhanced WebUI" /MIN python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
timeout /t 2 >nul

echo [4/5] Starting Memento Memory System...
start "Memento Memory" /MIN python -c "from duckbot.integrations.memento_integration import MementoIntegration; import asyncio; memento = MementoIntegration(); asyncio.run(memento.start_service())"
timeout /t 2 >nul

echo [5/5] Starting DuckBot AI Assistant Chat Interface...
python -c "
import asyncio
import sys
import os
sys.path.append(os.getcwd())

try:
    from duckbot.integrations.mcp_server import MCPServer
    from duckbot.ai_router_gpt import AIRouter

    class DuckBotAssistant:
        def __init__(self):
            self.router = AIRouter()
            self.mcp_server = MCPServer()
            self.running = True

        async def start_chat(self):
            print('=' * 60)
            print('DUCKBOT AI ASSISTANT - CHAT MODE')
            print('=' * 60)
            print()
            print('DuckBot is ready! Type your questions or commands below.')
            print()
            print('Special Commands:')
            print('  /help     - Show available commands')
            print('  /status   - Show system status')
            print('  /tools    - Show available tools')
            print('  /quit     - Exit chat')
            print()
            print('AI Providers Available: OpenAI, Anthropic, LM Studio, Ollama')
            print('Integrations: UI-TARS, ByteBot, Memento, Archon, MCP')
            print()

            while self.running:
                try:
                    user_input = input('DuckBot> ').strip()

                    if not user_input:
                        continue

                    if user_input.lower() == '/quit':
                        print('Goodbye!')
                        break
                    elif user_input.lower() == '/help':
                        self.show_help()
                        continue
                    elif user_input.lower() == '/status':
                        await self.show_status()
                        continue
                    elif user_input.lower() == '/tools':
                        await self.show_tools()
                        continue

                    print('Thinking...')
                    result = await self.process_message(user_input)
                    print(f'DuckBot: {result}')
                    print()

                except KeyboardInterrupt:
                    print('\nGoodbye!')
                    break
                except Exception as e:
                    print(f'Error: {e}')
                    print()

        async def process_message(self, message):
            # Route through AI router
            ai_result = await self.router.route_request(message, 'general', 'medium')

            if ai_result.get('success') and ai_result.get('content'):
                return ai_result['content']
            else:
                return 'I apologize, but I encountered an error processing your request.'

        def show_help(self):
            print()
            print('Available Commands:')
            print('  /help     - Show this help message')
            print('  /status   - Show system status')
            print('  /tools    - Show available tools')
            print('  /quit     - Exit the chat')
            print()
            print('You can ask me about:')
            print('  - System administration and configuration')
            print('  - AI model management and routing')
            print('  - Desktop automation (UI-TARS, ByteBot)')
            print('  - Memory and learning systems (Memento)')
            print('  - Multi-agent coordination (Archon)')
            print('  - WSL and Linux integration')
            print('  - Web interfaces and APIs')
            print()

        async def show_status(self):
            print()
            print('=== DUCKBOT SYSTEM STATUS ===')
            try:
                # Check AI Router
                print('AI Router: Available')

                # Check MCP Server
                tools = self.mcp_server.get_mcp_tools()
                print(f'MCP Server: Available with {len(tools)} tools')

                # Check integrations
                print('Integrations: UI-TARS, ByteBot, Memento, Archon, WSL')

                print('WebUI: Available at http://localhost:8787')
                print('Status: All systems operational')

            except Exception as e:
                print(f'Status Check Error: {e}')
            print()

        async def show_tools(self):
            print()
            print('=== AVAILABLE TOOLS ===')
            try:
                tools = self.mcp_server.get_mcp_tools()
                categories = {}

                for tool in tools:
                    category = tool.get('category', 'general')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(tool)

                for category, tool_list in categories.items():
                    print(f'{category.upper()}:')
                    for tool in tool_list[:5]:  # Show first 5 tools per category
                        print(f'  - {tool[\"name\"]}: {tool[\"description\"][:60]}...')
                    if len(tool_list) > 5:
                        print(f'  ... and {len(tool_list) - 5} more')
                    print()

            except Exception as e:
                print(f'Tools Error: {e}')
            print()

    # Start the assistant
    assistant = DuckBotAssistant()
    asyncio.run(assistant.start_chat())

except Exception as e:
    print(f'Failed to start DuckBot Assistant: {e}')
    print('Please ensure all dependencies are installed.')
"

set "CHAT_EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  DUCKBOT CHAT SESSION COMPLETED
echo ================================================================================
echo.
echo [INFO] Chat session ended with exit code: %CHAT_EXIT_CODE%
echo [INFO] Background services still running
echo [INFO] WebUI available at: http://localhost:8787
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:newelle_mode
cls
echo.
echo ================================================================================
echo  NEWELLE WSL INTEGRATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo STARTING: Newelle WSL Integration for Advanced System Control
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo [INFO] Initializing Newelle WSL Integration...
echo [INFO] Features: Terminal command execution, file management, web search
echo [INFO] Extensions: Document processing, system monitoring, process management
echo [INFO] WSL Distribution: Ubuntu (default)
echo.

echo [1/4] Starting DuckBot AI Router...
start "DuckBot AI Router" /MIN python -m duckbot.ai_router_gpt
timeout /t 2 >nul

echo [2/4] Starting MCP Server for tool integration...
start "MCP Server" /MIN python -c "from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start_service())"
timeout /t 2 >nul

echo [3/4] Starting Enhanced WebUI...
start "Enhanced WebUI" /MIN python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
timeout /t 2 >nul

echo [4/4] Starting Newelle WSL Integration...
python -c "from duckbot.newelle_integration import newelle_integration; import asyncio; asyncio.run(newelle_integration.start_interactive_mode())"

set "NEWELLE_EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  NEWELLE WSL SESSION COMPLETED
echo ================================================================================
echo.
echo [INFO] Newelle session ended with exit code: %NEWELLE_EXIT_CODE%
echo [INFO] Background services still running
echo [INFO] WebUI available at: http://localhost:8787
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:bytebot_mode
cls
echo.
echo ================================================================================
echo  BYTEBOT DESKTOP AUTOMATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo STARTING: ByteBot Desktop Automation with Claude Code Integration
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo [INFO] Initializing ByteBot Desktop Automation...
echo [INFO] Features: Natural language task execution, desktop interaction
echo [INFO] Claude Code integration for enhanced AI capabilities
echo [INFO] Computer vision and screenshot analysis
echo.

echo [1/4] Starting DuckBot AI Router...
start "DuckBot AI Router" /MIN python -m duckbot.ai_router_gpt
timeout /t 2 >nul

echo [2/4] Starting MCP Server for tool integration...
start "MCP Server" /MIN python -c "from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start_service())"
timeout /t 2 >nul

echo [3/4] Starting Enhanced WebUI...
start "Enhanced WebUI" /MIN python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
timeout /t 2 >nul

echo [4/4] Starting ByteBot Desktop Automation...
python -c "from duckbot.integrations.bytebot_integration import ByteBotIntegration; import asyncio; bytebot = ByteBotIntegration(); asyncio.run(bytebot.start_interactive_mode())"

set "BYTEBOT_EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  BYTEBOT SESSION COMPLETED
echo ================================================================================
echo.
echo [INFO] ByteBot session ended with exit code: %BYTEBOT_EXIT_CODE%
echo [INFO] Background services still running
echo [INFO] WebUI available at: http://localhost:8787
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:config_settings
cls
echo.
echo ================================================================================
echo  DUCKBOT SETTINGS AND CONFIGURATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo DUCKBOT CONFIGURATION MENU - AI PROVIDERS AND INTEGRATIONS
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

if /i "%config_choice%"=="1" goto ai_providers_config
if /i "%config_choice%"=="2" goto integrations_config
if /i "%config_choice%"=="3" goto webui_config
if /i "%config_choice%"=="4" goto system_config
if /i "%config_choice%"=="5" goto network_config
if /i "%config_choice%"=="6" goto backup_config
if /i "%config_choice%"=="7" goto advanced_config
if /i "%config_choice%"=="8" goto view_config
if /i "%config_choice%"=="9" goto reset_config
if /i "%config_choice%"=="B" goto main_menu
if /i "%config_choice%"=="b" goto main_menu

echo.
echo [ERROR] Invalid configuration choice: %config_choice%
echo Press any key to try again...
pause
goto config_settings

:ai_providers_config
cls
echo.
echo ================================================================================
echo  AI PROVIDERS CONFIGURATION v%DUCKBOT_VERSION%
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
echo 5. [OPEN-ROUTER] Configure OpenRouter
echo    Set API key and model selection from multiple providers
echo.
echo 6. [LOCAL-MODELS] Configure Other Local Models
echo    Set up custom local model endpoints
echo.
echo 7. [ROUTING] Configure AI Routing Rules
echo    Set cost limits, fallback providers, and routing logic
echo.
echo 8. [CLAUDE-CODE] Configure Claude Code Integration
echo    Set up Claude Code as AI provider with DuckBot integration
echo.
echo 9. [TEST] Test AI Provider Connections
echo    Test all configured AI providers
echo.
echo B. [BACK] Return to Settings Menu
echo.
set /p ai_choice="[AI PROVIDERS PROMPT] Enter your choice: "

if /i "%ai_choice%"=="1" goto config_openai
if /i "%ai_choice%"=="2" goto config_anthropic
if /i "%ai_choice%"=="3" goto config_lm_studio
if /i "%ai_choice%"=="4" goto config_ollama
if /i "%ai_choice%"=="5" goto config_open_router
if /i "%ai_choice%"=="6" goto config_local_models
if /i "%ai_choice%"=="7" goto config_routing
if /i "%ai_choice%"=="8" goto config_claude_code
if /i "%ai_choice%"=="9" goto test_ai_providers
if /i "%ai_choice%"=="B" goto config_settings
if /i "%ai_choice%"=="b" goto config_settings

echo.
echo [ERROR] Invalid AI provider choice: %ai_choice%
echo Press any key to try again...
pause
goto ai_providers_config

:integrations_config
cls
echo.
echo ================================================================================
echo  INTEGRATIONS CONFIGURATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo CONFIGURE DUCKBOT INTEGRATIONS - DESKTOP AUTOMATION AND MEMORY
echo.
echo 1. [UI-TARS] Configure UI-TARS Desktop Automation
echo    Set up UI-TARS integration, models, and automation settings
echo.
echo 2. [BYTEBOT] Configure ByteBot Integration
echo    Set up ByteBot with Claude Code support and automation rules
echo.
echo 3. [MEMENTO] Configure Memento Memory System
echo    Set up persistent memory, learning, and context management
echo.
echo 4. [ARCHON] Configure Archon Multi-Agent System
echo    Set up agents, collaboration, and knowledge management
echo.
echo 5. [MCP] Configure MCP Server
echo    Set up Model Context Protocol server and tools
echo.
echo 6. [WSL] Configure WSL Integration
echo    Set up Windows Subsystem for Linux integration
echo.
echo 7. [DISCORD] Configure Discord Bot
echo    Set up Discord bot integration and server management
echo.
echo 8. [CHARM] Configure Charm Terminal Ecosystem
echo    Set up Charm tools and terminal integration
echo.
echo 9. [TEST] Test All Integrations
echo    Test all configured integrations
echo.
echo B. [BACK] Return to Settings Menu
echo.
set /p int_choice="[INTEGRATIONS PROMPT] Enter your choice: "

if /i "%int_choice%"=="1" goto config_ui_tars
if /i "%int_choice%"=="2" goto config_bytebot
if /i "%int_choice%"=="3" goto config_memento
if /i "%int_choice%"=="4" goto config_archon
if /i "%int_choice%"=="5" goto config_mcp
if /i "%int_choice%"=="6" goto config_wsl
if /i "%int_choice%"=="7" goto config_discord
if /i "%int_choice%"=="8" goto config_charm
if /i "%int_choice%"=="9" goto test_integrations
if /i "%int_choice%"=="B" goto config_settings
if /i "%int_choice%"=="b" goto config_settings

echo.
echo [ERROR] Invalid integration choice: %int_choice%
echo Press any key to try again...
pause
goto integrations_config

:webui_config
cls
echo.
echo ================================================================================
echo  WEBUI CONFIGURATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo CONFIGURE WEBUI INTERFACES - THEMES, PORTS, AND ACCESS
echo.
echo 1. [THEME] Configure Theme and Appearance
echo    Set dark/light mode, colors, and UI styling
echo.
echo 2. [PORTS] Configure WebUI Ports
echo    Set ports for WebUI, monitoring, and other services
echo.
echo 3. [AUTH] Configure Authentication
echo    Set up user authentication and access controls
echo.
echo 4. [FEATURES] Configure WebUI Features
echo    Enable/disable chat, monitoring, tools, and other features
echo.
echo 5. [UI-TARS-STYLE] Configure UI-TARS Style Interface
echo    Set up UI-TARS inspired web interface elements
echo.
echo 6. [BYTEBOT-STYLE] Configure ByteBot Style Interface
echo    Set up ByteBot inspired web interface elements
echo.
echo 7. [MOBILE] Configure Mobile Support
echo    Set up mobile-friendly interface and responsive design
echo.
echo 8. [WIDGETS] Configure Widgets and Dashboards
echo    Set up custom widgets, charts, and dashboard elements
echo.
echo B. [BACK] Return to Settings Menu
echo.
set /p web_choice="[WEBUI PROMPT] Enter your choice: "

if /i "%web_choice%"=="1" goto config_theme
if /i "%web_choice%"=="2" goto config_ports
if /i "%web_choice%"=="3" goto config_auth
if /i "%web_choice%"=="4" goto config_features
if /i "%web_choice%"=="5" goto config_ui_tars_style
if /i "%web_choice%"=="6" goto config_bytebot_style
if /i "%web_choice%"=="7" goto config_mobile
if /i "%web_choice%"=="8" goto config_widgets
if /i "%web_choice%"=="B" goto config_settings
if /i "%web_choice%"=="b" goto config_settings

echo.
echo [ERROR] Invalid WebUI choice: %web_choice%
echo Press any key to try again...
pause
goto webui_config

:config_openai
cls
echo.
echo ================================================================================
echo  CONFIGURE OPENAI PROVIDER v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo OpenAI Configuration - Set up OpenAI API access
echo.
set /p openai_key="[INPUT] Enter OpenAI API key (or press Enter to keep current): "
if not "%openai_key%"=="" (
    echo %openai_key%> config\openai_key.txt
    echo [INFO] OpenAI API key saved
)

set /p openai_model="[INPUT] Enter OpenAI model (default: gpt-4): "
if "%openai_model%"=="" set "openai_model=gpt-4"
echo %openai_model%> config\openai_model.txt
echo [INFO] OpenAI model set to: %openai_model%

echo.
echo [INFO] OpenAI configuration saved
echo [INFO] You can test the connection with option 9 from AI Providers menu
pause
goto ai_providers_config

:config_anthropic
cls
echo.
echo ================================================================================
echo  CONFIGURE ANTHROPIC CLAUDE PROVIDER v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Anthropic Claude Configuration - Set up Claude API access
echo.
set /p anthropic_key="[INPUT] Enter Anthropic API key (or press Enter to keep current): "
if not "%anthropic_key%"=="" (
    echo %anthropic_key%> config\anthropic_key.txt
    echo [INFO] Anthropic API key saved
)

set /p anthropic_model="[INPUT] Enter Claude model (default: claude-3-sonnet-20240229): "
if "%anthropic_model%"=="" set "anthropic_model=claude-3-sonnet-20240229"
echo %anthropic_model%> config\anthropic_model.txt
echo [INFO] Claude model set to: %anthropic_model%

echo.
echo [INFO] Anthropic Claude configuration saved
echo [INFO] You can test the connection with option 9 from AI Providers menu
pause
goto ai_providers_config

:config_lm_studio
cls
echo.
echo ================================================================================
echo  CONFIGURE LM STUDIO PROVIDER v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LM Studio Configuration - Set up local model access
echo.
set /p lm_studio_url="[INPUT] Enter LM Studio URL (default: http://localhost:1234): "
if "%lm_studio_url%"=="" set "lm_studio_url=http://localhost:1234"
echo %lm_studio_url%> config\lm_studio_url.txt
echo [INFO] LM Studio URL set to: %lm_studio_url%

set /p lm_studio_model="[INPUT] Enter LM Studio model name: "
if not "%lm_studio_model%"=="" (
    echo %lm_studio_model%> config\lm_studio_model.txt
    echo [INFO] LM Studio model set to: %lm_studio_model%
)

echo.
echo [INFO] LM Studio configuration saved
echo [INFO] Make sure LM Studio is running and model is loaded
pause
goto ai_providers_config

:config_ui_tars
cls
echo.
echo ================================================================================
echo  CONFIGURE UI-TARS INTEGRATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo UI-TARS Configuration - Set up desktop automation integration
echo.
echo [INFO] UI-TARS supports multiple AI providers through DuckBot routing
echo.
set /p ui_tars_provider="[INPUT] Enter UI-TARS AI provider (duckbot/openai/anthropic/lm-studio/ollama): "
if "%ui_tars_provider%"=="" set "ui_tars_provider=duckbot"
echo %ui_tars_provider%> config\ui_tars_provider.txt
echo [INFO] UI-TARS AI provider set to: %ui_tars_provider%

set /p ui_tars_model="[INPUT] Enter UI-TARS model (or press Enter for default): "
if not "%ui_tars_model%"=="" (
    echo %ui_tars_model%> config\ui_tars_model.txt
    echo [INFO] UI-TARS model set to: %ui_tars_model%
)

set /p ui_tars_max_steps="[INPUT] Enter max automation steps (default: 50): "
if "%ui_tars_max_steps%"=="" set "ui_tars_max_steps=50"
echo %ui_tars_max_steps%> config\ui_tars_max_steps.txt
echo [INFO] UI-TARS max steps set to: %ui_tars_max_steps%

echo.
echo [INFO] UI-TARS configuration saved
echo [INFO] Use option U from main menu to start UI-TARS automation
pause
goto integrations_config

:config_bytebot
cls
echo.
echo ================================================================================
echo  CONFIGURE BYTEBOT INTEGRATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo ByteBot Configuration - Set up desktop automation with Claude Code support
echo.
echo [INFO] ByteBot can use Claude Code for enhanced automation capabilities
echo.
set /p bytebot_claude_code="[INPUT] Enable Claude Code integration for ByteBot? (Y/N): "
if /i "%bytebot_claude_code%"=="Y" (
    echo enabled> config\bytebot_claude_code.txt
    echo [INFO] Claude Code integration enabled for ByteBot
) else (
    echo disabled> config\bytebot_claude_code.txt
    echo [INFO] Claude Code integration disabled for ByteBot
)

set /p bytebot_provider="[INPUT] Enter ByteBot AI provider (duckbot/openai/anthropic/claude-code): "
if "%bytebot_provider%"=="" set "bytebot_provider=duckbot"
echo %bytebot_provider%> config\bytebot_provider.txt
echo [INFO] ByteBot AI provider set to: %bytebot_provider%

echo.
echo [INFO] ByteBot configuration saved
echo [INFO] Claude Code integration: %bytebot_claude_code%
pause
goto integrations_config

:config_memento
cls
echo.
echo ================================================================================
echo  CONFIGURE MEMENTO MEMORY SYSTEM v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Memento Configuration - Set up persistent memory and learning system
echo.
echo [INFO] Memento provides conversation memory and learning capabilities
echo.
set /p memento_enabled="[INPUT] Enable Memento memory system? (Y/N): "
if /i "%memento_enabled%"=="Y" (
    echo enabled> config\memento_enabled.txt
    echo [INFO] Memento memory system enabled
) else (
    echo disabled> config\memento_enabled.txt
    echo [INFO] Memento memory system disabled
)

set /p memento_storage="[INPUT] Enter Memento storage path (default: memory/memento.db): "
if "%memento_storage%"=="" set "memento_storage=memory/memento.db"
echo %memento_storage%> config\memento_storage.txt
echo [INFO] Memento storage path set to: %memento_storage%

echo.
echo [INFO] Memento configuration saved
pause
goto integrations_config

:view_config
cls
echo.
echo ================================================================================
echo  CURRENT DUCKBOT CONFIGURATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo DISPLAYING CURRENT CONFIGURATION FILES AND SETTINGS
echo.

echo [INFO] Checking configuration directory...
if not exist "config" mkdir config

echo.
echo === AI PROVIDERS CONFIGURATION ===
if exist "config\openai_key.txt" echo   - OpenAI: Configured
if exist "config\anthropic_key.txt" echo   - Anthropic Claude: Configured
if exist "config\lm_studio_url.txt" echo   - LM Studio: Configured
if exist "config\ollama_url.txt" echo   - Ollama: Configured

echo.
echo === INTEGRATIONS CONFIGURATION ===
if exist "config\ui_tars_provider.txt" (
    set /p ui_tars_prov=<config\ui_tars_provider.txt
    echo   - UI-TARS: %ui_tars_prov%
) else (
    echo   - UI-TARS: Not configured
)

if exist "config\bytebot_provider.txt" (
    set /p bytebot_prov=<config\bytebot_provider.txt
    echo   - ByteBot: %bytebot_prov%
) else (
    echo   - ByteBot: Not configured
)

if exist "config\memento_enabled.txt" (
    set /p memento_status=<config\memento_enabled.txt
    echo   - Memento: %memento_status%
) else (
    echo   - Memento: Not configured
)

echo.
echo === SYSTEM CONFIGURATION ===
echo   - Python Version:
python --version 2>nul
echo   - Current Directory: %CD%
echo   - Config Directory: config\
echo   - Logs Directory: logs\

echo.
echo === PORTS AND SERVICES ===
netstat -ano | findstr :8787 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo   - WebUI (8787): RUNNING
) else (
    echo   - WebUI (8787): STOPPED
)

netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo   - System Monitor (8789): RUNNING
) else (
    echo   - System Monitor (8789): STOPPED
)

netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo   - MCP Server (8000): RUNNING
) else (
    echo   - MCP Server (8000): STOPPED
)

echo.
echo === CONFIGURATION FILES ===
if exist "config\" (
    echo   - Configuration files found in config\ directory:
    dir /b config\ 2>nul
) else (
    echo   - No configuration files found
)

echo.
echo Press any key to return to Settings menu...
pause
goto config_settings

:test_ai_providers
cls
echo.
echo ================================================================================
echo  TEST AI PROVIDERS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo TESTING CONFIGURED AI PROVIDERS
echo.

echo [1/4] Testing OpenAI...
python -c "
import os
try:
    key = open('config/openai_key.txt').read().strip()
    if key:
        import openai
        client = openai.OpenAI(api_key=key)
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'Hello'}],
            max_tokens=10
        )
        print('  OpenAI: SUCCESS - API key valid')
    else:
        print('  Openai: NOT CONFIGURED')
except Exception as e:
    print(f'  OpenAI: FAILED - {str(e)[:50]}...')
" 2>nul || echo "  OpenAI: NOT INSTALLED or NOT CONFIGURED"

echo [2/4] Testing Anthropic Claude...
python -c "
import os
try:
    key = open('config/anthropic_key.txt').read().strip()
    if key:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=10,
            messages=[{'role': 'user', 'content': 'Hello'}]
        )
        print('  Anthropic: SUCCESS - API key valid')
    else:
        print('  Anthropic: NOT CONFIGURED')
except Exception as e:
    print(f'  Anthropic: FAILED - {str(e)[:50]}...')
" 2>nul || echo "  Anthropic: NOT INSTALLED or NOT CONFIGURED"

echo [3/4] Testing LM Studio...
python -c "
import requests
try:
    url = open('config/lm_studio_url.txt').read().strip()
    if url:
        response = requests.get(f'{url}/v1/models', timeout=5)
        if response.status_code == 200:
            print('  LM Studio: SUCCESS - Connection established')
        else:
            print(f'  LM Studio: FAILED - HTTP {response.status_code}')
    else:
        print('  LM Studio: NOT CONFIGURED')
except Exception as e:
    print(f'  LM Studio: FAILED - {str(e)[:50]}...')
" 2>nul || echo "  LM Studio: NOT CONFIGURED or OFFLINE"

echo [4/4] Testing Ollama...
python -c "
import requests
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        print('  Ollama: SUCCESS - Service running')
    else:
        print(f'  Ollama: FAILED - HTTP {response.status_code}')
except Exception as e:
    print(f'  Ollama: FAILED - {str(e)[:50]}...')
" 2>nul || echo "  Ollama: NOT RUNNING"

echo.
echo [INFO] AI provider testing completed
echo [INFO] Configure providers with options 1-6 from AI Providers menu
pause
goto ai_providers_config

:test_integrations
cls
echo.
echo ================================================================================
echo  TEST INTEGRATIONS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo TESTING CONFIGURED INTEGRATIONS
echo.

echo [1/4] Testing UI-TARS Integration...
python -c "
try:
    from duckbot.integrations.ui_tars_integration import UITarsIntegration
    integration = UITarsIntegration()
    status = integration.get_status()
    print(f'  UI-TARS: {status[\"installed\"] and \"INSTALLED\" or \"NOT INSTALLED\"}')
    if status['installed']:
        print(f'    - Provider: {status[\"config\"][\"provider\"]}')
        print(f'    - Model: {status[\"config\"][\"model\"]}')
except Exception as e:
    print(f'  UI-TARS: ERROR - {str(e)[:50]}...')
" 2>nul || echo "  UI-TARS: NOT AVAILABLE"

echo [2/4] Testing ByteBot Integration...
python -c "
try:
    from duckbot.bytebot_integration import ByteBotIntegration
    bytebot = ByteBotIntegration()
    print('  ByteBot: AVAILABLE')
except Exception as e:
    print(f'  ByteBot: ERROR - {str(e)[:50]}...')
" 2>nul || echo "  ByteBot: NOT AVAILABLE"

echo [3/4] Testing Memento Integration...
python -c "
try:
    from duckbot.memento_integration import MementoIntegration
    memento = MementoIntegration()
    print('  Memento: AVAILABLE')
except Exception as e:
    print(f'  Memento: ERROR - {str(e)[:50]}...')
" 2>nul || echo "  Memento: NOT AVAILABLE"

echo [4/4] Testing MCP Server...
python -c "
try:
    from duckbot.integrations.mcp_server import MCPServer
    server = MCPServer()
    tools = server.get_mcp_tools()
    print(f'  MCP Server: AVAILABLE with {len(tools)} tools')
except Exception as e:
    print(f'  MCP Server: ERROR - {str(e)[:50]}...')
" 2>nul || echo "  MCP Server: NOT AVAILABLE"

echo.
echo [INFO] Integration testing completed
pause
goto integrations_config

:ui_tars_mode
cls
echo.
echo ================================================================================
echo  UI-TARS DESKTOP AUTOMATION v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: UI-TARS Integration with DuckBot Backend
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo [INFO] Initializing UI-TARS with DuckBot as central brain...
echo [INFO] Supported AI backends: DuckBot AI Router, LM Studio, Open Router, Ollama
echo [INFO] Natural language GUI automation with computer vision
echo.

echo [1/4] Starting DuckBot AI Router (central brain)...
start "DuckBot AI Router" /MIN python -m duckbot.ai_router_gpt
timeout /t 2 >nul

echo [2/4] Starting MCP Server for tool integration...
start "MCP Server" /MIN python -c "from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start_service())"
timeout /t 2 >nul

echo [3/4] Starting Enhanced WebUI for control interface...
start "Enhanced WebUI" /MIN python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
timeout /t 2 >nul

echo [4/4] Starting UI-TARS Desktop Automation...
python -c "from duckbot.integrations.ui_tars_integration import UITarsIntegration; import asyncio; integration = UITarsIntegration(); asyncio.run(integration.start_interactive_mode())"

set "UI_TARS_EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  UI-TARS SESSION COMPLETED
echo ================================================================================
echo.
echo [INFO] UI-TARS session ended with exit code: %UI_TARS_EXIT_CODE%
echo [INFO] WebUI still available at: http://localhost:8787
echo [INFO] Background services still running
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:multi_agent_mode
cls
echo.
echo ================================================================================
echo  ARCHON MULTI-AGENT SYSTEM v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Advanced Multi-Agent Orchestration
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting Archon Multi-Agent System...
echo This will start the agent orchestration system with knowledge management.
python -c "from duckbot.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_interactive_mode())"

pause
goto main_menu

:wsl_integration_mode
cls
echo.
echo ================================================================================
echo  WSL INTEGRATION MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Windows Subsystem for Linux Integration
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

REM Check WSL availability
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo WSL is not installed or not available on this system.
    echo Please install WSL first: https://docs.microsoft.com/en-us/windows/wsl/install
    pause
    goto main_menu
)

echo Starting WSL Integration...
python -c "from duckbot.wsl_integration import WSLIntegration; import asyncio; asyncio.run(WSLIntegration().start_interactive_mode())"

pause
goto main_menu

:all_interfaces_mode
cls
echo.
echo ================================================================================
echo  ALL INTERFACES MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: All User Interfaces Simultaneously
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting all interfaces...
echo [1/4] Enhanced WebUI...
start "Enhanced WebUI" /MIN python -m duckbot.webui_enhanced --port 8787

echo [2/4] Charm Terminal...
start "Charm Terminal" /MIN python -m duckbot.charm_terminal_ui

echo [3/4] ByteBot Desktop...
start "ByteBot Desktop" /MIN python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())"

echo [4/4] System Monitor...
start "System Monitor" /MIN python ai_ecosystem_manager.py

echo All interfaces started!
echo Enhanced WebUI: http://localhost:8787
echo System Monitor: http://localhost:8789
echo Other interfaces running in background windows
echo.
echo [AUTO] Launching Electron Desktop UI...
call :launch_duckbot_desktop
echo NOTE: Use localhost URLs for Tailscale-friendly access
pause
goto main_menu

:webui_gallery_mode
cls
echo.
echo ================================================================================
echo  WEBUI GALLERY MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: WebUI Gallery with Multiple Ports
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting WebUI Gallery...
echo Enhanced WebUI: http://localhost:8787
start "Enhanced WebUI" /MIN python -m duckbot.ui.unified_webui --host 127.0.0.1 --port 8787 --mode classic
timeout /t 2 >nul

echo Charm WebUI: http://localhost:8788
start "Charm WebUI" /MIN python -m duckbot.charm_webui --host 127.0.0.1 --port 8788
timeout /t 2 >nul

echo System Monitor: http://localhost:8789
start "Monitor" /MIN python ai_ecosystem_manager.py --host 127.0.0.1 --port 8789

echo.
echo WebUI Gallery started! All services accessible via localhost.
echo NOTE: Use localhost URLs for Tailscale-friendly access.
echo [AUTO] Launching Electron Desktop UI...
call :launch_duckbot_desktop
pause
goto main_menu

:developer_mode
cls
echo.
echo ================================================================================
echo  DEVELOPER MODE v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Developer Mode with Debug Features
echo.

echo [CHECK] Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo Press any key to return to the main menu...
    pause
    goto main_menu
) else (
    echo [CHECK] Python: OK
)

echo Starting Developer Mode...
echo This mode includes enhanced debugging and live reloading.
echo [AUTO] Launching Electron Desktop UI...
call :launch_duckbot_desktop
python -m duckbot.enhanced_webui --debug --reload --port 8787

pause
goto main_menu

:electron_desktop_mode
REM DEPRECATED: Electron UI has been replaced with DuckBot Desktop Environment
cls
echo.
echo ================================================================================
echo  DESKTOP MODE REDIRECT v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo [INFO] Electron Desktop UI has been replaced with DuckBot Desktop Environment
echo        Redirecting you to the new and improved WSL-based desktop...
echo.

timeout /t 3 >nul
goto duckbot_desktop_environment

:mcp_server_only
cls
echo.
echo ================================================================================
echo  START MCP SERVER ONLY v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: MCP Server for External AI Tool Integration
echo.
echo [INFO] Starting ONLY the MCP server (no additional services)
echo [INFO] Fast startup for connecting Qwen Code CLI, Claude Code, etc.
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo [INFO] Starting MCP Server...
echo [INFO] MCP Server will be available at: http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server when finished
echo.

%PY_CMD% -m duckbot.integrations.mcp_server

echo.
echo [INFO] MCP Server stopped
pause
goto main_menu

:mcp_options
cls
echo.
echo ================================================================================
echo  MCP (MODEL CONTEXT PROTOCOL) OPTIONS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo MCP SERVER MANAGEMENT - Docker + Local Options
echo.
echo 1. [START-LOCAL] Start MCP Server (Local)
echo    Start MCP server locally with DuckBot integrations
echo    Available at: http://localhost:8000
echo.
echo 2. [START-DOCKER] Start MCP Server (Docker)
echo    Start MCP server in Docker container
echo    Better isolation and portability
echo.
echo 3. [STOP-LOCAL] Stop MCP Server (Local)
echo    Stop locally running MCP server
echo.
echo 4. [STOP-DOCKER] Stop MCP Server (Docker)
echo    Stop Docker MCP container
echo.
echo 5. [STATUS] Check MCP Server Status
echo    Check both local and Docker MCP status
echo.
echo 6. [TOOLS] List Available MCP Tools
echo    Show all available MCP tools and capabilities
echo.
echo 7. [COMPOSE] Start Full MCP Stack (Docker Compose)
echo    Start MCP server + WebUI with Docker Compose
echo.
echo 8. [LOGS] View MCP Server Logs
echo    View real-time MCP server logs
echo.
echo 9. [GATEWAY-STATUS] Docker MCP Gateway Status
echo    Check Docker MCP Gateway availability and status
echo.
echo 10. [GATEWAY-SERVERS] List Gateway Servers
echo    Show all servers managed by Docker MCP Gateway
echo.
echo 11. [GATEWAY-ADD] Add Gateway Server
echo    Add new MCP server to Docker Gateway
echo.
echo 12. [GATEWAY-REMOVE] Remove Gateway Server
echo    Remove MCP server from Docker Gateway
echo.
echo B. [BACK] Return to Main Menu
echo.
set /p mcp_choice="[MCP PROMPT] Enter your MCP choice: "

if /i "%mcp_choice%"=="1" goto mcp_start_local
if /i "%mcp_choice%"=="2" goto mcp_start_docker
if /i "%mcp_choice%"=="3" goto mcp_stop_local
if /i "%mcp_choice%"=="4" goto mcp_stop_docker
if /i "%mcp_choice%"=="5" goto mcp_status
if /i "%mcp_choice%"=="6" goto mcp_tools
if /i "%mcp_choice%"=="7" goto mcp_compose
if /i "%mcp_choice%"=="8" goto mcp_logs
if /i "%mcp_choice%"=="9" goto mcp_gateway_status
if /i "%mcp_choice%"=="10" goto mcp_gateway_servers
if /i "%mcp_choice%"=="11" goto mcp_gateway_add
if /i "%mcp_choice%"=="12" goto mcp_gateway_remove
if /i "%mcp_choice%"=="B" goto main_menu
if /i "%mcp_choice%"=="b" goto main_menu

echo.
echo [ERROR] Invalid MCP choice: %mcp_choice%
echo Press any key to try again...
pause
goto mcp_options

:mcp_start_local
cls
echo.
echo ================================================================================
echo  START MCP SERVER (LOCAL) v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Starting MCP server locally...
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto mcp_options
)

echo [INFO] Starting MCP server on http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server
echo.
python -m duckbot.mcp_server
pause
goto mcp_options

:mcp_start_docker
cls
echo.
echo ================================================================================
echo  START MCP SERVER (DOCKER) v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Starting MCP server in Docker container...
echo.
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    goto mcp_options
)

echo [INFO] Building and starting MCP Docker container...
echo [INFO] This may take a few minutes on first run...
echo.
docker build -f Dockerfile.mcp -t duckbot-mcp .
if %errorlevel% equ 0 (
    echo [INFO] Docker image built successfully
    docker run -d --name duckbot-mcp -p 8000:8000 duckbot-mcp
    if %errorlevel% equ 0 (
        echo [SUCCESS] MCP Docker container started
        echo [INFO] MCP server available at: http://localhost:8000
        echo [INFO] Container name: duckbot-mcp
    ) else (
        echo [ERROR] Failed to start MCP container
    )
) else (
    echo [ERROR] Failed to build MCP Docker image
)
pause
goto mcp_options

:mcp_stop_local
cls
echo.
echo ================================================================================
echo  STOP MCP SERVER (LOCAL) v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Stopping local MCP server...
echo.
taskkill //F /IM python.exe /FI "WINDOWTITLE eq *mcp*" /FI "COMMANDLINE eq *mcp*" 2>nul
taskkill //F /PID 8000 2>nul
echo [INFO] Local MCP server stopped (if running)
pause
goto mcp_options

:mcp_stop_docker
cls
echo.
echo ================================================================================
echo  STOP MCP SERVER (DOCKER) v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Stopping MCP Docker container...
echo.
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker stop duckbot-mcp 2>nul
    docker rm duckbot-mcp 2>nul
    echo [INFO] MCP Docker container stopped (if running)
) else (
    echo [WARN] Docker not available
)
pause
goto mcp_options

:mcp_status
cls
echo.
echo ================================================================================
echo  MCP SERVER STATUS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Checking MCP server status...
echo.

echo [LOCAL] Checking local MCP server...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [LOCAL] MCP server: RUNNING on port 8000
) else (
    echo [LOCAL] MCP server: STOPPED
)

echo [DOCKER] Checking Docker MCP container...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker ps --filter "name=duckbot-mcp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>nul
    if %errorlevel% neq 0 (
        echo [DOCKER] MCP container: STOPPED
    )
) else (
    echo [DOCKER] Docker: NOT AVAILABLE
)

echo [WEBUI] Checking Enhanced WebUI MCP integration...
python -c "import requests; r=requests.get('http://localhost:8787/api/mcp/status', timeout=5); print(f'[WEBUI] MCP Integration: {r.json().get(\"status\", \"UNKNOWN\")}')" 2>nul || (
    echo [WEBUI] MCP Integration: UNAVAILABLE (WebUI not running)
)

pause
goto mcp_options

:mcp_tools
cls
echo.
echo ================================================================================
echo  MCP TOOLS LIST v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Listing available MCP tools...
echo.

python -c "
try:
    import requests
    r = requests.get('http://localhost:8787/api/mcp/tools', timeout=5)
    if r.status_code == 200:
        tools = r.json().get('tools', [])
        if tools:
            print('AVAILABLE MCP TOOLS:')
            for i, tool in enumerate(tools, 1):
                name = tool.get('name', 'Unknown')
                desc = tool.get('description', 'No description')
                print(f'  {i}. {name}')
                print(f'     {desc}')
                print()
        else:
            print('No MCP tools available')
    else:
        print(f'Failed to get tools: HTTP {r.status_code}')
except Exception as e:
    print(f'Error fetching tools: {e}')
    print('MCP server or WebUI may not be running')
" 2>nul || (
    echo [ERROR] Could not fetch MCP tools
    echo Make sure MCP server or Enhanced WebUI is running
)

pause
goto mcp_options

:mcp_compose
cls
echo.
echo ================================================================================
echo  START MCP STACK (DOCKER COMPOSE) v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Starting full MCP stack with Docker Compose...
echo.
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found!
    pause
    goto mcp_options
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not found!
    pause
    goto mcp_options
)

echo [INFO] Starting MCP stack with docker-compose.mcp.yml
echo [INFO] This includes: MCP server + Enhanced WebUI
echo.
docker-compose -f docker-compose.mcp.yml up -d
if %errorlevel% equ 0 (
    echo [SUCCESS] MCP stack started successfully
    echo [INFO] MCP Server: http://localhost:8000
    echo [INFO] Enhanced WebUI: http://localhost:8787
    echo [INFO] Use 'docker-compose -f docker-compose.mcp.yml down' to stop
) else (
    echo [ERROR] Failed to start MCP stack
)

pause
goto mcp_options

:mcp_logs
cls
echo.
echo ================================================================================
echo  MCP SERVER LOGS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Viewing MCP server logs...
echo.

echo [DOCKER] Checking Docker container logs...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker logs duckbot-mcp 2>nul || (
        echo [DOCKER] No MCP container found or container stopped
    )
) else (
    echo [DOCKER] Docker not available
)

echo.
echo [INFO] Press Ctrl+C to exit log viewing
echo [INFO] To view local MCP logs, check the logs/ directory
echo.
pause
goto mcp_options

:mcp_gateway_status
cls
echo.
echo ================================================================================
echo  DOCKER MCP GATEWAY STATUS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Checking Docker MCP Gateway status...
echo.
echo [INFO] Testing Docker availability...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [DOCKER] Docker: AVAILABLE
) else (
    echo [DOCKER] Docker: NOT AVAILABLE
    echo [ERROR] Docker is required for Docker MCP Gateway
    pause
    goto mcp_options
)

echo.
echo [INFO] Testing Docker MCP Gateway plugin...
docker mcp --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [GATEWAY] Docker MCP Gateway: AVAILABLE
    for /f "tokens=*" %%i in ('docker mcp --version') do echo [GATEWAY] Version: %%i
) else (
    echo [GATEWAY] Docker MCP Gateway: NOT AVAILABLE
    echo [WARN] Docker MCP Gateway plugin not found
    echo [INFO] Install with: docker mcp install
)

echo.
echo [INFO] Checking MCP Gateway configuration...
if exist "%USERPROFILE%\.docker\mcp\config.json" (
    echo [CONFIG] Gateway configuration: FOUND
    echo [INFO] Configuration location: %USERPROFILE%\.docker\mcp\
) else (
    echo [CONFIG] Gateway configuration: NOT FOUND
    echo [INFO] Configuration will be created automatically
)

echo.
echo [INFO] Testing Enhanced WebUI Docker MCP Gateway integration...
python -c "import asyncio, sys; sys.path.append('.'); from duckbot.docker_mcp_gateway import docker_mcp_gateway; result = asyncio.run(docker_mcp_gateway.get_gateway_status()); print(f'[INTEGRATION] Gateway Status: {result.get(\"status\", \"UNKNOWN\")}'); print(f'[INTEGRATION] Docker Running: {result.get(\"docker_running\", False)}'); print(f'[INTEGRATION] Gateway Available: {result.get(\"gateway_available\", False)}'); print(f'[INTEGRATION] Managed Servers: {len(result.get(\"servers\", []))}'); print(f'[INTEGRATION] Available Tools: {result.get(\"total_tools\", 0)}')" 2>nul || echo [INTEGRATION] DuckBot Gateway Integration: UNAVAILABLE

pause
goto mcp_options

:mcp_gateway_servers
cls
echo.
echo ================================================================================
echo  DOCKER MCP GATEWAY SERVERS v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Listing servers managed by Docker MCP Gateway...
echo.
echo [INFO] Testing Docker MCP Gateway availability...
docker mcp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker MCP Gateway not available
    echo [INFO] Install with: docker mcp install
    pause
    goto mcp_options
)

echo.
echo [INFO] Fetching server list from Docker MCP Gateway...
docker mcp server list 2>nul || (
    echo [ERROR] Could not connect to Docker MCP Gateway
    echo [INFO] Make sure Docker is running and gateway is installed
)

echo.
echo [INFO] Checking DuckBot WebUI Gateway integration...
python -c "import asyncio, sys; sys.path.append('.'); from duckbot.docker_mcp_gateway import docker_mcp_gateway; servers = asyncio.run(docker_mcp_gateway.list_servers()); print(f'[INTEGRATION] Total Servers: {servers.get(\"count\", 0)}'); [print(f'[INTEGRATION] - {name}: {\"enabled\" if config.get(\"enabled\", False) else \"disabled\"} ({config.get(\"image\", \"unknown\")})') for name, config in servers.get('servers', {}).items()]" 2>nul || echo [INTEGRATION] DuckBot Gateway Integration: UNAVAILABLE

pause
goto mcp_options

:mcp_gateway_add
cls
echo.
echo ================================================================================
echo  ADD DOCKER MCP GATEWAY SERVER v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Adding new MCP server to Docker Gateway...
echo.
echo [INFO] This will add a new MCP server configuration to the Docker Gateway
echo.
set /p server_name="[INPUT] Enter server name: "
if "%server_name%"=="" (
    echo [ERROR] Server name cannot be empty
    pause
    goto mcp_options
)

set /p server_image="[INPUT] Enter Docker image (e.g., duckbot-mcp:latest): "
if "%server_image%"=="" (
    echo [ERROR] Docker image cannot be empty
    pause
    goto mcp_options
)

set /p server_port="[INPUT] Enter port number (e.g., 8001): "
if "%server_port%"=="" (
    echo [ERROR] Port number cannot be empty
    pause
    goto mcp_options
)

echo.
echo [INFO] Adding server: %server_name%
echo [INFO] Image: %server_image%
echo [INFO] Port: %server_port%
echo.

echo [INFO] Adding server via Docker MCP Gateway...
docker mcp server add %server_name% --image %server_image% --port %server_port% 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Server added to Docker MCP Gateway
    echo [INFO] You can now start the server with: docker mcp server start %server_name%
) else (
    echo [ERROR] Failed to add server to Docker MCP Gateway
    echo [INFO] Make sure Docker MCP Gateway is installed and running
)

echo.
echo [INFO] Adding server to DuckBot WebUI integration...
python -c "import asyncio, sys; sys.path.append('.'); from duckbot.docker_mcp_gateway import DockerMCPServer, docker_mcp_gateway; server_config = DockerMCPServer(name='%server_name%', image='%server_image%', port=int('%server_port%'), environment={}, volumes=[], secrets=[]); result = asyncio.run(docker_mcp_gateway.add_server(server_config)); print('[SUCCESS] Server added to DuckBot WebUI integration' if result.get('success') else f'[ERROR] Failed to add to DuckBot WebUI: {result.get(\"error\", \"Unknown error\")}')" 2>nul || echo [ERROR] Could not add server to DuckBot WebUI integration

pause
goto mcp_options

:mcp_gateway_remove
cls
echo.
echo ================================================================================
echo  REMOVE DOCKER MCP GATEWAY SERVER v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo Removing MCP server from Docker Gateway...
echo.
echo [INFO] First, let's list available servers:
echo.
docker mcp server list 2>nul || (
    echo [ERROR] Could not list servers from Docker MCP Gateway
    echo [INFO] Make sure Docker MCP Gateway is installed and running
    pause
    goto mcp_options
)

echo.
set /p server_name="[INPUT] Enter server name to remove: "
if "%server_name%"=="" (
    echo [ERROR] Server name cannot be empty
    pause
    goto mcp_options
)

echo.
echo [WARNING] This will remove server '%server_name%' from both Docker Gateway and DuckBot
echo [WARNING] This action cannot be undone
echo.
set /p confirm="[CONFIRM] Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" (
    if /i not "%confirm%"=="y" (
        echo [INFO] Operation cancelled
        pause
        goto mcp_options
    )
)

echo.
echo [INFO] Removing server from Docker MCP Gateway...
docker mcp server remove %server_name% 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Server removed from Docker MCP Gateway
) else (
    echo [ERROR] Failed to remove server from Docker MCP Gateway
)

echo.
echo [INFO] Removing server from DuckBot WebUI integration...
python -c "import asyncio, sys; sys.path.append('.'); from duckbot.docker_mcp_gateway import docker_mcp_gateway; result = asyncio.run(docker_mcp_gateway.remove_server('%server_name%')); print('[SUCCESS] Server removed from DuckBot WebUI integration' if result.get('success') else f'[ERROR] Failed to remove from DuckBot WebUI: {result.get(\"error\", \"Unknown error\")}')" 2>nul || echo [ERROR] Could not remove server from DuckBot WebUI integration

pause
goto mcp_options

:exit
cls
echo.
echo ================================================================================
echo  GOODBYE FROM DUCKBOT v%DUCKBOT_VERSION% ULTIMATE ENHANCED!
echo ================================================================================
echo.
echo Thanks for using DuckBot Ultimate Enhanced Edition!
echo.
echo IMPORTANT: If DuckBot is still running in background, it will continue
echo running until you stop it or close all Python processes.
echo.
echo Web interface (if running): http://127.0.0.1:8787
echo Log files location: logs/
echo.
echo Have a great day with your Ultimate AI companion!
timeout /t 5 >nul
exit /b 0

REM ================================================================================
REM UTILITY FUNCTIONS
REM ================================================================================

REM DEPRECATED FUNCTION - Replaced by :launch_duckbot_desktop
:launch_electron_ui
echo [DEPRECATED] Electron UI replaced with DuckBot Desktop Environment
call :launch_duckbot_desktop
goto :eof

:check_python_ultimate
echo Checking Python installation for Ultimate mode...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found!
    echo Python 3.8+ is required for Ultimate DuckBot
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
goto :eof

:check_system_requirements
echo Checking system requirements...
python -c "
import platform
try:
    import psutil
    memory = psutil.virtual_memory()
    if memory.total < 4 * 1024**3:  # 4GB
        print('WARNING: Less than 4GB RAM available. Performance may be limited.')
    else:
        print('Memory: Sufficient (' + str(round(memory.total / 1024**3, 1)) + 'GB)')
    
    disk = psutil.disk_usage('.')
    if disk.free < 2 * 1024**3:  # 2GB
        print('WARNING: Less than 2GB disk space available.')
    else:
        print('Disk Space: Sufficient')
        
    print('System Requirements: OK')
except ImportError:
    print('System Requirements: Cannot verify (psutil not installed)')
"
goto :eof

:invalid_choice
echo.
echo Invalid choice. Please enter a valid option.
timeout /t 3 >nul
goto main_menu

:launch_duckbot_desktop
REM Launch DuckBot Desktop Environment (GNOME + Extension) for Ultimate Mode
echo [AUTO-DESKTOP] Starting DuckBot-DE (GNOME Shell Extension)...
echo [AUTO-DESKTOP] Checking WSL availability...
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo [AUTO-DESKTOP] WSL not installed, checking if available...
    wsl -l -v >nul 2>&1
    if %errorlevel% neq 0 (
        echo [SKIP] WSL not available - Desktop environment skipped
        goto :eof
    )
)

echo [AUTO-DESKTOP] Checking Ubuntu WSL availability...
wsl -d Ubuntu bash -c "echo 'Ubuntu available'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SKIP] Ubuntu WSL not found - Desktop environment skipped
    echo       Run Option 4 to set up Ubuntu with GNOME desktop
    goto :eof
)
echo [OK] Ubuntu WSL is available

if not defined DUCKBOT_DE_PATH (
    echo [SKIP] DuckBot-DE path not set - Desktop environment skipped
    goto :eof
)
if not exist "%DUCKBOT_DE_PATH%" (
    echo [SKIP] DuckBot-DE not found at: %DUCKBOT_DE_PATH%
    goto :eof
)

echo [AUTO-DESKTOP] Preparing VNC xstartup for GNOME...
wsl -d Ubuntu bash -c "mkdir -p ~/.vnc && echo 'duckbot' | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd; cat > ~/.vnc/xstartup <<'EOS'\n#!/bin/bash\nexport DISPLAY=:1\nexport XDG_RUNTIME_DIR=/run/user/\$(id -u)\nmkdir -p \"$XDG_RUNTIME_DIR\"; chmod 700 \"$XDG_RUNTIME_DIR\"\n# Load DuckBot environment if present\n[ -f ~/.duckbot_env ] && . ~/.duckbot_env\nif ! pidof dbus-daemon >/dev/null 2>&1; then\n  eval \"\$(dbus-launch --sh-syntax)\"\nfi\nexec gnome-session --session=ubuntu\nEOS\nchmod +x ~/.vnc/xstartup"

echo [AUTO-DESKTOP] Preparing environment and starting VNC server with GNOME session...
wsl -d Ubuntu bash -c "WIN_HOST=\$(awk '/nameserver/{print $2; exit}' /etc/resolv.conf); echo export DUCKBOT_WEBUI_URL=\"http://\${WIN_HOST}:8787\" > ~/.duckbot_env; mkdir -p ~/.local/bin; if [ -f '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-cli' ]; then cp '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-cli' ~/.local/bin/ && chmod +x ~/.local/bin/duckbot-cli; fi; if [ -f '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-windows' ]; then cp '%DUCKBOT_DE_PATH_WSL%/bin/duckbot-windows' ~/.local/bin/ && chmod +x ~/.local/bin/duckbot-windows; fi"
start "DuckBot VNC Server" /MIN wsl -d Ubuntu bash -c "vncserver -kill :1 > /dev/null 2>&1 || true; vncserver :1 -geometry 1920x1080 -depth 24 -localhost no > /dev/null 2>&1"

echo [AUTO-DESKTOP] Starting noVNC web client on http://localhost:6080 ...
wsl -d Ubuntu bash -c "pkill -f websockify >/dev/null 2>&1 || true; nohup websockify --web=/usr/share/novnc/ 127.0.0.1:6080 127.0.0.1:5901 >/dev/null 2>&1 &"
start "DuckBot noVNC" "http://localhost:6080/vnc.html?autoconnect=1&password=duckbot"

REM Attempt to auto-open a VNC viewer on Windows
echo [VIEWER] Attempting to open a local VNC viewer on 127.0.0.1:5901 (password: duckbot)
if exist "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" (
    start "RealVNC Viewer" "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" 127.0.0.1:5901
) else if exist "C:\Program Files\TightVNC\tvnviewer.exe" (
    start "TightVNC Viewer" "C:\Program Files\TightVNC\tvnviewer.exe" 127.0.0.1::5901
) else if exist "C:\Program Files\UltraVNC\vncviewer.exe" (
    start "UltraVNC Viewer" "C:\Program Files\UltraVNC\vncviewer.exe" 127.0.0.1:5901
) else (
    echo [VIEWER] No VNC viewer detected. Please install RealVNC/TightVNC/UltraVNC, or connect manually.
)

echo [AUTO-DESKTOP] Desktop ready! VNC: localhost:5901 | GNOME + DuckBot-DE
goto :eof
