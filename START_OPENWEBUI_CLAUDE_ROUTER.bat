@echo off
REM OpenWebUI + Claude Code Router + OpenRouter Free Models Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title OpenWebUI + Claude Code Router + OpenRouter Free Models
color 0E
cls

cd /d "%~dp0"

echo.
echo ================================================================
echo  🚀 OPENWEBUI + CLAUDE CODE ROUTER + OPENROUTER FREE MODELS
echo ================================================================
echo.
echo 🎯 WHAT THIS DOES:
echo   ✅ Starts Claude Code Router (proxy to OpenRouter)
echo   ✅ Starts OpenWebUI connected to Claude Code Router  
echo   ✅ Access FREE OpenRouter models through OpenWebUI
echo   ✅ Use /model commands to switch between free models
echo.
echo 🆓 FREE MODELS AVAILABLE:
echo   • microsoft/phi-3-mini-128k-instruct:free
echo   • google/gemma-7b-it:free
echo   • meta-llama/llama-3-8b-instruct:free
echo   • mistralai/mistral-7b-instruct:free
echo   • huggingfaceh4/zephyr-7b-beta:free
echo.

echo 🔍 Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python available

REM Check Node.js and npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js/npm not found!
    echo 📥 Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js/npm available

REM Check Claude Code Router
ccr --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Claude Code Router not found!
    echo 📦 Installing Claude Code Router...
    npm install -g @musistudio/claude-code-router
    if errorlevel 1 (
        echo ❌ Installation failed - check npm permissions
        pause
        exit /b 1
    )
    echo ✅ Claude Code Router installed
) else (
    echo ✅ Claude Code Router available
)

REM Check OpenWebUI
pip show open-webui >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenWebUI not found!
    echo 📦 Installing OpenWebUI...
    pip install open-webui
    if errorlevel 1 (
        echo ❌ OpenWebUI installation failed
        pause
        exit /b 1
    )
    echo ✅ OpenWebUI installed
) else (
    echo ✅ OpenWebUI available
)

echo.
echo 🚀 Starting integrated setup...
echo.

REM Run the Python setup script
python setup_openwebui_claude_router.py

if errorlevel 1 (
    echo.
    echo ❌ Setup failed! Check the error messages above.
    echo.
    echo 💡 TROUBLESHOOTING:
    echo   • Make sure you have internet access
    echo   • Check if ports 8080 and 8765 are available
    echo   • Verify OpenRouter API key if using paid models
    echo   • Run as administrator if permission issues
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
pause