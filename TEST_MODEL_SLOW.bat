@echo off
REM Slow Model Test with Pauses
echo Testing Qwen3-Omni Model...
cd /d "%~dp0"

echo.
echo [STEP 1] Creating temporary test script...
echo @echo off > temp_model_test.bat
echo echo Testing Qwen3-Omni model loading... >> temp_model_test.bat
echo echo. >> temp_model_test.bat
echo echo This will test if the model can be loaded... >> temp_model_test.bat
echo echo. >> temp_model_test.bat
echo python -c "import sys; import os; sys.path.append(os.getcwd()); from duckbot.core.qwen3_omni_integration import Qwen3OmniIntegration; integration = Qwen3OmniIntegration(); print('✓ Integration object created'); print('Loading model...'); result = integration.load_model(); print('✓ Model load completed:', result)" >> temp_model_test.bat
echo echo. >> temp_model_test.bat
echo echo If you see this, the test completed. >> temp_model_test.bat
echo pause >> temp_model_test.bat

echo [STEP 2] Starting model test in new window...
echo.
echo A new window will open to run the test.
echo Watch for error messages in that window.
echo.
pause

start "Qwen3-Omni Model Test" temp_model_test.bat

echo [INFO] Test started in new window.
echo.
echo Check the new window for results.
echo.
pause