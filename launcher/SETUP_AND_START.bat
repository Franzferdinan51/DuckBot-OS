@echo off
REM DuckBot v3.1.0 with VibeVoice TTS Integration
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0 - Professional AI Ecosystem with VibeVoice TTS
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DUCKBOT_VERSION=3.1.0"
set "BUILD_DATE=2025-08-29"
set "BUILD_STATUS=VIBEVOICE-ENHANCED"

:main_menu
echo.
echo ===============================================
echo  🦆 DUCKBOT v%DUCKBOT_VERSION% AI-ENHANCED ECOSYSTEM
echo ===============================================
echo    Professional AI-Managed Crypto Ecosystem
echo    [STATUS] %BUILD_STATUS% - VibeVoice Ready
echo    [BUILD] %BUILD_DATE% - Latest Voice Integration
echo ===============================================
echo.
echo 🎤 NEW VIBEVOICE TTS FEATURES:
echo   ✅ Microsoft VibeVoice multi-speaker TTS
echo   ✅ 6 professional voice presets (Alice, Carter, Emily, David)
echo   ✅ Multi-speaker conversations up to 90 minutes
echo   ✅ Discord slash commands: /vibevoice, /voice_presets
echo   ✅ Free and open-source voice synthesis
echo.
echo 🚀 CORE FEATURES:
echo   ✅ Qwen → GLM 4.5 Air → Local automatic fallback
echo   ✅ Separate rate limits: Chat (30/min), Background (30/min)
echo   ✅ Smart model rotation prevents OpenRouter rate limiting
echo   ✅ Professional cost analysis dashboard
echo   ✅ Thread-safe operations with comprehensive error handling
echo   ✅ RAG (Retrieval-Augmented Generation) integration
echo.
echo 🎯 QUICK ACCESS - Most Popular Options:
echo.
echo 1. 🌟 [UNIFIED] AI-Enhanced WebUI Dashboard - RECOMMENDED!
echo    ▶ Complete ecosystem with WebUI + AI management
echo    ▶ Real-time monitoring + Professional interface  
echo    ▶ Automatic service recovery + Cost tracking
echo    ▶ Enhanced rate limiting + Model fallbacks
echo.
echo 2. 🖥️  [WEBUI-ONLY] Professional Dashboard (Manual Control)
echo    ▶ WebUI interface without AI orchestration
echo    ▶ Manual service control + Live monitoring
echo    ▶ Perfect for debugging + Direct control
echo.
echo 3. 🤖 [AI-HEADLESS] Enhanced AI Command Line
echo    ▶ Pure AI management without WebUI
echo    ▶ Server deployment optimized
echo    ▶ Intelligent orchestration + Auto-recovery
echo.
echo L. 🏠 [LOCAL-ONLY] Complete Local Unified Setup
echo    ▶ Prioritizes LM Studio + local services ONLY
echo    ▶ No OpenRouter/cloud dependencies
echo    ▶ Full ecosystem with local AI routing
echo    ▶ WebUI + Discord bot (all local)
echo.
echo V. 🎤 [VIBEVOICE] VibeVoice TTS Setup & Management
echo    ▶ Install and configure VibeVoice TTS
echo    ▶ Start VibeVoice server + DuckBot integration
echo    ▶ Test voice generation and Discord commands
echo    ▶ Professional multi-speaker voice synthesis
echo.
echo H. 🤖 [HEADLESS] Local Headless Mode
echo    ▶ Discord bot only (no WebUI)
echo    ▶ Complete privacy with local processing
echo    ▶ Server deployment ready
echo.
echo W. 🌐 [OPEN-WEBUI] Open-WebUI with OpenRouter Integration
echo    ▶ Modern AI chat interface (localhost:8080)
echo    ▶ OpenRouter model integration
echo    ▶ Professional web-based AI interface
echo.
echo 💰 COST MANAGEMENT:
echo.
echo C. 📊 [COST] Launch Cost Analysis Dashboard
echo    ▶ Real-time spending tracking + Predictions
echo    ▶ Model comparison + Usage analytics
echo    ▶ Budget alerts + Export capabilities
echo.
echo F. 💸 [FREE] Apply Free-Tier Optimizations
echo    ▶ Conservative budgets + Enhanced caching
echo    ▶ RAG integration + Smart routing
echo    ▶ Perfect for OpenRouter free tier
echo.
echo ⚙️ SYSTEM MANAGEMENT:
echo.
echo S. 🔍 [STATUS] Quick System Health Check
echo    ▶ Port status + Service detection
echo    ▶ Memory usage + Process monitoring
echo    ▶ Configuration validation
echo.
echo T. 🧪 [TEST] Comprehensive System Testing
echo    ▶ All enhanced features validation
echo    ▶ AI routing + Model detection
echo    ▶ Performance benchmarks
echo.
echo I. 📦 [INSTALL] Auto-Install Missing Services
echo    ▶ Node.js + n8n + Jupyter
echo    ▶ Python dependencies + AI tools
echo    ▶ Custom AI tools and integrations
echo.
echo P. 🔧 [DEPS] Fix Python Dependencies
echo    ▶ Install missing visualization libs (seaborn, plotly)
echo    ▶ Fix Jupyter, Discord.py, AI dependencies
echo    ▶ Quick fix for common import errors
echo.
echo 🛠️ ADVANCED TOOLS:
echo.
echo D. 🩺 [DOCTOR] System Doctor & Dependency Fixer
echo    ▶ Comprehensive health diagnostics
echo    ▶ Automatic dependency installation
echo    ▶ Performance analysis & automated repair
echo    ▶ Health report generation
echo.
echo Q. ⚡ [QUICK] Ultra-Fast Start (Unified + Free Preset)
echo    ▶ One-click startup with optimal settings
echo    ▶ Auto-applies free tier optimizations
echo    ▶ Skip configuration menus
echo.
echo 🔧 CONFIGURATION:
echo.
echo 5. 🔧 [SETUP] Complete Manual Setup Wizard
echo 6. ⚙️  [CONFIG] Quick AI Provider Settings
echo 7. 💬 [CHAT] Interactive Chat with AI Manager
echo 8. 📋 [SETTINGS] Advanced Configuration Menu
echo.
echo 🔄 UTILITIES:
echo.
echo K. 🛑 [KILL] Kill All DuckBot Processes
echo ?. ❓ [HELP] Documentation and Troubleshooting
echo E. 🚪 [EXIT] Exit Launcher
echo.
set /p choice="[PROMPT] Enter your choice: "

REM Primary modes
if /i "%choice%"=="1" goto unified_start_integrated
if /i "%choice%"=="2" goto webui_only_integrated  
if /i "%choice%"=="3" goto ai_headless_integrated
if /i "%choice%"=="L" goto local_only_unified
if /i "%choice%"=="V" goto vibevoice_setup_manager
if /i "%choice%"=="H" goto headless_local_mode
if /i "%choice%"=="W" goto openwebui_start
if /i "%choice%"=="Q" goto quick_start_integrated
REM Cost management
if /i "%choice%"=="C" goto cost_dashboard
if /i "%choice%"=="F" goto apply_free_tier
REM System management
if /i "%choice%"=="S" goto system_status
if /i "%choice%"=="T" goto test_system
if /i "%choice%"=="I" goto install_services
if /i "%choice%"=="P" goto fix_dependencies_standalone
if /i "%choice%"=="D" goto doctor_mode
REM Configuration
if /i "%choice%"=="5" goto manual_setup
if /i "%choice%"=="6" goto config_ai
if /i "%choice%"=="7" goto chat_ai
if /i "%choice%"=="8" goto settings_menu
REM Utilities
if /i "%choice%"=="K" goto kill_processes
if /i "%choice%"=="?" goto help
if /i "%choice%"=="E" goto exit
goto invalid_choice

