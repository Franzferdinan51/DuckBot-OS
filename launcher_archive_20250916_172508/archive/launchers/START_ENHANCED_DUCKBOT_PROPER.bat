@echo off
REM DuckBot v3.1.0+ Proper Fixed Launcher - Shows logs and stays open
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Ultimate Enhanced - Complete AI Integration Suite
color 0A

REM Change to script directory
cd /d "%~dp0"

REM Set console buffer size for better log visibility
mode con: cols=120 lines=50

:main_menu
cls
echo.
echo ================================================================================
echo  DUCKBOT v3.1.0+ ULTIMATE ENHANCED - COMPLETE AI INTEGRATION SUITE
echo ================================================================================
echo    Professional AI-Managed Enhanced Ecosystem with ALL Integrations
echo    [STATUS] ULTIMATE-ENHANCED-READY - ByteBot + Archon + Charm + ChromiumOS Ready
echo    [BUILD] 2025-09-09 - Ultimate Enhanced Edition with PROPER LOGGING
echo ================================================================================
echo.
echo ULTIMATE INTEGRATION FEATURES:
echo   ByteBot Desktop Automation - Complete computer control and task automation
echo   Archon Multi-Agent System - Advanced orchestration and knowledge management
echo   Charm Terminal Interface - Beautiful, interactive command-line experience
echo   ChromiumOS System Features - Advanced OS-level integration and security
echo   WSL Integration - Full Windows Subsystem for Linux support
echo   Enhanced WebUI - Modern real-time dashboard with WebSocket updates
echo   Multi-Model AI Routing - Intelligent local/cloud hybrid processing
echo   Real-Time Monitoring - Live system metrics and performance tracking
echo.
echo ULTIMATE LAUNCH MODES:
echo.
echo 1. [ULTIMATE] Complete Ultimate Enhanced Mode - RECOMMENDED!
echo    ALL integrations active: ByteBot + Archon + Charm + ChromiumOS + WSL
echo    Enhanced WebUI + Terminal Interface + Desktop Automation + Multi-Agent AI
echo    Real-time monitoring + Advanced system integration
echo    LOGS SHOWN IN CONSOLE + Files in logs/ directory
echo.
echo 2. [ENHANCED-WEBUI] Enhanced WebUI Dashboard
echo    Modern web interface with real-time updates
echo    Multi-agent coordination + System monitoring
echo    Task management + Knowledge base integration
echo.
echo 3. [VIEW-LOGS] View Live Log Files
echo    Watch real-time DuckBot logs
echo    Monitor ecosystem performance and errors
echo.
echo 4. [STATUS] Quick System Status
echo    Integration health checks + Service status
echo    Port availability + Process monitoring
echo.
echo S. [STOP] Stop All DuckBot Processes
echo    Clean shutdown + Process cleanup
echo.
echo Q. [QUIT] Exit Launcher
echo.
set /p choice="[ULTIMATE PROMPT] Enter your choice: "

if /i "%choice%"=="1" goto ultimate_complete_mode
if /i "%choice%"=="2" goto enhanced_webui_mode  
if /i "%choice%"=="3" goto view_logs
if /i "%choice%"=="4" goto system_status
if /i "%choice%"=="S" goto stop_processes
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto main_menu

:ultimate_complete_mode
cls
echo.
echo ================================================================================
echo  DUCKBOT v3.1.0+ ULTIMATE COMPLETE MODE
echo ================================================================================
echo.
echo LAUNCHING: Complete Ultimate Integration Experience
echo.

REM Pre-flight checks
call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

call :check_system_requirements

echo.
echo ✅ All pre-flight checks passed!
echo.
echo IMPORTANT: DuckBot will now start and show logs in this console window.
echo.
echo • The console will stay open and show live activity
echo • Web interface will be available at: http://127.0.0.1:8787  
echo • Press Ctrl+C to stop DuckBot when you're done
echo • All activity is also logged to the logs/ directory
echo.
echo Starting in 5 seconds... (Press Ctrl+C now to cancel)
timeout /t 5

echo.
echo ================================================================================
echo  DUCKBOT ECOSYSTEM STARTING - LIVE LOG OUTPUT
echo ================================================================================
echo.
echo [STARTUP] Launching main ecosystem orchestrator...
echo [INFO] This console will show live logs and stay open
echo [INFO] DuckBot services starting in background...
echo.

REM Start with proper console output and logging
python start_ecosystem.py

REM Always pause after Python exits (success or failure)
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo ================================================================================
echo  DUCKBOT ECOSYSTEM HAS STOPPED
echo ================================================================================
echo.
if %EXIT_CODE% equ 0 (
    echo [STATUS] Normal shutdown - DuckBot stopped cleanly
) else (
    echo [STATUS] Exit with code %EXIT_CODE% - Check logs for details
    echo [LOGS] Check logs/ecosystem_errors.log for error details
    echo [LOGS] Check logs/ecosystem_main.log for full activity log
)
echo.
echo [INFO] All logs saved to logs/ directory
echo [INFO] You can view detailed logs using option 3 from main menu
echo.
echo Press any key to return to the main menu...
pause >nul
goto main_menu

:enhanced_webui_mode
cls
echo.
echo ================================================================================
echo  ENHANCED WEBUI DASHBOARD v3.1.0+
echo ================================================================================
echo.
echo LAUNCHING: Enhanced WebUI with Real-Time Features
echo.

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

echo Starting Enhanced WebUI with all integrations...
echo.
echo • Web interface will be available at: http://127.0.0.1:8787
echo • Press Ctrl+C to stop the WebUI
echo • This console will show live logs
echo.

python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

