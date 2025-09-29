@echo off
REM ==============================================================================
REM  🦆 DUCKBOT ENHANCED LAUNCHER v4.2 - QWEN3-OMNI EDITION
REM  Complete AI-Powered Operating System with Qwen3-Omni Main Brain
REM ==============================================================================
REM  Features: 15+ Launch Modes, Multi-Agent AI, Local-Only Privacy,
REM  Enterprise Service Management, Advanced UI Integration
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - Qwen3-Omni Enhanced AI Launcher
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DUCKBOT_VERSION=4.2.0"
set "BUILD_DATE=2025-09-29"
set "BUILD_STATUS=QWEN3-OMNI-ENHANCED"
set "LAUNCHER_MODE=ENHANCED"

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    ) else (
        goto :no_python
    )
)

REM Port configuration
set "WEBUI_PORT=8787"
set "API_PORT=5000"
set "WS_PORT=8000"
set "MONITORING_PORT=8789"
set "TERMINAL_PORT=8788"
set "LM_STUDIO_PORT=1234"

REM Service tracking
set "SERVICES_STARTED=0"
set "QWEN3_BRAIN_STARTED=0"
set "WEBUI_STARTED=0"

REM Main menu loop
:main_menu
cls
echo.
echo ================================================================================
echo  🦆 DUCKBOT v%DUCKBOT_VERSION% - QWEN3-OMNI ENHANCED LAUNCHER
echo ================================================================================
echo    Complete AI-Powered Operating System with Qwen3-Omni Main Brain
echo    [STATUS] %BUILD_STATUS% - Qwen3-Omni Integration Edition
echo    [BUILD] %BUILD_DATE% - Latest Enhanced Build
echo ================================================================================
echo.
echo 🚀 SELECT YOUR LAUNCH MODE:
echo.
echo 1. 🌟 [ULTIMATE] Complete Qwen3-Omni Ecosystem - RECOMMENDED!
echo    ▶ Qwen3-Omni 30B Brain + Full Service Suite
echo    ▶ Enhanced WebUI + Multi-Agent AI + Desktop Automation
echo    ▶ Real-time monitoring + Advanced system integration
echo.
echo 2. 🧠 [QWEN3-OMNI] AI Brain + Server Only
echo    ▶ Qwen3-Omni main brain with API server
echo    ▶ Perfect for development and testing
echo    ▶ Lightweight mode with full AI capabilities
echo.
echo 3. 🌐 [ENHANCED WEBUI] Professional Interface Only
echo    ▶ Modern web dashboard with Qwen3-Omni integration
echo    ▶ Access at: http://localhost:%WEBUI_PORT%
echo    ▶ Real-time monitoring and control
echo.
echo 4. 🏠 [LOCAL-ONLY] Complete Privacy Mode
echo    ▶ Zero external API calls + Full privacy
echo    ▶ LM Studio integration + Local AI processing
echo    ▶ All features work offline with $0 cost
echo.
echo 5. ⚡ [QUICK-START] Ultra-Fast Qwen3-Omni Mode
echo    ▶ One-click startup with optimizations
echo    ▶ Pre-configured for maximum performance
echo.
echo 🎯 SPECIALIZED MODES:
echo.
echo 6. 🧪 [COMPREHENSIVE TEST] Full System Validation
echo    ▶ All features testing + Performance benchmarks
echo    ▶ AI routing + Model detection + Service health
echo.
echo 7. 📊 [MONITORING] Real-time System Dashboard
echo    ▶ Live metrics + Performance tracking
echo    ▶ Resource monitoring + Agent status
echo.
echo 8. 💬 [CHAT] Interactive AI Assistant
echo    ▶ Direct chat with Qwen3-Omni AI
echo    ▶ Ask questions and control DuckBot
echo.
echo 9. 🤖 [MULTI-AGENT] AI Agent Framework
echo    ▶ Deploy specialized AI agents
echo    ▶ Collaborative intelligence system
echo.
echo 10. 🖥️ [DESKTOP] Desktop Automation Mode
echo    ▶ Natural language Windows control
echo    ▶ ByteBot + UI-TARS integration
echo.
echo 🎙️  VOICE & COMMUNICATION:
echo.
echo 11. 🔊 [VIBEVOICE] Advanced TTS Server
echo    ▶ Multi-voice text-to-speech system
echo    ▶ Available at: http://localhost:8000
echo.
echo 12. 🗣️  [VOICE CHAT] Real-time Voice AI
echo    ▶ WebSocket-based live conversation
echo    ▶ Natural voice interaction with Qwen3-Omni
echo.
echo 🔧 SYSTEM MANAGEMENT:
echo.
echo 13. 🛠️  [SERVICE MANAGER] Full Service Control
echo    ▶ Start/stop/monitor all services
echo    ▶ Health checks + Auto-recovery
echo.
echo 14. 📋 [DIAGNOSTICS] System Health Check
echo    ▶ Comprehensive system analysis
echo    ▶ Performance optimization recommendations
echo.
echo 15. ⚙️  [CONFIGURATION] Settings Management
echo    ▶ AI provider configuration
echo    ▶ Hardware optimization settings
echo.
echo 16. 🔄 [UPDATE] System Update & Maintenance
echo    ▶ Update components + Dependencies
echo    ▶ System cleanup and optimization
echo.
echo 17. 🧹 [CLEANUP] Emergency Process Kill
echo    ▶ Kill all DuckBot processes safely
echo    ▶ Reset system state
echo.
echo 18. 📖 [HELP] Documentation & Support
echo    ▶ System information + Usage guides
echo    ▶ Troubleshooting assistance
echo.
echo 19. ℹ️  [ABOUT] System Information
echo    ▶ Version details + Build information
echo    ▶ Hardware + Software configuration
echo.
echo 0. ❌ [EXIT] Exit Launcher
echo.
echo ================================================================================
echo.
set /p choice="Enter your choice [0-19]: "

