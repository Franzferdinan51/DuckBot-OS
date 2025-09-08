@echo off

title QWEN DuckBot v3.0.5 Professional Setup and Launcher - Production Ready
-color 0A
cls

REM Ensure we're in the correct directory
CD /D "%~dp0"

:main_menu
cls
echo.
echo ===============================================
echo  [DUCKBOT] QWEN DuckBot v3.0.5 AI-Enhanced Ecosystem
echo ===============================================
echo    Professional Setup and Launcher v2.0 (QWEN Enhanced)
echo    Production-Grade AI-Managed Crypto Ecosystem
echo    [STATUS] PRODUCTION READY - Thread-Safe Architecture
echo ===============================================
echo.
echo [PRIMARY MODES - Choose Your Experience]
echo.
echo 1. [UNIFIED] AI-Enhanced WebUI Dashboard - RECOMMENDED!
echo    Combined WebUI + AI management + Auto-recovery
echo    Real-time monitoring + Professional interface
echo.
echo 2. [WEBUI-ONLY] WebUI Dashboard (No AI Management)
echo    Professional interface without AI orchestration
echo    Manual service control + Monitoring only
echo.
echo 3. [NO-UI] AI Command Line (Background Services)
echo    AI management without WebUI interface
echo    Intelligent orchestration + Auto-recovery
echo.
echo 4. [DOCTOR] System Doctor + Advanced Diagnostics
echo    Claude Code-style health checks + Code analysis
echo    Performance monitoring + Error log analysis
echo.
echo [CONFIGURATION & SUPPORT]
echo.
echo 5. [MANUAL] Complete Manual Setup Wizard
echo    Step-by-step guided configuration
echo    Dependency installation + Provider setup + Testing
echo.
echo 6. [SETUP] Quick AI Provider Settings
echo 7. [CHAT] Interactive Chat with AI Manager
echo 8. [SETTINGS] Advanced Configuration Menu
echo.
echo [INFORMATION & UTILITIES]
echo.
echo 9. [STATUS] System Status and Health Check
echo I. [INFO] System Information and Diagnostics
echo H. [HELP] Documentation and Troubleshooting
echo.
echo [OTHER]
echo.
echo S. [STANDARD] Legacy Standard Mode (Deprecated)
echo T. [TEST] Run System Tests and Validation
echo U. [UPDATE] Check for Updates and Dependencies
echo E. [EXIT] Exit Launcher
echo.
set /p choice="[PROMPT] Enter your choice: "

REM Primary modes
if /i "%choice%"=="1" goto unified_start
if /i "%choice%"=="2" goto webui_only
if /i "%choice%"=="3" goto ai_only
if /i "%choice%"=="4" goto doctor_mode
REM Configuration
if /i "%choice%"=="5" goto manual_setup
if /i "%choice%"=="6" goto setup_ai
if /i "%choice%"=="7" goto chat_ai
if /i "%choice%"=="8" goto settings_menu
REM Information
if /i "%choice%"=="9" goto system_status
if /i "%choice%"=="i" goto system_info
if /i "%choice%"=="h" goto help
REM Other options
if /i "%choice%"=="s" goto standard_start
if /i "%choice%"=="t" goto test_system
if /i "%choice%"=="u" goto update_check
if /i "%choice%"=="e" goto exit
goto invalid_choice

:quick_start
cls
echo.
echo ===============================================
echo  [STARTING] Starting AI-Enhanced DuckBot Ecosystem
echo ===============================================
echo.
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    goto main_menu
)

echo [AI] Launching AI-Enhanced Ecosystem...
echo [WARNING] First run may take longer (dependency installation)
echo [INFO] This includes automatic LM Studio -> OpenRouter fallback
echo [AUTO] AI will manage all services automatically
echo.
echo Press Ctrl+C to stop the ecosystem
echo.
echo [LOG] AI ecosystem logs will be saved to ai_ecosystem.log
python start_ai_ecosystem.py > ai_ecosystem.log 2>&1
if errorlevel 1 (
    echo [ERROR] AI ecosystem failed to start
    echo [SOLUTION] Check configuration or try manual setup
    echo [LOG] Detailed error information saved to ai_ecosystem.log
    echo [CONTINUE] Do not close this window - check logs for details
    echo.
    echo [ERROR DETAILS] Last 20 lines of ai_ecosystem.log:
    echo ====================
    if exist ai_ecosystem.log (
        powershell -Command "Get-Content -Path 'ai_ecosystem.log' -Tail 20"
    ) else (
        echo No log file available
    )
    echo ====================
    echo.
    echo Press any key to return to main menu (this will close the AI ecosystem)...
    pause >nul
)
echo.
echo Ecosystem stopped. Press any key to return to menu...
pause >nul
goto main_menu