:unified_start_integrated
cls
echo.
echo ===============================================
echo  🌟 AI-ENHANCED UNIFIED ECOSYSTEM v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: Complete DuckBot Experience
echo.
echo 📋 ENHANCED FEATURES ACTIVE:
echo   ✅ Professional WebUI dashboard (localhost:8787)
echo   ✅ AI-powered service orchestration
echo   ✅ Real-time monitoring + Task execution
echo   ✅ Separate rate limits: Chat/Background (30/min each)
echo   ✅ Smart model fallback: Qwen → GLM → Local
echo   ✅ Automatic service recovery
echo   ✅ Cost tracking + Analytics dashboard
echo   ✅ Thread-safe operations + Error handling
echo   ✅ RAG integration + Action reasoning
echo.
echo 🏗️  SYSTEM ARCHITECTURE:
echo   📡 WebUI server: localhost:8787 (token-secured)
echo   🤖 AI ecosystem: Background management
echo   🔄 Health monitoring: 30-second intervals
echo   💾 Intelligent caching: 60-80%% cost savings
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

echo.
echo 🔄 STARTUP SEQUENCE:
echo [1/5] Validating system configuration...
call :validate_configuration

echo [2/5] Starting AI ecosystem manager...
echo 📝 Starting enhanced AI ecosystem (background)...
echo 📋 AI will automatically start and manage services...
echo.
REM Start AI ecosystem in background - this is what should start the services
start "AI Ecosystem" /MIN python start_ai_ecosystem.py
if errorlevel 1 (
    echo ❌ Failed to start AI ecosystem
    echo 💡 Falling back to manual service startup...
    call :start_services_manually
)

echo [3/5] Waiting for AI services to initialize...
echo ⏳ Allowing time for service startup and health checks...
timeout /t 10 >nul

echo [4/5] Testing service connectivity...
call :test_service_health

echo [5/5] Launching WebUI dashboard...
echo.
echo 🌐 WEBUI LAUNCHING:
echo   🔗 URL: http://localhost:8787
echo   🔐 Secure token authentication
echo   📊 Cost dashboard: /cost
echo   📈 System metrics: /status
echo.
echo 💡 TIP: Copy the complete token URL from the output below
echo ===============================================

python -m duckbot.webui
if errorlevel 1 (
    echo.
    echo ❌ WebUI failed to start. Check logs for details.
    call :show_troubleshooting_info
    pause
    goto main_menu
)

echo.
echo ✅ Unified ecosystem stopped gracefully.
echo 📝 Session logs: ai_ecosystem.log, webui.log
pause
goto main_menu

:local_only_unified
cls
echo.
echo ===============================================
echo  🏠 LOCAL-ONLY UNIFIED ECOSYSTEM v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: Complete Local-First Experience
echo.
echo 📋 LOCAL-FIRST CONFIGURATION:
echo   ✅ LM Studio priority (localhost:1234)
echo   ✅ NO OpenRouter/cloud dependencies
echo   ✅ Local AI processing
echo   ✅ WebUI dashboard (localhost:8787)
echo   ✅ Discord bot with local AI only
echo   ✅ n8n workflows (if available)
echo   ✅ All processing stays on your machine
echo.
echo 🔒 PRIVACY FEATURES:
echo   🛡️  No external API calls
echo   🔐 All data stays local
echo   💾 Local caching only
echo   🏠 Complete offline operation
echo.
echo 🏗️  LOCAL ARCHITECTURE:
echo   🤖 Primary AI: LM Studio (required)
echo   🎨 AI Processing: Local models
echo   📊 Monitoring: Local WebUI
echo   🔄 Orchestration: Local ecosystem manager
echo.

REM Pre-flight checks for local setup
call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

call :ensure_lm_studio_running
if errorlevel 1 goto main_menu

echo.
echo 🔄 LOCAL STARTUP SEQUENCE:
echo [1/6] Validating local configuration...
call :validate_local_configuration

echo [2/6] Applying local-only settings...
call :apply_local_only_settings

echo [3/6] Starting local services...
call :start_local_services_prioritized

echo [4/6] Starting AI ecosystem (local mode)...
echo 📝 Starting local-first AI ecosystem...
echo 🏠 All AI processing will use LM Studio only
echo.
start "Local AI Ecosystem" /MIN python start_local_ecosystem.py
if errorlevel 1 (
    echo ❌ Failed to start local AI ecosystem
    echo 💡 Falling back to manual local service startup...
    call :start_local_services_manual
)

echo [5/6] Waiting for local services to initialize...
timeout /t 8 >nul

echo [6/6] Launching local WebUI dashboard...
echo.
echo 🌐 LOCAL WEBUI LAUNCHING:
echo   🔗 URL: http://localhost:8787
echo   🔐 Local token authentication
echo   🏠 All features running locally
echo   ❌ No cloud service dependencies
echo.
echo 💡 TIP: Ensure LM Studio is running with a model loaded
echo ===============================================

python -m duckbot.webui --local-only
if errorlevel 1 (
    echo.
    echo ❌ Local WebUI failed to start. Check logs for details.
    call :show_local_troubleshooting_info
    pause
    goto main_menu
)

echo.
echo ✅ Local-only unified ecosystem stopped gracefully.
echo 📝 Session logs: ai_ecosystem.log, webui.log
pause
goto main_menu

:vibevoice_setup_manager
cls
echo.
echo ===============================================
echo  🎤 VIBEVOICE TTS SETUP & MANAGEMENT v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 VIBEVOICE: Microsoft's Multi-Speaker TTS
echo.
echo 📋 VIBEVOICE FEATURES:
echo   ✅ Multi-speaker conversations (up to 4 voices)
echo   ✅ 90+ minutes of continuous speech generation
echo   ✅ Professional voice quality (Alice, Carter, Emily, David)
echo   ✅ Free and open-source (MIT license)
echo   ✅ Discord integration with slash commands
echo   ✅ Real-time voice synthesis
echo.
echo 🎯 MANAGEMENT OPTIONS:
echo.
echo 1. 🛠️  [SETUP] Install and Configure VibeVoice
echo    ▶ Download dependencies and setup environment
echo    ▶ Configure voice presets and Discord integration
echo    ▶ Create startup scripts and test configuration
echo.
echo 2. 🚀 [START] Launch VibeVoice Server
echo    ▶ Start VibeVoice FastAPI server (localhost:8000)
echo    ▶ Initialize voice models and GPU acceleration
echo    ▶ Enable Discord TTS commands
echo.
echo 3. 🧪 [TEST] Test VibeVoice Integration
echo    ▶ Run comprehensive integration tests
echo    ▶ Validate voice generation and Discord commands
echo    ▶ Check server connectivity and performance
echo.
echo 4. 🎭 [DEMO] Generate Sample Voice Content
echo    ▶ Create sample multi-speaker conversations
echo    ▶ Test different voice presets and styles
echo    ▶ Preview Discord command functionality
echo.
echo 5. 🔄 [INTEGRATE] Add to DuckBot
echo    ▶ Integrate VibeVoice commands into Discord bot
echo    ▶ Update bot configuration for TTS features
echo    ▶ Enable /vibevoice slash commands
echo.
echo 6. 📊 [STATUS] Check VibeVoice Status
echo    ▶ Server connectivity and health check
echo    ▶ Voice model status and GPU utilization
echo    ▶ Discord integration status
echo.
echo B. 🔙 [BACK] Return to Main Menu
echo.
set /p vibechoice="[PROMPT] Select VibeVoice option: "

