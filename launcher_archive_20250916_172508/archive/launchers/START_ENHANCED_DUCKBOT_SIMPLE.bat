@echo off
REM DuckBot Simple Fixed Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Simple Fixed Launcher
color 0A

REM Change to script directory
cd /d "%~dp0"

:main_menu
cls
echo.
echo ================================================================================
echo  DUCKBOT v3.1.0+ SIMPLE FIXED LAUNCHER
echo ================================================================================
echo.
echo Current Directory: %CD%
echo.
echo MAIN OPTIONS:
echo.
echo 1. [ULTIMATE] Start Ultimate Mode (ecosystem orchestrator)
echo 2. [WEBUI] Enhanced WebUI Dashboard  
echo 3. [STATUS] System Status Check
echo 4. [TEST] Test Python and Dependencies
echo Q. [QUIT] Exit
echo.
set /p choice="Enter your choice (1-4 or Q): "

if /i "%choice%"=="1" goto ultimate_mode
if /i "%choice%"=="2" goto webui_mode
if /i "%choice%"=="3" goto status_check
if /i "%choice%"=="4" goto test_system
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto main_menu

:ultimate_mode
cls
echo.
echo ================================================================================
echo  ULTIMATE MODE - ECOSYSTEM ORCHESTRATOR
echo ================================================================================
echo.

REM Check Python
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found or not working!
    echo.
    pause
    goto main_menu
)

REM Check required file
if not exist "start_ecosystem.py" (
    echo ERROR: start_ecosystem.py not found!
    echo Expected location: %CD%\start_ecosystem.py
    echo.
    dir start_ecosystem.py 2>nul || echo File does not exist
    echo.
    pause
    goto main_menu
)

echo Python OK - Starting ecosystem orchestrator...
echo.
python start_ecosystem.py
echo.
echo Ecosystem orchestrator finished with exit code: %ERRORLEVEL%
pause
goto main_menu

:webui_mode
cls
echo.
echo ================================================================================
echo  ENHANCED WEBUI MODE
echo ================================================================================
echo.

REM Check Python
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    goto main_menu
)

REM Check duckbot directory
if not exist "duckbot" (
    echo ERROR: duckbot directory not found!
    echo Expected location: %CD%\duckbot
    echo.
    pause
    goto main_menu
)

echo Starting Enhanced WebUI...
echo.
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787
echo.
echo WebUI finished with exit code: %ERRORLEVEL%
pause
goto main_menu

:status_check
cls
echo.
echo ================================================================================
echo  SYSTEM STATUS CHECK
echo ================================================================================
echo.

echo BASIC SYSTEM INFO:
echo Current Directory: %CD%
echo.

echo PYTHON CHECK:
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found or not working!
) else (
    echo Python OK
)
echo.

echo FILE CHECK:
if exist "start_ecosystem.py" (
    echo ✓ start_ecosystem.py found
) else (
    echo ✗ start_ecosystem.py missing
)

if exist "duckbot" (
    echo ✓ duckbot directory found
) else (
    echo ✗ duckbot directory missing
)

if exist "requirements.txt" (
    echo ✓ requirements.txt found
) else (
    echo ✗ requirements.txt missing
)
echo.

echo PYTHON MODULES CHECK:
python -c "
try:
    import sys
    print(f'Python version: {sys.version}')
    print('Basic Python working')
except Exception as e:
    print(f'Python error: {e}')
"
echo.

pause
goto main_menu

:test_system
cls
echo.
echo ================================================================================
echo  SYSTEM TEST
echo ================================================================================
echo.

echo Testing basic functionality...
echo.

echo 1. Python test:
python -c "print('Python working correctly')"
echo Exit code: %ERRORLEVEL%
echo.

echo 2. Directory listing:
dir /b | findstr /i "start_ecosystem duckbot requirements"
echo.

echo 3. Import test:
python -c "
import sys, os
print('Python path:', sys.executable)
print('Current dir:', os.getcwd())
try:
    import importlib.util
    if os.path.exists('duckbot'):
        print('duckbot directory exists')
        if os.path.exists('duckbot/__init__.py'):
            print('duckbot appears to be a Python package')
        else:
            print('duckbot missing __init__.py')
    else:
        print('duckbot directory not found')
except Exception as e:
    print('Error:', e)
"
echo.

pause
goto main_menu

:exit
cls
echo.
echo Thanks for using DuckBot Simple Fixed Launcher!
echo.
timeout /t 3 >nul
exit /b 0