@echo off
echo Simple launcher test
echo.

echo Testing Python...
python --version
if errorlevel 1 (
    echo Python failed
    pause
    exit /b 1
) else (
    echo Python OK
)

echo.
echo Testing Node.js...
node --version
if errorlevel 1 (
    echo Node.js failed
    pause
    exit /b 1
) else (
    echo Node.js OK
)

echo.
echo Testing transformers...
python -c "import transformers; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo Transformers failed
    pause
    exit /b 1
) else (
    echo Transformers OK
)

echo.
echo Testing torch...
python -c "import torch; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo Torch failed
    pause
    exit /b 1
) else (
    echo Torch OK
)

echo.
echo Testing directory...
if exist "qwen3-omni-ui" (
    echo Directory OK
) else (
    echo Directory failed
    pause
    exit /b 1
)

echo.
echo All tests passed!
pause