echo.
echo Enhanced WebUI session ended with exit code: %ERRORLEVEL%
echo Press any key to return to the main menu...
pause >nul
goto main_menu

:view_logs
cls
echo.
echo ================================================================================
echo  DUCKBOT LIVE LOGS VIEWER
echo ================================================================================
echo.
echo Available log files:
echo.
if exist "logs\ecosystem_main.log" (
    for %%I in ("logs\ecosystem_main.log") do echo • Main Log: ecosystem_main.log (%%~zI bytes)
)
if exist "logs\ecosystem_errors.log" (
    for %%I in ("logs\ecosystem_errors.log") do echo • Error Log: ecosystem_errors.log (%%~zI bytes)
)
if exist "logs\ecosystem_performance.log" (
    for %%I in ("logs\ecosystem_performance.log") do echo • Performance Log: ecosystem_performance.log (%%~zI bytes)
)
echo.
echo Choose log to view:
echo.
echo 1. Main Activity Log (most recent 50 lines)
echo 2. Error Log (most recent 50 lines) 
echo 3. Performance Log (most recent 50 lines)
echo 4. All Recent Activity (last 20 lines each)
echo B. Back to main menu
echo.
set /p logchoice="Enter choice: "

if /i "%logchoice%"=="1" goto view_main_log
if /i "%logchoice%"=="2" goto view_error_log
if /i "%logchoice%"=="3" goto view_perf_log
if /i "%logchoice%"=="4" goto view_all_logs
if /i "%logchoice%"=="B" goto main_menu
if /i "%logchoice%"=="b" goto main_menu

goto view_logs

:view_main_log
cls
echo.
echo === MAIN ACTIVITY LOG (Last 50 lines) ===
echo.
if exist "logs\ecosystem_main.log" (
    powershell "Get-Content 'logs\ecosystem_main.log' | Select-Object -Last 50"
) else (
    echo No main log file found
)
echo.
echo Press any key to return to logs menu...
pause >nul
goto view_logs

:view_error_log
cls
echo.
echo === ERROR LOG (Last 50 lines) ===
echo.
if exist "logs\ecosystem_errors.log" (
    powershell "Get-Content 'logs\ecosystem_errors.log' | Select-Object -Last 50"
) else (
    echo No error log file found
)
echo.
echo Press any key to return to logs menu...
pause >nul
goto view_logs

:view_perf_log
cls
echo.
echo === PERFORMANCE LOG (Last 50 lines) ===
echo.
if exist "logs\ecosystem_performance.log" (
    powershell "Get-Content 'logs\ecosystem_performance.log' | Select-Object -Last 50"
) else (
    echo No performance log file found
)
echo.
echo Press any key to return to logs menu...
pause >nul
goto view_logs

:view_all_logs
cls
echo.
echo === ALL RECENT ACTIVITY ===
echo.
echo --- MAIN LOG (Last 20 lines) ---
if exist "logs\ecosystem_main.log" (
    powershell "Get-Content 'logs\ecosystem_main.log' | Select-Object -Last 20"
) else (
    echo No main log found
)
echo.
echo --- ERROR LOG (Last 20 lines) ---
if exist "logs\ecosystem_errors.log" (
    powershell "Get-Content 'logs\ecosystem_errors.log' | Select-Object -Last 20"
) else (
    echo No error log found
)
echo.
echo --- PERFORMANCE LOG (Last 20 lines) ---  
if exist "logs\ecosystem_performance.log" (
    powershell "Get-Content 'logs\ecosystem_performance.log' | Select-Object -Last 20"
) else (
    echo No performance log found
)
echo.
echo Press any key to return to logs menu...
pause >nul
goto view_logs

:system_status
cls
echo.
echo ================================================================================
echo  SYSTEM STATUS v3.1.0+
echo ================================================================================
echo.

call :check_python_ultimate
if %errorlevel% neq 0 goto main_menu

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
import importlib, subprocess
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
echo LOG FILES STATUS:
if exist "logs" (
    echo Log directory: logs/
    for %%F in (logs\*.log) do (
        for %%I in ("%%F") do echo   %%~nxF: %%~zI bytes
    )
) else (
    echo Log directory not found
)

echo.
pause
goto main_menu

:stop_processes
cls
echo.
echo ================================================================================
echo  STOPPING DUCKBOT PROCESSES
echo ================================================================================
echo.

echo Stopping all Python processes (this will stop DuckBot)...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo.
echo Checking if processes stopped...
timeout /t 2 >nul
tasklist | findstr /i python >nul
if %errorlevel% equ 0 (
    echo Some Python processes may still be running:
    tasklist | findstr /i python
) else (
    echo ✅ All Python processes stopped
)

echo.
echo DuckBot should now be stopped.
pause
goto main_menu

:check_python_ultimate
echo Checking Python installation for Ultimate mode...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Python 3.8+ is required for Ultimate DuckBot
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python -c "import sys; print(f'Python version: {sys.version}'); exit(0 if sys.version_info >= (3, 8) else 1)" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.8+ required!
    echo Please upgrade your Python installation
    pause
    exit /b 1
)

echo ✅ Python installation verified for Ultimate mode
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
" 2>&1
exit /b 0

:exit
cls
echo.
echo ================================================================================
echo  GOODBYE FROM DUCKBOT v3.1.0+ ULTIMATE ENHANCED!
echo ================================================================================
echo.
echo Thanks for using DuckBot Ultimate Enhanced Edition!
echo.
echo IMPORTANT: If DuckBot is still running in background, it will continue
echo running until you stop it using option S or close all Python processes.
echo.
echo Web interface (if running): http://127.0.0.1:8787
echo Log files location: logs/
echo.
echo Have a great day with your Ultimate AI companion!
timeout /t 5 >nul
exit /b 0