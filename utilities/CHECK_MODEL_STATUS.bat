@echo off
REM Check DuckBot Dynamic Model Manager Status
chcp 65001 >nul
title DuckBot Model Status Checker
color 0B

cd /d "%~dp0"

echo.
echo ===============================================
echo  🧠 DUCKBOT MODEL STATUS CHECKER
echo ===============================================
echo.

python model_status.py

echo.
echo Press any key to exit...
pause >nul