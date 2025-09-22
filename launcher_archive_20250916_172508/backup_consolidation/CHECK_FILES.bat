@echo off
echo ================================================================================
echo  DUCKBOT FILE STRUCTURE DIAGNOSTIC
echo ================================================================================
echo.
echo Current Directory: %CD%
echo.
echo Checking for required files and directories...
echo.

echo [CHECK 1] Python installation:
python --version 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found or not working
) else (
    echo ✅ Python is working
)

echo.
echo [CHECK 2] Required files:
if exist "start_ecosystem.py" (
    echo ✅ start_ecosystem.py - FOUND
) else (
    echo ❌ start_ecosystem.py - MISSING
)

if exist "duckbot" (
    echo ✅ duckbot directory - FOUND
    if exist "duckbot\enhanced_webui.py" (
        echo   ✅ duckbot\enhanced_webui.py - FOUND
    ) else (
        echo   ❌ duckbot\enhanced_webui.py - MISSING
    )
) else (
    echo ❌ duckbot directory - MISSING
)

echo.
echo [CHECK 3] Directory contents:
echo ================================================================================
dir /b
echo ================================================================================

echo.
echo [CHECK 4] Python path and modules:
python -c "import sys; print('Python executable:', sys.executable)"
python -c "import os; print('Current working directory:', os.getcwd())"

echo.
echo [CHECK 5] Testing duckbot module import:
python -c "
try:
    import duckbot
    print('✅ duckbot module can be imported')
except ImportError as e:
    print('❌ duckbot module import failed:', e)
except Exception as e:
    print('❌ duckbot module error:', e)
"

echo.
echo ================================================================================
echo  DIAGNOSTIC COMPLETE
echo ================================================================================
echo.
echo If any required files are missing, make sure you're running this from
echo the correct DuckBot directory that contains:
echo   - start_ecosystem.py
echo   - duckbot/ directory
echo   - All the Python module files
echo.
pause