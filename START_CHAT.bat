@echo off
REM ==============================================================================
REM  💬 DUCKBOT CHAT LAUNCHER v4.2
REM  Interactive AI Assistant with Direct Chat Interface
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Chat Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  💬 DUCKBOT CHAT MODE v4.2
echo ================================================================================
echo.
echo 💬 CHAT FEATURES:
echo   ✅ Direct chat with DuckBot AI Assistant
echo   ✅ Ask questions and get help
echo   ✅ Control DuckBot via natural language
echo   ✅ Interactive task assistance
echo.
echo 🚀 STARTING DUCKBOT AI ASSISTANT...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo [INFO] Initializing DuckBot AI Assistant...
echo [INFO] Starting interactive chat interface...
echo.

REM Check if AI assistant module exists
python -c "import importlib; importlib.import_module('duckbot.ai_assistant')" >nul 2>&1
if errorlevel 1 (
    echo [INFO] AI Assistant not available, starting basic chat interface...
    echo [INFO] Starting basic chat with available AI modules...
    python -c "
import sys
import os
sys.path.append('.')
print('=== DuckBot Chat Interface ===')
print('Type your messages below (type \"exit\" to quit)')
print()

try:
    from duckbot.chat_with_ai import chat_with_ai
    chat_with_ai()
except ImportError:
    print('Chat module not found. Trying basic interaction...')
    try:
        from duckbot.ai_router_gpt import AIRouter
        router = AIRouter()
        while True:
            user_input = input('You: ')
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            response = router.route_and_respond(user_input)
            print(f'DuckBot: {response}')
    except ImportError:
        print('Basic AI modules not available. Please install dependencies.')
        print('Run: pip install -r requirements.txt')
except KeyboardInterrupt:
    print('\\nGoodbye!')
except Exception as e:
    print(f'Error: {e}')
"
) else (
    python -m duckbot.ai_assistant
)

if errorlevel 1 (
    echo.
    echo ❌ Failed to start chat interface
    echo 💡 Please check if AI modules are properly installed
    pause
)

echo.
echo ✅ Chat session ended
pause