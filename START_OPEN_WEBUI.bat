@echo off
REM Open-WebUI with OpenRouter Integration Standalone Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Open-WebUI with OpenRouter Integration
color 0B
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

echo.
echo ===============================================
echo  🌐 OPEN-WEBUI WITH OPENROUTER INTEGRATION
echo ===============================================
echo.
echo 🚀 Starting Open-WebUI with OpenRouter model support...
echo.

REM Check Python
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python installation verified

REM Check Open-WebUI installation
echo 🔍 Checking Open-WebUI installation...
python -c "import open_webui" >nul 2>&1
if errorlevel 1 (
    echo ❌ Open-WebUI not installed!
    echo.
    echo 📦 Installing Open-WebUI...
    pip install open-webui
    if errorlevel 1 (
        echo ❌ Installation failed
        echo 💡 Try: pip install --user open-webui
        pause
        exit /b 1
    )
    echo ✅ Open-WebUI installed successfully!
) else (
    echo ✅ Open-WebUI installation verified
)

REM Setup OpenRouter function
echo 🔌 Setting up OpenRouter function integration...

REM Create functions directory
set "FUNCTIONS_DIR=%USERPROFILE%\.open-webui\functions"
if not exist "%FUNCTIONS_DIR%" (
    echo 📁 Creating functions directory...
    mkdir "%FUNCTIONS_DIR%"
)

REM Copy OpenRouter function if it exists
if exist "function-OpenRouter Integration for OpenWebUI.json" (
    echo 📄 Installing OpenRouter function...
    copy "function-OpenRouter Integration for OpenWebUI.json" "%FUNCTIONS_DIR%\openrouter_integration.json" >nul
    echo ✅ OpenRouter function installed to: %FUNCTIONS_DIR%\openrouter_integration.json
) else (
    echo ⚠️  OpenRouter function file not found
    echo 💡 You can manually add the function through Open-WebUI admin panel
)

REM Check for OpenRouter API key
echo 🔑 Checking OpenRouter API configuration...
set "OPENROUTER_KEY_FOUND="
if exist ".env" (
    findstr /i "OPENROUTER_API_KEY" .env >nul 2>&1
    if not errorlevel 1 (
        echo ✅ OpenRouter API key found in .env file
        set "OPENROUTER_KEY_FOUND=1"
    )
)

if not defined OPENROUTER_KEY_FOUND (
    echo ⚠️  OpenRouter API key not configured
    echo 💡 Configure your OpenRouter API key in Open-WebUI function settings
)

echo.
echo 🌐 Starting Open-WebUI server...
echo ⏳ This may take 30-60 seconds to initialize...
echo.
echo 📋 ACCESS INFORMATION:
echo   🔗 URL: http://localhost:8080
echo   📊 Models: OpenRouter models via function integration
echo   💰 Features: Free model filtering, cost optimization
echo   🔧 Admin: Access function settings through web interface
echo.
echo 💡 FIRST-TIME SETUP:
echo   1. Create admin account on first visit
echo   2. Go to Admin Panel > Functions
echo   3. Configure OpenRouter API key in function settings
echo   4. Enable the OpenRouter integration function
echo.
echo 📝 Press Ctrl+C to stop the server
echo ===============================================
echo.

REM Start Open-WebUI
open-webui serve --port 8080 --host 127.0.0.1

echo.
echo ✅ Open-WebUI server stopped
echo 📝 Thanks for using Open-WebUI with OpenRouter integration!
pause