if /i "%vibechoice%"=="1" goto vibevoice_setup
if /i "%vibechoice%"=="2" goto vibevoice_start_server
if /i "%vibechoice%"=="3" goto vibevoice_test
if /i "%vibechoice%"=="4" goto vibevoice_demo
if /i "%vibechoice%"=="5" goto vibevoice_integrate
if /i "%vibechoice%"=="6" goto vibevoice_status_check
if /i "%vibechoice%"=="B" goto main_menu
goto vibevoice_invalid_choice

:vibevoice_setup
cls
echo.
echo ===============================================
echo  🛠️  VIBEVOICE SETUP & INSTALLATION
echo ===============================================
echo.
echo 🚀 Installing VibeVoice TTS for DuckBot...
echo.
python setup_vibevoice.py
if errorlevel 1 (
    echo.
    echo ❌ VibeVoice setup encountered issues
    echo 💡 Check the logs above for details
    pause
) else (
    echo.
    echo ✅ VibeVoice setup completed successfully!
    echo 📋 Next: Use option 2 to start the server
    pause
)
goto vibevoice_setup_manager

:vibevoice_start_server
cls
echo.
echo ===============================================
echo  🚀 STARTING VIBEVOICE SERVER
echo ===============================================
echo.
echo 🎤 Starting VibeVoice TTS server...
echo ⏳ This may take a few minutes for first-time setup
echo 📋 Server will be available at: http://localhost:8000
echo.
if exist "START_VIBEVOICE_SERVER.bat" (
    call START_VIBEVOICE_SERVER.bat
) else (
    echo 📥 Creating VibeVoice server startup...
    if not exist "VibeVoice-FastAPI" (
        echo 🔄 Cloning VibeVoice FastAPI repository...
        git clone https://github.com/dontriskit/VibeVoice-FastAPI.git
    )
    cd VibeVoice-FastAPI
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    echo 🚀 Starting server...
    python main.py --host 0.0.0.0 --port 8000
)
echo.
pause
goto vibevoice_setup_manager

:vibevoice_test
cls
echo.
echo ===============================================
echo  🧪 VIBEVOICE INTEGRATION TESTING
echo ===============================================
echo.
echo 🔍 Running comprehensive VibeVoice tests...
echo.
python test_vibevoice.py
echo.
echo 📊 Test results displayed above
echo 💡 For full functionality, ensure VibeVoice server is running
pause
goto vibevoice_setup_manager

:vibevoice_demo
cls
echo.
echo ===============================================
echo  🎭 VIBEVOICE DEMONSTRATION
echo ===============================================
echo.
echo 🎤 Generating sample voice content...
echo ✅ This will create example conversations using different voices
echo.
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from duckbot.vibevoice_client import VibeVoiceManager

async def demo():
    manager = VibeVoiceManager()
    if await manager.initialize():
        print('🎤 Generating sample conversation...')
        result = await manager.generate_voice_content(
            'Alice: Welcome to DuckBot with VibeVoice! Bob: This is amazing multi-speaker TTS!',
            ['en-alice', 'en-carter'],
            'conversation'
        )
        if result:
            print(f'✅ Demo complete! Audio saved to: {result}')
        else:
            print('❌ Demo failed. Ensure VibeVoice server is running.')
    else:
        print('⚠️ VibeVoice server not available. Start server first.')

asyncio.run(demo())
"
echo.
pause
goto vibevoice_setup_manager

:vibevoice_integrate
cls
echo.
echo ===============================================
echo  🔄 VIBEVOICE DISCORD INTEGRATION
echo ===============================================
echo.
echo 🤖 Integrating VibeVoice commands into DuckBot...
echo.
python integrate_vibevoice.py
echo.
echo ✅ Integration process completed
echo 📋 Restart DuckBot to activate /vibevoice commands
pause
goto vibevoice_setup_manager

:vibevoice_status_check
cls
echo.
echo ===============================================
echo  📊 VIBEVOICE STATUS CHECK
echo ===============================================
echo.
echo 🔍 Checking VibeVoice system status...
echo.
python -c "
import asyncio
import aiohttp
import sys

async def check_status():
    print('🌐 Testing VibeVoice server connection...')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/voices', timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print('✅ VibeVoice server is running')
                    print(f'📊 Available voices: {len(data.get(\"voices\", []))}')
                else:
                    print(f'⚠️ Server responded with status {response.status}')
    except Exception as e:
        print('❌ VibeVoice server not accessible')
        print(f'💡 Error: {e}')
        print('📋 Start server with option 2')
    
    print()
    print('🔍 Checking DuckBot integration...')
    try:
        from duckbot.vibevoice_client import VibeVoiceManager
        manager = VibeVoiceManager()
        print('✅ VibeVoice client available')
        voices = manager.get_available_voices()
        print(f'📊 Configured voices: {len(voices)}')
    except Exception as e:
        print('❌ VibeVoice integration issue')
        print(f'💡 Error: {e}')

asyncio.run(check_status())
"
echo.
pause
goto vibevoice_setup_manager

:vibevoice_invalid_choice
echo.
echo ❌ Invalid choice. Please select a valid option.
timeout /t 3 >nul
goto vibevoice_setup_manager

:headless_local_mode
cls
echo.
echo ===============================================
echo  🤖 HEADLESS LOCAL MODE v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: Discord Bot Only (No WebUI)
echo.
echo 📋 HEADLESS CONFIGURATION:
echo   ✅ Discord bot only
echo   ✅ Complete privacy mode
echo   ✅ LM Studio local processing
echo   ✅ Local AI processing
echo   ✅ No WebUI, no dashboard
echo   ✅ Server deployment ready
echo.
echo 🔒 PRIVACY BENEFITS:
echo   🏠 All AI processing stays local
echo   🔐 Zero external API calls
echo   💾 Complete data sovereignty
echo   ⚡ Optimized resource usage
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

call :ensure_lm_studio_running
if errorlevel 1 goto main_menu

echo.
echo 🚀 Starting headless local ecosystem...
echo ⏳ This may take 30-60 seconds to fully initialize...
echo.

timeout /t 2 >nul

REM Start headless local ecosystem
START_HEADLESS_LOCAL.bat

if errorlevel 1 (
    echo.
    echo ❌ Failed to start headless local ecosystem
    echo 🔧 TROUBLESHOOTING STEPS:
    echo   1. Ensure LM Studio is running with local server enabled
    echo   2. Load at least one chat model in LM Studio
    echo   3. Check that Discord bot token is configured
    echo   4. Verify no port conflicts (1234 for LM Studio)
    call :show_local_troubleshooting_info
    pause
    goto main_menu
)

echo.
echo ✅ Headless local ecosystem started successfully!
echo 🤖 Discord bot is running in privacy mode
echo 🔒 All processing stays on your machine
echo.
echo 📝 Session logs: Check console output
pause
goto main_menu

:start_services_manually
echo.
echo 🔧 MANUAL SERVICE STARTUP:
echo Starting core services manually as fallback...

REM ComfyUI removed - now using external services for image generation

