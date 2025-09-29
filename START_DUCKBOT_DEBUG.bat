@echo off
REM DuckBot Qwen3-Omni Debug Launcher - Shows what's happening
REM Slower startup with pauses to see what's happening

echo.
echo ================================================================================
echo  DUCKBOT DEBUG LAUNCHER - STEP BY STEP
echo ================================================================================
echo.
echo This launcher will show you exactly what's happening...
echo.

REM Change to project root
cd /d "%~dp0"

REM Step 1: Check Python
echo [STEP 1] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://python.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Step 2: Check Node.js
echo [STEP 2] Checking Node.js installation...
node --version
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 16+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js is installed
echo.

REM Step 3: Check Qwen3-Omni-UI directory
echo [STEP 3] Checking Qwen3-Omni-UI directory...
if not exist "qwen3-omni-ui" (
    echo [ERROR] Qwen3-Omni-UI directory not found!
    echo Make sure you cloned the repository properly.
    echo.
    pause
    exit /b 1
)
echo [OK] Qwen3-Omni-UI directory exists
echo.

REM Step 4: Check Python dependencies
echo [STEP 4] Checking Python dependencies...
python -c "import transformers" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Transformers not installed. Installing...
    pip install transformers>=4.40.0
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install transformers!
        pause
        exit /b 1
    )
)

python -c "import torch" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] PyTorch not installed. Installing...
    pip install torch torchvision torchaudio
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyTorch!
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies are ready
echo.

REM Step 5: Check if core files exist
echo [STEP 5] Checking core DuckBot files...
if not exist "duckbot\core\qwen3_omni_integration.py" (
    echo [ERROR] Qwen3-Omni integration file not found!
    echo Make sure the DuckBot core files are properly set up.
    pause
    exit /b 1
)
echo [OK] Core DuckBot files exist
echo.

REM Step 6: Start Qwen3-Omni AI Brain
echo [STEP 6] Starting Qwen3-Omni AI Brain...
echo This will open in a new window. Keep it open!
echo.
pause

echo @echo off > temp_qwen3_start.bat
echo cd /d "%~dp0" >> temp_qwen3_start.bat
echo echo Starting Qwen3-Omni AI Brain... >> temp_qwen3_start.bat
echo python -c "import asyncio; import sys; import os; sys.path.append(os.getcwd()); from duckbot.core.qwen3_omni_integration import qwen3_omni_integration; from duckbot.integrations.qwen3_voice_assistant import qwen3_voice_assistant; asyncio.run(qwen3_omni_integration.load_model())" >> temp_qwen3_start.bat
echo pause >> temp_qwen3_start.bat

start "Qwen3-Omni AI Brain" temp_qwen3_start.bat

echo [INFO] Qwen3-Omni AI Brain started in new window
echo.
echo [STEP 7] Waiting for AI Brain to initialize (30 seconds)...
echo Watch the other window for progress...
timeout /t 30 /nobreak
echo.

REM Step 8: Start DuckBot Services
echo [STEP 8] Starting DuckBot Services...
echo This will open another window. Keep it open too!
echo.
pause

echo @echo off > temp_services_start.bat
echo cd /d "%~dp0" >> temp_services_start.bat
echo echo Starting DuckBot Services... >> temp_services_start.bat
echo python -c "import asyncio; import sys; import os; sys.path.append(os.getcwd()); from duckbot.core.service_manager import UnifiedServiceManager; asyncio.run(UnifiedServiceManager().start_all_services())" >> temp_services_start.bat
echo pause >> temp_services_start.bat

start "DuckBot Services" temp_services_start.bat

echo [INFO] DuckBot Services started in new window
echo.
echo [STEP 9] Waiting for services to synchronize (10 seconds)...
timeout /t 10 /nobreak
echo.

REM Step 10: Start WebSocket Services
echo [STEP 10] Starting WebSocket Services...
if exist "simple_websocket_server.py" (
    start "WebSocket Server" python simple_websocket_server.py
    echo [OK] WebSocket Server started
)

if exist "start_mcp_server.py" (
    start "MCP Server" python start_mcp_server.py
    echo [OK] MCP Server started
)
echo.

REM Step 11: Setup UI
echo [STEP 11] Setting up Qwen3-Omni-UI...
cd qwen3-omni-ui

if not exist "node_modules" (
    echo [INFO] Installing UI dependencies (this may take a while)...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install UI dependencies!
        cd ..
        pause
        exit /b 1
    )
)

if not exist ".env.local" (
    echo [INFO] Creating .env.local file...
    echo GEMINI_API_KEY=your_gemini_api_key_here > .env.local
    echo QWEN3_OMNI_BRAIN_URL=http://localhost:8000 >> .env.local
    echo QWEN3_OMNI_WS_URL=ws://localhost:8001 >> .env.local
    echo Please edit .env.local and add your API key if needed.
)
echo.

REM Step 12: Start UI
echo [STEP 12] Starting Qwen3-Omni-UI...
echo This will open the web interface in your browser.
echo.
pause

call npm run dev

echo.
echo [DONE] DuckBot Qwen3-Omni integration complete!
echo.
echo Keep all windows open for full functionality:
echo - Qwen3-Omni AI Brain window
echo - DuckBot Services window
echo - WebSocket/MCP Server windows
echo - Browser with Qwen3-Omni-UI
echo.
pause