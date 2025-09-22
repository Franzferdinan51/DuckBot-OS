@echo off
REM ==============================================================================
REM  🧪 DUCKBOT TEST LAUNCHER v4.2
REM  Comprehensive System Testing and Validation
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Test Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🧪 DUCKBOT TEST MODE v4.2
echo ================================================================================
echo.
echo 🧪 TESTING FEATURES:
echo   ✅ Comprehensive system testing
echo   ✅ All features validation and performance benchmarks
echo   ✅ AI routing and model detection
echo   ✅ Health checks and diagnostics
echo.
echo 🚀 RUNNING COMPREHENSIVE SYSTEM TESTS...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Create test results directory
if not exist "test_results" mkdir test_results

echo 🧪 Running comprehensive system tests...
echo    Test results will be saved to test_results/ directory
echo.

REM Check for unified test suite
if exist "tests\unified_test_suite.py" (
    echo [RUNNING] Unified Test Suite...
    python tests\unified_test_suite.py --mode full
    echo.
)

REM Check for feature test
if exist "tests\test_all_features.py" (
    echo [RUNNING] Feature Validation Test...
    python tests\test_all_features.py
    echo.
)

REM Run diagnostic checks
echo [RUNNING] System Diagnostics...
python -c "
import sys, os, platform
import subprocess

print('=== System Information ===')
print(f'OS: {platform.platform()}')
print(f'Python: {sys.version}')
print(f'Working Directory: {os.getcwd()}')

print('\\n=== Python Module Checks ===')
modules_to_check = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('requests', 'Requests'),
    ('psutil', 'PSUtil'),
    ('aiohttp', 'AIOHTTP'),
    ('websockets', 'WebSockets'),
    ('PIL', 'Pillow'),
    ('numpy', 'NumPy'),
]

for module, name in modules_to_check:
    try:
        __import__(module)
        print(f'✅ {name}: Available')
    except ImportError:
        print(f'❌ {name}: Not Available')

print('\\n=== Port Availability ===')
ports_to_check = [8787, 8788, 8789]
import socket
for port in ports_to_check:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    status = 'IN USE' if result == 0 else 'AVAILABLE'
    print(f'Port {port}: {status}')
    sock.close()

print('\\n=== Test Complete ===')
"

echo.
echo 📊 Test results saved to test_results/ directory
echo ✅ System testing completed
pause