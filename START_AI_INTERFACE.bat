@echo off
REM DuckBot AI Interface Launcher
REM Modern alternatives to the traditional startup script

echo.
echo ================================================================================
echo  DUCKBOT AI INTERFACE LAUNCHER
echo ================================================================================
echo.
echo Choose your preferred interface:
echo.
echo 1. 🤖 AI-Powered Terminal Interface
echo    - Interactive terminal with Charm tools
echo    - API key management
echo    - AI recommendations
echo    - Real-time status monitoring
echo.
echo 2. 🌐 Web-Based Launcher Dashboard
echo    - Modern web interface
echo    - Drag-and-drop service management
echo    - Real-time visual monitoring
echo    - API key configuration
echo.
echo 3. 🎤 Voice-Controlled Launcher
echo    - Voice commands for launching services
echo    - AI voice responses
echo    - Hands-free operation
echo    - Natural language control
echo.
echo 4. 📋 Traditional Startup Script
echo    - Original batch script interface
echo    - All 29 launch options
echo    - Comprehensive AI logging
echo.
echo 5. 🔧 Quick Launch Menu
echo    - Fast access to common modes
echo    - Simplified interface
echo    - AI-powered recommendations
echo.
echo 6. ⚙️  API Key Configuration
echo    - Setup Gemini, OpenRouter, Z.ai keys
echo    - Configure coding plans
echo    - Test API connectivity
echo.
echo.
set /p choice="Enter your choice (1-6): "

if /i "%choice%"=="1" goto ai_terminal
if /i "%choice%"=="2" goto web_launcher
if /i "%choice%"=="3" goto voice_launcher
if /i "%choice%"=="4" goto traditional
if /i "%choice%"=="5" goto quick_launch
if /i "%choice%"=="6" goto api_setup
if /i "%choice%"=="q" goto end
if /i "%choice%"=="quit" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto start

:ai_terminal
echo.
echo 🤖 Starting AI-Powered Terminal Interface...
echo.
python duckbot/ai_startup_interface.py
goto end

:web_launcher
echo.
echo 🌐 Starting Web-Based Launcher Dashboard...
echo.
echo Checking dependencies...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] FastAPI not installed. Installing...
    pip install fastapi uvicorn
)

echo Starting web launcher on http://127.0.0.1:8080
python duckbot/web_launcher.py
goto end

:voice_launcher
echo.
echo 🎤 Starting Voice-Controlled Launcher...
echo.
echo Checking dependencies...
python -c "import speech_recognition" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Speech recognition not available. Install: pip install SpeechRecognition
    echo [WARN] PyAudio may also be required for microphone access
)

python duckbot/voice_launcher.py
goto end

:traditional
echo.
echo 📋 Starting Traditional Startup Script...
echo.
START_ENHANCED_DUCKBOT.bat
goto end

:quick_launch
echo.
echo ⚡ Quick Launch Menu
echo.
echo Popular Modes:
echo.
echo A. 🌟 AI-Enhanced WebUI (All Features)
echo B. 🏠 Local-Only Privacy Mode
echo C. 🤖 ByteBot Desktop Automation
echo D. 🧠 Archon Multi-Agent System
echo E. 🎯 UI-TARS GUI Automation
echo F. 🌐 Complete WebUI Stack
echo G. 🔍 AI System Monitor
echo.
set /p quick_choice="Enter quick launch choice (A-G): "

if /i "%quick_choice%"=="a" (
    echo Launching AI-Enhanced WebUI...
    START_ENHANCED_DUCKBOT.bat
    echo 1
)
if /i "%quick_choice%"=="b" (
    echo Launching Local-Only Mode...
    START_ENHANCED_DUCKBOT.bat
    echo L
)
if /i "%quick_choice%"=="c" (
    echo Launching ByteBot...
    START_ENHANCED_DUCKBOT.bat
    echo 15
)
if /i "%quick_choice%"=="d" (
    echo Launching Archon...
    START_ENHANCED_DUCKBOT.bat
    echo 17
)
if /i "%quick_choice%"=="e" (
    echo Launching UI-TARS...
    START_ENHANCED_DUCKBOT.bat
    echo 16
)
if /i "%quick_choice%"=="f" (
    echo Launching WebUI Stack...
    START_ENHANCED_DUCKBOT.bat
    echo 21
)
if /i "%quick_choice%"=="g" (
    echo Launching AI Monitor...
    START_ENHANCED_DUCKBOT.bat
    echo 22
)

