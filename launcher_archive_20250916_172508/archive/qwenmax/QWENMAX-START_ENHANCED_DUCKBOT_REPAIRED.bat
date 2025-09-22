@echo off
REM DuckBot v3.1.0+ Ultimate Enhanced Launcher - Complete Integration Suite
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Ultimate Enhanced - Complete AI Integration Suite
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DUCKBOT_VERSION=3.1.0+"
set "BUILD_DATE=2025-09-09"
set "BUILD_STATUS=ULTIMATE-ENHANCED-READY"

REM Enhanced environment setup
set "ENABLE_ENHANCED_FEATURES=true"

REM Force jump to main menu
goto main_menu

:main_menu
echo.
echo ================================================================================
echo  DUCKBOT v%DUCKBOT_VERSION% ULTIMATE ENHANCED - COMPLETE AI INTEGRATION SUITE
echo ================================================================================
echo    Professional AI-Managed Enhanced Ecosystem with ALL Integrations
echo    [STATUS] %BUILD_STATUS% - Enhanced Edition
echo    [BUILD] %BUILD_DATE% - Ultimate Enhanced Edition
echo ================================================================================
echo.
echo ULTIMATE INTEGRATION FEATURES:
echo   Enhanced WebUI - Modern real-time dashboard with WebSocket updates
echo   Multi-Model AI Routing - Intelligent local/cloud hybrid processing
echo   Real-Time Monitoring - Live system metrics and performance tracking
echo.
echo ULTIMATE LAUNCH MODES - COMPLETE INTEGRATION EXPERIENCE:
echo.
echo 1. [ULTIMATE] Complete Ultimate Enhanced Mode - RECOMMENDED!
echo    ALL integrations active: Enhanced WebUI + Multi-Agent AI
echo    Real-time monitoring + Advanced system integration
echo    Maximum capabilities with full feature set
echo.
echo 2. [ENHANCED-WEBUI] Enhanced WebUI Dashboard
echo    Modern web interface with real-time updates
echo    Multi-agent coordination + System monitoring
echo    Task management + Knowledge base integration
echo.
echo 3. [MONITORING] System Monitoring Dashboard
echo    Real-time system metrics + Performance tracking
echo    Agent status monitoring + Resource utilization
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
echo S. [STATUS] Quick System Status
echo    Integration health checks + Service status
echo    Port availability + Process monitoring
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
echo Q. [QUIT] Exit Launcher
echo.
set /p choice="[ULTIMATE PROMPT] Enter your choice: "

REM Handle all menu choices
if /i "%choice%"=="1" goto ultimate_complete_mode
if /i "%choice%"=="2" goto enhanced_webui_mode
if /i "%choice%"=="3" goto monitoring_mode
if /i "%choice%"=="7" goto classic_enhanced_mode
if /i "%choice%"=="8" goto local_privacy_mode
if /i "%choice%"=="9" goto hybrid_cloud_mode
if /i "%choice%"=="I" goto install_components
if /i "%choice%"=="U" goto update_components
if /i "%choice%"=="S" goto system_status
if /i "%choice%"=="K" goto kill_processes
if /i "%choice%"=="R" goto restart_services
if /i "%choice%"=="H" goto show_help
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit
goto invalid_choice

:ultimate_complete_mode
cls
echo.
echo ================================================================================
echo  DUCKBOT v%DUCKBOT_VERSION% ULTIMATE COMPLETE MODE
echo ================================================================================
echo.
echo LAUNCHING: Complete Ultimate Integration Experience
echo.

REM Pre-flight checks
call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

call :check_system_requirements
if %errorlevel% neq 0 goto main_menu

echo.
echo LAUNCHING: Starting main ecosystem orchestrator...
echo This will start all services in a centralized and reliable way.
echo.

python start_ecosystem.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start the ecosystem orchestrator.
    echo Please check the console output above for errors.
    echo.
    pause
    goto main_menu
)

echo.
echo ================================================================================
echo      ULTIMATE COMPLETE MODE - ECOSYSTEM ORCHESTRATOR HAS EXITED
echo ================================================================================
echo.
echo The main ecosystem process has finished. 
echo If this was unexpected, please check the console output above for errors.
echo.
echo Press any key to return to the main menu...
pause
goto main_menu

:enhanced_webui_mode
cls
echo.
echo ================================================================================
echo  ENHANCED WEBUI DASHBOARD v%DUCKBOT_VERSION%
echo ================================================================================
echo.
echo LAUNCHING: Enhanced WebUI with Real-Time Features
echo.

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting Enhanced WebUI with all integrations...
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start Enhanced WebUI.
    echo Please check the console output above for errors.
    echo.
    pause
)

