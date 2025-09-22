@echo off
REM DuckBot Model Training Module Launcher for Electron
REM This script is called by the Electron launcher

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Model Training Module

echo.
echo ================================================================================
echo  🦆 DUCKBOT MODEL TRAINING MODULE
echo ================================================================================
echo.
echo Starting model training module from Electron launcher...
echo.

REM Change to the model training module directory
cd /d "%~dp0"

REM Check if required files exist
if not exist "model_trainer.py" (
    echo ❌ Model trainer script not found!
    echo Please ensure model_trainer.py is in the launcher-modules\model-training directory.
    echo.
    pause
    exit /b 1
)

REM Launch the web UI for the model training module
echo [INFO] Starting Model Training Web UI...
python model_trainer.py --web-ui --port 8080

if errorlevel 1 (
    echo ❌ Failed to start Model Training Web UI!
    echo.
    pause
    exit /b 1
)

echo.
echo 🚀 Model Training Module started successfully!
echo Access the UI at http://localhost:8080/autotrain_ui.html
echo.

REM Keep the window open
cmd /k