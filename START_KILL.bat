@echo off
REM ==============================================================================
REM  🛑 DUCKBOT KILL LAUNCHER v4.2
REM  Emergency Process Termination and Cleanup
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Kill Mode
color 0C
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  🛑 DUCKBOT EMERGENCY KILL MODE v4.2
echo ================================================================================
echo.
echo ⚠️  WARNING: This will forcefully terminate ALL DuckBot processes!
echo    - All running services will be stopped
echo    - All ports will be freed
echo    - Any unsaved work will be lost
echo.
echo 🛑 EMERGENCY PROCESS TERMINATION...
echo.

set /p confirm="Are you sure you want to kill all DuckBot processes? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ Operation cancelled
    pause
    exit /b 0
)

echo.
echo 🛑 Starting emergency shutdown sequence...
echo.

echo [1/4] Killing Python processes related to DuckBot...
taskkill //F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul
taskkill //F /IM pythonw.exe /FI "WINDOWTITLE eq DuckBot*" 2>nul
taskkill //F /IM python.exe /FI "WINDOWTITLE eq *WebUI*" 2>nul
taskkill //F /IM pythonw.exe /FI "WINDOWTITLE eq *WebUI*" 2>nul

echo [2/4] Stopping web servers on common DuckBot ports...
for %%p in (8787 8788 8789 8790 8791) do (
    echo Checking port %%p...
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if not errorlevel 1 (
        echo 🛑 Stopping service on port %%p
        for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do (
            taskkill //F /PID %%i 2>nul
            if not errorlevel 1 (
                echo [DONE] Process %%i terminated
            )
        )
    )
)

echo [3/4] Killing any remaining Python processes with DuckBot modules...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /i "duckbot\|webui\|ecosystem"') do (
    echo 🛑 Killing Python process: %%i
    taskkill //F /PID %%i 2>nul
)

echo [4/4] Verifying cleanup...
timeout /t 2 >nul

echo.
echo 📋 CLEANUP REPORT:
for %%p in (8787 8788 8789) do (
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if errorlevel 1 (
        echo ✅ Port %%p: FREED
    ) else (
        echo ❌ Port %%p: STILL IN USE
    )
)

echo.
echo 🛑 Checking for remaining processes...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /i "duckbot\|webui\|ecosystem" >nul
if errorlevel 1 (
    echo ✅ All DuckBot processes terminated
) else (
    echo ⚠️  Some DuckBot processes may still be running
    echo 💡 You may need to restart your computer
)

echo.
echo ✅ Emergency shutdown completed
echo 💡 All DuckBot services have been stopped
echo 🔄 You can now restart DuckBot safely
pause