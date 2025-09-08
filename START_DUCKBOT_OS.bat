@echo off
title DuckBot OS - Complete AI Management Console
color 0E

echo.
echo ========================================
echo  🦆 DuckBot OS - Complete Console
echo ========================================
echo.
echo Starting the new DuckBot OS interface...
echo This replaces the old WebUI with a complete
echo desktop-style AI management console.
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ first
    pause
    exit /b 1
)

:: Check if we're in the right directory
if not exist "duckbot\webui.py" (
    echo ERROR: DuckBot files not found
    echo Please run this from the DuckBot root directory
    pause
    exit /b 1
)

echo Starting DuckBot OS WebUI server...
echo The new interface includes:
echo  • Complete AI Chat Integration
echo  • Task Runner with all AI types
echo  • Service Management Console
echo  • Cost Analytics Dashboard  
echo  • Model Management Interface
echo  • Queue and RAG Management
echo  • Voice and Image Generation
echo  • Action Logs and Monitoring
echo  • File Manager and Code Editor
echo  • 3D Avatar Assistant
echo.

:: Start the WebUI with DuckBot OS
python -m duckbot.webui

echo.
echo DuckBot OS server stopped.
echo.
echo Note: You can access the classic WebUI at /classic
pause
