@echo off
REM Test transformers model loading directly
echo.
echo ================================================================================
echo  TESTING TRANSFORMERS MODEL LOADING
echo ================================================================================
echo.
echo Testing direct transformers loading of Qwen3-Omni...
echo.
cd /d "%~dp0"

echo @echo off > temp_transformers_test.bat
echo echo Testing direct transformers import... >> temp_transformers_test.bat
echo echo. >> temp_transformers_test.bat
echo python -c "from transformers import Qwen2AudioForConditionalGeneration, Qwen2AudioProcessor; print('✓ Qwen2Audio classes imported successfully')" >> temp_transformers_test.bat
echo echo. >> temp_transformers_test.bat
echo python -c "from transformers import Qwen2AudioForConditionalGeneration, Qwen2AudioProcessor; model = Qwen2AudioForConditionalGeneration.from_pretrained('./models/Qwen3-Omni-30B-A3B-Instruct'); print('✓ Model loaded successfully'); processor = Qwen2AudioProcessor.from_pretrained('./models/Qwen3-Omni-30B-A3B-Instruct'); print('✓ Processor loaded successfully')" >> temp_transformers_test.bat
echo echo. >> temp_transformers_test.bat
echo echo Test completed successfully! >> temp_transformers_test.bat
echo pause >> temp_transformers_test.bat

echo Starting transformers test in new window...
echo.
start "Transformers Test" temp_transformers_test.bat

echo.
echo Check the new window for results.
echo.
pause