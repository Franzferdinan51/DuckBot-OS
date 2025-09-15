@echo off
REM Test the exact preflight sequence that should work now
echo Testing preflight sequence...
echo.

echo [CHECK 1/3] Testing Python installation...
python --version 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
) else (
    echo [CHECK 1/3] Python: OK
)

echo.
echo [CHECK 2/3] Testing required files...
if not exist "start_ecosystem.py" (
    echo [ERROR] start_ecosystem.py not found!
    pause
    exit /b 1
) else (
    echo [CHECK 2/3] start_ecosystem.py: FOUND
)

if not exist "duckbot" (
    echo [ERROR] duckbot directory not found!
    pause
    exit /b 1
) else (
    echo [CHECK 2/3] duckbot directory: FOUND
)

echo.
echo [CHECK 3/3] Testing Python ecosystem...
python -c "print('[CHECK 3/3] Basic Python test: OK')"
if %errorlevel% neq 0 (
    echo [ERROR] Python ecosystem test failed!
    pause
    exit /b 1
)

echo.
echo [PREFLIGHT] All checks passed! Ready to start DuckBot.
echo.
echo This is what you should see when running option 1.
echo.
pause
exit /b 0