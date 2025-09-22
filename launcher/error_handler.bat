@echo off
REM ==============================================================================
REM  🛡️ DUCKBOT STANDARDIZED ERROR HANDLING FRAMEWORK v4.2
REM  Unified Error Handling Utilities for All DuckBot Startup Scripts
REM ==============================================================================
REM
REM This module provides standardized error handling functions for all DuckBot
REM startup scripts. It ensures consistent error checking, logging, and recovery
REM across all batch files in the DuckBot ecosystem.
REM
REM USAGE:
REM   call error_handler.bat init              [Initialize error handling]
REM   call error_handler.bat check "command"   [Check command execution]
REM   call error_handler.bat log "message"     [Log error message]
REM   call error_handler.bat recover "action" [Attempt recovery]
REM   call error_handler.bat exit code         [Exit with error code]
REM
REM ==============================================================================

REM Error handling state variables
set "ERROR_HANDLER_INITIALIZED=0"
set "ERROR_LAST_CODE=0"
set "ERROR_LAST_MESSAGE="
set "ERROR_LOG_FILE=logs\error_handler.log"
set "ERROR_VERBOSE=1"
set "ERROR_RECOVERY_ATTEMPTS=3"

:main
if "%~1"=="" goto show_help
if "%~1"=="init" goto init_error_handler
if "%~1"=="check" goto check_command
if "%~1"=="log" goto log_error
if "%~1"=="recover" goto recover_action
if "%~1"=="exit" goto exit_with_code
if "%~1"=="reset" goto reset_error_state
if "%~1"=="status" goto show_status
goto show_help

:init_error_handler
REM Initialize error handling environment
set "ERROR_HANDLER_INITIALIZED=1"
set "ERROR_LAST_CODE=0"
set "ERROR_LAST_MESSAGE="
set "ERROR_START_TIME=%time%"

REM Ensure logs directory exists
if not exist "logs" mkdir logs 2>nul

REM Initialize log file
echo [%date% %time%] ERROR HANDLER INITIALIZED >> "%ERROR_LOG_FILE%"
echo [%date% %time%] Script: %~nx0 >> "%ERROR_LOG_FILE%"
echo [%date% %time%] User: %USERNAME% >> "%ERROR_LOG_FILE%"
echo [%date% %time%] Working Directory: %CD% >> "%ERROR_LOG_FILE%"
echo [%date% %time%] ======================================== >> "%ERROR_LOG_FILE%"

if "%ERROR_VERBOSE%"=="1" echo [✅] Error handler initialized successfully
exit /b 0

:check_command
REM Check command execution and handle errors
if "%ERROR_HANDLER_INITIALIZED%"=="0" call :init_error_handler

set "COMMAND_TO_CHECK=%~2"
if "%COMMAND_TO_CHECK%"=="" (
    call :log_error "No command specified for error check"
    exit /b 1
)

REM Execute the command and check result
%COMMAND_TO_CHECK%
set "ERROR_LAST_CODE=%errorlevel%"

if %ERROR_LAST_CODE% equ 0 (
    if "%ERROR_VERBOSE%"=="1" echo [✅] Command succeeded: %COMMAND_TO_CHECK%
    echo [%date% %time%] [SUCCESS] %COMMAND_TO_CHECK% >> "%ERROR_LOG_FILE%"
) else (
    call :log_error "Command failed with code %ERROR_LAST_CODE%: %COMMAND_TO_CHECK%"
    if "%ERROR_VERBOSE%"=="1" echo [❌] Command failed (code %ERROR_LAST_CODE%): %COMMAND_TO_CHECK%
)

exit /b %ERROR_LAST_CODE%

:log_error
REM Log error message with timestamp
set "ERROR_MESSAGE=%~1"
if "%ERROR_MESSAGE%"=="" set "ERROR_MESSAGE=Unknown error"

set "ERROR_LAST_MESSAGE=%ERROR_MESSAGE%"

REM Log to file
echo [%date% %time%] [ERROR] %ERROR_MESSAGE% >> "%ERROR_LOG_FILE%"

REM Display to console if verbose mode
if "%ERROR_VERBOSE%"=="1" echo [❌] %ERROR_MESSAGE%

REM Also log to system log if available
if exist "logs\system.log" echo [%date% %time%] [ERROR_HANDLER] %ERROR_MESSAGE% >> "logs\system.log"

exit /b 0

:recover_action
REM Attempt to recover from error
set "RECOVERY_ACTION=%~1"
if "%RECOVERY_ACTION%"=="" (
    call :log_error "No recovery action specified"
    exit /b 1
)

