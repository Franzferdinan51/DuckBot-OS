@echo off
REM ==============================================================================
REM  🦆 DUCKBOT STARTUP SCRIPT TEMPLATE v4.2
REM  Standardized Error Handling Template for New Startup Scripts
REM ==============================================================================
REM
REM This template shows how to implement standardized error handling
REM in all DuckBot startup scripts. Copy and modify this template
REM for new startup scripts to ensure consistency.
REM
REM ==============================================================================

REM Initialize standardized error handling
call "%~dp0error_handling_config.bat"
if %errorlevel% neq 0 (
    echo [❌] Failed to initialize error handling
    pause
    exit /b 1
)

REM Set up script-specific configuration
set "SCRIPT_NAME=Template Script"
set "SCRIPT_VERSION=1.0.0"
set "SCRIPT_DESCRIPTION=Template script with standardized error handling"

REM Initialize script
title %SCRIPT_NAME% v%SCRIPT_VERSION%
color 0A
cls

REM Log script start
call "%ERROR_HANDLER_PATH%" log "Starting %SCRIPT_NAME% v%SCRIPT_VERSION%"
call :log_performance "script_start" 0

REM Main script function
:main
call :show_header
call :check_prerequisites
if %errorlevel% neq 0 exit /b %errorlevel%

call :perform_setup
if %errorlevel% neq 0 exit /b %errorlevel%

call :start_services
if %errorlevel% neq 0 exit /b %errorlevel%

call :show_completion
goto cleanup

:show_header
echo.
echo ================================================================================
echo  %SCRIPT_NAME% v%SCRIPT_VERSION%
echo ================================================================================
echo.
echo %SCRIPT_DESCRIPTION%
echo.
echo %INFO_PREFIX% Initializing script...
echo.

REM Log header display
call :log_performance "header_displayed" 0
exit /b 0

:check_prerequisites
echo %INFO_PREFIX% Checking prerequisites...

REM Check Python
call :check_single_dependency "python"
if %errorlevel% neq 0 (
    call :handle_error %ERROR_PYTHON% "Python is required but not found" %CATEGORY_DEPENDENCY% %SEVERITY_CRITICAL%
    exit /b %errorlevel%
)

REM Check required Python modules
call :check_dependencies "requests psutil fastapi uvicorn"
if %errorlevel% neq 0 (
    call :handle_error %ERROR_DEPENDENCIES% "Required Python modules not found" %CATEGORY_DEPENDENCY% %SEVERITY_HIGH%
    exit /b %errorlevel%
)

REM Check required ports
call :check_port "8787"
if %errorlevel% neq 0 (
    echo %INFO_PREFIX% Attempting to free port 8787...
    call :free_port "8787"
    if %errorlevel% neq 0 (
        call :handle_error %ERROR_NETWORK% "Could not free port 8787" %CATEGORY_NETWORK% %SEVERITY_HIGH%
        exit /b %errorlevel%
    )
)

REM Check configuration files
if exist "config\config.json" (
    call :validate_config "config\config.json"
    if %errorlevel% neq 0 (
        call :handle_error %ERROR_CONFIG% "Invalid configuration file" %CATEGORY_CONFIG% %SEVERITY_HIGH%
        exit /b %errorlevel%
    )
)

echo %SUCCESS_PREFIX% All prerequisites verified
call :log_performance "prerequisites_checked" 0
exit /b 0

:perform_setup
echo %INFO_PREFIX% Performing setup...

REM Example: Setup environment variables
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

REM Example: Create required directories
if not exist "logs" mkdir logs 2>nul
if not exist "temp" mkdir temp 2>nul

REM Example: Setup configuration (with error handling)
echo %INFO_PREFIX% Setting up configuration...
python -c "
import json
import os
config = {
    'script_name': '%SCRIPT_NAME%',
    'version': '%SCRIPT_VERSION%',
    'setup_time': '%date% %time%'
}
os.makedirs('config', exist_ok=True)
with open('config\template_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ Configuration created successfully')
"

if %errorlevel% neq 0 (
    call :handle_error %ERROR_CONFIG% "Failed to create configuration" %CATEGORY_CONFIG% %SEVERITY_MEDIUM%
    exit /b %errorlevel%
)

echo %SUCCESS_PREFIX% Setup completed
call :log_performance "setup_completed" 0
exit /b 0

:start_services
echo %INFO_PREFIX% Starting services...

REM Example: Start main service (with error handling and timeout)
echo %INFO_PREFIX% Starting main service...
start "Template Service" python template_service.py

REM Wait for service to start
echo %INFO_PREFIX% Waiting for service to initialize...
timeout /t 10 >nul

