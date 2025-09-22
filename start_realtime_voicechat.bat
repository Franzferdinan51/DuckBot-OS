@echo off
echo Starting RealtimeVoiceChat Server...
echo =================================

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check for required dependencies
echo Checking dependencies...
python -c "import fastapi, uvicorn, websockets, aiohttp, aiofiles" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install fastapi uvicorn websockets aiohttp aiofiles
)

REM Check for additional dependencies
echo Checking AI provider dependencies...
python -c "import openai, google.generativeai" >nul 2>&1
if errorlevel 1 (
    echo Installing AI provider dependencies...
    pip install openai google-generativeai
)

REM Start the RealtimeVoiceChat server
echo Starting RealtimeVoiceChat Server on port 8001...
echo Web interface will be available at: http://localhost:8001
echo WebSocket endpoint: ws://localhost:8001/ws/{session_id}
echo.
echo Press Ctrl+C to stop the server
echo.

python realtime_voicechat.py

pause