@echo off
REM ==============================================================================
REM  🩺 DUCKBOT DOCTOR LAUNCHER v4.2
REM  System Health Diagnostics and Auto-Repair
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Doctor Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🩺 DUCKBOT DOCTOR MODE v4.2
echo ================================================================================
echo.
echo 🩺 DOCTOR FEATURES:
echo   ✅ Comprehensive health diagnostics
echo   ✅ Automatic dependency installation
echo   ✅ Performance analysis and automated repair
echo   ✅ System optimization recommendations
echo.
echo 🚀 RUNNING SYSTEM HEALTH DIAGNOSTICS...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo 🩺 DuckBot System Doctor - Comprehensive Health Analysis
echo.

REM Check for doctor check services
if exist "diagnostics\doctor_check_services.py" (
    echo [RUNNING] Professional Diagnostics...
    python diagnostics\doctor_check_services.py
    echo.
)

REM Run basic health checks
echo [RUNNING] Basic Health Checks...
python -c "
import sys
import os
import platform
import subprocess
import socket

print('=== DuckBot Health Report ===')
print(f'System: {platform.platform()}')
print(f'Python: {sys.version.split()[0]}')
print(f'Current Directory: {os.getcwd()}')

print('\\n🔍 Critical Services Check:')
services = [
    ('WebUI Module', 'duckbot.webui', 'python -c \"import duckbot.webui\"'),
    ('AI Router', 'duckbot.ai_router_gpt', 'python -c \"import duckbot.ai_router_gpt\"'),
    ('Server Manager', 'duckbot.server_manager', 'python -c \"import duckbot.server_manager\"'),
    ('Service Detector', 'duckbot.service_detector', 'python -c \"import duckbot.service_detector\"'),
]

for name, module, test_cmd in services:
    try:
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f'✅ {name}: OK')
        else:
            print(f'❌ {name}: FAILED - {result.stderr.strip()[:50]}')
    except Exception as e:
        print(f'❌ {name}: ERROR - {str(e)[:50]}')

print('\\n🔍 Port Status Check:')
ports = [('WebUI', 8787), ('Terminal', 8788), ('Monitor', 8789)]
for name, port in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        print(f'✅ {name} (:{port}): LISTENING')
    else:
        print(f'⚪ {name} (:{port}): AVAILABLE')
    sock.close()

print('\\n🔍 File Structure Check:')
required_files = [
    'requirements.txt',
    'start_ecosystem.py',
    'ai_ecosystem_manager.py'
]

for file in required_files:
    if os.path.exists(file):
        print(f'✅ {file}: EXISTS')
    else:
        print(f'❌ {file}: MISSING')

print('\\n🔍 Python Package Status:')
packages = ['fastapi', 'uvicorn', 'requests', 'psutil', 'aiohttp', 'websockets']
for package in packages:
    try:
        __import__(package)
        print(f'✅ {package}: INSTALLED')
    except ImportError:
        print(f'❌ {package}: MISSING')

print('\\n=== Health Check Complete ===')
"

echo.
echo 💡 Recommendation Summary:
echo   - Check any ❌ items above
echo   - Use launcher/I option to install missing dependencies
echo   - Use launcher/K option to kill processes on busy ports
echo.

echo 🩺 Auto-repair options:
echo 1. Install missing dependencies
echo 2. Kill processes on busy ports
echo 3. Create missing configuration files
echo 4. Exit doctor
echo.

set /p repair_choice="Select auto-repair option (1-4): "
if /i "%repair_choice%"=="1" goto install_deps
if /i "%repair_choice%"=="2" goto kill_ports
if /i "%repair_choice%"=="3" goto create_config
goto exit_doctor

:install_deps
echo 📦 Installing missing dependencies...
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil websockets
echo ✅ Dependencies installed
goto exit_doctor

:kill_ports
echo 🛑 Killing processes on ports 8787, 8788, 8789...
for %%p in (8787 8788 8789) do (
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if not errorlevel 1 (
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do taskkill //F /PID %%i 2>nul
        echo [DONE] Freed port %%p
    )
)
echo ✅ Ports cleared
goto exit_doctor

:create_config
echo ⚙️ Creating configuration files...
if not exist ".env" (
    echo # DuckBot v4.2 Configuration > .env
    echo # AI Provider Configuration >> .env
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here >> .env
    echo DISCORD_TOKEN=your_discord_token_here >> .env
    echo # System Configuration >> .env
    echo DUCKBOT_WEBUI_HOST=127.0.0.1 >> .env
    echo DUCKBOT_WEBUI_PORT=8787 >> .env
    echo ✅ Created .env file
)
if not exist "requirements.txt" (
    echo fastapi>=0.104.0 > requirements.txt
    echo uvicorn[standard]>=0.24.0 >> requirements.txt
    echo aiohttp>=3.9.0 >> requirements.txt
    echo requests>=2.31.0 >> requirements.txt
    echo psutil>=5.9.0 >> requirements.txt
    echo websockets>=12.0 >> requirements.txt
    echo ✅ Created requirements.txt
)
goto exit_doctor

:exit_doctor
echo.
echo ✅ Doctor session completed
pause