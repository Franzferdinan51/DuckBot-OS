@echo off
setlocal EnableDelayedExpansion

:: =============================================================================
:: DuckBot v3.1.0+ Ultimate Launcher
:: Enhanced with ByteBot, Archon, ChromiumOS, and Charm integrations
:: Comprehensive startup script with intelligent system detection
:: =============================================================================

title DuckBot v3.1.0+ Ultimate Launcher

:: Color definitions
set "COLOR_RESET=[0m"
set "COLOR_CYAN=[96m"
set "COLOR_GREEN=[92m"
set "COLOR_YELLOW=[93m"
set "COLOR_RED=[91m"
set "COLOR_BLUE=[94m"
set "COLOR_MAGENTA=[95m"
set "COLOR_BOLD=[1m"

:: Clear screen and show header
cls
echo %COLOR_CYAN%%COLOR_BOLD%
echo ================================================================================
echo   ____             __   ____        __     _    _ _ _   _                 _       
echo  ^| __ ^) _   _  ___^| ^|__^| __ ^)  ___ ^| ^|_  ^| ^| ^| ^| ^| ^| ^|_^|^| ^|_ ^|^| ^|_^| ^|^ ^|^|^|^ ^|
echo  ^|  _ \^| ^| ^| ^|^/ __^| '_ \^|  _ \ ^/ _ \^| __^| ^| ^| ^| ^| ^| ^| __ ^|^| __^| ^| _ ^| ^| _ ^| _ ^|
echo  ^| ^|_^) ^| ^|_^| ^| ^(__^| ^| ^| ^| ^|_^) ^|  __^/ ^|_   ^| ^| ^| ^| ^| ^| ^| ^| ^| ^| ^|_^| ^| ^| ^| ^| ^| ^| ^| ^|
echo  ^|____^/ \__^|_^|^|\___ ^|_^| ^|_^|____^/ \___^| \__^|  ^| ^|_^| ^|_^|_^| ^|_^| ^|_^|\__^|_^| ^|_^| ^|_^| ^|_^|
echo
echo                          v3.1.0+ Ultimate Edition
echo          Enhanced with ByteBot + Archon + ChromiumOS + Charm Features
echo ================================================================================
echo %COLOR_RESET%

:: System information
echo %COLOR_GREEN%[INFO]%COLOR_RESET% Detecting system configuration...
echo %COLOR_BLUE%System Information:%COLOR_RESET%
echo   - OS Version: %OS%
echo   - Architecture: %PROCESSOR_ARCHITECTURE%
echo   - User: %USERNAME%
echo   - Date/Time: %DATE% %TIME%

:: Check Python installation
echo.
echo %COLOR_GREEN%[CHECK]%COLOR_RESET% Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo %COLOR_RED%[ERROR]%COLOR_RESET% Python is not installed or not in PATH!
    echo %COLOR_YELLOW%[HELP]%COLOR_RESET% Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
) else (
    python --version
    echo %COLOR_GREEN%[OK]%COLOR_RESET% Python detected successfully
)

:: Check WSL availability  
echo.
echo %COLOR_GREEN%[CHECK]%COLOR_RESET% Checking WSL integration...
wsl --status >nul 2>&1
if errorlevel 1 (
    echo %COLOR_YELLOW%[WARNING]%COLOR_RESET% WSL not available - some features will be limited
    set "WSL_AVAILABLE=false"
) else (
    echo %COLOR_GREEN%[OK]%COLOR_RESET% WSL detected and available
    set "WSL_AVAILABLE=true"
    echo %COLOR_BLUE%[INFO]%COLOR_RESET% Available WSL distributions:
    wsl --list --verbose
)

:: Check GPU availability
echo.
echo %COLOR_GREEN%[CHECK]%COLOR_RESET% Checking GPU acceleration...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo %COLOR_YELLOW%[WARNING]%COLOR_RESET% NVIDIA GPU not detected - using CPU fallback
    set "GPU_AVAILABLE=false"
) else (
    echo %COLOR_GREEN%[OK]%COLOR_RESET% NVIDIA GPU detected
    set "GPU_AVAILABLE=true"
)

:: Check dependencies
echo.
echo %COLOR_GREEN%[CHECK]%COLOR_RESET% Checking required dependencies...
python -c "import fastapi, uvicorn, discord, asyncio" >nul 2>&1
if errorlevel 1 (
    echo %COLOR_YELLOW%[WARNING]%COLOR_RESET% Some dependencies missing - attempting installation...
    echo %COLOR_BLUE%[INFO]%COLOR_RESET% Installing requirements...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo %COLOR_RED%[ERROR]%COLOR_RESET% Failed to install dependencies!
        pause
        exit /b 1
    )
)

