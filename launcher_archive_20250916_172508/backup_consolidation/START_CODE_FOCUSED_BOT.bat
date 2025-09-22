@echo off
REM DuckBot Code-Focused Startup
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Code-Focused Mode - AI Coding Assistant
color 0E
cls

cd /d "%~dp0"

echo.
echo ===============================================
echo  💻 DUCKBOT CODE-FOCUSED MODE
echo ===============================================
echo.
echo 🚀 LAUNCHING: AI-Powered Coding Assistant
echo.
echo 📋 CODE-FOCUSED FEATURES:
echo   ✅ Qwen Code models (primary coding AI)
echo   ✅ Claude Code Router (advanced analysis)
echo   ✅ Provider abstraction (easy switching)
echo   ✅ Code review and optimization
echo   ✅ Intelligent debugging assistance
echo   ✅ Repository analysis and suggestions
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Set code-focused configuration
echo 📝 Applying code-focused settings...
python -c "
import json
config = {
    'AI_MODE': 'CODE_FOCUSED',
    'PRIMARY_PROVIDER': 'qwen_code',
    'FALLBACK_PROVIDER': 'claude_code_router', 
    'CODE_ANALYSIS_ENABLED': 'true',
    'INTELLIGENT_AGENTS_ENABLED': 'true',
    'PROVIDER_SWITCHING_ENABLED': 'true'
}
with open('.env.code', 'w') as f:
    for k, v in config.items():
        f.write(f'{k}={v}\n')
print('✅ Code-focused configuration applied')
"

echo.
echo 🤖 Starting code-focused DuckBot...
echo.
echo 💡 AVAILABLE COMMANDS:
echo   /switch qwen - Primary Qwen code models  
echo   /switch claude - Claude Code Router
echo   /analyze code - Analyze code repositories
echo   /review code - Get code review suggestions
echo   /debug help - Debugging assistance
echo.
echo 🌐 Access: Discord bot with code-focused AI routing
echo.

REM Start with enhanced configuration focused on coding
python start_ecosystem.py --enhanced --config enhanced_config.json --mode code_focused

if errorlevel 1 (
    echo ❌ Failed to start code-focused mode
    echo 💡 Try the main enhanced launcher instead
    pause
    exit /b 1
)

echo ✅ Code-focused DuckBot started successfully!
pause