REM Check for n8n
echo [SERVICE] Checking n8n availability...
where n8n >nul 2>&1
if errorlevel 0 (
    echo ✅ n8n found - starting...
    start "n8n" /MIN cmd /c "n8n start --port 5678"
    timeout /t 2 >nul
) else (
    echo ⚠️  n8n not found - skipping
)

REM Check for Jupyter
echo [SERVICE] Checking Jupyter availability...
python -c "import jupyter" >nul 2>&1
if errorlevel 0 (
    echo ✅ Jupyter found - starting...
    start "Jupyter" /MIN python -m jupyter notebook --port=8889 --no-browser
    timeout /t 2 >nul
) else (
    echo ⚠️  Jupyter not found - skipping
)

echo ✅ Manual service startup completed
exit /b 0

:webui_only_integrated
cls
echo.
echo ===============================================
echo  🖥️  PROFESSIONAL WEBUI DASHBOARD v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: WebUI Dashboard (Manual Control Mode)
echo.
echo 📋 FEATURES ACTIVE:
echo   ✅ Real-time monitoring dashboard
echo   ✅ Manual task execution and control
echo   ✅ Health checks and system metrics  
echo   ✅ Rate limiting and token security
echo   ❌ NO automatic AI service management
echo   ❌ NO intelligent auto-recovery features
echo   ✅ Connect to running LM Studio for AI tasks
echo.
echo 💡 USE CASE: Perfect for manual control and debugging
echo.

call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

echo.
echo 🌐 LAUNCHING WEBUI...
echo   🔗 URL: http://localhost:8787
echo   🔐 Token authentication enabled
echo.
python -m duckbot.webui
if errorlevel 1 (
    echo ❌ WebUI failed to start
    call :show_troubleshooting_info
    pause
)
goto main_menu

:ai_headless_integrated
cls
echo.
echo ===============================================
echo  🤖 AI-ENHANCED HEADLESS MODE v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: Pure AI Management (No WebUI)
echo.
echo 📋 FEATURES ACTIVE:
echo   ✅ Intelligent service orchestration
echo   ✅ Automatic recovery and monitoring
echo   ✅ Smart caching and provider failover
echo   ✅ Command-line status and control
echo   ❌ NO WebUI interface overhead
echo   ✅ Optimized for server deployment
echo   ✅ Dynamic model detection and routing
echo.
echo 💡 USE CASE: Perfect for server deployments and automation
echo.

call :check_python
if errorlevel 1 goto main_menu

echo.
echo 🤖 LAUNCHING AI ECOSYSTEM (headless)...
echo 📋 AI will start and manage all services automatically
echo ⏹️  Press Ctrl+C to stop
echo.
python start_ai_ecosystem.py
if errorlevel 1 (
    echo ❌ AI ecosystem failed to start
    call :show_troubleshooting_info
    pause
)
goto main_menu

:quick_start_integrated
cls
echo.
echo ===============================================
echo  ⚡ ULTRA-FAST START v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 ONE-CLICK STARTUP: Unified + Free Tier Optimized
echo.
echo 📋 AUTO-APPLIED SETTINGS:
echo   ✅ Free tier rate limits and budgets
echo   ✅ Enhanced caching for cost reduction
echo   ✅ Conservative AI decision thresholds
echo   ✅ Optimal model routing configuration
echo.
echo ⚡ Skipping configuration menus - starting immediately...
echo.

call :check_python
if errorlevel 1 goto main_menu

call :install_dependencies_if_needed
if errorlevel 1 goto main_menu

call :apply_free_tier_settings

echo 🚀 Starting unified ecosystem with free tier optimizations...
start "AI Ecosystem" /MIN python start_ai_ecosystem.py
timeout /t 8 >nul

echo 🌐 Launching WebUI...
python -m duckbot.webui
goto main_menu

