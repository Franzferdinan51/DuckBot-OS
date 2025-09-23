@echo off
REM Debug launcher to test each step

echo Testing Python...
python --version
echo Error level: %errorlevel%

echo.
echo Testing transformers...
python -c "import transformers; print(transformers.__version__)"
echo Error level: %errorlevel%

echo.
echo Testing transformers silently...
python -c "import transformers; print(transformers.__version__)" >nul 2>&1
echo Error level: %errorlevel%

echo.
echo Testing torch...
python -c "import torch; print(torch.__version__)"
echo Error level: %errorlevel%

echo.
echo Testing torch silently...
python -c "import torch; print(torch.__version__)" >nul 2>&1
echo Error level: %errorlevel%

pause