@echo off
title DuckBot v3.0.4 AI-Enhanced Ecosystem
color 0A
cls

echo.
echo ===============================================
echo  [DUCKBOT] DuckBot v3.0.4 AI-Enhanced Ecosystem
echo ===============================================
echo  Starting AI-managed crypto ecosystem...
echo  This window will remain open for monitoring
echo ===============================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Show current directory
echo [INFO] Working Directory: %cd%
echo.

:: Check if AI ecosystem manager exists
if not exist "start_ai_ecosystem.py" (
    echo [ERROR] start_ai_ecosystem.py not found!
    echo Make sure you're running this from the DuckBot directory.
    echo.
    pause
    exit /b 1
)

echo [STARTING] DuckBot AI-Enhanced Ecosystem...
echo [WARNING] First run may take longer due to dependency installation
echo [INFO] Press Ctrl+C to stop the ecosystem
echo.

:: Start the AI ecosystem with error handling
python start_ai_ecosystem.py
set exit_code=%errorlevel%

echo.
echo ===============================================
if %exit_code% equ 0 (
    echo [SUCCESS] DuckBot ecosystem shut down normally
) else (
    echo [ERROR] DuckBot ecosystem stopped with errors
    echo Exit code: %exit_code%
)
echo ===============================================
echo.

:: Keep window open for user to see results
echo Press any key to close this window...
pause >nul