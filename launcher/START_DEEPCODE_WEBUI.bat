@echo off
REM DuckBot DeepCode WebUI Launcher
REM Starts the DeepCode WebUI service with comprehensive integration

echo.
echo ========================================
echo    🧠 DuckBot DeepCode WebUI Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if required modules are available
echo [INFO] Checking dependencies...
python -c "import fastapi, uvicorn, jinja2" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some dependencies may be missing
    echo Installing required packages...
    pip install fastapi uvicorn jinja2 pydantic python-multipart
)

REM Set up environment variables
set DEEPCODE_HOST=127.0.0.1
set DEEPCODE_PORT=8790
set DEEPCODE_LOG_LEVEL=INFO

REM Create necessary directories
if not exist "uploads\deepcode" mkdir uploads\deepcode
if not exist "logs" mkdir logs

REM Check if service is already running
netstat -ano | findstr ":%DEEPCODE_PORT%" >nul
if not errorlevel 1 (
    echo [WARNING] Port %DEEPCODE_PORT% is already in use
    echo [INFO] Attempting to stop existing service...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%DEEPCODE_PORT%"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
)

echo [INFO] Starting DeepCode WebUI Service...
echo [INFO] Host: %DEEPCODE_HOST%
echo [INFO] Port: %DEEPCODE_PORT%
echo [INFO] Log Level: %DEEPCODE_LOG_LEVEL%
echo.

REM Start the service
start "DeepCode WebUI" cmd /k python -m duckbot.services.deepcode_webui_service --host %DEEPCODE_HOST% --port %DEEPCODE_PORT% --log-level %DEEPCODE_LOG_LEVEL%

echo [INFO] DeepCode WebUI Service is starting up...
echo [INFO] Please wait a few moments for the service to initialize
echo.
echo [INFO] WebUI will be available at: http://%DEEPCODE_HOST%:%DEEPCODE_PORT%/deepcode
echo [INFO] API Documentation at: http://%DEEPCODE_HOST%:%DEEPCODE_PORT%/docs
echo [INFO] Health check at: http://%DEEPCODE_HOST%:%DEEPCODE_PORT%/health
echo.
echo [INFO] Default login credentials:
echo [INFO]   Username: admin
echo [INFO]   Password: admin
echo.
echo [INFO] Press any key to open the WebUI in your browser...
pause >nul

REM Open browser
start http://%DEEPCODE_HOST%:%DEEPCODE_PORT%/deepcode

echo [SUCCESS] DeepCode WebUI Service started successfully!
echo.
echo [INFO] To stop the service, close the command window or press Ctrl+C
echo [INFO] Check logs\deepcode.log for detailed service logs
echo.

REM Keep the launcher window open
pause