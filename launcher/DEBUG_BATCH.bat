@echo off
echo DEBUG: Batch file starting
chcp 65001 >nul
echo DEBUG: Code page set
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo DEBUG: Environment variables set
title DuckBot Debug Test
echo DEBUG: Title set
cd /d "%~dp0"
echo DEBUG: Directory changed to %CD%

echo DEBUG: Setting version variables
set "DUCKBOT_VERSION=3.1.0+"
set "BUILD_DATE=2025-09-09"
set "BUILD_STATUS=ULTIMATE-ENHANCED-READY"
echo DEBUG: Version variables set

echo DEBUG: About to show menu
goto main_menu

:main_menu
echo DEBUG: Reached main_menu label
cls
echo.
echo ================================================================================
echo  DUCKBOT DEBUG TEST - SIMPLIFIED MENU
echo ================================================================================
echo.
echo Current Directory: %CD%
echo Python Version Check:
python --version 2>&1
echo.
echo MENU OPTIONS:
echo.
echo 1. Test Ultimate Mode
echo 2. Test System Status
echo Q. Quit
echo.
set /p choice="Enter your choice: "

echo DEBUG: User entered choice: [%choice%]

if /i "%choice%"=="1" goto test_ultimate
if /i "%choice%"=="2" goto test_status
if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo Invalid choice: %choice%
pause
goto main_menu

:test_ultimate
echo DEBUG: Reached test_ultimate
echo Testing Ultimate Mode functionality...
echo.
echo Python test:
python -c "print('Python is working')"
echo.
echo Starting ecosystem test:
timeout 3 python start_ecosystem.py
echo.
echo Test completed.
pause
goto main_menu

:test_status
echo DEBUG: Reached test_status
echo System Status:
echo Current Directory: %CD%
echo Python: 
python --version
echo.
echo Files:
if exist start_ecosystem.py (echo start_ecosystem.py: EXISTS) else (echo start_ecosystem.py: MISSING)
if exist duckbot (echo duckbot directory: EXISTS) else (echo duckbot directory: MISSING)
echo.
pause
goto main_menu

:exit
echo DEBUG: Reached exit
echo Exiting debug batch file
exit /b 0