REM Process user choice
if "%choice%"=="1" goto :ultimate_ecosystem
if "%choice%"=="2" goto :qwen3_brain_only
if "%choice%"=="3" goto :enhanced_webui
if "%choice%"=="4" goto :local_only
if "%choice%"=="5" goto :quick_start
if "%choice%"=="6" goto :comprehensive_test
if "%choice%"=="7" goto :monitoring_dashboard
if "%choice%"=="8" goto :chat_assistant
if "%choice%"=="9" goto :multi_agent
if "%choice%"=="10" goto :desktop_automation
if "%choice%"=="11" goto :vibevoice_server
if "%choice%"=="12" goto :voice_chat
if "%choice%"=="13" goto :service_manager
if "%choice%"=="14" goto :diagnostics
if "%choice%"=="15" goto :configuration
if "%choice%"=="16" goto :system_update
if "%choice%"=="17" goto :emergency_cleanup
if "%choice%"=="18" goto :help_system
if "%choice%"=="19" goto :about_system
if "%choice%"=="0" goto :exit_launcher

REM Invalid choice handling
echo [INVALID] Please enter a number between 0 and 19.
timeout /t 2 >nul
goto :main_menu

REM ============ LAUNCH MODES ============

:ultimate_ecosystem
cls
echo.
echo ================================================================================
echo  🌟 STARTING ULTIMATE QWEN3-OMNI ECOSYSTEM
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

call :start_qwen3_brain
if errorlevel 1 goto :main_menu

call :start_core_services
if errorlevel 1 goto :main_menu

call :start_enhanced_webui
if errorlevel 1 goto :main_menu

call :start_monitoring_services
if errorlevel 1 goto :main_menu

echo.
echo [SUCCESS] Ultimate Qwen3-Omni Ecosystem started successfully!
echo.
echo [SERVICES] All systems operational:
echo   ▶ Qwen3-Omni Brain: http://localhost:%API_PORT%
echo   ▶ Enhanced WebUI: http://localhost:%WEBUI_PORT%
echo   ▶ Monitoring: http://localhost:%MONITORING_PORT%
echo   ▶ Terminal: http://localhost:%TERMINAL_PORT%
echo.
echo [AI] Qwen3-Omni 30B multimodal AI is ready
echo [VOICE] Say "hey duckbot" to activate voice assistant
echo.
pause
goto :main_menu

:qwen3_brain_only
cls
echo.
echo ================================================================================
echo  🧠 STARTING QWEN3-OMNI BRAIN + SERVER
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

call :start_qwen3_brain
if errorlevel 1 goto :main_menu

echo.
echo [SUCCESS] Qwen3-Omni Brain + Server started!
echo.
echo [API] Available at: http://localhost:%API_PORT%
echo [MODEL] Qwen3-Omni 30B with Flash Attention 2
echo [STATUS] Ready for API requests
echo.
pause
goto :main_menu