:: Show main menu
:MAIN_MENU
cls
echo %COLOR_CYAN%%COLOR_BOLD%
echo ================================================================================
echo                           DuckBot v3.1.0+ Launch Options
echo ================================================================================
echo %COLOR_RESET%
echo %COLOR_GREEN%[ULTIMATE MODES]%COLOR_RESET%
echo   1. 🚀 Ultimate Enhanced Mode    - All features enabled (Recommended)
echo   2. 🏠 Local-First Privacy Mode  - Complete offline experience
echo   3. 🌐 Hybrid Cloud+Local Mode   - Best of both worlds
echo   4. 🔧 Developer Debug Mode      - Full debugging enabled
echo.
echo %COLOR_BLUE%[SPECIALIZED INTERFACES]%COLOR_RESET%
echo   5. 🎨 Enhanced WebUI Dashboard  - Modern web interface
echo   6. 💻 Charm Terminal Interface  - Beautiful terminal UI
echo   7. 🖥️ Desktop Integration Mode   - ByteBot automation
echo   8. 🐧 WSL Integration Mode      - Linux subsystem control
echo.
echo %COLOR_YELLOW%[SYSTEM MANAGEMENT]%COLOR_RESET%
echo   9. 📊 System Monitoring         - Real-time diagnostics
echo   10. ⚙️ Configuration Manager     - Settings and optimization
echo   11. 🧪 Test All Features         - Comprehensive validation
echo   12. 📦 Create Deployment Package - Generate distribution
echo.
echo %COLOR_MAGENTA%[UTILITIES]%COLOR_RESET%
echo   Q. ⚡ Quick Start (Optimized)   - One-click launch
echo   S. 🛠️ System Diagnostics        - Deep system analysis
echo   H. ❓ Help & Documentation      - Show detailed help
echo   X. ❌ Exit                      - Close launcher
echo.

set /p "choice=Enter your choice: "

:: Handle menu choices
if /i "!choice!"=="1" goto ULTIMATE_MODE
if /i "!choice!"=="2" goto LOCAL_MODE
if /i "!choice!"=="3" goto HYBRID_MODE  
if /i "!choice!"=="4" goto DEBUG_MODE
if /i "!choice!"=="5" goto WEBUI_MODE
if /i "!choice!"=="6" goto TERMINAL_MODE
if /i "!choice!"=="7" goto DESKTOP_MODE
if /i "!choice!"=="8" goto WSL_MODE
if /i "!choice!"=="9" goto MONITORING_MODE
if /i "!choice!"=="10" goto CONFIG_MODE
if /i "!choice!"=="11" goto TEST_MODE
if /i "!choice!"=="12" goto PACKAGE_MODE
if /i "!choice!"=="Q" goto QUICK_START
if /i "!choice!"=="S" goto DIAGNOSTICS
if /i "!choice!"=="H" goto HELP
if /i "!choice!"=="X" goto EXIT

echo %COLOR_RED%[ERROR]%COLOR_RESET% Invalid choice. Please try again.
timeout /t 2 >nul
goto MAIN_MENU

:ULTIMATE_MODE
echo.
echo %COLOR_CYAN%[ULTIMATE MODE]%COLOR_RESET% Starting DuckBot with all enhancements...
echo %COLOR_GREEN%[INFO]%COLOR_RESET% Features enabled:
echo   ✓ Enhanced WebUI with real-time updates
echo   ✓ Charm terminal interface
echo   ✓ ByteBot desktop automation
echo   ✓ Archon multi-agent orchestration
echo   ✓ WSL integration (if available)
echo   ✓ Advanced monitoring and analytics
echo   ✓ Multi-model AI routing
echo   ✓ Real-time collaboration features

:: Set environment for ultimate mode
set "ENABLE_ENHANCED_WEBUI=true"
set "ENABLE_CHARM_TERMINAL=true"
set "ENABLE_BYTEBOT=true"
set "ENABLE_ARCHON_FEATURES=true"
set "ENABLE_WSL_INTEGRATION=%WSL_AVAILABLE%"
set "ENABLE_ADVANCED_MONITORING=true"
set "AI_MODE=hybrid"
set "LOG_LEVEL=info"

echo.
echo %COLOR_GREEN%[LAUNCH]%COLOR_RESET% Starting enhanced ecosystem...
start "DuckBot Enhanced WebUI" python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787
timeout /t 3 >nul
start "DuckBot Charm Terminal" python -m duckbot.charm_terminal_ui
timeout /t 2 >nul
python start_ecosystem.py --mode ultimate --enable-all
goto END