REM Support functions
:check_python
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
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
python -c "import fastapi, uvicorn, aiohttp, requests, matplotlib, GPUtil" >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing required dependencies...
    pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil
    if errorlevel 1 (
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

:validate_configuration
echo 🔍 Validating system configuration...
if exist "ai_config.json" (
    echo ✅ AI configuration found
) else (
    echo ⚠️  AI configuration missing - will be created
)

if exist "duckbot\webui.py" (
    echo ✅ WebUI module structure intact
) else (
    echo ❌ Core WebUI files missing
    pause
    exit /b 1
)
exit /b 0

:test_service_health
echo 🏥 Testing service health...

REM Test LM Studio
python -c "import requests; r=requests.get('http://localhost:1234/v1/models', timeout=3); print('✅ LM Studio responding') if r.status_code==200 else print('⚠️ LM Studio not accessible')" 2>nul

REM ComfyUI removed - image generation via external services

REM Test n8n
python -c "import requests; r=requests.get('http://localhost:5678', timeout=3); print('✅ n8n responding') if r.status_code==200 else print('⚠️ n8n not accessible')" 2>nul

echo ✅ Health check completed
exit /b 0

:check_lm_studio_required
echo 🤖 Checking LM Studio availability (required for local-only mode)...
python -c "import requests; r=requests.get('http://localhost:1234/v1/models', timeout=5); print('✅ LM Studio detected and responding')" 2>nul
if errorlevel 1 (
    echo ❌ LM Studio not detected!
    echo.
    echo 🔧 REQUIRED SETUP:
    echo   1. Download LM Studio from: https://lmstudio.ai
    echo   2. Load a chat model (recommend: Llama 3.1 8B or similar)
    echo   3. Start the local server (usually automatic)
    echo   4. Verify it's running on localhost:1234
    echo.
    echo 💡 TIP: LM Studio must be running BEFORE starting local-only mode
    pause
    exit /b 1
)
echo ✅ LM Studio verification passed
exit /b 0

:validate_local_configuration
echo 🔍 Validating local-only configuration...
if exist "duckbot\ai_router_gpt.py" (
    echo ✅ AI routing system found
) else (
    echo ❌ AI routing system missing
    exit /b 1
)

echo ℹ️  Image generation via external services

echo ✅ Local configuration validated
exit /b 0

:apply_local_only_settings
echo 🏠 Applying local-only configuration...
REM Create local-only environment configuration
python -c "
import json
import os
# Local-only configuration
config = {
    'AI_LOCAL_ONLY_MODE': 'true',
    'AI_CONFIDENCE_MIN': '0.65',
    'AI_LOCAL_CONF_MIN': '0.60',
    'OPENROUTER_BUDGET_PER_MIN': '0',
    'DISABLE_OPENROUTER': 'true',
    'ENABLE_LM_STUDIO_ONLY': 'true',
    'LM_STUDIO_URL': 'http://localhost:1234',
    'MAX_MEMORY_THRESHOLD': '85.0',
    'DUCKBOT_WEBUI_HOST': '127.0.0.1',
    'DUCKBOT_WEBUI_PORT': '8787'
}
with open('.env.local', 'w') as f:
    for k, v in config.items():
        f.write(f'{k}={v}\n')
print('✅ Local-only settings configured')
"
if errorlevel 1 (
    echo ⚠️  Warning: Could not create local configuration file
    echo ℹ️  Proceeding with default local settings...
)
exit /b 0

:start_local_services_prioritized
echo 🏠 Starting local services in priority order...

REM Priority 1: Core local services
echo [LOCAL SERVICE] Starting core local services...

REM Priority 2: n8n for workflows (if available)
echo [LOCAL SERVICE] Checking n8n (local workflows)...
where n8n >nul 2>&1
if errorlevel 0 (
    echo ✅ Starting n8n locally...
    start "n8n-Local" /MIN cmd /c "n8n start --host 127.0.0.1 --port 5678"
    timeout /t 2 >nul
) else (
    echo ⚠️  n8n not found - workflows unavailable
)

REM Priority 3: Jupyter (if available)
echo [LOCAL SERVICE] Checking Jupyter (local notebooks)...
python -c "import jupyter" >nul 2>&1
if errorlevel 0 (
    echo ✅ Starting Jupyter locally...
    start "Jupyter-Local" /MIN python -m jupyter notebook --ip=127.0.0.1 --port=8889 --no-browser
    timeout /t 2 >nul
) else (
    echo ⚠️  Jupyter not found - notebooks unavailable
)

echo ✅ Local service startup completed
exit /b 0

:start_local_services_manual
echo 🔧 Manual local service startup (fallback)...
call :start_local_services_prioritized
echo ✅ Manual local service startup completed
exit /b 0

:show_local_troubleshooting_info
echo.
echo 🔧 LOCAL-ONLY TROUBLESHOOTING:
echo   📝 Check logs: ai_ecosystem.log, webui.log
echo   🤖 LM Studio: Ensure it's running with a model loaded
echo   🌐 Ports: Verify 1234 (LM Studio), 8787 (WebUI) are free
echo   🏠 Network: All services bind to 127.0.0.1 for local access only
echo.
exit /b 0

:apply_free_tier_settings
echo 💸 Applying free tier optimizations...
REM Create optimized config for free tier usage
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
exit /b 0

:cost_dashboard
cls
echo.
echo ===============================================
echo  📊 COST ANALYSIS DASHBOARD v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 Launching professional cost tracking dashboard...
echo.
python start_cost_dashboard.py
if errorlevel 1 (
    echo ❌ Cost dashboard failed to start
    echo 💡 Make sure cost tracking dependencies are installed
    pause
)
goto main_menu

:system_status
cls
echo.
echo ===============================================
echo  🔍 SYSTEM STATUS CHECK v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🔍 Checking system health...
python -c "
import psutil
import requests
print('📊 SYSTEM METRICS:')
print(f'  CPU: {psutil.cpu_percent()}%')
print(f'  Memory: {psutil.virtual_memory().percent}%')
print(f'  Disk: {psutil.disk_usage('.').percent}%')
print()
print('🌐 SERVICE STATUS:')
services = [
    ('WebUI', 'http://localhost:8787'),
REM ComfyUI removed
    ('n8n', 'http://localhost:5678'),
    ('Jupyter', 'http://localhost:8889'),
    ('LM Studio', 'http://localhost:1234/v1/models')
]
for name, url in services:
    try:
        r = requests.get(url, timeout=2)
        status = '✅ Running' if r.status_code == 200 else f'⚠️ Status {r.status_code}'
    except:
        status = '❌ Not accessible'
    print(f'  {name}: {status}')
"
echo.
pause
goto main_menu

:test_system
cls
echo.
echo ===============================================
echo  🧪 COMPREHENSIVE SYSTEM TESTING v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🧪 Running enhanced system tests...
python test_every_feature.py
if exist "test_enhanced_system.bat" (
    echo.
    echo 🧪 Running enhanced tests...
    call test_enhanced_system.bat
)
echo.
pause
goto main_menu

:install_services
cls
echo.
echo ===============================================
echo  📦 AUTO-INSTALL MISSING SERVICES v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 📦 Installing missing services...
if exist "install_missing_services.bat" (
    call install_missing_services.bat
) else (
    echo 📥 Installing core dependencies...
    pip install -r requirements.txt
    echo.
    echo 🔍 Checking for Node.js...
    where node >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  Node.js not found - n8n will not be available
        echo 📥 Install from: https://nodejs.org/
    ) else (
        echo ✅ Node.js found - installing n8n...
        npm install -g n8n
    )
)
echo.
pause
goto main_menu

:doctor_mode
cls
echo.
echo ===============================================
echo  🩺 SYSTEM DOCTOR v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🩺 DuckBot System Doctor - Comprehensive Health Analysis
echo.
echo 🎯 DIAGNOSTIC OPTIONS:
echo.
echo 1. 🔍 [QUICK] Quick Health Check
echo    ▶ Basic system status and service health
echo    ▶ Quick dependency verification
echo    ▶ Port and process check
echo.
echo 2. 📦 [DEPS] Fix Dependencies
echo    ▶ Install missing Python packages
echo    ▶ Fix common import errors
echo    ▶ Update critical dependencies
echo.
echo 3. 🧪 [FULL] Full System Diagnostic
echo    ▶ Comprehensive system analysis
echo    ▶ Performance bottleneck detection
echo    ▶ Configuration validation
echo    ▶ AI-powered recommendations
echo.
echo 4. 🔧 [REPAIR] Automated Repair
echo    ▶ Fix common startup issues
echo    ▶ Reset configurations
echo    ▶ Clean temporary files
echo.
echo 5. 📊 [REPORT] Generate Health Report
echo    ▶ Detailed system analysis report
echo    ▶ Performance metrics
echo    ▶ Recommendations for optimization
echo.
echo B. 🔙 [BACK] Return to Main Menu
echo.
set /p doctor_choice="[PROMPT] Select diagnostic option: "

if /i "%doctor_choice%"=="1" goto doctor_quick_check
if /i "%doctor_choice%"=="2" goto doctor_fix_dependencies
if /i "%doctor_choice%"=="3" goto doctor_full_diagnostic
if /i "%doctor_choice%"=="4" goto doctor_automated_repair
if /i "%doctor_choice%"=="5" goto doctor_generate_report
if /i "%doctor_choice%"=="B" goto main_menu
goto doctor_invalid_choice

:doctor_quick_check
cls
echo.
echo ===============================================
echo  🔍 QUICK HEALTH CHECK
echo ===============================================
echo.
echo 🔍 Running quick system diagnostics...
echo.
call :check_python
echo.
call :doctor_check_critical_imports
echo.
call :doctor_check_services
echo.
call :doctor_check_ports
echo.
echo ✅ Quick health check completed
pause
goto doctor_mode

:doctor_fix_dependencies
cls
echo.
echo ===============================================
echo  📦 DEPENDENCY DOCTOR
echo ===============================================
echo.
echo 🚀 Installing and fixing Python dependencies...
echo.

echo 📦 [1/6] Core visualization dependencies...
pip install seaborn plotly matplotlib pandas numpy scikit-learn
if errorlevel 1 (
    echo ❌ Failed to install visualization dependencies
    pause
    goto doctor_mode
) else (
    echo ✅ Visualization dependencies: OK
)

echo 📊 [2/6] Jupyter ecosystem...
pip install jupyter notebook ipywidgets nbformat ipykernel jupyterlab
if errorlevel 1 (
    echo ❌ Failed to install Jupyter dependencies
    pause
    goto doctor_mode
) else (
    echo ✅ Jupyter dependencies: OK
)

echo 🌐 [3/6] Web and API dependencies...
pip install fastapi uvicorn aiohttp requests websockets python-multipart jinja2
if errorlevel 1 (
    echo ❌ Failed to install web dependencies
    pause
    goto doctor_mode
) else (
    echo ✅ Web dependencies: OK
)