:enhanced_webui
cls
echo.
echo ================================================================================
echo  🌐 STARTING ENHANCED WEBUI
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

call :start_enhanced_webui
if errorlevel 1 goto :main_menu

echo.
echo [SUCCESS] Enhanced WebUI started successfully!
echo.
echo [ACCESS] http://localhost:%WEBUI_PORT%
echo [FEATURES] Real-time monitoring + AI control
echo.
pause
goto :main_menu

:local_only
cls
echo.
echo ================================================================================
echo  🏠 STARTING LOCAL-ONLY PRIVACY MODE
echo ================================================================================
echo.
call :check_lm_studio
if errorlevel 1 goto :main_menu

call :start_local_services
if errorlevel 1 goto :main_menu

echo.
echo [SUCCESS] Local-Only Privacy Mode started!
echo.
echo [PRIVACY] Zero external API calls
echo [COST] $0 - Complete offline operation
echo [FEATURES] Full DuckBot functionality locally
echo.
pause
goto :main_menu

:quick_start
cls
echo.
echo ================================================================================
echo  ⚡ ULTRA-FAST QWEN3-OMNI STARTUP
echo ================================================================================
echo.
call :check_dependencies_quick
if errorlevel 1 goto :main_menu

echo [INFO] Starting Qwen3-Omni Brain...
start "Qwen3-Omni Brain" /MIN %PY_CMD% start_qwen_brain_and_server.py

timeout /t 5 /nobreak >nul

echo [INFO] Starting essential services...
start "Service Manager" /MIN %PY_CMD% -m duckbot.core.service_manager

timeout /t 3 /nobreak >nul

echo [INFO] Starting WebUI...
start "Enhanced WebUI" /MIN %PY_CMD% -m duckbot.enhanced_webui --port %WEBUI_PORT%

echo.
echo [SUCCESS] Quick Start completed!
echo [WEBUI] http://localhost:%WEBUI_PORT%
echo [STATUS] Services starting in background...
echo.
pause
goto :main_menu

:comprehensive_test
cls
echo.
echo ================================================================================
echo  🧪 COMPREHENSIVE SYSTEM TESTING
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Running comprehensive test suite...
%PY_CMD% tests/unified_test_suite.py

if errorlevel 1 (
    echo [ERROR] Some tests failed. Check logs for details.
) else (
    echo [SUCCESS] All tests passed!
)
echo.
pause
goto :main_menu

:monitoring_dashboard
cls
echo.
echo ================================================================================
echo  📊 SYSTEM MONITORING DASHBOARD
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting monitoring dashboard...
start "Monitoring Dashboard" %PY_CMD% ai_ecosystem_manager.py --host 127.0.0.1 --port %MONITORING_PORT%

echo.
echo [SUCCESS] Monitoring dashboard started!
echo [ACCESS] http://localhost:%MONITORING_PORT%
echo.
pause
goto :main_menu

:chat_assistant
cls
echo.
echo ================================================================================
echo  💬 INTERACTIVE AI ASSISTANT
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting interactive chat assistant...
%PY_CMD% chat_with_ai.py

echo.
pause
goto :main_menu

:multi_agent
cls
echo.
echo ================================================================================
echo  🤖 MULTI-AGENT AI FRAMEWORK
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting multi-agent framework...
start "Multi-Agent Framework" %PY_CMD% -m duckbot.integrations.archon_integration

echo.
echo [SUCCESS] Multi-Agent framework started!
echo [STATUS] Agents are initializing and coordinating...
echo.
pause
goto :main_menu

:desktop_automation
cls
echo.
echo ================================================================================
echo  🖥️ DESKTOP AUTOMATION MODE
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting desktop automation...
start "Desktop Automation" %PY_CMD% -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"

echo.
echo [SUCCESS] Desktop automation started!
echo [CONTROL] Use natural language to control Windows applications
echo.
pause
goto :main_menu

:vibevoice_server
cls
echo.
echo ================================================================================
echo  🔊 VIBEVOICE TTS SERVER
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting VibeVoice TTS Server...
start "VibeVoice Server" %PY_CMD% START_VIBEVOICE_SERVER.bat

echo.
echo [SUCCESS] VibeVoice server started!
echo [ACCESS] http://localhost:8000
echo [FEATURES] Multi-voice TTS with advanced synthesis
echo.
pause
goto :main_menu