:LOCAL_MODE
echo.
echo %COLOR_GREEN%[LOCAL MODE]%COLOR_RESET% Starting privacy-first local mode...
echo %COLOR_BLUE%[INFO]%COLOR_RESET% All processing stays on your machine
set "AI_LOCAL_ONLY_MODE=true"
set "DISABLE_OPENROUTER=true" 
set "ENABLE_LM_STUDIO_ONLY=true"
set "ENABLE_OFFLINE_FEATURES=true"
python start_local_ecosystem.py --privacy-mode
goto END

:HYBRID_MODE
echo.
echo %COLOR_BLUE%[HYBRID MODE]%COLOR_RESET% Starting cloud+local hybrid mode...
set "AI_MODE=hybrid"
set "ENABLE_CLOUD_FALLBACK=true"
set "ENABLE_LOCAL_PRIORITY=true"
python start_ecosystem.py --mode hybrid
goto END

:DEBUG_MODE
echo.
echo %COLOR_YELLOW%[DEBUG MODE]%COLOR_RESET% Starting with full debugging enabled...
set "LOG_LEVEL=debug"
set "ENABLE_DEBUG_UI=true"
set "ENABLE_DETAILED_LOGGING=true"
set "ENABLE_PERFORMANCE_MONITORING=true"
python start_ecosystem.py --debug --verbose
goto END

:WEBUI_MODE
echo.
echo %COLOR_CYAN%[WEBUI MODE]%COLOR_RESET% Starting Enhanced WebUI...
python -m duckbot.enhanced_webui
goto END

:TERMINAL_MODE
echo.
echo %COLOR_MAGENTA%[TERMINAL MODE]%COLOR_RESET% Starting Charm Terminal Interface...
python -m duckbot.charm_terminal_ui
goto END

:DESKTOP_MODE
echo.
echo %COLOR_GREEN%[DESKTOP MODE]%COLOR_RESET% Starting ByteBot Desktop Integration...
set "ENABLE_DESKTOP_AUTOMATION=true"
set "ENABLE_SCREENSHOT_API=true"
set "ENABLE_UI_INTERACTION=true"
python -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
goto END

:WSL_MODE
if "!WSL_AVAILABLE!"=="false" (
    echo %COLOR_RED%[ERROR]%COLOR_RESET% WSL not available on this system!
    pause
    goto MAIN_MENU
)
echo.
echo %COLOR_BLUE%[WSL MODE]%COLOR_RESET% Starting WSL Integration Interface...
python -c "from duckbot.wsl_integration import wsl_integration; import asyncio; asyncio.run(wsl_integration.start_interactive_mode())"
goto END

:MONITORING_MODE
echo.
echo %COLOR_GREEN%[MONITORING]%COLOR_RESET% Starting system monitoring...
start "System Monitor" python -m duckbot.enhanced_webui --monitoring-only
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}%')"
pause
goto MAIN_MENU

:CONFIG_MODE
echo.
echo %COLOR_YELLOW%[CONFIG]%COLOR_RESET% Opening configuration manager...
python -c "from duckbot.settings_gpt import interactive_config; interactive_config()"
goto MAIN_MENU

:TEST_MODE
echo.
echo %COLOR_CYAN%[TESTING]%COLOR_RESET% Running comprehensive feature tests...
echo %COLOR_BLUE%[INFO]%COLOR_RESET% This will test all integrations and features...
python test_every_feature.py
python test_enhanced_duckbot.py  
if exist test_local_feature_parity.py python test_local_feature_parity.py
echo.
echo %COLOR_GREEN%[COMPLETE]%COLOR_RESET% All tests completed. Check results above.
pause
goto MAIN_MENU

:PACKAGE_MODE
echo.
echo %COLOR_MAGENTA%[PACKAGING]%COLOR_RESET% Creating deployment package...
echo %COLOR_BLUE%[INFO]%COLOR_RESET% This will create a ZIP file with all necessary files...
python create_deployment_package.py --include-integrations --optimize
echo %COLOR_GREEN%[COMPLETE]%COLOR_RESET% Deployment package created successfully!
pause
goto MAIN_MENU

:QUICK_START
echo.
echo %COLOR_GREEN%[QUICK START]%COLOR_RESET% Launching optimized configuration...
echo %COLOR_BLUE%[INFO]%COLOR_RESET% Using intelligent defaults based on system capabilities...

if "!GPU_AVAILABLE!"=="true" (
    set "AI_ACCELERATION=gpu"
    echo %COLOR_GREEN%[GPU]%COLOR_RESET% GPU acceleration enabled
) else (
    set "AI_ACCELERATION=cpu"
    echo %COLOR_YELLOW%[CPU]%COLOR_RESET% Using CPU processing
)

