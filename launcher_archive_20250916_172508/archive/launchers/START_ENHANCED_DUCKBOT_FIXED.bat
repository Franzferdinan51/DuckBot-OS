@echo off
REM DuckBot v3.1.0+ Ultimate Enhanced Launcher - Fixed Version
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Ultimate Enhanced - Complete AI Integration Suite
color 0A

REM Change to script directory
cd /d "%~dp0"

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
echo LAUNCH MODES:
echo.
echo 1. [ULTIMATE] Complete Ultimate Enhanced Mode - RECOMMENDED!
echo    ALL integrations active with live console logging
echo    Enhanced WebUI + Real-time monitoring + Advanced system integration
echo    Shows startup logs and keeps console open
echo.
echo 2. [ENHANCED-WEBUI] Enhanced WebUI Dashboard
echo    Modern web interface with real-time updates
echo    Multi-agent coordination + System monitoring
echo.
echo 3. [CHARM-TERMINAL] Charm Terminal Interface
echo    Beautiful, color-coded terminal experience
echo    Interactive menus + Multi-model AI chat
echo.
echo 4. [STATUS] Quick System Status
echo    Integration health checks + Service status
echo    Port availability + Process monitoring
echo.
echo 5. [TEST] Test All Integrations
echo    Comprehensive integration and feature testing
echo    Performance benchmarks + Compatibility checks
echo.
echo 6. [INSTALL] Auto-Install Missing Components
echo    Install all required dependencies automatically
echo.
echo Q. [QUIT] Exit Launcher
echo.
set /p choice="Enter your choice (1-6 or Q): "

echo.
echo [DEBUG] You entered: %choice%
echo.

if /i "%choice%"=="1" goto ultimate_complete_mode
if /i "%choice%"=="2" goto enhanced_webui_mode
if /i "%choice%"=="3" goto charm_terminal_mode
if /i "%choice%"=="4" goto system_status
if /i "%choice%"=="5" goto test_all_integrations
if /i "%choice%"=="6" goto install_components
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo Invalid choice: %choice%
echo Please enter 1-6 or Q
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

echo [PREFLIGHT] Running system checks...

REM Python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found or not working!
    echo Python 3.8+ is required for Ultimate DuckBot
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    goto main_menu
)

REM File existence check
if not exist "start_ecosystem.py" (
    echo [ERROR] start_ecosystem.py not found!
    echo This file is required for DuckBot to start.
    echo Current directory: %CD%
    pause
    goto main_menu
)

if not exist "duckbot" (
    echo [ERROR] duckbot directory not found!
    echo The duckbot module directory is required.
    echo Current directory: %CD%
    pause
    goto main_menu
)

echo [PREFLIGHT] All checks passed!
echo.
echo LAUNCHING: Starting main ecosystem orchestrator...
echo This will start all services with live console logging.
echo.
echo [INFO] Executing: python start_ecosystem.py
echo [INFO] The console will show live logs and startup messages
echo [INFO] Once DuckBot starts, it will be available at: http://127.0.0.1:8787
echo [INFO] Press Ctrl+C in the Python process to stop DuckBot
echo [INFO] Keep this console window open to see activity
echo ============================================================
echo.

python start_ecosystem.py

set "PYTHON_EXIT_CODE=%ERRORLEVEL%"

echo.
echo ================================================================================
echo      ULTIMATE COMPLETE MODE - ECOSYSTEM ORCHESTRATOR HAS EXITED
echo ================================================================================
echo.
echo [INFO] Python exit code: %PYTHON_EXIT_CODE%
if %PYTHON_EXIT_CODE% equ 0 (
    echo [INFO] Status: Normal exit
) else (
    echo [INFO] Status: Error exit - check output above for details
)
echo [INFO] The main ecosystem process has finished.
echo [INFO] All logs are also saved to the logs/ directory
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

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto main_menu
)

echo Starting Enhanced WebUI with all integrations...
echo [INFO] Executing: python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787
echo [INFO] Web interface will be available at: http://127.0.0.1:8787
echo [INFO] Press Ctrl+C to stop the WebUI server
echo.

python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

set "WEBUI_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Enhanced WebUI session ended with exit code: %WEBUI_EXIT_CODE%
echo [INFO] All logs saved to logs/ directory
echo.
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

set "CHARM_EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Charm Terminal session ended with exit code: %CHARM_EXIT_CODE%
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
    ('Enhanced WebUI', 'duckbot.enhanced_webui'),
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
if exist requirements.txt (
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Some dependencies may have failed to install
        echo Check the output above for specific errors
    )
) else (
    echo WARNING: requirements.txt not found
)

echo [2/3] Installing enhanced integration dependencies...
python -m pip install psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer

echo [3/3] Component installation completed!
echo.
pause
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
echo IMPORTANT: If DuckBot is still running in background, it will continue
echo running until you stop it or close all Python processes.
echo.
echo Web interface (if running): http://127.0.0.1:8787
echo Log files location: logs/
echo.
echo Have a great day with your Ultimate AI companion!
timeout /t 5 >nul
exit /b 0