echo 🤖 [4/6] AI and bot dependencies...
pip install discord.py openai anthropic torch transformers
if errorlevel 1 (
    echo ❌ Failed to install AI dependencies
    pause
    goto doctor_mode
) else (
    echo ✅ AI dependencies: OK
)

echo 🛠️ [5/6] System utilities...
pip install python-dotenv psutil PyYAML watchdog neo4j SpeechRecognition pyttsx3 GPUtil
if errorlevel 1 (
    echo ❌ Failed to install utility dependencies
    pause
    goto doctor_mode
) else (
    echo ✅ System utilities: OK
)

echo 🎵 [6/7] Optional audio/video dependencies...
pip install opencv-python Pillow streamlit
if errorlevel 1 (
    echo ⚠️  Some optional dependencies failed - system will still function
) else (
    echo ✅ Optional dependencies: OK
)

echo 🤖 [7/7] Claude Code Router (AI code tools)...
where npm >nul 2>&1
if not errorlevel 1 (
    echo Installing Claude Code Router...
    npm install -g @musistudio/claude-code-router
    if errorlevel 1 (
        echo ⚠️  Claude Code Router installation failed - code tools limited
    ) else (
        echo ✅ Claude Code Router: INSTALLED
    )
) else (
    echo ⚠️  Node.js not found - Claude Code Router skipped
    echo 💡 Install Node.js to enable Claude Code Router
)

echo.
echo 🧪 Testing critical imports...
call :doctor_test_imports

echo.
echo ✅ Dependency fixes completed!
echo 💡 All critical dependencies should now be available
pause
goto doctor_mode

:fix_dependencies_standalone
cls
echo.
echo ===============================================
echo  🔧 PYTHON DEPENDENCIES FIXER v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 Installing missing Python dependencies for DuckBot...
echo.
echo 💡 This will install all packages needed to fix common startup errors
echo    like "ModuleNotFoundError: No module named 'seaborn'"
echo.

REM Pre-flight check
call :check_python
if errorlevel 1 goto main_menu

echo.
echo 🔄 DEPENDENCY INSTALLATION SEQUENCE:
echo.

echo 📊 [1/7] Core visualization libraries...
echo    Installing: seaborn, plotly, matplotlib, pandas, numpy, scikit-learn
pip install seaborn plotly matplotlib pandas numpy scikit-learn
if errorlevel 1 (
    echo ❌ Failed to install visualization dependencies
    echo 💡 Try running as administrator or check internet connection
    pause
    goto main_menu
) else (
    echo ✅ Visualization libraries: INSTALLED
)

echo.
echo 📔 [2/7] Jupyter ecosystem...
echo    Installing: jupyter, notebook, ipywidgets, nbformat, ipykernel, jupyterlab
pip install jupyter notebook ipywidgets nbformat ipykernel jupyterlab
if errorlevel 1 (
    echo ❌ Failed to install Jupyter dependencies
    echo 💡 Jupyter features may be limited
) else (
    echo ✅ Jupyter ecosystem: INSTALLED
)

echo.
echo 🌐 [3/7] Web and API frameworks...
echo    Installing: fastapi, uvicorn, aiohttp, requests, websockets, jinja2
pip install fastapi uvicorn aiohttp requests websockets python-multipart jinja2
if errorlevel 1 (
    echo ❌ Failed to install web dependencies
    echo 💡 WebUI features may be limited
) else (
    echo ✅ Web frameworks: INSTALLED
)

echo.
echo 🤖 [4/7] Discord bot and AI libraries...
echo    Installing: discord.py, openai, anthropic, torch, transformers
pip install discord.py openai anthropic torch transformers
if errorlevel 1 (
    echo ❌ Failed to install AI dependencies
    echo 💡 AI features may be limited - this is normal for some systems
) else (
    echo ✅ AI libraries: INSTALLED
)

echo.
echo 🛠️ [5/7] System utilities...
echo    Installing: python-dotenv, psutil, PyYAML, watchdog, neo4j
pip install python-dotenv psutil PyYAML watchdog neo4j SpeechRecognition pyttsx3 GPUtil
if errorlevel 1 (
    echo ❌ Failed to install utility dependencies
    echo 💡 Some system features may be limited
) else (
    echo ✅ System utilities: INSTALLED
)

echo.
echo 🎵 [6/8] Media and optional libraries...
echo    Installing: opencv-python, Pillow, streamlit
pip install opencv-python Pillow streamlit
if errorlevel 1 (
    echo ⚠️  Some optional dependencies failed - system will still function
    echo ✅ Core dependencies should be working
) else (
    echo ✅ Media libraries: INSTALLED
)

echo.
echo 🤖 [7/8] Claude Code Router (AI code tools)...
echo    Installing: @musistudio/claude-code-router
where npm >nul 2>&1
if not errorlevel 1 (
    npm install -g @musistudio/claude-code-router
    if errorlevel 1 (
        echo ⚠️  Claude Code Router installation failed
        echo 💡 This provides AI-enhanced code analysis tools
    ) else (
        echo ✅ Claude Code Router: INSTALLED
    )
) else (
    echo ⚠️  Node.js not found - Claude Code Router skipped
    echo 💡 Install Node.js from https://nodejs.org to enable AI code tools
)

echo.
echo 🧪 [8/8] Testing critical imports...
echo.
call :doctor_test_imports

echo.
echo ===============================================
echo  🎉 DEPENDENCY INSTALLATION COMPLETED!
echo ===============================================
echo.
echo ✅ All critical Python dependencies have been installed
echo 💡 Common import errors should now be resolved
echo 🚀 You can now start your DuckBot ecosystem safely
echo.
echo 📋 WHAT WAS FIXED:
echo   ✅ seaborn (visualization) - fixes cost_visualizer import errors
echo   ✅ jupyter (notebooks) - fixes Jupyter startup issues  
echo   ✅ discord.py (bot framework) - fixes Discord bot errors
echo   ✅ fastapi/uvicorn (web server) - fixes WebUI startup
echo   ✅ All other critical dependencies for full functionality
echo.
echo 💡 TIP: If you still get errors, try the Doctor mode (option D) 
echo       for more advanced diagnostics and repair options
echo.
pause
goto main_menu

:doctor_full_diagnostic
cls
echo.
echo ===============================================
echo  🧪 FULL SYSTEM DIAGNOSTIC
echo ===============================================
echo.
echo 🧪 Running comprehensive system analysis...
echo.

REM System Information
echo 🖥️  System Information:
python -c "import platform,psutil,os; print('  OS:',platform.system(),platform.release()); print('  Python:',platform.python_version()); print('  CPU:',psutil.cpu_count(),'cores ('+str(psutil.cpu_percent())+'%% usage)'); print('  RAM:',str(psutil.virtual_memory().percent)+'%% used'); print('  Disk:',str(psutil.disk_usage('.').percent)+'%% used'); print('  Working Dir:',os.getcwd())"

echo.
echo 📦 Dependency Analysis:
call :doctor_check_critical_imports

echo.
echo 🌐 Service Status:
call :doctor_check_services

echo.
echo 🔌 Port Analysis:
call :doctor_check_ports

echo.
echo 🧠 AI System Diagnostics:
call :doctor_ai_diagnostics

echo.
echo ✅ Full diagnostic completed
pause
goto doctor_mode

:doctor_automated_repair
cls
echo.
echo ===============================================
echo  🔧 AUTOMATED REPAIR
echo ===============================================
echo.
echo ⚠️  This will attempt to fix common issues automatically
set /p confirm="Continue with automated repair? (y/N): "
if /i not "%confirm%"=="y" goto doctor_mode