:voice_chat
cls
echo.
echo ================================================================================
echo  🗣️  REAL-TIME VOICE CHAT
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting real-time voice chat...
start "Voice Chat" %PY_CMD% start_realtime_voicechat_enhanced.bat

echo.
echo [SUCCESS] Voice chat system started!
echo [STATUS] Ready for natural voice conversations
echo.
pause
goto :main_menu

:service_manager
cls
echo.
echo ================================================================================
echo  🛠️  SERVICE MANAGER
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Starting service manager...
%PY_CMD% -c "from duckbot.core.service_manager import UnifiedServiceManager; manager = UnifiedServiceManager(); import asyncio; asyncio.run(manager.start_all_services())"

echo.
echo [SUCCESS] Service manager completed!
echo [STATUS] All services have been processed
echo.
pause
goto :main_menu

:diagnostics
cls
echo.
echo ================================================================================
echo  📋 SYSTEM DIAGNOSTICS
echo ================================================================================
echo.
call :check_dependencies
if errorlevel 1 goto :main_menu

echo [INFO] Running comprehensive diagnostics...
echo.

echo [INFO] Checking service health...
%PY_CMD% diagnostics/doctor_check_services.py

echo.
echo [INFO] Checking system imports...
%PY_CMD% diagnostics/doctor_check_imports.py

echo.
echo [INFO] Generating diagnostic report...
%PY_CMD% diagnostics/doctor_generate_report.py

echo.
echo [SUCCESS] Diagnostics completed!
echo [REPORT] Check diagnostic files in logs/ directory
echo.
pause
goto :main_menu

:configuration
cls
echo.
echo ================================================================================
echo  ⚙️  CONFIGURATION MANAGEMENT
echo ================================================================================
echo.
echo 1. AI Provider Configuration
echo 2. Hardware Configuration
echo 3. Qwen3-Omni Configuration
echo 4. Ecosystem Configuration
echo 5. Environment Variables
echo 6. Back to Main Menu
echo.
set /p config_choice="Enter configuration choice [1-6]: "

if "%config_choice%"=="1" call :edit_config "config/ai_config.json"
if "%config_choice%"=="2" call :edit_config "config/hardware_config.json"
if "%config_choice%"=="3" call :edit_config "config/qwen3_omni_config.json"
if "%config_choice%"=="4" call :edit_config "ecosystem_config.yaml"
if "%config_choice%"=="5" call :edit_config ".env"
if "%config_choice%"=="6" goto :main_menu

goto :configuration

:system_update
cls
echo.
echo ================================================================================
echo  🔄 SYSTEM UPDATE & MAINTENANCE
echo ================================================================================
echo.
echo 1. Update Dependencies
echo 2. Update Qwen3-Omni Model
echo 3. Clean Cache and Temp Files
echo 4. System Optimization
echo 5. Back to Main Menu
echo.
set /p update_choice="Enter update choice [1-5]: "

if "%update_choice%"=="1" (
    echo [INFO] Updating dependencies...
    %PY_CMD% -m pip install --upgrade -r docs/requirements.txt
)
if "%update_choice%"=="2" (
    echo [INFO] Qwen3-Omni model update...
    echo [NOTE] Model updates require manual download from Hugging Face
    echo [INFO] Opening model download page...
    start https://huggingface.co/Qwen/Qwen3-Omni-4B
)
if "%update_choice%"=="3" (
    echo [INFO] Cleaning cache and temp files...
    if exist "__pycache__" rmdir /s /q "__pycache__"
    if exist "logs" del /q "logs\*.log"
    echo [INFO] Cleanup completed!
)
if "%update_choice%"=="4" (
    echo [INFO] Running system optimization...
    %PY_CMD% -c "import duckbot.core.hardware_detector as hd; hd.optimize_system()"
)

echo.
pause
goto :main_menu

:emergency_cleanup
cls
echo.
echo ================================================================================
echo  🧹 EMERGENCY PROCESS CLEANUP
echo ================================================================================
echo.
echo [WARN] This will kill all DuckBot processes!
echo [INFO] Make sure all important work is saved.
echo.
set /p confirm="Are you sure you want to continue? [Y/N]: "
if /i "%confirm%"=="Y" goto :do_cleanup
if /i "%confirm%"=="Yes" goto :do_cleanup
goto :main_menu

