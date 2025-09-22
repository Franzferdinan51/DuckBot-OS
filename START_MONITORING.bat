@echo off
REM ==============================================================================
REM  📊 DUCKBOT MONITORING LAUNCHER v4.2
REM  System Monitoring Dashboard with Real-time Metrics
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Monitoring Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  📊 DUCKBOT MONITORING MODE v4.2
echo ================================================================================
echo.
echo 📊 MONITORING FEATURES:
echo   ✅ Real-time system metrics and performance tracking
echo   ✅ Agent status monitoring and resource utilization
echo   ✅ Service health checks and diagnostics
echo   ✅ Performance analytics and reporting
echo.
echo 🚀 LAUNCHING MONITORING DASHBOARD...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if port 8789 is available
echo 🔍 Checking port 8789 availability...
netstat -ano | findstr :8789 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8789 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8789 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 2 >nul
)

echo 📊 Starting System Monitoring Dashboard...
echo    Access URL: http://localhost:8789
echo    Press Ctrl+C to stop when done
echo.

REM Check if monitoring dashboard module exists
python -c "import importlib; importlib.import_module('duckbot.monitoring_dashboard')" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Monitoring dashboard not available, starting basic monitoring...
    python -c "
import time
import psutil
import platform
print('=== DuckBot System Monitor ===')
print(f'OS: {platform.platform()}')
print(f'Python: {platform.python_version()}')
try:
    while True:
        print(f'\\rCPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}% | Disk: {psutil.disk_usage(\".\").percent}%', end='')
        time.sleep(2)
except KeyboardInterrupt:
    print('\\nMonitoring stopped.')
"
) else (
    python -m duckbot.monitoring_dashboard --host 127.0.0.1 --port 8789
)

if errorlevel 1 (
    echo.
    echo ❌ Failed to start monitoring dashboard
    pause
)

echo.
echo ✅ Monitoring session ended
pause