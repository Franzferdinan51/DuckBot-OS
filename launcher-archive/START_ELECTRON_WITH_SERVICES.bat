@echo off
REM DuckBot Electron Launcher with Services
REM Starts WebSocket services and Electron launcher together

echo.
echo ================================================================================
echo  DUCKBOT ELECTRON LAUNCHER WITH SERVICES
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://python.org/
    echo.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js 16+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM Check if websockets is installed
echo [INFO] Checking dependencies...
python -c "import websockets" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing websockets dependency...
    pip install websockets
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install websockets!
        echo.
        pause
        exit /b 1
    )
)

REM Start WebSocket services in background
echo [INFO] Starting WebSocket services...
start "DuckBot WebSocket Server" /MIN python simple_websocket_server.py

REM Wait a moment for services to start
timeout /t 3 /nobreak >nul

REM Check if services are running
echo [INFO] Checking service status...
timeout /t 2 /nobreak >nul

REM Start Electron launcher
echo [INFO] Starting Electron launcher...
echo.

REM Change to electron-launcher directory
if exist "electron-launcher" (
    cd /d electron-launcher

    REM Check if node_modules exists
    if not exist "node_modules" (
        echo [INFO] Installing Electron dependencies...
        call npm install
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install Electron dependencies!
            echo.
            pause
            exit /b 1
        )
    )

    REM Start Electron app
    call npm start
) else (
    echo [ERROR] electron-launcher directory not found!
    echo Please ensure the launcher files are properly installed.
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Electron launcher closed.
echo [INFO] WebSocket services are still running.
echo.
pause