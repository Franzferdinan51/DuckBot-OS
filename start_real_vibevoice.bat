@echo off
echo Starting Microsoft VibeVoice Real Server...
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
python -c "import transformers, torch, torchaudio, fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install transformers torch torchaudio fastapi uvicorn soundfile pydub aiofiles aiohttp
)

REM Start the real VibeVoice server
echo Starting Microsoft VibeVoice Server on port 8000...
echo Server will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python vibevoice_server_real.py

pause