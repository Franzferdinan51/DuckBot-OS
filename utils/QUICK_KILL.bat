@echo off
REM Ensure UTF-8 code page for proper Unicode output on Windows terminals
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0 VibeVoice Quick Kill & Process Management
color 0C
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

:start
echo.
echo ===============================================
echo  DUCKBOT v3.1.0 QUICK KILL & PROCESS MANAGEMENT
echo ===============================================
echo  Emergency process termination and system control
echo  STREAMLINED: No ComfyUI/Open Notebook - VibeVoice Ready
echo  Current Directory: %CD%
echo ===============================================
echo.
echo EMERGENCY OPTIONS:
echo.
echo 1. Emergency Kill All - Terminate ALL DuckBot processes
echo    [Kills: Python, Node.js, VibeVoice, LM Studio, Jupyter, WebUI]
echo.
echo 2. Selective Kill - Choose specific services to terminate
echo    [Interactive selection of individual services]
echo.
echo 3. Process Status - View current DuckBot processes
echo    [Shows running services and port usage]
echo.
echo 4. Restart Services - Kill and restart specific services
echo    [Safe restart with dependency checking]
echo.
echo 5. Main Launcher - Go to SETUP_AND_START menu
echo    [Access full DuckBot control center]
echo.
echo 6. Cancel - Exit without changes
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto emergency_kill
if "%choice%"=="2" goto selective_kill
if "%choice%"=="3" goto process_status
if "%choice%"=="4" goto restart_services
if "%choice%"=="5" goto main_launcher
if "%choice%"=="6" goto cancel

echo Invalid choice. Please enter 1-6.
timeout /t 2 >nul
goto start

:emergency_kill
echo.
echo EMERGENCY KILL ALL PROCESSES
echo ===============================================
echo WARNING: This will terminate ALL DuckBot processes
echo    - Discord Bot
echo    - WebUI Dashboard
echo    - VibeVoice TTS Server
echo    - AI Services
echo    - n8n Workflows
echo    - Jupyter Notebooks
echo    - LM Studio
echo.
set /p confirm="Are you sure? Type 'YES' to confirm: "
if /i not "%confirm%"=="YES" (
    echo Cancelled by user.
    timeout /t 2 >nul
    goto start
)

echo.
echo Running EMERGENCY_KILL.bat...
call EMERGENCY_KILL.bat
echo.
echo Emergency kill completed.
goto end

:selective_kill
echo.
echo SELECTIVE PROCESS TERMINATION
echo ===============================================
echo.
echo Choose services to terminate:
echo.
echo 1. Discord Bot (Python processes)
echo 2. WebUI Dashboard (port 8787)
echo 3. VibeVoice Server (port 8000)
echo 4. n8n Workflows (port 5678)
echo 5. Jupyter Notebooks (port 8889)
echo 6. LM Studio (port 1234)
echo A. All Python processes
echo B. All Node.js processes
echo 0. Back to main menu
echo.
set /p service="Enter service number: "

if "%service%"=="1" (
    echo Terminating Discord Bot processes...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq DuckBot*" >nul 2>&1
    wmic process where "commandline like '%%ai_ecosystem_manager.py%%'" delete >nul 2>&1
    echo Discord Bot terminated.
)
if "%service%"=="2" (
    echo Terminating WebUI Dashboard...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8787') do taskkill /F /PID %%a >nul 2>&1
    echo WebUI Dashboard terminated.
)
if "%service%"=="3" (
    echo Terminating VibeVoice Server...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
    taskkill /F /FI "commandline eq *VibeVoice*" >nul 2>&1
    echo VibeVoice Server terminated.
)
if "%service%"=="4" (
    echo Terminating n8n Workflows...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5678') do taskkill /F /PID %%a >nul 2>&1
    echo n8n Workflows terminated.
)
if "%service%"=="5" (
    echo Terminating Jupyter Notebooks...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8889') do taskkill /F /PID %%a >nul 2>&1
    echo Jupyter Notebooks terminated.
)
if "%service%"=="6" (
    echo Terminating LM Studio...
    taskkill /F /IM "LM Studio.exe" >nul 2>&1
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1234') do taskkill /F /PID %%a >nul 2>&1
    echo LM Studio terminated.
)
if /i "%service%"=="A" (
    echo Terminating all Python processes...
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM pythonw.exe >nul 2>&1
    echo All Python processes terminated.
)
if /i "%service%"=="B" (
    echo Terminating all Node.js processes...
    taskkill /F /IM node.exe >nul 2>&1
    taskkill /F /IM nodejs.exe >nul 2>&1
    echo All Node.js processes terminated.
)
if /i "%service%"=="C" (
    echo Terminating all Docker containers...
    docker stop $(docker ps -q) >nul 2>&1
    echo All Docker containers stopped.
)
if "%service%"=="0" goto start

