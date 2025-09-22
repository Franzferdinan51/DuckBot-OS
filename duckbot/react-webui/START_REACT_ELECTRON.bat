@echo off
title DuckBot React + Electron Launcher
color 0A

echo.
echo ================================================================
echo              🤖 DuckBot React + Electron Launcher
echo ================================================================
echo.

cd /d "%~dp0"

echo 🔄 Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js is available

echo 📦 Checking dependencies...
if not exist "node_modules" (
    echo 📥 Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ Dependencies are already installed
)

echo.
echo 🚀 Starting DuckBot React + Electron application...
echo.

:: Check if we want to run in development mode
if "%1"=="--dev" (
    echo 🔄 Development mode selected
    echo 📝 Starting React development server...
    start "React Dev Server" cmd /k npm start

    echo ⏳ Waiting for React server to start...
    timeout /t 5 /nobreak >nul

    echo 🖥️  Starting Electron app...
    npm run electron:start
) else (
    echo 🎯 Using integrated startup script...
    node start-react-electron.js
)

echo.
echo ================================================================
echo 🎉 DuckBot application finished
echo ================================================================
echo.

pause