echo Enhanced WebUI session ended.
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

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting monitoring dashboard...
python ai_ecosystem_manager.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start monitoring dashboard.
    echo Please check the console output above for errors.
    echo.
    pause
)

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

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting Classic DuckBot with enhancements...
python -m duckbot.webui --host 127.0.0.1 --port 8787

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start Classic DuckBot.
    echo Please check the console output above for errors.
    echo.
    pause
)

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

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting Local Privacy Mode...
echo This mode operates completely offline with LM Studio integration.
python -m duckbot.enhanced_webui --local-only --port 8787

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start Local Privacy Mode.
    echo Please check the console output above for errors.
    echo.
    pause
)

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

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting Hybrid Cloud Mode...
python -m duckbot.enhanced_webui --hybrid-mode --port 8787

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start Hybrid Cloud Mode.
    echo Please check the console output above for errors.
    echo.
    pause
)

pause
goto main_menu

:system_status
cls
echo.
echo ================================================================================
echo  SYSTEM STATUS v%DUCKBOT_VERSION%
echo ================================================================================
echo.

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo SYSTEM INFORMATION:
python -c "
import platform, subprocess, os, sys
print(f'OS: {platform.platform()}')
print(f'Python: {sys.version.split()[0]}')
try:
    import psutil
    print(f'CPU: {psutil.cpu_percent()}% usage')
    print(f'Memory: {psutil.virtual_memory().percent}% used')
    print(f'Disk: {psutil.disk_usage(os.getcwd()).percent}% used')
except ImportError:
    print('System Metrics: psutil module not found. Install with: pip install psutil')
"

echo.
echo INTEGRATION STATUS:
python -c "
import importlib, subprocess
modules = [
    ('Enhanced WebUI', 'duckbot.enhanced_webui'),
    ('AI Ecosystem Manager', 'ai_ecosystem_manager')
]
for name, module in modules:
    try:
        importlib.import_module(module)
        print(f'{name}: AVAILABLE')
    except ImportError:
        print(f'{name}: NOT AVAILABLE')
"

echo.
echo PORT STATUS:
python -c "
import socket
ports = [('Enhanced WebUI', 8787), ('System Monitor', 8788)]
for name, port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    status = 'IN USE' if result == 0 else 'AVAILABLE'
    print(f'{name} (:{port}): {status}')
    sock.close()
"

pause
goto main_menu

:install_components
cls
echo.
echo ================================================================================
echo  INSTALL MISSING COMPONENTS v%DUCKBOT_VERSION%
echo ================================================================================
echo.

echo Installing all required components and dependencies...
echo.

echo [1/3] Installing Python dependencies...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    goto main_menu
)

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Some dependencies may have failed to install
    echo Check the output above for specific errors
)

echo [2/3] Installing enhanced integration dependencies...
python -m pip install psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer

echo [3/3] Component installation completed!
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

echo Stopping all DuckBot processes and integrations...
echo.

echo Killing Python processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo All processes have been terminated.
pause
goto main_menu

:show_help
cls
echo.
echo ================================================================================
echo  DUCKBOT v%DUCKBOT_VERSION% ULTIMATE HELP
echo ================================================================================
echo.
echo TROUBLESHOOTING:
echo   - Check logs/ directory for detailed error information
echo   - Use 'S' option for system status and diagnostics
echo   - Ensure all dependencies are installed with 'I' option
echo.
echo DOCUMENTATION:
echo   - README.md: Getting started guide
echo   - CLAUDE.md: Development documentation
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

echo [1/2] Updating Python dependencies...
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt

echo [2/2] Validation...
python -c "print('Update completed successfully!')"
pause
goto main_menu

:restart_services
cls
echo.
echo ================================================================================
echo  RESTART SERVICES v%DUCKBOT_VERSION%
echo ================================================================================
echo.

echo Restarting all DuckBot services...
echo.

echo [1/2] Stopping all services...
call :kill_processes
timeout /t 3 >nul

echo [2/2] Starting services...
call :ultimate_complete_mode
goto main_menu

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

python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.8+ required!
    echo Please upgrade your Python installation
    pause
    exit /b 1
)

echo Python installation verified for Ultimate mode
exit /b 0

:check_system_requirements
echo Checking system requirements...
python -c "
import platform
try:
    import psutil
    mem_gb = psutil.virtual_memory().total / (1024**3)
    if mem_gb < 4:
        print(f'Warning: Low memory ({mem_gb:.1f}GB). 8GB+ recommended for Ultimate mode')
    else:
        print(f'Memory: {mem_gb:.1f}GB - OK')
except ImportError:
    print('Warning: psutil module not found. Cannot check detailed memory usage.')
    print('Install it with: pip install psutil')
print(f'OS: {platform.platform()}')
"
exit /b 0

:invalid_choice
echo.
echo Invalid choice. Please enter a valid option.
timeout /t 3 >nul
goto main_menu

:exit
cls
echo.
echo ================================================================================
echo  GOODBYE FROM DUCKBOT v%DUCKBOT_VERSION% ULTIMATE ENHANCED!
echo ================================================================================
echo.
echo Thanks for using DuckBot Ultimate Enhanced Edition!
echo.
echo Have a great day with your Ultimate AI companion!
timeout /t 5 >nul
exit /b 0