@echo off
REM DuckBot Qwen3-Omni-UI Launcher with Full AI Brain Integration
REM Complete AI-powered desktop interface with Qwen3-Omni as main brain

echo.
echo ================================================================================
echo  DUCKBOT QWEN3-OMNI-UI LAUNCHER - FULL AI INTEGRATION
echo ================================================================================
echo.
echo Starting complete Qwen3-Omni-UI with AI Brain Integration...
echo.
echo Features:
echo   [QWEN3-OMNI BRAIN] Advanced multimodal AI with Flash Attention 2
echo   [VOICE ASSISTANT] Native Qwen3-Omni voice capabilities
echo   [FULL INTEGRATION] Complete DuckBot ecosystem under Qwen3-Omni control
echo   [AUTOMATIC START] Qwen3-Omni server auto-starts as main brain
echo   [MULTI-PROVIDER] LM Studio, Ollama, OpenRouter fallback support
echo   [REAL-TIME] Live WebSocket communication and monitoring
echo   [ADVANCED UI] Sleek interface with full AI control
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://python.org/
    echo.
    timeout /t 3 >nul
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 16+ from https://nodejs.org/
    echo.
    timeout /t 3 >nul
    exit /b 1
)

REM Check if Qwen3-Omni-UI directory exists
if not exist "qwen3-omni-ui" (
    echo [ERROR] Qwen3-Omni-UI directory not found!
    echo Please ensure the Qwen3-Omni-UI is properly installed.
    echo.
    timeout /t 3 >nul
    exit /b 1
)

REM Change to project root
cd /d "%~dp0"

REM Check for Qwen3-Omni dependencies
echo [INFO] Checking Qwen3-Omni dependencies...

python -c "import transformers" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing transformers for Qwen3-Omni...
    pip install transformers>=4.40.0
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install transformers!
        echo Please check your internet connection and try again.
        echo.
        timeout /t 3 >nul
        exit /b 1
    )
)

python -c "import torch" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing PyTorch for Qwen3-Omni...
    pip install torch torchvision torchaudio
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyTorch!
        echo Please check your internet connection and try again.
        echo.
        timeout /t 3 >nul
        exit /b 1
    )
)

REM Start Qwen3-Omni AI Brain Server (Main Brain)
echo [INFO] Starting Qwen3-Omni AI Brain Server...
start "Qwen3-Omni AI Brain" /MIN python -c "
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from duckbot.core.qwen3_omni_integration import qwen3_omni_integration
from duckbot.integrations.qwen3_voice_assistant import qwen3_voice_assistant

async def start_qwen3_brain():
    try:
        print('Loading Qwen3-Omni model with Flash Attention 2...')
        await qwen3_omni_integration.load_model()
        print('Qwen3-Omni model loaded successfully!')

        print('Starting Qwen3-Omni Voice Assistant...')
        await qwen3_voice_assistant.start_interactive_mode()
        print('Qwen3-Omni Voice Assistant started!')

        print('Qwen3-Omni AI Brain is ready!')
        print('Say \"hey duckbot\" to activate voice assistant')

        # Keep the service running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f'Error starting Qwen3-Omni AI Brain: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(start_qwen3_brain())
"

REM Wait for Qwen3-Omni AI Brain to initialize
echo [INFO] Waiting 15 seconds for Qwen3-Omni AI Brain to initialize...
timeout /t 15 /nobreak >nul
echo [INFO] Qwen3-Omni AI Brain should now be ready.

REM Start Core DuckBot Services
echo [INFO] Starting Core DuckBot Services...
start "DuckBot Service Manager" /MIN python -c "
import asyncio
import sys
import os
sys.path.append(os.getcwd())

from duckbot.core.service_manager import UnifiedServiceManager

async def start_services():
    try:
        manager = UnifiedServiceManager()
        await manager.start_all_services()
        print('All DuckBot services started successfully!')
    except Exception as e:
        print(f'Error starting services: {e}')

if __name__ == '__main__':
    asyncio.run(start_services())
"

REM Start WebSocket Services
echo [INFO] Starting WebSocket Services...
start "DuckBot WebSocket Server" /MIN python simple_websocket_server.py
start "DuckBot MCP Server" /MIN python start_mcp_server.py

REM Wait for services to initialize
echo [INFO] Waiting 8 seconds for services to synchronize...
timeout /t 8 /nobreak >nul

REM Change to Qwen3-Omni-UI directory
cd /d "%~dp0qwen3-omni-ui"

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing Qwen3-Omni-UI dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Qwen3-Omni-UI dependencies!
        echo Please check your internet connection and try again.
        echo.
        timeout /t 3 >nul
        exit /b 1
    )
)

REM Check for .env.local file for Qwen3-Omni-UI
if not exist ".env.local" (
    echo [WARN] .env.local file not found. Creating template...
    echo GEMINI_API_KEY=your_gemini_api_key_here > .env.local
    echo QWEN3_OMNI_BRAIN_URL=http://localhost:8000 >> .env.local
    echo QWEN3_OMNI_WS_URL=ws://localhost:8001 >> .env.local
    echo Please edit .env.local file and add your GEMINI_API_KEY
    echo.
)

REM Start the Qwen3-Omni-UI app
echo [INFO] Starting Qwen3-Omni-UI with Full AI Integration...
call npm run dev
echo.
echo [INFO] Qwen3-Omni-UI with Full AI Integration started!
echo [INFO] Qwen3-Omni AI Brain is running in background
echo [INFO] Voice Assistant: Say "hey duckbot" to activate
echo [INFO] All DuckBot services are synchronized with Qwen3-Omni
echo [INFO] Check for the application window.
echo.
timeout /t 3 >nul