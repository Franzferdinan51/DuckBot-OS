@echo off
cls
echo ====================================
echo  DuckBot v3.0.6+ HEADLESS LOCAL MODE
echo ====================================
echo.
echo Starting headless local-only ecosystem...
echo - No WebUI dashboard
echo - No user interface
echo - Discord bot only
echo - Complete privacy mode
echo - All processing stays local
echo.

REM Set headless mode environment variables
set AI_LOCAL_ONLY_MODE=true
set DISABLE_OPENROUTER=true
set ENABLE_LM_STUDIO_ONLY=true
set ENABLE_DYNAMIC_LOADING=true
set DUCKBOT_HEADLESS_MODE=true
set DISABLE_WEBUI=true
set DISABLE_COST_DASHBOARD=true
set DISABLE_JUPYTER=true
set DISABLE_N8N=true
set DISABLE_OPEN_NOTEBOOK=true

REM Only keep essential services
set ENABLE_DISCORD_BOT=true
set ENABLE_COMFYUI=true
set LM_STUDIO_URL=http://localhost:1234/v1
set AI_ROUTING_MODE=local_first
set FORCE_CLOUD_FOR_CHAT=0

echo Checking LM Studio availability...
curl -s http://localhost:1234/v1/models > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] LM Studio not detected at localhost:1234
    echo Please start LM Studio with local server enabled before running headless mode.
    echo.
    pause
    exit /b 1
)

echo LM Studio detected! Starting headless ecosystem...
echo.

REM Start the local ecosystem in headless mode
python start_local_ecosystem.py --headless

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start headless local ecosystem
    echo Check logs for details
    pause
    exit /b 1
)

echo.
echo Headless local ecosystem started successfully!
echo Discord bot is running in privacy mode.
echo Press Ctrl+C to stop the ecosystem.
echo.
pause
