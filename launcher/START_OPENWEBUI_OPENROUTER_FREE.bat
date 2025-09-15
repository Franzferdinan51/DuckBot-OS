@echo off
REM OpenWebUI + OpenRouter Free Models Plugin Launcher
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title OpenWebUI + OpenRouter Free Models Plugin
color 0E
cls

cd /d "%~dp0"

echo.
echo ================================================================
echo  🚀 OPENWEBUI + OPENROUTER FREE MODELS PLUGIN
echo ================================================================
echo.
echo 🎯 WHAT THIS SETUP PROVIDES:
echo   ✅ Official OpenRouter integration plugin for OpenWebUI
echo   ✅ Access to FREE OpenRouter models (no API key required)
echo   ✅ Professional web interface with chat history
echo   ✅ Model switching, streaming responses, citations
echo   ✅ Reasoning tokens support for advanced models
echo.
echo 🆓 FREE MODELS AVAILABLE:
echo   • microsoft/phi-3-mini-128k-instruct:free
echo   • google/gemma-7b-it:free  
echo   • meta-llama/llama-3-8b-instruct:free
echo   • mistralai/mistral-7b-instruct:free
echo   • huggingfaceh4/zephyr-7b-beta:free
echo   • nousresearch/nous-capybara-7b:free
echo   • openchat/openchat-7b:free
echo.
echo 🔧 FEATURES:
echo   • Streaming responses
echo   • Citation support
echo   • Reasoning tokens (for supported models)
echo   • Model filtering (free models only)
echo   • Cache control for cost optimization
echo   • Professional chat interface
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

REM Check if OpenWebUI is installed
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

REM Check internet connection
echo 🌐 Testing OpenRouter API access...
python -c "import requests; requests.get('https://openrouter.ai/api/v1/models', timeout=5)" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  No internet connection or OpenRouter unreachable
    echo 💡 Some features may be limited without internet access
) else (
    echo ✅ OpenRouter API accessible
)

echo.
echo 🚀 Starting OpenWebUI with OpenRouter Free Models Plugin...
echo.

REM Run the setup script
python setup_openwebui_openrouter_plugin.py

if errorlevel 1 (
    echo.
    echo ❌ Setup failed! Check the error messages above.
    echo.
    echo 💡 TROUBLESHOOTING:
    echo   • Ensure you have internet access
    echo   • Check if port 8080 is available
    echo   • Try running as administrator
    echo   • Make sure OpenWebUI is properly installed
    echo.
    echo 📞 SUPPORT:
    echo   • Check OpenWebUI docs: https://docs.openwebui.com
    echo   • Check OpenRouter docs: https://openrouter.ai/docs
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 💡 NEXT STEPS:
echo   1. Open http://localhost:8080 in your browser
echo   2. Go to Settings > Functions  
echo   3. Enable "OpenRouter Free Models" function
echo   4. Select a free model from the dropdown
echo   5. Start chatting with FREE AI models!
echo.
echo 🎯 NO API KEY REQUIRED FOR FREE MODELS!
echo.
pause