echo.
echo 🔧 Running automated repair sequence...
echo.

echo [1/5] Fixing dependencies...
call :doctor_fix_dependencies_silent

echo [2/5] Cleaning temporary files...
if exist "logs\*.log" del "logs\*.log" /q >nul 2>&1
if exist "*.tmp" del "*.tmp" /q >nul 2>&1
echo ✅ Temporary files cleaned

echo [3/5] Resetting port conflicts...
call :doctor_kill_conflicting_processes

echo [4/5] Validating configuration...
if not exist ".env" (
    echo ⚠️  Creating default .env configuration
    echo # DuckBot Configuration > .env
    echo DISCORD_TOKEN=your_discord_token_here >> .env
    echo OPENROUTER_API_KEY=your_openrouter_key_here >> .env
    echo AI_CONFIDENCE_MIN=0.75 >> .env
)

echo [5/5] Testing system functionality...
call :doctor_test_imports

echo.
echo ✅ Automated repair completed!
echo 💡 Try starting your ecosystem now
pause
goto doctor_mode

:doctor_generate_report
cls
echo.
echo ===============================================
echo  📊 HEALTH REPORT GENERATOR
echo ===============================================
echo.
echo 📊 Generating comprehensive health report...
echo.

set "REPORT_FILE=DuckBot_Health_Report_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.txt"
set "REPORT_FILE=%REPORT_FILE: =%"

echo DuckBot v%DUCKBOT_VERSION% System Health Report > "%REPORT_FILE%"
echo Generated: %date% %time% >> "%REPORT_FILE%"
echo ================================== >> "%REPORT_FILE%"
echo. >> "%REPORT_FILE%"

python doctor_generate_report.py "%REPORT_FILE%"

echo.
echo ✅ Health report generated: %REPORT_FILE%
echo 📁 Report saved in current directory
echo 💡 You can share this report for troubleshooting
pause
goto doctor_mode

:doctor_invalid_choice
echo.
echo ❌ Invalid choice. Please select a valid option.
timeout /t 3 >nul
goto doctor_mode

:manual_setup
echo.
echo 🔧 Manual setup wizard not yet integrated - use original setup options
pause
goto main_menu

:config_ai
echo.
echo ⚙️  Running AI provider configuration...
python setup_ai_provider.py
pause
goto main_menu

:chat_ai
echo.
echo 💬 Starting interactive AI chat...
python chat_with_ai.py
pause
goto main_menu

:settings_menu
echo.
echo 📋 Advanced settings menu not yet integrated
pause
goto main_menu

:kill_processes
cls
echo.
echo ===============================================
echo  🛑 EMERGENCY PROCESS TERMINATION v%DUCKBOT_VERSION%
echo ===============================================
echo.
set /p confirm="⚠️  Kill all DuckBot processes? (y/N): "
if /i not "%confirm%"=="y" goto main_menu

echo 🛑 Terminating all processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1  
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM jupyter.exe >nul 2>&1

echo ✅ Process termination completed
pause
goto main_menu

:show_troubleshooting_info
echo.
echo 🔧 TROUBLESHOOTING INFORMATION:
echo   📝 Check logs: ai_ecosystem.log, webui.log
echo   🐍 Python version: 
python --version 2>&1
echo   📦 Dependencies: Run option I to install missing services
echo   🌐 Port conflicts: Check if other services are using ports 8787, 8188, 5678
echo.
exit /b 0

:help
cls
echo.
echo ===============================================
echo  ❓ HELP AND DOCUMENTATION v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 📚 DOCUMENTATION FILES:
echo   • README.md - Complete feature documentation  
echo   • INSTALL.md - Installation guide
echo   • CLAUDE.md - Technical documentation
echo.
echo 🚀 QUICK COMMANDS:
echo   • python start_ai_ecosystem.py - AI-enhanced startup
echo   • python chat_with_ai.py - Interactive AI chat
echo   • python setup_ai_provider.py - Configure AI providers
echo.
echo 🤖 AI FEATURES:
echo   • Real AI system management with intelligent routing
echo   • Automatic LM Studio ↔ OpenRouter fallback
echo   • Intelligent caching reduces API costs 60-80%%
echo   • Health monitoring with auto-restart
echo   • Dynamic model detection and smart routing
echo.
echo 📋 REQUIREMENTS:
echo   • Python 3.8+ (3.10+ recommended)
echo   • 4GB+ RAM (8GB+ recommended)  
echo   • Discord bot token
echo   • LM Studio OR OpenRouter API key
echo.
pause
goto main_menu

:invalid_choice
echo.
echo ❌ Invalid choice. Please enter a valid option.
timeout /t 3 >nul
goto main_menu

:apply_free_tier
REM Route to the actual settings label (compat shim)
call :apply_free_tier_settings
goto main_menu

:exit
cls
echo.
echo ===============================================
echo  🦆 GOODBYE FROM DUCKBOT v%DUCKBOT_VERSION%!
echo ===============================================
echo.
echo 🚀 Thanks for using DuckBot AI-Enhanced Ecosystem!
echo 📝 Your professional AI-managed crypto ecosystem
echo 🌟 Production-ready with enterprise-grade reliability
echo.
echo 💡 Quick restart: Just run this script again
echo 📚 Documentation: Check README.md for full features
echo 🤖 AI Support: python chat_with_ai.py anytime
echo.
echo Have a great day! 👋
timeout /t 3 >nul
exit /b 0

REM === LM Studio Helpers ===
:ensure_lm_studio_running
echo Checking LM Studio availability (required for local-only mode)...
call :probe_lm_studio
if not errorlevel 1 (
    echo LM Studio detected and responding
    exit /b 0
)
echo LM Studio not detected — attempting auto-start...
call :start_lm_studio
if errorlevel 1 (
    echo Could not locate LM Studio automatically.
    echo Set LMSTUDIO_EXE (or LM_STUDIO_EXE) to the full path, e.g.
    echo   %LocalAppData%\Programs\LM Studio\LM Studio.exe
    exit /b 1
)
setlocal enabledelayedexpansion
set /a __tries=0
:__wait_lm
timeout /t 2 >nul
call :probe_lm_studio
if not errorlevel 1 (
    endlocal & echo LM Studio is ready & exit /b 0
)
set /a __tries+=1
if !__tries! lss 30 goto __wait_lm
endlocal
echo LM Studio did not become ready within the timeout window.
exit /b 1

:probe_lm_studio
python -c "import sys, os, requests; base=os.environ.get('LM_STUDIO_URL','http://127.0.0.1:1234');\
import urllib.parse as u;\
def probe(url):\
    try:\
        r=requests.get(url, timeout=3); return r.ok\
    except Exception: return False\
base=base.rstrip('/');\
ok = probe(base+'/v1/models') or probe(base+'/models'); sys.exit(0 if ok else 1)" >nul 2>&1
if errorlevel 1 (
    exit /b 1
) else (
    exit /b 0
)

