@echo off
REM DuckBot Enhanced WebUI Launcher
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Enhanced WebUI

cd /d "%~dp0"

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

echo.
echo ================================================================================
echo  DUCKBOT ENHANCED WEBUI
echo ================================================================================
echo.
echo Starting Enhanced WebUI with Gradio interface...
echo URL: http://localhost:8787
echo.
echo Features:
echo   - Multi-agent chat system
echo   - System monitoring dashboard
echo   - MCP tools interface
echo   - Dark theme by default
echo.
%PY_CMD% -m duckbot.webui_enhanced --host 127.0.0.1 --port 8787
pause