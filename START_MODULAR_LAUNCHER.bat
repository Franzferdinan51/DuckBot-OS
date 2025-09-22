@echo off
REM ==============================================================================
REM  🚀 DUCKBOT MODULAR LAUNCHER v4.2
REM  Next-generation launcher architecture - replaces monolithic batch file
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Modular Launcher v4.2
color 0A

REM Change to script directory
cd /d "%~dp0"

echo.
echo ================================================================================
echo  🚀 DUCKBOT MODULAR LAUNCHER v4.2
echo ================================================================================
echo.
echo Initializing next-generation launcher architecture...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    echo.
    echo Download Python from: https://python.org
    pause
    exit /b 1
)

REM Verify launcher files exist
if not exist "launcher_main.py" (
    echo ❌ Modular launcher not found!
    echo.
    echo Expected file: launcher_main.py
    echo Please ensure the modular launcher is properly installed.
    pause
    exit /b 1
)

REM Check if required modules directory exists
if not exist "launcher\core" (
    echo ❌ Launcher core modules not found!
    echo.
    echo Expected directory: launcher\core\
    echo Please ensure the modular launcher is properly installed.
    pause
    exit /b 1
)

REM Check if Electron launcher is available
if exist "electron-launcher" (
    echo ℹ️  Electron launcher detected - full UI integration available
) else (
    echo ℹ️  Electron launcher not found - console mode only
)

echo ✅ Environment validation complete
echo 🚀 Starting modular launcher...
echo.

REM Launch the modular system
python launcher_main.py

REM Exit with the same code as the Python script
exit /b %errorlevel%