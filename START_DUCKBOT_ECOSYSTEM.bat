@echo off
REM DuckBot Desktop UI Launcher
REM Modern comprehensive desktop interface for DuckBot ecosystem

echo.
echo ================================================================================
echo  DUCKBOT DESKTOP UI LAUNCHER
echo ================================================================================
echo.
echo Starting comprehensive DuckBot desktop interface...
echo.
echo Features:
echo   [DASHBOARD] Complete service management and monitoring
echo   [AI AGENTS] Multi-agent coordination and visualization
echo   [AUTOMATION] Drag-and-drop workflow builder
echo   [COST TRACKING] Real-time cost analytics and optimization
echo   [MONITORING] System metrics and performance tracking
echo   [INTEGRATION] Complete DuckBot ecosystem management
echo   [REAL-TIME] Live updates and WebSocket communication
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 16+ from https://nodejs.org/
    echo.
    timeout /t 3 >nul
    exit /b 1
)

REM Check if Desktop UI directory exists
if not exist "desktop-ui" (
    echo [ERROR] DuckBot Desktop UI directory not found!
    echo Please ensure the DuckBot Desktop UI is properly installed.
    echo.
    timeout /t 3 >nul
    exit /b 1
)

REM Change to Desktop UI directory
cd /d "%~dp0desktop-ui"

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies!
        echo Please check your internet connection and try again.
        echo.
        timeout /t 3 >nul
        exit /b 1
    )
)

REM Check for required API keys
echo [INFO] Checking API key configuration...

if not exist "..\config\startup_config.json" (
    echo [WARN] API keys not configured. Please configure them in the launcher settings.
    echo.
    echo Required API Keys:
    echo   - Gemini API Key (for ByteBot, UI-TARS, Learning System)
    echo   - OpenRouter API Key (for AI-Enhanced modes, Archon)
    echo   - Z.ai API Key (for N8N Workflow Automation)
    echo.
    echo You can configure these in the launcher Settings panel.
    echo.
)

REM Check if modular launcher is available
if exist "..\launcher_main.py" (
    echo [INFO] Modular launcher detected - enhanced integration available
) else (
    echo [INFO] Modular launcher not found - using legacy mode
)

REM Check command line arguments
set START_SERVICES=false
if "%1"=="--with-services" set START_SERVICES=true
if "%1"=="-services" set START_SERVICES=true

REM Start WebSocket services if requested
if "%START_SERVICES%"=="true" (
    echo [INFO] Starting WebSocket services...

    REM Check if websockets is installed
    python -c "import websockets" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] Installing websockets dependency...
        pip install websockets
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install websockets!
            echo.
            timeout /t 3 >nul
            exit /b 1
        )
    )

    REM Start WebSocket services in background
    echo [INFO] Starting WebSocket services for UI...
    cd /d "%~dp0"
    start "DuckBot WebSocket Server" /MIN python simple_websocket_server.py
    start "DuckBot MCP Server" /MIN python start_mcp_server.py
    cd /d "%~dp0desktop-ui"

    REM Wait for services to initialize before launching the UI.
    echo [INFO] Waiting 10 seconds for backend services to start...
    timeout /t 10 /nobreak >nul
    echo [INFO] Services are likely ready. Launching UI.
) else (
    REM Auto-start minimal services for better connectivity
    echo [INFO] Auto-starting minimal DuckBot services for better connectivity...
    cd /d "%~dp0"
    start "DuckBot WebSocket Server" python simple_websocket_server.py
    cd /d "%~dp0desktop-ui"

    REM Wait for services to initialize
    echo [INFO] Waiting 8 seconds for DuckBot services to start...
    timeout /t 8 /nobreak >nul
    echo [INFO] DuckBot services should now be ready.
)

REM Start the Electron app
echo [INFO] Starting DuckBot Desktop UI...
call npm run dev
echo.
echo [INFO] DuckBot Desktop UI started. Check for the application window.
echo.
timeout /t 3 >nul
