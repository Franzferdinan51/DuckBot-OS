@echo off
echo ===============================================
echo   Installing Missing DuckBot Services
echo ===============================================
echo This script will install:
echo - Node.js (required for n8n)
echo - n8n (workflow automation)
echo - Jupyter (notebook server)
echo ===============================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/4] Node.js not found - Installing Node.js...
    
    REM Try using winget first (Windows 10/11)
    winget install OpenJS.NodeJS >nul 2>&1
    if %errorlevel% neq 0 (
        echo [MANUAL] Please install Node.js manually from https://nodejs.org/
        echo [MANUAL] After installation, re-run this script
        pause
        exit /b 1
    )
    
    echo [1/4] Node.js installed successfully
) else (
    echo [1/4] Node.js already installed
)

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not available after Node.js installation
    echo [MANUAL] Please restart your command prompt and try again
    pause
    exit /b 1
)

REM Install n8n globally
echo [2/4] Installing n8n workflow automation...
npm install -g n8n
if %errorlevel% neq 0 (
    echo [2/4] n8n installation failed - trying with --force flag...
    npm install -g n8n --force
)
echo [2/4] n8n installation completed

REM Install Jupyter using pip
echo [3/4] Installing Jupyter notebook server...
pip install jupyter notebook jupyterlab
if %errorlevel% neq 0 (
    echo [3/4] Jupyter installation failed - trying with --user flag...
    pip install --user jupyter notebook jupyterlab
)
echo [3/4] Jupyter installation completed

REM Install additional Python packages for DuckBot integration
echo [4/4] Installing additional Python packages...
pip install requests websockets aiohttp
echo [4/4] Additional packages installed

echo.
echo ===============================================
echo   Installation Complete!
echo ===============================================
echo Services installed:
echo - Node.js: %cd%
npm --version 2>nul && echo - n8n: Available globally || echo - n8n: Installation may have failed
pip show jupyter 2>nul && echo - Jupyter: Available || echo - Jupyter: Installation may have failed
echo.
echo Next steps:
echo 1. Restart your DuckBot system
echo 2. Try starting services with: python start_ecosystem.py
echo 3. Or start individual services:
echo    - n8n: Start from Windows menu or 'n8n' command
echo    - Jupyter: Start from DuckBot WebUI or 'jupyter notebook'
echo.
echo ===============================================

pause