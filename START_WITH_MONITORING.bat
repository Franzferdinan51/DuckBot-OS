@echo off
REM DuckBot Electron Launcher with Real-time Monitoring
REM Starts the Electron launcher and comprehensive monitoring tools

echo.
echo ================================================================================
echo  DUCKBOT ELECTRON LAUNCHER WITH REAL-TIME MONITORING
echo ================================================================================
echo.
echo This script will:
echo   [🚀] Start the DuckBot Electron launcher
echo   [👀] Start real-time log monitoring
echo   [📊] Start comprehensive server monitoring
echo   [🔌] Monitor port allocation and conflicts
echo   [🌐] Monitor WebSocket connectivity
echo   [⚙️] Monitor processes and system resources
echo.
echo The monitoring will show you exactly what's happening when the server starts!
echo.
pause

REM Check if log directory exists
if not exist "duckbot\logs" mkdir "duckbot\logs"

REM Start log watcher in background
echo [👀] Starting log watcher...
start "Log Watcher" /MIN cmd /c "python log_watcher.py"

REM Wait a moment for log watcher to start
timeout /t 2 /nobreak >nul

REM Start server monitor in background
echo [📊] Starting server monitor...
start "Server Monitor" /MIN cmd /c "python server_monitor.py"

REM Wait a moment for server monitor to start
timeout /t 2 /nobreak >nul

echo.
echo [🚀] Starting DuckBot Electron launcher with monitoring...
echo [ℹ️]  Watch the other windows for real-time monitoring data!
echo.

REM Start the Electron launcher
call START_ELECTRON_LAUNCHER.bat

echo.
echo [✅] Electron launcher completed.
echo [ℹ️]  Monitoring tools are still running in separate windows.
echo [ℹ️]  Close the monitoring windows when you're done.
echo.
pause