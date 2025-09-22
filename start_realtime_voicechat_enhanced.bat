@echo off
REM ==============================================================================
REM  🗣️  REALTIME VOICE CHAT STARTUP SCRIPT v4.2
REM  Real-time Voice Conversation with AI Integration
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Realtime Voice Chat - DuckBot Integration
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "VOICECHAT_VERSION=1.0.0"
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
echo  🗣️  REALTIME VOICE CHAT v%VOICECHAT_VERSION%
echo ================================================================================
echo    Real-time Voice Conversation with AI Integration
echo    [BUILD] %BUILD_DATE% - Enhanced Edition
echo ================================================================================
echo.

echo 🚀 LAUNCHING: Realtime Voice Chat Server
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
echo   - Port: 8001
echo   - Web Interface: http://localhost:8001
echo   - WebSocket: ws://localhost:8001/ws/{session_id}
echo   - API Documentation: http://localhost:8001/docs
echo   - Health Check: http://localhost:8001/health
echo   - Log file: logs/voicechat.log
echo.

echo 🎯 FEATURES INCLUDED:
echo   - Real-time voice conversation with AI
echo   - WebSocket-based live communication
echo   - Multiple AI provider support (OpenAI, Anthropic, etc.)
echo   - Session management and conversation history
echo   - Voice activity detection and noise cancellation
echo   - Cross-browser compatibility
echo.

echo 🤖 AI PROVIDER SUPPORT:
echo   - OpenAI (GPT-4, GPT-3.5, etc.)
echo   - Anthropic (Claude 3, Claude 3.5, etc.)
echo   - Google (Gemini Pro, etc.)
echo   - Local models via LM Studio
echo   - Custom AI endpoints
echo.

REM Check if port 8001 is already in use
echo [CHECK] Checking port availability...
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8001 already in use, attempting to free it...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill //F //PID %%i >nul 2>&1
    timeout /t 3 >nul
    netstat -ano | findstr :8001 | findstr LISTENING >nul
    if %errorlevel% equ 0 (
        echo [ERROR] Could not free port 8001. Please stop the service using it.
        pause
        exit /b 1
    )
)

echo [LAUNCHING] Starting Realtime Voice Chat Server...
echo       Press Ctrl+C to stop the server
echo.

REM Start the server with logging
start "Realtime Voice Chat" %PY_CMD% realtime_voicechat.py > logs\voicechat.log 2>&1

REM Wait a moment and check if it started successfully
timeout /t 5 >nul
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] Realtime Voice Chat Server started successfully!
    echo [INFO] Server is running at: http://localhost:8001
    echo [INFO] API documentation available at: http://localhost:8001/docs
    echo [INFO] WebSocket endpoint: ws://localhost:8001/ws/{session_id}
    echo.
    echo 🔍 QUICK TEST:
    echo   You can test the server by opening http://localhost:8001 in your browser
    echo   Or use curl: curl http://localhost:8001/health
    echo.
    echo 🎙️  VOICE CHAT FEATURES:
    echo   - Click "Start Voice Chat" in the web interface
    echo   - Allow microphone access when prompted
    echo   - Speak naturally and AI will respond
    echo   - Supports multiple languages and accents
    echo.
    echo 📋 LOGS: Service logs are being written to logs\voicechat.log
    echo 💡 STOP: Press Ctrl+C in the server window to stop the service
) else (
    echo [ERROR] Failed to start Realtime Voice Chat Server!
    echo [DEBUG] Check logs\voicechat.log for error details
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo   1. Ensure Python 3.8+ is installed and in PATH
    echo   2. Check if port 8001 is blocked by firewall
    echo   3. Verify dependencies: pip install fastapi uvicorn websockets aiohttp aiofiles
    echo   4. Check microphone permissions in your browser
    echo   5. Ensure AI provider API keys are configured
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
%PY_CMD% -c "import fastapi, uvicorn, websockets, aiohttp, aiofiles, json" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing required dependencies...
    %PY_CMD% -m pip install fastapi uvicorn websockets aiohttp aiofiles python-multipart jinja2
    if %errorlevel% neq 0 (
        echo ❌ Failed to install core dependencies
        echo 💡 Try manually: pip install fastapi uvicorn websockets aiohttp aiofiles python-multipart jinja2
        pause
        exit /b 1
    )
    echo ✅ Core dependencies installed successfully
) else (
    echo ✅ All core dependencies are available
)

REM Check for AI provider dependencies
echo 🤖 Checking AI provider dependencies...
%PY_CMD% -c "import openai, anthropic" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing AI provider dependencies (optional)...
    %PY_CMD% -m pip install openai anthropic google-generativeai
    if %errorlevel% neq 0 (
        echo [WARN] Some AI provider dependencies failed to install
        echo [INFO] You can still use the server with configured AI providers
    )
)

REM Check for audio processing dependencies
echo 🔊 Checking audio processing dependencies...
%PY_CMD% -c "import sounddevice, numpy, scipy" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing audio processing dependencies...
    %PY_CMD% -m pip install sounddevice numpy scipy
    if %errorlevel% neq 0 (
        echo [WARN] Audio processing dependencies failed to install
        echo [INFO] Basic audio functionality will still work
    )
)

echo ✅ Dependencies check completed
exit /b 0