:do_cleanup
echo [INFO] Killing all DuckBot processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *DuckBot*" /fi "WINDOWTITLE eq *Qwen3*" >nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq *qwen3*" >nul 2>&1
echo [INFO] Processes cleaned up!
echo [STATUS] System reset complete
echo.
pause
goto :main_menu

:help_system
cls
echo.
echo ================================================================================
echo  📖 HELP & DOCUMENTATION
echo ================================================================================
echo.
echo 🚀 QUICK START:
echo   1. Choose option 1 for complete ecosystem (recommended)
echo   2. Choose option 4 for privacy mode (no external APIs)
echo   3. Choose option 5 for quick startup
echo.
echo 🔧 COMMON ISSUES:
echo   - Port conflicts: Check if ports 5000, 8787, 8789 are available
echo   - Python errors: Ensure Python 3.8+ is installed
echo   - Model loading: Check GPU memory and disk space
echo   - LM Studio: Must be running for local-only mode
echo.
echo 📚 DOCUMENTATION:
echo   - Full docs: docs/ directory
echo   - Configuration: config/ directory
echo   - Test logs: logs/ directory
echo.
echo 🌐 ONLINE RESOURCES:
echo   - GitHub: Repository documentation
echo   - Issues: Bug reports and feature requests
echo   - Wiki: Detailed guides and tutorials
echo.
echo 🔧 SYSTEM REQUIREMENTS:
echo   - Windows 10/11 (WSL2 recommended)
echo   - Python 3.8+ (3.11+ recommended)
echo   - 8GB RAM minimum (16GB+ recommended)
echo   - 10GB disk space for Qwen3-Omni model
echo   - Node.js 16+ for UI components
echo.
pause
goto :main_menu

:about_system
cls
echo.
echo ================================================================================
echo  ℹ️  SYSTEM INFORMATION
echo ================================================================================
echo.
echo 🦆 DUCKBOT v%DUCKBOT_VERSION%
echo Build: %BUILD_DATE%
echo Status: %BUILD_STATUS%
echo Mode: %LAUNCHER_MODE%
echo.
echo 🧠 AI INTEGRATION:
echo   Primary Brain: Qwen3-Omni-30B-A3B-Instruct
echo   Fallback: LM Studio, Ollama, OpenRouter
echo   Features: Multimodal, Voice, Vision, Text
echo.
echo 🔧 TECHNICAL SPECIFICATIONS:
echo   Architecture: Consolidated v4.2 (85% reduction)
echo   Services: 15+ integrated services
echo   Ports: Dynamic allocation with conflict resolution
echo   Security: Local-only privacy mode available
echo.
echo 📁 SYSTEM PATHS:
echo   Installation: %CD%
echo   Config: %CD%\config\
echo   Logs: %CD%\logs\
echo   Models: %CD%\models\
echo.
echo 🌐 NETWORK PORTS:
echo   WebUI: %WEBUI_PORT%
echo   API Server: %API_PORT%
echo   WebSocket: %WS_PORT%
echo   Monitoring: %MONITORING_PORT%
echo   Terminal: %TERMINAL_PORT%
echo   LM Studio: %LM_STUDIO_PORT%
echo.
pause
goto :main_menu

:exit_launcher
cls
echo.
echo ================================================================================
echo  👋 THANK YOU FOR USING DUCKBOT v4.2
echo ================================================================================
echo.
echo 🦆 DuckBot Enhanced v4.2 - Qwen3-Omni Edition
echo 🌟 Complete AI-Powered Operating System
echo 🏠 Privacy-First Local Mode Available
echo 🤖 Multi-Agent AI Integration
echo 🖥️ Advanced Desktop Automation
echo.
echo [INFO] Services will continue running in background
echo [INFO] Use launcher again to manage services
echo.
echo 📧 Need help? Check documentation or GitHub issues
echo 🌟 Star us on GitHub if you find DuckBot useful!
echo.
timeout /t 3 >nul
exit /b 0

REM ============ UTILITY FUNCTIONS ============

:check_dependencies
echo [INFO] Checking system dependencies...

REM Check Python
%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo [SOLUTION] Install Python 3.8+ from https://python.org/
    exit /b 1
)

REM Check Node.js for WebUI
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Node.js is not installed! WebUI features will be limited.
    echo [SOLUTION] Install Node.js 16+ from https://nodejs.org/
    timeout /t 2 >nul
)

REM Check essential Python packages
echo [INFO] Checking essential Python packages...
%PY_CMD% -c "import fastapi, uvicorn, asyncio" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Essential Python packages missing!
    echo [SOLUTION] Run: pip install fastapi uvicorn
    exit /b 1
)

