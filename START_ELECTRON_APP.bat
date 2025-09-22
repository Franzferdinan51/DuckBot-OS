@echo off
REM DuckBot Electron App Launcher
REM Starts all required services and the Electron app with proper coordination

echo ===========================================
echo DuckBot Electron App Launcher
echo ===========================================

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Kill any existing processes
echo Cleaning up existing processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM electron.exe 2>nul

REM Wait a moment for processes to terminate
timeout /t 2 /nobreak >nul

echo Starting service orchestrator...
start "DuckBot Service Orchestrator" cmd /k "python electron_startup_orchestrator.py"

REM Wait for services to start
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are ready
echo Checking service availability...
:check_services
if exist "duckbot\react-webui\services_config.json" (
    echo Services are ready!
    goto start_electron
) else (
    echo Waiting for services to be ready...
    timeout /t 5 /nobreak >nul
    goto check_services
)

:start_electron
echo Starting Electron app...
cd /d "duckbot\react-webui"

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)

REM Start Electron app
echo Starting Electron app...
start "DuckBot Electron App" cmd /k "npm run electron:dev"

echo ===========================================
echo DuckBot Electron App is starting...
echo ===========================================
echo.
echo Service URLs:
echo - Enhanced WebUI Backend: http://localhost:8787
echo - MCP Server: Check services_config.json for actual port
echo - React Dev Server: http://localhost:3000
echo.
echo Press any key to stop all services...
pause >nul

REM Cleanup
echo Stopping all services...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM electron.exe 2>nul

echo All services stopped.
pause