@echo off
echo ======================================================================
echo                   OpenWebUI-DuckBot Integration Adapter
echo ======================================================================
echo.
echo This adapter makes DuckBot's AI system compatible with OpenWebUI
echo by providing Ollama-compatible API endpoints that route to DuckBot.
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not available or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if DuckBot WebUI is running
echo [1/4] Checking DuckBot WebUI availability...
curl -s http://localhost:8787/token >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: DuckBot WebUI is not running at localhost:8787
    echo Please start DuckBot WebUI first using:
    echo   - START_ENHANCED_DUCKBOT.bat, or
    echo   - python -m duckbot.webui
    echo.
    echo Press any key to continue anyway (adapter will run in mock mode)
    pause
) else (
    echo [OK] DuckBot WebUI is available at localhost:8787
)

REM Install required dependencies
echo.
echo [2/4] Installing required dependencies...
pip install fastapi uvicorn httpx pydantic

REM Check installation
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed successfully

REM Start the adapter
echo.
echo [3/4] Starting OpenWebUI-DuckBot Adapter...
echo.
echo ======================================================================
echo                           INTEGRATION READY
echo ======================================================================
echo.
echo Configure OpenWebUI to use DuckBot as follows:
echo.
echo   1. Open OpenWebUI Settings
echo   2. Go to Connections/Integrations 
echo   3. Set Ollama API URL to: http://127.0.0.1:11434
echo   4. Save settings and refresh models
echo.
echo Available DuckBot Models:
echo   - duckbot-auto          (Smart AI routing)
echo   - duckbot-code          (Code specialist)
echo   - duckbot-reasoning     (Reasoning expert)  
echo   - duckbot-summary       (Summary generator)
echo   - duckbot-long-form     (Long-form writer)
echo   - duckbot-qwen          (Qwen enhanced)
echo   + Any LM Studio models will also appear
echo.
echo ======================================================================
echo [4/4] Launching adapter server...

python openwebui_duckbot_adapter.py

echo.
echo Adapter stopped. Press any key to exit.
pause