@echo off
echo ========================================
echo DuckBot-OS v4.2 GitHub Push Script
echo ========================================
echo.

cd /d C:\Users\Ryan\Desktop\DuckBot-OS

echo Current directory: %CD%
echo.

echo Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo ERROR: Git push failed
    echo Please check your GitHub credentials and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! DuckBot-OS v4.2 pushed to GitHub!
echo Repository: https://github.com/Franzferdinan51/DuckBot-OS.git
echo ========================================
echo.

echo Your repository now includes:
echo - Complete Charm ecosystem integration (8 tools)
echo - GitHub Spec-Kit for spec-driven development
echo - Interactive terminal UI components
echo - AI-powered development workflows
echo - All new Python integrations and wrappers
echo.

pause