goto end

:api_setup
echo.
echo 🔧 API Key Configuration
echo.
echo This will help you setup API keys for AI-powered features:
echo.
echo 1. Setup Gemini API Key (for Google AI features)
echo 2. Setup OpenRouter API Key (for cloud AI models)
echo 3. Setup Z.ai API Key (for coding assistance)
echo 4. Setup All API Keys
echo 5. Test API Connectivity
echo 6. View Current Configuration
echo.
set /p api_choice="Enter your choice (1-6): "

if /i "%api_choice%"=="1" goto setup_gemini
if /i "%api_choice%"=="2" goto setup_openrouter
if /i "%api_choice%"=="3" goto setup_zai
if /i "%api_choice%"=="4" goto setup_all
if /i "%api_choice%"=="5" goto test_api
if /i "%api_choice%"=="6" goto view_config

goto end

:setup_gemini
echo.
echo 🔑 Gemini API Key Setup
echo.
echo Get your API key from: https://makersuite.google.com/app/apikey
echo.
set /p gemini_key="Enter Gemini API Key: "
if not "%gemini_key%"=="" (
    echo GEMINI_API_KEY=%gemini_key% >> .env
    echo ✅ Gemini API Key saved to .env
) else (
    echo ❌ No API key provided
)
goto end

:setup_openrouter
echo.
echo 🔑 OpenRouter API Key Setup
echo.
echo Get your API key from: https://openrouter.ai/keys
echo.
set /p openrouter_key="Enter OpenRouter API Key: "
if not "%openrouter_key%"=="" (
    echo OPENROUTER_API_KEY=%openrouter_key% >> .env
    echo ✅ OpenRouter API Key saved to .env
) else (
    echo ❌ No API key provided
)
goto end

:setup_zai
echo.
echo 🔑 Z.ai API Key Setup
echo.
echo Get your API key from: https://z.ai
echo.
set /p zai_key="Enter Z.ai API Key: "
if not "%zai_key%"=="" (
    echo ZAI_API_KEY=%zai_key% >> .env
    echo ✅ Z.ai API Key saved to .env
) else (
    echo ❌ No API key provided
)

echo.
echo 💻 Z.ai Coding Plan (Optional):
set /p zai_plan="Enter Z.ai Coding Plan ID (or press Enter to skip): "
if not "%zai_plan%"=="" (
    echo ZAI_CODING_PLAN=%zai_plan% >> .env
    echo ✅ Z.ai Coding Plan saved to .env
)
goto end

:setup_all
echo.
echo 🔑 Complete API Setup
echo.
echo Setting up all API keys...
echo.

call :setup_gemini
call :setup_openrouter
call :setup_zai

echo.
echo 🎉 All API keys configured!
echo You can now use AI-powered features across all DuckBot modes.
goto end

:test_api
echo.
echo 🔍 Testing API Connectivity
echo.

REM Test Gemini
echo Testing Gemini API...
python -c "import os; print('Gemini:', 'Available' if os.getenv('GEMINI_API_KEY') else 'Not configured')"

REM Test OpenRouter
echo Testing OpenRouter API...
python -c "import os; print('OpenRouter:', 'Available' if os.getenv('OPENROUTER_API_KEY') else 'Not configured')"

REM Test Z.ai
echo Testing Z.ai API...
python -c "import os; print('Z.ai:', 'Available' if os.getenv('ZAI_API_KEY') else 'Not configured')"

echo.
echo 📊 API Status Check Complete
goto end

:view_config
echo.
echo 📋 Current API Configuration
echo.

if exist .env (
    echo Current .env file:
    type .env
) else (
    echo No .env file found. API keys not configured.
)
goto end

:end
echo.
echo Press any key to exit...
pause >nul