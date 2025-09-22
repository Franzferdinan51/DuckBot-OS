@echo off
echo Testing file detection...
echo.
echo Current directory: %CD%
echo.
echo Testing if start_ecosystem.py exists...
if exist "start_ecosystem.py" (
    echo ✅ start_ecosystem.py found using 'if exist'
) else (
    echo ❌ start_ecosystem.py NOT found using 'if exist'
)

echo.
echo Testing with dir command...
dir start_ecosystem.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ start_ecosystem.py found using 'dir'
) else (
    echo ❌ start_ecosystem.py NOT found using 'dir'
)

echo.
echo Testing with full path...
if exist "%CD%\start_ecosystem.py" (
    echo ✅ start_ecosystem.py found using full path
) else (
    echo ❌ start_ecosystem.py NOT found using full path
)

echo.
echo File details:
dir start_ecosystem.py 2>nul

echo.
echo Directory listing of *.py files:
dir *.py 2>nul

pause