@echo off
title DuckBot v3.1.0 VibeVoice Emergency Kill Script
echo =========================================
echo  DUCKBOT v3.1.0 EMERGENCY KILL SCRIPT
echo =========================================
echo  STREAMLINED: No ComfyUI/Open Notebook
echo =========================================
echo.
echo Terminating all DuckBot processes...
echo.

REM Kill Python processes (covers AI ecosystem, WebUI, VibeVoice, etc.)
echo [1/6] Killing Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

REM Kill Node.js processes (n8n, etc.)
echo [2/6] Killing Node.js processes...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM nodejs.exe >nul 2>&1

REM Kill VibeVoice processes
echo [3/6] Killing VibeVoice TTS processes...
taskkill /F /FI "commandline eq *VibeVoice*" >nul 2>&1
taskkill /F /FI "commandline eq *vibevoice*" >nul 2>&1

REM Kill LM Studio processes
echo [4/6] Killing LM Studio processes...
taskkill /F /IM "LM Studio.exe" >nul 2>&1
taskkill /F /IM lmstudio.exe >nul 2>&1

REM Kill Jupyter processes
echo [5/6] Killing Jupyter processes...
taskkill /F /IM jupyter.exe >nul 2>&1
taskkill /F /IM jupyter-lab.exe >nul 2>&1
taskkill /F /IM jupyter-notebook.exe >nul 2>&1

REM Kill processes using DuckBot ports
echo [6/6] Killing processes on DuckBot ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8787') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8889') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5678') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1234') do taskkill /F /PID %%a >nul 2>&1

REM Kill any remaining DuckBot processes
wmic process where "name like '%%python%%' and commandline like '%%duckbot%%'" delete >nul 2>&1
wmic process where "name like '%%python%%' and commandline like '%%webui%%'" delete >nul 2>&1
wmic process where "name like '%%python%%' and commandline like '%%vibevoice%%'" delete >nul 2>&1
wmic process where "name like '%%python%%' and commandline like '%%ecosystem%%'" delete >nul 2>&1

echo.
echo =========================================
echo  ALL DUCKBOT PROCESSES TERMINATED
echo =========================================
echo.
echo Press any key to exit...
pause >nul