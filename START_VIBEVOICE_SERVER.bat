@echo off
REM ==============================================================================
REM  🔊 VIBEVOICE TTS SERVER STARTUP SCRIPT v4.2
REM  Advanced Text-to-Speech Server for DuckBot Integration
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title VibeVoice TTS Server - DuckBot Integration
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "VIBEVOICE_VERSION=1.0.0"
set "BUILD_DATE=2025-09-17"

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

echo.
echo ================================================================================
echo  🔊 VIBEVOICE TTS SERVER v%VIBEVOICE_VERSION%
echo ================================================================================
echo    Advanced Text-to-Speech Server for DuckBot Integration
echo    [BUILD] %BUILD_DATE% - Enhanced Edition
echo ================================================================================
echo.

echo 🚀 LAUNCHING: VibeVoice TTS Server
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto :eof

call :install_dependencies_if_needed
if errorlevel 1 goto :eof

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo.
echo 📋 STARTUP INFORMATION:
echo   - Host: 127.0.0.1 (localhost)
echo   - Port: 8000
echo   - API Endpoint: http://localhost:8000/tts
echo   - Health Check: http://localhost:8000/health
echo   - Web Interface: http://localhost:8000
echo   - Log file: logs/vibevoice.log
echo.

echo 🎯 FEATURES INCLUDED:
echo   - Microsoft Edge TTS (online voices)
echo   - pyttsx3 (offline TTS engine)
echo   - Coqui TTS (advanced neural TTS)
echo   - Multiple voice options and languages
echo   - REST API for external integration
echo   - Real-time voice synthesis
echo.

REM Check if port 8000 is already in use
echo [CHECK] Checking port availability...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 3 >nul
    netstat -ano | findstr :8000 | findstr LISTENING >nul
    if %errorlevel% equ 0 (
        echo [ERROR] Could not free port 8000. Please stop the service using it.
        pause
        exit /b 1
    )
)

echo [LAUNCHING] Starting VibeVoice TTS Server...
echo       Press Ctrl+C to stop the server
echo.

REM Start the server with logging
start "VibeVoice TTS Server" %PY_CMD% start_vibevoice_server.py > logs\vibevoice.log 2>&1

REM Wait a moment and check if it started successfully
timeout /t 5 >nul
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] VibeVoice TTS Server started successfully!
    echo [INFO] Server is running at: http://localhost:8000
    echo [INFO] API documentation available at: http://localhost:8000/docs
    echo.
    echo 🔍 QUICK TEST:
    echo   You can test the server by opening http://localhost:8000 in your browser
    echo   Or use curl: curl http://localhost:8000/health
    echo.
    echo 📋 LOGS: Service logs are being written to logs\vibevoice.log
    echo 💡 STOP: Press Ctrl+C in the server window to stop the service
) else (
    echo [ERROR] Failed to start VibeVoice TTS Server!
    echo [DEBUG] Check logs\vibevoice.log for error details
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo   1. Ensure Python 3.8+ is installed and in PATH
    echo   2. Check if port 8000 is blocked by firewall
    echo   3. Verify dependencies: pip install edge-tts pyttsx3 coqui-tts
    echo.
)

echo.
pause
goto :eof

REM =============================================================================
REM SUPPORT FUNCTIONS
REM ==============================================================================

:check_python
echo 🐍 Checking Python installation...
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    echo 📝 During installation, make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ Python installation verified
exit /b 0

:install_dependencies_if_needed
echo 📦 Checking dependencies...
%PY_CMD% -c "import edge_tts, pyttsx3, fastapi, uvicorn, aiofiles, soundfile" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing required dependencies...
    %PY_CMD% -m pip install edge-tts pyttsx3 fastapi uvicorn aiofiles soundfile pydub
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        echo 💡 Try manually: pip install edge-tts pyttsx3 fastapi uvicorn aiofiles soundfile pydub
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ All dependencies are available
)
exit /b 0