if "!WSL_AVAILABLE!"=="true" (
    set "ENABLE_WSL_INTEGRATION=true"
    echo %COLOR_GREEN%[WSL]%COLOR_RESET% WSL integration enabled
)

python start_ecosystem.py --quick-start --optimize-for-system
goto END

:DIAGNOSTICS  
echo.
echo %COLOR_CYAN%[DIAGNOSTICS]%COLOR_RESET% Running deep system analysis...
echo %COLOR_BLUE%[INFO]%COLOR_RESET% Checking all components and integrations...
echo.

:: System diagnostics
echo %COLOR_GREEN%[SYSTEM]%COLOR_RESET%
systeminfo | findstr /C:"Total Physical Memory" /C:"Available Physical Memory"
wmic cpu get name
wmic gpu get name

:: Python environment  
echo.
echo %COLOR_GREEN%[PYTHON]%COLOR_RESET%
python -c "import sys; print(f'Python: {sys.version}')"
python -c "import platform; print(f'Platform: {platform.platform()}')"

:: Check all dependencies
echo.
echo %COLOR_GREEN%[DEPENDENCIES]%COLOR_RESET%
python -c "
import importlib
modules = ['fastapi', 'uvicorn', 'discord', 'asyncio', 'psutil', 'PIL', 'cv2', 'numpy']
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f'✓ {mod}')
    except ImportError:
        print(f'✗ {mod} - missing')
"

:: Integration checks
echo.
echo %COLOR_GREEN%[INTEGRATIONS]%COLOR_RESET%
python -c "
from duckbot.wsl_integration import is_wsl_available
from duckbot.bytebot_integration import ByteBotIntegration
print(f'WSL Available: {is_wsl_available()}')
print(f'ByteBot Ready: {ByteBotIntegration()._check_dependencies()}')
"

echo.
echo %COLOR_GREEN%[COMPLETE]%COLOR_RESET% Diagnostics completed.
pause
goto MAIN_MENU

:HELP
cls
echo %COLOR_CYAN%%COLOR_BOLD%
echo ================================================================================
echo                              DuckBot v3.1.0+ Help
echo ================================================================================
echo %COLOR_RESET%
echo %COLOR_GREEN%[OVERVIEW]%COLOR_RESET%
echo DuckBot v3.1.0+ is an enhanced AI ecosystem with advanced integrations:
echo.
echo %COLOR_BLUE%[KEY FEATURES]%COLOR_RESET%
echo   • Multi-Agent AI Orchestration (Archon-inspired)
echo   • Desktop Automation & Control (ByteBot integration)  
echo   • Beautiful Terminal Interfaces (Charm-inspired)
echo   • Windows Subsystem for Linux integration
echo   • Real-time WebUI with monitoring
echo   • Privacy-first local-only mode
echo   • Hybrid cloud+local AI routing
echo   • Advanced system monitoring
echo.
echo %COLOR_YELLOW%[QUICK SETUP]%COLOR_RESET%
echo   1. Choose "Ultimate Enhanced Mode" for full experience
echo   2. Or "Local-First Privacy Mode" for offline usage
echo   3. Configure your .env file with API keys (optional for local mode)
echo   4. Access WebUI at http://127.0.0.1:8787
echo.
echo %COLOR_MAGENTA%[DOCUMENTATION]%COLOR_RESET%
echo   • README.md - Getting started guide
echo   • CLAUDE.md - Development documentation
echo   • DUCKBOT_OS_README.md - OS integration guide
echo   • GitHub: Enhanced with multiple integrations
echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo %COLOR_GREEN%Thank you for using DuckBot v3.1.0+ Ultimate Edition!%COLOR_RESET%
echo %COLOR_BLUE%Visit our documentation for more advanced features.%COLOR_RESET%
timeout /t 2 >nul
exit /b 0

:END
echo.
echo %COLOR_CYAN%[INFO]%COLOR_RESET% DuckBot is now running with selected configuration.
echo %COLOR_GREEN%[ACCESS]%COLOR_RESET% WebUI available at: http://127.0.0.1:8787  
echo %COLOR_BLUE%[LOGS]%COLOR_RESET% Check the logs/ directory for detailed information.
echo %COLOR_YELLOW%[STOP]%COLOR_RESET% Use EMERGENCY_KILL.bat to stop all processes.
echo.
echo %COLOR_MAGENTA%Press any key to return to menu or Ctrl+C to exit...%COLOR_RESET%
pause >nul
goto MAIN_MENU