@echo off
REM ==============================================================================
REM  ⚙️ DUCKBOT ERROR HANDLING CONFIGURATION v4.2
REM  Standardized Error Handling Configuration for All Startup Scripts
REM ==============================================================================
REM
REM This configuration file defines standardized error handling behavior
REM for all DuckBot startup scripts. It should be included at the beginning
REM of every batch file to ensure consistent error handling.
REM
REM USAGE:
REM   call error_handling_config.bat
REM
REM ==============================================================================

REM Initialize error handling environment
set "ERROR_HANDLER_PATH=%~dp0error_handler.bat"
if not exist "%ERROR_HANDLER_PATH%" (
    echo [❌] Error handler not found: %ERROR_HANDLER_PATH%
    echo [📋] Please ensure error_handler.bat exists in the launcher directory
    pause
    exit /b 1
)

REM Standard error codes
set "ERROR_SUCCESS=0"
set "ERROR_GENERAL=1"
set "ERROR_PYTHON=2"
set "ERROR_DEPENDENCIES=3"
set "ERROR_CONFIG=4"
set "ERROR_NETWORK=5"
set "ERROR_PERMISSION=6"
set "ERROR_RESOURCE=7"
set "ERROR_TIMEOUT=8"
set "ERROR_VALIDATION=9"
set "ERROR_SERVICE=10"

REM Error handling configuration
set "ERROR_LOGGING_ENABLED=1"
set "ERROR_LOG_LEVEL=INFO"  DEBUG, INFO, WARN, ERROR
set "ERROR_CONSOLE_OUTPUT=1"
set "ERROR_FILE_OUTPUT=1"
set "ERROR_RECOVERY_ENABLED=1"
set "ERROR_MAX_RETRIES=3"
set "ERROR_RETRY_DELAY=2"

REM Standard error message prefixes
set "ERROR_PREFIX=[❌]"
set "WARNING_PREFIX=[⚠️]"
set "SUCCESS_PREFIX=[✅]"
set "INFO_PREFIX=[ℹ️]"
set "DEBUG_PREFIX=[🔍]"

REM Log file configuration
set "LOG_DIR=logs"
set "ERROR_LOG_FILE=%LOG_DIR%\startup_errors.log"
set "SYSTEM_LOG_FILE=%LOG_DIR%\system.log"
set "PERFORMANCE_LOG_FILE=%LOG_DIR%\performance.log"

REM Error severity levels
set "SEVERITY_LOW=1"
set "SEVERITY_MEDIUM=2"
set "SEVERITY_HIGH=3"
set "SEVERITY_CRITICAL=4"

REM Error categories
set "CATEGORY_SYSTEM=system"
set "CATEGORY_NETWORK=network"
set "CATEGORY_CONFIG=config"
set "CATEGORY_DEPENDENCY=dependency"
set "CATEGORY_SERVICE=service"
set "CATEGORY_PERMISSION=permission"
set "CATEGORY_RESOURCE=resource"
set "CATEGORY_TIMEOUT=timeout"

REM Initialize error handling
call "%ERROR_HANDLER_PATH%" init
if %errorlevel% neq 0 (
    echo [❌] Failed to initialize error handler
    pause
    exit /b %ERROR_GENERAL%
)

REM Standard error handling functions
goto :eof

:handle_error
REM Standard error handling function
REM Usage: call :handle_error error_code "error_message" [category] [severity]
set "err_code=%~1"
set "err_msg=%~2"
set "err_category=%~3"
if "%err_category%"=="" set "err_category=%CATEGORY_SYSTEM%"
set "err_severity=%~4"
if "%err_severity%"=="" set "err_severity=%SEVERITY_MEDIUM%"

REM Log the error
call "%ERROR_HANDLER_PATH%" log "Error %err_code%: %err_msg% (Category: %err_category%, Severity: %err_severity%)"

REM Display error based on severity
if %err_severity% geq %SEVERITY_CRITICAL% (
    echo %ERROR_PREFIX% CRITICAL ERROR: %err_msg%
    echo %ERROR_PREFIX% System will terminate due to critical error
    timeout /t 5 >nul
    exit /b %err_code%
) else if %err_severity% geq %SEVERITY_HIGH% (
    echo %ERROR_PREFIX% HIGH SEVERITY ERROR: %err_msg%
    echo %ERROR_PREFIX% Please check logs for details
    pause
    exit /b %err_code%
) else if %err_severity% geq %SEVERITY_MEDIUM% (
    echo %ERROR_PREFIX% ERROR: %err_msg%
    echo %INFO_PREFIX% Attempting to continue...
    timeout /t 2 >nul
) else (
    echo %WARNING_PREFIX% WARNING: %err_msg%
    echo %INFO_PREFIX% Continuing with reduced functionality
    timeout /t 1 >nul
)

exit /b %err_code%

:check_dependencies
REM Standard dependency checking function
REM Usage: call :check_dependencies "dependency_list"
set "dep_list=%~1"
if "%dep_list%"=="" (
    call :handle_error %ERROR_VALIDATION% "No dependencies specified" %CATEGORY_CONFIG% %SEVERITY_MEDIUM%
    exit /b %ERROR_VALIDATION%
)

echo %INFO_PREFIX% Checking dependencies...

