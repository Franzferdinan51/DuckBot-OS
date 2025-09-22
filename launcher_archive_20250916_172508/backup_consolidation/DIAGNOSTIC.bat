@echo off
echo Testing basic batch functionality...
echo Current directory: %CD%
echo.
echo Python test:
python --version
echo Python exit code: %ERRORLEVEL%
echo.
echo File check:
if exist start_ecosystem.py echo start_ecosystem.py found
if exist duckbot echo duckbot directory found
echo.
echo This diagnostic completed successfully.
pause