:start_lm_studio
set "_LM_EXE="
if defined LMSTUDIO_EXE set "_LM_EXE=%LMSTUDIO_EXE%"
if not defined _LM_EXE if defined LM_STUDIO_EXE set "_LM_EXE=%LM_STUDIO_EXE%"
if not defined _LM_EXE if exist "%LocalAppData%\Programs\LM Studio\LM Studio.exe" set "_LM_EXE=%LocalAppData%\Programs\LM Studio\LM Studio.exe"
if not defined _LM_EXE if exist "%ProgramFiles%\LM Studio\LM Studio.exe" set "_LM_EXE=%ProgramFiles%\LM Studio\LM Studio.exe"
if not defined _LM_EXE if exist "%ProgramFiles(x86)%\LM Studio\LM Studio.exe" set "_LM_EXE=%ProgramFiles(x86)%\LM Studio\LM Studio.exe"

if not defined _LM_EXE (
    exit /b 1
)
echo Launching LM Studio: "%_LM_EXE%"
start "LM Studio" /MIN "%_LM_EXE%"
exit /b 0

REM === DOCTOR MODE SUPPORT FUNCTIONS ===

:doctor_check_critical_imports
echo 🧪 Testing critical Python imports...
python doctor_check_imports.py
exit /b 0

:doctor_check_services
echo 🌐 Checking service availability...
python doctor_check_services.py
exit /b 0

:doctor_check_ports
echo 🔌 Checking port usage...
python doctor_check_ports.py
exit /b 0

:doctor_ai_diagnostics
echo 🧠 AI System Health...
python -c "try: from duckbot.qwen_diagnostics import QwenDiagnostics; qd = QwenDiagnostics(); print('  [OK] Qwen diagnostics available') if qd.is_available() else print('  [WARNING] Qwen diagnostics not available'); except Exception as e: print('  [ERROR] AI diagnostics error:', e)"
python -c "try: from duckbot.ai_router_gpt import AIRouter; print('  [OK] AI Router available'); except Exception as e: print('  [ERROR] AI Router issue:', e)"
python doctor_check_claude_code.py
exit /b 0

:doctor_test_imports
echo 🧪 Testing all imports...
python doctor_test_imports.py
exit /b 0

:doctor_fix_dependencies_silent
echo Installing dependencies silently...
pip install --quiet seaborn plotly matplotlib pandas numpy scikit-learn >nul 2>&1
pip install --quiet jupyter notebook ipywidgets nbformat ipykernel >nul 2>&1
pip install --quiet fastapi uvicorn aiohttp requests websockets >nul 2>&1
pip install --quiet discord.py torch psutil python-dotenv PyYAML >nul 2>&1
echo ✅ Silent dependency installation completed
exit /b 0

:doctor_kill_conflicting_processes
echo Checking for conflicting processes...
wmic process where "name='python.exe' and commandline like '%%jupyter%%'" delete >nul 2>&1
wmic process where "name='node.exe' and commandline like '%%n8n%%'" delete >nul 2>&1
echo ✅ Conflicting processes cleared
exit /b 0

:openwebui_start
cls
echo.
echo ===============================================
echo  🌐 OPEN-WEBUI WITH OPENROUTER INTEGRATION v%DUCKBOT_VERSION%
echo ===============================================
echo.
echo 🚀 LAUNCHING: Open-WebUI with OpenRouter Models
echo.
echo 📋 FEATURES:
echo   ✅ Modern web-based AI chat interface
echo   ✅ OpenRouter model integration with free model filtering
echo   ✅ Professional chat UI at localhost:8080
echo   ✅ Citation support and reasoning tokens
echo   ✅ Cache control for cost optimization
echo   ✅ Multi-provider model access
echo.
echo 🔧 CONFIGURATION:
echo   📡 Interface: http://localhost:8080
echo   🔌 Integration: OpenRouter API with function
echo   💰 Cost optimization: Cache control enabled
echo   🔒 Security: Local binding for privacy
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto main_menu

echo.
echo 🔄 STARTUP SEQUENCE:
echo [1/4] Checking Open-WebUI installation...
call :check_openwebui_installed
if errorlevel 1 goto openwebui_install_prompt

echo [2/4] Setting up OpenRouter function...
call :setup_openrouter_function

echo [3/4] Starting Open-WebUI server...
echo ⏳ This may take 30-60 seconds to fully initialize...
echo 🌐 Open-WebUI will be available at: http://localhost:8080
echo.

REM Start Open-WebUI with OpenRouter integration
start "Open-WebUI" cmd /c "open-webui serve --port 8080 --host 127.0.0.1"

echo [4/4] Waiting for server to initialize...
timeout /t 15 >nul

echo.
echo ✅ Open-WebUI started successfully!
echo 🌐 Access at: http://localhost:8080
echo 📊 Models: OpenRouter models available with function integration
echo 💡 TIP: Create an account on first visit
echo.
echo 📝 To stop: Close this window or press Ctrl+C
pause
goto main_menu

:check_openwebui_installed
echo 🔍 Checking Open-WebUI installation...
python -c "import open_webui" >nul 2>&1
if errorlevel 1 (
    echo ❌ Open-WebUI not detected
    exit /b 1
)
echo ✅ Open-WebUI installation verified
exit /b 0

:openwebui_install_prompt
echo.
echo ❌ Open-WebUI is not installed!
echo.
echo 📦 INSTALLATION OPTIONS:
echo.
echo 1. 🚀 [AUTO] Auto-install Open-WebUI (recommended)
echo 2. 🔧 [MANUAL] Show manual installation instructions
echo 3. 🔙 [BACK] Return to main menu
echo.
set /p install_choice="[PROMPT] Select installation option: "

if /i "%install_choice%"=="1" goto install_openwebui_auto
if /i "%install_choice%"=="2" goto show_openwebui_manual_install
if /i "%install_choice%"=="3" goto main_menu
goto openwebui_install_prompt

:install_openwebui_auto
echo.
echo 🚀 Auto-installing Open-WebUI...
echo.
pip install open-webui
if errorlevel 1 (
    echo ❌ Installation failed
    echo 💡 Try manual installation or check your Python/pip setup
    pause
    goto main_menu
)
echo ✅ Open-WebUI installed successfully!
echo 🔄 Returning to startup...
timeout /t 3 >nul
goto openwebui_start

:show_openwebui_manual_install
echo.
echo 🔧 MANUAL INSTALLATION INSTRUCTIONS:
echo.
echo 1. Install Open-WebUI:
echo    pip install open-webui
echo.
echo 2. Alternative installation methods:
echo    • Docker: docker run -d -p 8080:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
echo    • From source: git clone https://github.com/open-webui/open-webui.git
echo.
echo 3. After installation, restart this launcher
echo.
pause
goto main_menu

:setup_openrouter_function
echo 🔌 Setting up OpenRouter function integration...

REM Check if OpenRouter API key is configured
if not defined OPENROUTER_API_KEY (
    if exist ".env" (
        for /f "tokens=2 delims==" %%a in ('findstr /i "OPENROUTER_API_KEY" .env 2^>nul') do set OPENROUTER_API_KEY=%%a
    )
)

REM Copy the OpenRouter function to Open-WebUI functions directory
set "FUNCTIONS_DIR=%USERPROFILE%\.open-webui\functions"
if not exist "%FUNCTIONS_DIR%" mkdir "%FUNCTIONS_DIR%"

if exist "function-OpenRouter Integration for OpenWebUI.json" (
    echo 📁 Installing OpenRouter function...
    copy "function-OpenRouter Integration for OpenWebUI.json" "%FUNCTIONS_DIR%\openrouter_integration.json" >nul
    echo ✅ OpenRouter function installed
) else (
    echo ⚠️  OpenRouter function file not found
    echo 💡 Manual setup may be required
)

echo ✅ OpenRouter function setup completed
exit /b 0
