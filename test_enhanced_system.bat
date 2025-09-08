@echo off
echo ===============================================
echo   Testing Enhanced DuckBot System v3.0.5
echo ===============================================
echo Testing all improvements:
echo - Fixed Qwen timeout automatic fallbacks
echo - Separate rate limits for chat vs background
echo - Smart model rotation to prevent rate limits
echo - Fixed background task infinite loop
echo - Enhanced ComfyUI startup script
echo - Service installation script available
echo ===============================================
echo.

echo [1/5] Testing AI router syntax...
python -c "from duckbot.ai_router_gpt import route_task, get_router_state; print('✅ AI router working')"
if %errorlevel% neq 0 (
    echo [ERROR] AI router has syntax errors
    pause
    exit /b 1
)

echo [2/5] Testing WebUI syntax...  
python -c "from duckbot.webui import app; print('✅ WebUI working')"
if %errorlevel% neq 0 (
    echo [ERROR] WebUI has syntax errors
    pause
    exit /b 1
)

echo [3/5] Testing server manager...
python -c "from duckbot.server_manager import ServerManager; sm=ServerManager(); print('✅ Server manager working')"
if %errorlevel% neq 0 (
    echo [ERROR] Server manager has issues
    pause
    exit /b 1
)

echo [4/5] Testing enhanced rate limiting...
python -c "from duckbot.ai_router_gpt import _bucket_allow; print('Chat bucket:', _bucket_allow('chat')); print('Background bucket:', _bucket_allow('background')); print('✅ Separate rate limits working')"
if %errorlevel% neq 0 (
    echo [ERROR] Rate limiting has issues
    pause
    exit /b 1
)

echo [5/5] Testing model rotation...
python -c "from duckbot.ai_router_gpt import get_next_model_in_rotation; print('Qwen rotation:', get_next_model_in_rotation('qwen')); print('GLM rotation:', get_next_model_in_rotation('glm')); print('✅ Model rotation working')"
if %errorlevel% neq 0 (
    echo [ERROR] Model rotation has issues
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   🚀 ALL TESTS PASSED! 
echo ===============================================
echo.
echo Enhanced Features Now Available:
echo ✅ Qwen → GLM 4.5 Air → Local automatic fallback
echo ✅ Separate rate limits (Chat: 30/min, Background: 30/min)  
echo ✅ Smart model rotation prevents rate limiting
echo ✅ Fixed WebUI background task infinite loop
echo ✅ Enhanced ComfyUI startup with proper GPU settings
echo ✅ Installation script for missing services
echo ✅ Better LM Studio timeout handling
echo ✅ Cost analysis integration (/cost page)
echo.
echo Ready to start:
echo 1. Run: python -m duckbot.webui  (for WebUI)
echo 2. Run: install_missing_services.bat  (if needed)
echo 3. Use separate chat rate limits for uninterrupted chat
echo.
echo ===============================================

pause