set "RECOVERY_ATTEMPT=0"
:recovery_loop
if %RECOVERY_ATTEMPT% geq %ERROR_RECOVERY_ATTEMPTS% (
    call :log_error "Recovery failed after %ERROR_RECOVERY_ATTEMPTS% attempts: %RECOVERY_ACTION%"
    exit /b 1
)

set /a RECOVERY_ATTEMPT+=1
if "%ERROR_VERBOSE%"=="1" echo [🔄] Recovery attempt %RECOVERY_ATTEMPT%/%ERROR_RECOVERY_ATTEMPTS%: %RECOVERY_ACTION%

REM Execute recovery action
%RECOVERY_ACTION%
if %errorlevel% equ 0 (
    call :log_error "Recovery succeeded on attempt %RECOVERY_ATTEMPT%: %RECOVERY_ACTION%"
    if "%ERROR_VERBOSE%"=="1" echo [✅] Recovery successful
    exit /b 0
)

REM Wait before retry
timeout /t 2 >nul
goto recovery_loop

:exit_with_code
REM Exit script with error code and logging
set "EXIT_CODE=%~1"
if "%EXIT_CODE%"=="" set "EXIT_CODE=0"

if %EXIT_CODE% equ 0 (
    if "%ERROR_VERBOSE%"=="1" echo [✅] Script completed successfully
    echo [%date% %time%] [SUCCESS] Script completed successfully (Exit code: %EXIT_CODE%) >> "%ERROR_LOG_FILE%"
) else (
    call :log_error "Script failed with exit code %EXIT_CODE%"
    if "%ERROR_VERBOSE%"=="1" echo [💀] Script terminated with error code %EXIT_CODE%
)

REM Calculate execution time if start time is available
if not "%ERROR_START_TIME%"=="" (
    echo [%date% %time%] [DURATION] Execution time: %ERROR_START_TIME% to %time% >> "%ERROR_LOG_FILE%"
)

echo [%date% %time%] ======================================== >> "%ERROR_LOG_FILE%"
exit /b %EXIT_CODE%

:reset_error_state
REM Reset error handling state
set "ERROR_LAST_CODE=0"
set "ERROR_LAST_MESSAGE="
set "ERROR_START_TIME=%time%"
if "%ERROR_VERBOSE%"=="1" echo [🔄] Error state reset
exit /b 0

:show_status
REM Show current error handling status
echo.
echo ================================================================================
echo  🛡️ ERROR HANDLER STATUS
echo ================================================================================
echo.
echo Initialized: %ERROR_HANDLER_INITIALIZED%
echo Last Error Code: %ERROR_LAST_CODE%
echo Last Error Message: %ERROR_LAST_MESSAGE%
echo Log File: %ERROR_LOG_FILE%
echo Verbose Mode: %ERROR_VERBOSE%
echo Recovery Attempts: %ERROR_RECOVERY_ATTEMPTS%
if not "%ERROR_START_TIME%"=="" echo Start Time: %ERROR_START_TIME%
echo.

REM Show recent log entries
if exist "%ERROR_LOG_FILE%" (
    echo Recent log entries:
    echo ----------------------------------------------------------------
    tail -10 "%ERROR_LOG_FILE%" 2>nul || type "%ERROR_LOG_FILE%" | findstr "[ERROR]" | tail -5
    echo ----------------------------------------------------------------
)
echo.
pause
exit /b 0

:show_help
echo.
echo ================================================================================
echo  🛡️ DUCKBOT ERROR HANDLING FRAMEWORK v4.2
echo ================================================================================
echo.
echo USAGE:
echo   call error_handler.bat init              [Initialize error handling]
echo   call error_handler.bat check "command"   [Check command execution]
echo   call error_handler.bat log "message"     [Log error message]
echo   call error_handler.bat recover "action" [Attempt recovery]
echo   call error_handler.bat exit code         [Exit with error code]
echo   call error_handler.bat reset             [Reset error state]
echo   call error_handler.bat status            [Show current status]
echo.
echo EXAMPLES:
echo   call error_handler.bat init
echo   call error_handler.bat check "python --version"
echo   call error_handler.bat log "Python not found"
echo   call error_handler.bat recover "pip install python"
echo   call error_handler.bat exit 1
echo.
echo ENVIRONMENT VARIABLES:
echo   ERROR_HANDLER_INITIALIZED  - Handler state (0/1)
echo   ERROR_LAST_CODE           - Last error code
echo   ERROR_LAST_MESSAGE        - Last error message
echo   ERROR_LOG_FILE           - Log file path
echo   ERROR_VERBOSE            - Verbose output (0/1)
echo   ERROR_RECOVERY_ATTEMPTS  - Max recovery attempts
echo.
pause
exit /b 0