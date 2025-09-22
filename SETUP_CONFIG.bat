@echo off
REM DuckBot v4.2 Configuration Setup Launcher
REM Interactive wizard for configuring API keys and settings

echo.
echo 🦆 DuckBot v4.2 Configuration Setup
echo ===================================
echo.

REM Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Change to config directory
cd /d "%~dp0config"

REM Check if required dependencies are installed
echo 📦 Checking dependencies...
python -c "import inquirer, yaml, requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        echo Please run: pip install inquirer PyYAML requests python-dotenv
        pause
        exit /b 1
    )
)

REM Run the setup wizard
echo 🚀 Starting configuration wizard...
echo.
python setup_wizard.py

if errorlevel 1 (
    echo ❌ Setup wizard encountered an error
    pause
    exit /b 1
)

echo.
echo ✅ Configuration setup complete!
echo.
echo 📊 Next steps:
echo 1. Run validation: python validate_config.py
echo 2. Start DuckBot: START_ENHANCED_DUCKBOT.bat
echo.
pause