timeout /t 3 >nul
goto start

:process_status
echo.
echo CURRENT PROCESS STATUS
echo ===============================================
echo.
echo Checking DuckBot processes...
echo.

echo [Python Processes]
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE 2>nul | find /i "python.exe" || echo   No Python processes running

echo.
echo [Node.js Processes]
tasklist /FI "IMAGENAME eq node.exe" /FO TABLE 2>nul | find /i "node.exe" || echo   No Node.js processes running

echo.
echo [Port Usage - DuckBot Services]
echo   Port 8787 (WebUI):     
netstat -an | findstr :8787 | findstr LISTENING >nul && echo     ACTIVE || echo     INACTIVE

echo   Port 8000 (VibeVoice): 
netstat -an | findstr :8000 | findstr LISTENING >nul && echo     ACTIVE || echo     INACTIVE

echo   Port 5678 (n8n):       
netstat -an | findstr :5678 | findstr LISTENING >nul && echo     ACTIVE || echo     INACTIVE

echo   Port 8889 (Jupyter):   
netstat -an | findstr :8889 | findstr LISTENING >nul && echo     ACTIVE || echo     INACTIVE

echo   Port 1234 (LM Studio): 
netstat -an | findstr :1234 | findstr LISTENING >nul && echo     ACTIVE || echo     INACTIVE

echo.
echo System Resources:
echo   Memory Usage: 
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list | findstr "=" 2>nul

echo.
echo Press any key to return to menu...
pause >nul
goto start

:restart_services
echo.
echo RESTART SERVICES
echo ===============================================
echo.
echo This will safely terminate and restart services
echo.
echo 1. Restart WebUI Dashboard
echo 2. Restart VibeVoice Server
echo 3. Restart AI Ecosystem (Full restart)
echo 4. Restart n8n Workflows
echo 5. Back to main menu
echo.
set /p restart_choice="Enter choice (1-5): "

if "%restart_choice%"=="1" (
    echo.
    echo Restarting WebUI Dashboard...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8787') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
    echo Starting WebUI...
    start "DuckBot WebUI" python -m duckbot.webui
    echo WebUI Dashboard restarted.
)

if "%restart_choice%"=="2" (
    echo.
    echo Restarting VibeVoice Server...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
    taskkill /F /FI "commandline eq *VibeVoice*" >nul 2>&1
    timeout /t 2 >nul
    echo Starting VibeVoice...
    if exist "START_VIBEVOICE_SERVER.bat" (
        start "VibeVoice" START_VIBEVOICE_SERVER.bat
    ) else (
        echo VibeVoice server script not found. Install VibeVoice first.
    )
    echo VibeVoice Server restarted.
)

if "%restart_choice%"=="3" (
    echo.
    echo Restarting Full AI Ecosystem...
    echo Terminating current processes...
    call EMERGENCY_KILL.bat
    timeout /t 3 >nul
    echo Starting ecosystem...
    start "DuckBot Ecosystem" python start_ai_ecosystem.py
    echo AI Ecosystem restarted.
)

if "%restart_choice%"=="4" (
    echo.
    echo Restarting n8n Workflows...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5678') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 >nul
    echo Starting n8n...
    start "n8n" n8n start
    echo n8n Workflows restarted.
)

if "%restart_choice%"=="5" goto start

timeout /t 3 >nul
goto start

:main_launcher
echo.
echo Opening main launcher...
if exist "SETUP_AND_START_ENHANCED.bat" (
    call SETUP_AND_START_ENHANCED.bat
) else (
    call SETUP_AND_START.bat
)
goto end

:cancel
echo.
echo Operation cancelled by user.
goto end

:end
echo.
echo ===============================================
echo  QUICK KILL SESSION COMPLETED
echo ===============================================
echo Press any key to exit...
pause >nul