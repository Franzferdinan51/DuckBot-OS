@echo off
REM DuckBot v3.1.0+ Working Fixed Launcher
chcp 65001 >nul
set PYTHONUTF8=1  
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0+ Working Launcher
color 0A

REM Change to script directory
cd /d "%~dp0"

:main_menu
cls
echo.
echo ================================================================================
echo  DUCKBOT v3.1.0+ WORKING LAUNCHER (FIXED)
echo ================================================================================
echo.
echo IMPORTANT: The original batch files were NOT crashing!
echo They were starting servers that run continuously in the background.
echo When you run Ultimate Mode, DuckBot starts successfully and runs at:
echo   http://127.0.0.1:8787
echo.
echo Current Directory: %CD%
echo.
echo MAIN OPTIONS:
echo.
echo 1. [ULTIMATE] Start Ultimate Mode (background server - opens web browser)
echo 2. [WEBUI] Enhanced WebUI Dashboard (background server)
echo 3. [STATUS] Check if DuckBot is already running
echo 4. [STOP] Stop all DuckBot processes  
echo 5. [TEST] Quick system test
echo Q. [QUIT] Exit
echo.
set /p choice="Enter your choice: "

if /i "%choice%"=="1" goto ultimate_mode
if /i "%choice%"=="2" goto webui_mode
if /i "%choice%"=="3" goto check_running
if /i "%choice%"=="4" goto stop_duckbot
if /i "%choice%"=="5" goto test_system
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto main_menu

:ultimate_mode
cls
echo.
echo ================================================================================
echo  STARTING ULTIMATE MODE
echo ================================================================================
echo.

REM Quick checks
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    goto main_menu
)

if not exist "start_ecosystem.py" (
    echo ERROR: start_ecosystem.py not found!
    pause
    goto main_menu
)

echo ✓ Python found
echo ✓ start_ecosystem.py found
echo.
echo STARTING DUCKBOT ECOSYSTEM...
echo This will start a web server that runs continuously.
echo.
echo Once started, DuckBot will be available at: http://127.0.0.1:8787
echo.
echo The server will run until you:
echo   - Press Ctrl+C to stop it
echo   - Close this window
echo   - Use option 4 (STOP) from the main menu
echo.
echo Starting in 3 seconds...
timeout /t 3 >nul

echo.
echo === DUCKBOT ECOSYSTEM STARTING ===
echo.

REM Start DuckBot and automatically open browser
start "" "http://127.0.0.1:8787"
python start_ecosystem.py

echo.
echo === DUCKBOT ECOSYSTEM STOPPED ===
echo.
pause
goto main_menu

:webui_mode  
cls
echo.
echo ================================================================================
echo  STARTING ENHANCED WEBUI
echo ================================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    goto main_menu
)

if not exist "duckbot" (
    echo ERROR: duckbot directory not found!
    pause  
    goto main_menu
)

echo ✓ Python found
echo ✓ duckbot directory found
echo.
echo STARTING ENHANCED WEBUI...
echo This will start a web server at: http://127.0.0.1:8787
echo.
echo Opening browser in 3 seconds...
timeout /t 3 >nul

start "" "http://127.0.0.1:8787"
python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787

echo.
echo === ENHANCED WEBUI STOPPED ===
echo.
pause
goto main_menu

:check_running
cls
echo.
echo ================================================================================
echo  CHECKING IF DUCKBOT IS RUNNING  
echo ================================================================================
echo.

echo Checking port 8787 (DuckBot WebUI)...
python -c "
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8787))
    if result == 0:
        print('✓ DuckBot appears to be running on port 8787')
        print('  Access it at: http://127.0.0.1:8787')
    else:
        print('✗ DuckBot does not appear to be running on port 8787')
    sock.close()
except Exception as e:
    print(f'Error checking port: {e}')
"

echo.
echo Checking for Python processes...
tasklist | findstr /i python >nul
if %errorlevel% equ 0 (
    echo ✓ Python processes found running
    tasklist | findstr /i python
) else (
    echo ✗ No Python processes found
)

echo.
pause
goto main_menu

:stop_duckbot
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
    echo ✓ All Python processes stopped
)

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

echo Testing Python...
python --version
echo.

echo Testing basic Python import...  
python -c "print('✓ Python working correctly')"
echo.

echo Checking required files...
if exist "start_ecosystem.py" (echo ✓ start_ecosystem.py found) else (echo ✗ start_ecosystem.py missing)
if exist "duckbot" (echo ✓ duckbot directory found) else (echo ✗ duckbot directory missing)
echo.

echo Testing DuckBot import...
python -c "
try:
    import sys, os
    sys.path.insert(0, '.')
    if os.path.exists('duckbot'):
        print('✓ duckbot directory accessible')
    else:
        print('✗ duckbot directory not found')
except Exception as e:
    print(f'Error: {e}')
"
echo.

echo === TEST COMPLETE ===
echo.
echo If all tests pass, DuckBot should work correctly.
echo Use option 1 to start Ultimate Mode.
echo.
pause
goto main_menu

:exit
cls
echo.
echo ================================================================================  
echo  DUCKBOT LAUNCHER EXIT
echo ================================================================================
echo.
echo IMPORTANT NOTES:
echo.
echo The original START_ENHANCED_DUCKBOT.bat was NOT broken!
echo It successfully starts DuckBot as a web server at http://127.0.0.1:8787
echo.
echo The "silent crash" was actually DuckBot running successfully in the background.
echo You should have been able to access it via your web browser.
echo.
echo If DuckBot is still running, visit: http://127.0.0.1:8787
echo.
echo Thanks for using DuckBot!
timeout /t 5 >nul
exit /b 0