REM Check if service is running
echo %INFO_PREFIX% Verifying service status...
python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:8787/health', timeout=5)
    if response.status_code == 200:
        print('✅ Service is running and responsive')
    else:
        print(f'⚠️ Service returned status {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Service health check failed: {e}')
    sys.exit(1)
"

if %errorlevel% neq 0 (
    call :handle_error %ERROR_SERVICE% "Service failed to start properly" %CATEGORY_SERVICE% %SEVERITY_HIGH%
    call :cleanup_on_error
    exit /b %errorlevel%
)

echo %SUCCESS_PREFIX% Services started successfully
call :log_performance "services_started" 0
exit /b 0

:show_completion
echo.
echo ================================================================================
echo  ✅ %SCRIPT_NAME% COMPLETED SUCCESSFULLY
echo ================================================================================
echo.
echo %INFO_PREFIX% Service is running at: http://localhost:8787
echo %INFO_PREFIX% Logs are available in: logs\ directory
echo %INFO_PREFIX% Press Ctrl+C to stop the service
echo.
echo %SUCCESS_PREFIX% All systems operational!
echo.

REM Log completion
call "%ERROR_HANDLER_PATH%" log "%SCRIPT_NAME% completed successfully"
call :log_performance "script_completed" 0
exit /b 0

:cleanup
REM Cleanup function called on script exit
echo %INFO_PREFIX% Performing cleanup...

REM Example: Cleanup temporary files
if exist "temp\template_*" del /q "temp\template_*" 2>nul

REM Log cleanup
call :log_performance "cleanup_completed" 0

REM Exit with success code
call "%ERROR_HANDLER_PATH%" exit 0
goto :eof

REM Error handling function (example of custom error handling)
:custom_error_handling
REM Usage: call :custom_error_handling error_code "error_message"
set "custom_code=%~1"
set "custom_msg=%~2"

REM Log custom error
call "%ERROR_HANDLER_PATH%" log "Custom error %custom_code%: %custom_msg"

REM Handle custom recovery based on error code
if "%custom_code%"=="1001" (
    echo %INFO_PREFIX% Attempting custom recovery for error 1001...
    REM Custom recovery logic here
    timeout /t 3 >nul
    echo %SUCCESS_PREFIX% Custom recovery completed
    exit /b 0
)

REM Default error handling
call :handle_error %custom_code% "%custom_msg%"
exit /b %custom_code%

REM Helper functions for common operations
:get_timestamp
REM Get current timestamp for logging
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do set "dt=%%c-%%a-%%b"
for /f "tokens=1-3 delims=:." %%a in ("%time%") do set "tm=%%a:%%b:%%c"
set "timestamp=%dt% %tm%"
exit /b 0

:check_memory
REM Check available memory
python -c "
import psutil
memory = psutil.virtual_memory()
available_gb = memory.available / (1024**3)
if available_gb < 1:
    print(f'❌ Low memory: {available_gb:.1f}GB available')
    exit(1)
else:
    print(f'✅ Sufficient memory: {available_gb:.1f}GB available')
    exit(0)
"
exit /b %errorlevel%

:show_help
echo.
echo ================================================================================
echo  📋 %SCRIPT_NAME% HELP
echo ================================================================================
echo.
echo %SCRIPT_DESCRIPTION%
echo.
echo USAGE:
echo   %~nx0 [options]
echo.
echo OPTIONS:
echo   --help         Show this help message
echo   --version      Show version information
echo   --verbose      Enable verbose output
echo   --config FILE  Use specific configuration file
echo   --port PORT    Use specific port number
echo.
echo EXAMPLES:
echo   %~nx0                    # Start with default settings
echo   %~nx0 --verbose         # Start with verbose output
echo   %~nx0 --port 9000       # Start on port 9000
echo.
echo ERROR CODES:
echo   0 = Success
echo   1 = General error
echo   2 = Python not found
echo   3 = Dependencies missing
echo   4 = Configuration error
echo   5 = Network error
echo   6 = Permission error
echo   7 = Resource error
echo   8 = Timeout error
echo   9 = Validation error
echo   10 = Service error
echo.
pause
exit /b 0

REM Command line argument processing
if "%~1"=="--help" goto show_help
if "%~1"=="--version" (
    echo %SCRIPT_NAME% v%SCRIPT_VERSION%
    exit /b 0
)
if "%~1"=="--verbose" set "ERROR_VERBOSE=1"
if "%~1"=="--config" (
    if "%~2"=="" (
        echo %ERROR_PREFIX% Configuration file not specified
        exit /b %ERROR_VALIDATION%
    )
    set "CONFIG_FILE=%~2"
)
if "%~1"=="--port" (
    if "%~2"=="" (
        echo %ERROR_PREFIX% Port number not specified
        exit /b %ERROR_VALIDATION%
    )
    set "SERVICE_PORT=%~2"
)

REM Start main script
goto main