@echo off
REM ==============================================================================
REM  🦆 DUCKBOT SIMPLE LAUNCHER v4.2
REM  Clean, working launcher for DuckBot modes
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - Simple Launcher
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0.."

REM Check Python availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

:main_menu
cls
echo.
echo ================================================================================
echo  🦆 DUCKBOT v4.2 SIMPLE LAUNCHER
echo ================================================================================
echo.
echo  1. Local-Only Mode (Privacy First)
echo  2. Full Ecosystem Mode
echo  3. WebUI Only
echo  4. AI Ecosystem Manager
echo  5. Exit
echo.
echo ================================================================================
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto local_only
if "%choice%"=="2" goto full_ecosystem
if "%choice%"=="3" goto webui_only
if "%choice%"=="4" goto ai_manager
if "%choice%"=="5" goto exit
goto main_menu

:local_only
cls
echo Starting DuckBot in Local-Only Mode...
echo This will use only your local AI models (LM Studio)
echo.
python START_LOCAL_ONLY.bat
goto main_menu

:full_ecosystem
cls
echo Starting Full DuckBot Ecosystem...
echo This will start all services including WebUI and AI management
echo.
python core_ai/start_ai_ecosystem.py
goto main_menu

:webui_only
cls
echo Starting WebUI Only...
echo This will start just the web interface
echo.
python -m duckbot.enhanced_webui
goto main_menu

:ai_manager
cls
echo Starting AI Ecosystem Manager...
echo This will start the AI-powered system management
echo.
python ai_ecosystem_manager.py
goto main_menu

:exit
cls
echo Thank you for using DuckBot!
echo.
pause
exit

REM Error handling for invalid choices
goto main_menu