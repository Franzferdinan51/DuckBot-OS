@echo off
title DuckBot Health Maintenance System

echo 🚀 Starting DuckBot Health Maintenance System...
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Set working directory
cd /d "%~dp0"

REM Check if required modules are available
echo 🔍 Checking dependencies...
python -c "import duckbot.core.health_predictive_maintenance" >nul 2>&1
if errorlevel 1 (
    echo ❌ Health maintenance modules not found
    echo Please ensure DuckBot is properly installed
    pause
    exit /b 1
)

echo ✅ Dependencies verified

REM Check command line arguments
if "%1"=="" (
    echo 📋 Usage: START_HEALTH_MAINTENANCE.bat [option]
    echo.
    echo Available options:
    echo   check          - Run immediate health check
    echo   dashboard      - Show health dashboard
    echo   maintenance    - Show maintenance recommendations
    echo   predictions    - Show prediction insights
    echo   trends day     - Show health trends
    echo   standalone     - Run continuous monitoring
    echo   web            - Start web dashboard
    echo.
    echo Default: Showing dashboard
    python start_health_maintenance.py --dashboard
) else if "%1"=="check" (
    echo 🔍 Running health check...
    python start_health_maintenance.py --check
) else if "%1"=="dashboard" (
    echo 📊 Showing health dashboard...
    python start_health_maintenance.py --dashboard
) else if "%1"=="maintenance" (
    echo 🔧 Showing maintenance recommendations...
    python start_health_maintenance.py --maintenance
) else if "%1"=="predictions" (
    echo 🔮 Showing prediction insights...
    python start_health_maintenance.py --predictions
) else if "%1"=="trends" (
    if "%2"=="" (
        echo 📈 Showing daily health trends...
        python start_health_maintenance.py --trends day
    ) else (
        echo 📈 Showing %2 health trends...
        python start_health_maintenance.py --trends %2
    )
) else if "%1"=="standalone" (
    echo 🚀 Starting continuous monitoring...
    python start_health_maintenance.py --standalone
) else if "%1"=="web" (
    echo 🌐 Starting web dashboard...
    echo Dashboard will be available at: http://localhost:8790
    python start_health_maintenance.py --standalone
) else (
    echo ❌ Unknown option: %1
    echo Use START_HEALTH_MAINTENANCE.bat without arguments to see options
    pause
)

echo.
echo ✨ DuckBot Health Maintenance System completed
pause