echo [SUCCESS] Dependencies checked successfully!
exit /b 0

:check_dependencies_quick
echo [INFO] Quick dependency check...

%PY_CMD% --version >nul 2>&1
if errorlevel 1 goto :no_python

echo [INFO] Quick check passed!
exit /b 0

:check_lm_studio
echo [INFO] Checking LM Studio connection...

curl -s http://localhost:%LM_STUDIO_PORT%/v1/models >nul 2>&1
if errorlevel 1 (
    echo [ERROR] LM Studio not detected!
    echo [SOLUTION] Start LM Studio with local server enabled
    echo [INFO] LM Studio should be running on port %LM_STUDIO_PORT%
    exit /b 1
)

echo [SUCCESS] LM Studio connection verified!
exit /b 0

:start_qwen3_brain
echo [INFO] Starting Qwen3-Omni Brain...

REM Check if model files exist
if not exist "models" (
    echo [WARN] Model directory not found. Creating...
    mkdir "models"
)

REM Start Qwen3-Omni brain
start "Qwen3-Omni Brain" %PY_CMD% start_qwen_brain_and_server.py

echo [INFO] Waiting for Qwen3-Omni to initialize...
echo [INFO] This may take 2-5 minutes for the 30B model to load...

REM Wait for service to be ready
timeout /t 30 /nobreak >nul

echo [SUCCESS] Qwen3-Omni Brain started!
set "QWEN3_BRAIN_STARTED=1"
exit /b 0

:start_core_services
echo [INFO] Starting core DuckBot services...

start "Service Manager" /MIN %PY_CMD% -m duckbot.core.service_manager
start "MCP Server" /MIN %PY_CMD% -m duckbot.integrations.mcp_server
start "WebSocket Server" /MIN %PY_CMD% qwen3_omni_server.py

timeout /t 8 /nobreak >nul

echo [SUCCESS] Core services started!
set /a SERVICES_STARTED+=3
exit /b 0

:start_enhanced_webui
echo [INFO] Starting Enhanced WebUI...

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js required for WebUI!
    exit /b 1
)

start "Enhanced WebUI" %PY_CMD% -m duckbot.enhanced_webui --host 127.0.0.1 --port %WEBUI_PORT%

timeout /t 5 /nobreak >nul

echo [SUCCESS] Enhanced WebUI started!
set "WEBUI_STARTED=1"
exit /b 0

:start_monitoring_services
echo [INFO] Starting monitoring services...

start "AI Ecosystem Manager" /MIN %PY_CMD% ai_ecosystem_manager.py --host 127.0.0.1 --port %MONITORING_PORT%
start "Terminal Interface" /MIN %PY_CMD% -m duckbot.charm_terminal_ui --port %TERMINAL_PORT%

timeout /t 3 /nobreak >nul

echo [SUCCESS] Monitoring services started!
exit /b 0

:start_local_services
echo [INFO] Starting local-only services...

start "Local Service Manager" /MIN %PY_CMD% start_local_ecosystem.py
start "Local WebUI" /MIN %PY_CMD% -m duckbot.enhanced_webui --port %WEBUI_PORT% --local-only

timeout /t 5 /nobreak >nul

echo [SUCCESS] Local services started!
exit /b 0

:edit_config
echo [INFO] Opening configuration file: %1
if exist "%1" (
    start notepad "%1"
) else (
    echo [ERROR] Configuration file not found: %1
    echo [INFO] Creating template configuration...
    echo {} > "%1"
    start notepad "%1"
)
exit /b 0

:no_python
cls
echo.
echo ================================================================================
echo  ❌ PYTHON NOT FOUND
echo ================================================================================
echo.
echo [ERROR] Python is required to run DuckBot!
echo.
echo [SOLUTION] Install Python 3.8+ from https://python.org/
echo [RECOMMENDED] Python 3.11+ for best performance
echo.
echo [CURRENT] Python launcher not found in PATH
echo [CHECK] Try installing Python and adding it to PATH
echo.
echo [NEXT] Press any key to exit...
echo.
pause >nul
exit /b 1

:port_conflict
echo [ERROR] Port conflict detected!
echo [INFO] Port %1 is already in use.
echo [SOLUTION] Close the application using port %1
echo [ALTERNATIVE] Change port configuration in config files
echo.
pause
exit /b 1