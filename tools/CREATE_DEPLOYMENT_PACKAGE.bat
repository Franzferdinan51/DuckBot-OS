@echo off
title Creating DuckBot v3.1.0 Enhanced Deployment Package
color 0B

echo ================================================================
echo    Creating DuckBot v3.1.0 Enhanced Deployment Package
echo ================================================================
echo.

echo [CLEANUP] Preparing deployment package...

:: Create temp deployment directory
set DEPLOY_DIR=%TEMP%\DuckBot-v3.1.0-Enhanced-Deploy
if exist "%DEPLOY_DIR%" rmdir /s /q "%DEPLOY_DIR%"
mkdir "%DEPLOY_DIR%"

echo [COPY] Copying core files...

:: Copy essential files (excluding runtime data)
robocopy . "%DEPLOY_DIR%" *.py /S
robocopy . "%DEPLOY_DIR%" *.bat
robocopy . "%DEPLOY_DIR%" *.md
robocopy . "%DEPLOY_DIR%" *.txt
robocopy . "%DEPLOY_DIR%" *.yaml
robocopy . "%DEPLOY_DIR%" *.yml
robocopy . "%DEPLOY_DIR%" *.json
robocopy . "%DEPLOY_DIR%" *.html
robocopy . "%DEPLOY_DIR%" *.css
robocopy . "%DEPLOY_DIR%" *.js

:: Copy directories but exclude runtime data
robocopy duckbot "%DEPLOY_DIR%\duckbot" /S /XD __pycache__
robocopy workflows "%DEPLOY_DIR%\workflows" /S
robocopy ComfyUI "%DEPLOY_DIR%\ComfyUI" /S /XD __pycache__

:: Create necessary empty directories
mkdir "%DEPLOY_DIR%\data"
mkdir "%DEPLOY_DIR%\logs"
mkdir "%DEPLOY_DIR%\temp"

echo [CLEANUP] Removing unnecessary files...

:: Remove runtime and temporary files from deployment
del /s /q "%DEPLOY_DIR%\*.pyc" >nul 2>&1
del /s /q "%DEPLOY_DIR%\*.pyo" >nul 2>&1
del /s /q "%DEPLOY_DIR%\*.db" >nul 2>&1
del /s /q "%DEPLOY_DIR%\*.log" >nul 2>&1
rmdir /s /q "%DEPLOY_DIR%\__pycache__" >nul 2>&1

echo [PACKAGE] Creating deployment zip...

:: Create final deployment package
powershell "Compress-Archive -Path '%DEPLOY_DIR%\*' -DestinationPath 'C:\Users\Ryan\Desktop\DuckBot-v3.1.0-Enhanced-Complete.zip' -Force"

if exist "C:\Users\Ryan\Desktop\DuckBot-v3.1.0-Enhanced-Complete.zip" (
    echo.
    echo ================================================================
    echo    🎉 DEPLOYMENT PACKAGE CREATED SUCCESSFULLY!
    echo ================================================================
    echo.
    echo 📦 Package Location: C:\Users\Ryan\Desktop\DuckBot-v3.1.0-Enhanced-Complete.zip
    echo 🗂️ Package Contents:
    echo    • Complete DuckBot v3.1.0 Enhanced source code
    echo    • Real WSL Integration (Linux commands)
    echo    • ByteBot Task Automation (Natural language)
    echo    • Archon Multi-Agent System (Knowledge management)
    echo    • ChromiumOS Browser Integration (Advanced web features)
    echo    • DuckBot OS WebUI (35 professional applications)
    echo    • Enhanced startup scripts and documentation
    echo    • All dependencies and configuration files
    echo.
    echo 🚀 Ready for:
    echo    • GitHub repository upload
    echo    • Distribution to other systems
    echo    • Production deployment
    echo.
    echo 📋 Installation Instructions:
    echo    1. Extract the zip file
    echo    2. Run START_ENHANCED_ECOSYSTEM.bat
    echo    3. Choose startup mode (Full/Local/Hybrid)
    echo    4. Access http://localhost:8787 for DuckBot OS
    echo.
) else (
    echo.
    echo ❌ Package creation failed!
    echo Please check for errors and try again.
)

:: Cleanup temp directory
rmdir /s /q "%DEPLOY_DIR%"

echo.
echo Press any key to continue...
pause >nul