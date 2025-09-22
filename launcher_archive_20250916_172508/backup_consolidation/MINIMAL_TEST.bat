@echo off
echo Starting minimal test...
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Testing Python:
python --version
echo.
echo Testing ecosystem:
python start_ecosystem.py
echo.
echo Test complete.
pause