REM Split dependency list and check each
for %%d in (%dep_list%) do (
    call :check_single_dependency "%%d"
    if %errorlevel% neq 0 (
        call :handle_error %ERROR_DEPENDENCIES% "Dependency check failed: %%d" %CATEGORY_DEPENDENCY% %SEVERITY_HIGH%
        exit /b %errorlevel%
    )
)

echo %SUCCESS_PREFIX% All dependencies verified
exit /b 0

:check_single_dependency
REM Check a single dependency
REM Usage: call :check_single_dependency "dependency_name"
set "dep=%~1"
set "dep_found=0"

REM Check Python modules
if "%dep%"=="python" (
    python --version >nul 2>&1
    if %errorlevel% equ 0 set "dep_found=1"
) else if "%dep%"=="pip" (
    pip --version >nul 2>&1
    if %errorlevel% equ 0 set "dep_found=1"
) else if "%dep%"=="node" (
    node --version >nul 2>&1
    if %errorlevel% equ 0 set "dep_found=1"
) else if "%dep%"=="npm" (
    npm --version >nul 2>&1
    if %errorlevel% equ 0 set "dep_found=1"
) else (
    REM Check Python modules
    python -c "import %dep%" >nul 2>&1
    if %errorlevel% equ 0 set "dep_found=1"
)

if %dep_found% equ 1 (
    echo %SUCCESS_PREFIX% %dep% is available
    exit /b 0
) else (
    echo %ERROR_PREFIX% %dep% not found
    exit /b 1
)

:check_port
REM Check if a port is available
REM Usage: call :check_port port_number
set "port=%~1"
if "%port%"=="" (
    call :handle_error %ERROR_VALIDATION% "No port specified" %CATEGORY_CONFIG% %SEVERITY_MEDIUM%
    exit /b %ERROR_VALIDATION%
)

netstat -ano | findstr ":%port%" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo %WARNING_PREFIX% Port %port% is already in use
    exit /b 1
) else (
    echo %SUCCESS_PREFIX% Port %port% is available
    exit /b 0
)

:free_port
REM Free a port if it's in use
REM Usage: call :free_port port_number
set "port=%~1"
if "%port%"=="" (
    call :handle_error %ERROR_VALIDATION% "No port specified" %CATEGORY_CONFIG% %SEVERITY_MEDIUM%
    exit /b %ERROR_VALIDATION%
)

call :check_port %port%
if %errorlevel% equ 0 (
    echo %INFO_PREFIX% Port %port% is already available
    exit /b 0
)

echo %INFO_PREFIX% Attempting to free port %port%...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":%port%" ^| findstr "LISTENING"') do (
    echo %INFO_PREFIX% Terminating process %%i on port %port%
    taskkill /F /PID %%i >nul 2>&1
)

timeout /t 2 >nul
call :check_port %port%
if %errorlevel% equ 0 (
    echo %SUCCESS_PREFIX% Port %port% successfully freed
    exit /b 0
) else (
    echo %ERROR_PREFIX% Failed to free port %port%
    exit /b 1
)

:validate_config
REM Validate configuration files
REM Usage: call :validate_config "config_file_path"
set "config_file=%~1"
if "%config_file%"=="" (
    call :handle_error %ERROR_VALIDATION% "No config file specified" %CATEGORY_CONFIG% %SEVERITY_MEDIUM%
    exit /b %ERROR_VALIDATION%
)

if not exist "%config_file%" (
    call :handle_error %ERROR_CONFIG% "Config file not found: %config_file%" %CATEGORY_CONFIG% %SEVERITY_HIGH%
    exit /b %ERROR_CONFIG%
)

echo %INFO_PREFIX% Validating config file: %config_file%
python -c "
import json
import sys
try:
    with open('%config_file%', 'r') as f:
        config = json.load(f)
    print('✅ Config file is valid JSON')
    if isinstance(config, dict):
        print(f'✅ Config contains {len(config)} settings')
    else:
        print('⚠️ Config is not a dictionary')
        sys.exit(1)
except json.JSONDecodeError as e:
    print(f'❌ Invalid JSON in config file: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Config validation error: {e}')
    sys.exit(1)
"

if %errorlevel% neq 0 (
    call :handle_error %ERROR_CONFIG% "Config file validation failed: %config_file%" %CATEGORY_CONFIG% %SEVERITY_HIGH%
    exit /b %ERROR_CONFIG%
)

echo %SUCCESS_PREFIX% Config file validation completed
exit /b 0

:log_performance
REM Log performance metrics
REM Usage: call :log_performance "action" "duration_ms"
set "action=%~1"
set "duration=%~2"
if "%action%"=="" set "action=unknown"
if "%duration%"=="" set "duration=0"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" 2>nul
echo [%date% %time%] [PERFORMANCE] %action% took %duration%ms >> "%PERFORMANCE_LOG_FILE%"
exit /b 0

:cleanup_on_error
REM Cleanup resources when an error occurs
REM Usage: call :cleanup_on_error
echo %INFO_PREFIX% Performing cleanup on error...

REM Clean up temporary files
if exist "%TEMP%\duckbot_*" del /q "%TEMP%\duckbot_*" 2>nul

REM Kill any stray DuckBot processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1

echo %INFO_PREFIX% Cleanup completed
exit /b 0

:eof