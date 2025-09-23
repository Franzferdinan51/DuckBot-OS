@echo off
echo Diagnosing launcher issues...
echo.

echo Current directory: %CD%
echo.

echo Testing Python:
python --version
echo Error level: %errorlevel%

echo.
echo Testing transformers:
python -c "import transformers; print('Transformers works')" 2>nul
echo Error level: %errorlevel%

echo.
echo Testing torch:
python -c "import torch; print('Torch works')" 2>nul
echo Error level: %errorlevel%

echo.
echo Testing Node.js:
node --version
echo Error level: %errorlevel%

echo.
echo Testing directories:
if exist "qwen3-omni-ui" (
    echo qwen3-omni-ui: EXISTS
) else (
    echo qwen3-omni-ui: MISSING
)

if exist "models" (
    echo models: EXISTS
) else (
    echo models: MISSING
)

echo.
echo Testing Python path:
where python

pause