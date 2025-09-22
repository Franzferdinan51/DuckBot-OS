@echo off
REM ==============================================================================
REM  ⚡ DUCKBOT QUICK START LAUNCHER v4.2
REM  Ultra-Fast One-Click Startup with Optimizations
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Quick Start
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  ⚡ DUCKBOT ULTRA-FAST START v4.2
echo ================================================================================
echo.
echo 🚀 ONE-CLICK STARTUP: Unified + Free Tier Optimized
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Apply free tier optimizations
echo 💸 Applying free tier optimizations...
python -c "
import os
config = {
    'OPENROUTER_BUDGET_PER_MIN': '3',
    'AI_CONFIDENCE_MIN': '0.75',
    'AI_LOCAL_CONF_MIN': '0.68',
    'AI_TTL_CACHE_SEC': '120',
    'MAX_MEMORY_THRESHOLD': '80.0',
    'ENABLE_ENHANCED_CACHING': 'true',
    'FREE_TIER_OPTIMIZED': 'true'
}
with open('.env.quick', 'w') as f:
    for k, v in config.items():
        f.write(f'{k}={v}\n')
print('✅ Free tier settings applied')
"

REM Install dependencies if needed
echo 📦 Checking dependencies...
python -c "import fastapi, uvicorn, aiohttp, requests" >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing required dependencies...
    pip install fastapi uvicorn aiohttp python-multipart jinja2 requests psutil matplotlib GPUtil
)

REM Start ecosystem with optimizations
echo.
echo 🚀 Starting unified ecosystem with optimizations...
start "AI Ecosystem" /MIN python start_ai_ecosystem.py
timeout /t 8 >nul

echo 🌐 Launching WebUI...
python -m duckbot.webui --host 127.0.0.1 --port 8787 --mode classic

echo.
echo ✅ Quick start session ended
pause