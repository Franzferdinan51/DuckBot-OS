@echo off
REM DuckBot Model Training Module Launcher
REM Launches the model training interface

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Model Training Module

echo.
echo ================================================================================
echo  🦆 DUCKBOT MODEL TRAINING MODULE
echo ================================================================================
echo.
echo Starting model training module...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if required files exist
if not exist "model_trainer.py" (
    echo ❌ Model trainer script not found!
    echo Please ensure model_trainer.py is in the current directory.
    echo.
    pause
    exit /b 1
)

REM Install required packages if needed
echo [INFO] Checking required packages...
python -c "import transformers, datasets, torch" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages...
    pip install transformers datasets torch accelerate peft bitsandbytes huggingface_hub
    if errorlevel 1 (
        echo ❌ Failed to install required packages!
        echo Please check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
)

REM Launch the model training module with web UI
echo [INFO] Starting model training module with web UI...
python model_trainer.py --web-ui

echo.
echo 📋 Available commands:
echo    model_trainer.py --config [config_file]        - Train using config file
echo    model_trainer.py --model [model] --dataset [dataset] --output [output] 
echo                         - Train with specified parameters
echo    model_trainer.py --list-models                 - List available models
echo    model_trainer.py --download [hf_model_id]      - Download Hugging Face model
echo    model_trainer.py --web-ui                      - Start web UI (default)
echo.
echo 🚀 Model training module ready!
echo.

REM Keep the window open
cmd /k