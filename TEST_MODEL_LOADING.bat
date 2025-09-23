@echo off
REM Test Qwen3-Omni Model Loading
echo.
echo ================================================================================
echo  TESTING QWEN3-OMNI MODEL LOADING
echo ================================================================================
echo.
echo This will test if the Qwen3-Omni model can be loaded successfully.
echo.
cd /d "%~dp0"

echo [STEP 1] Testing basic model import...
python -c "
import sys
import os
sys.path.append(os.getcwd())

try:
    from duckbot.core.qwen3_omni_integration import Qwen3OmniIntegration
    print('✓ Qwen3OmniIntegration imported successfully')

    print('✓ Creating integration object...')
    integration = Qwen3OmniIntegration()
    print('✓ Integration object created successfully')

    print('✓ Configuration loaded')
    print(f'  Model ID: {integration.config.model_id}')
    print(f'  Device: {integration.config.device}')
    print(f'  Flash Attention: {integration.config.use_flash_attention}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    input('Press Enter to exit...')
    exit(1)
"
if %errorlevel% neq 0 (
    echo [ERROR] Basic import test failed!
    pause
    exit /b 1
)

echo.
echo [STEP 2] Testing model loading (this may take a while)...
echo.

python -c "
import sys
import os
sys.path.append(os.getcwd())

try:
    from duckbot.core.qwen3_omni_integration import Qwen3OmniIntegration

    print('Loading Qwen3-Omni model...')
    print('This may take several minutes for the first load...')
    print()

    integration = Qwen3OmniIntegration()

    # Load the model
    success = integration.load_model()

    if success:
        print('✓ Model loaded successfully!')
        print(f'  Model type: {type(integration.model).__name__}')
        print(f'  Device: {integration.device}')
        print(f'  Model loaded on: {next(integration.model.parameters()).device}')

        if integration.processor:
            print('✓ Processor loaded successfully')
            print(f'  Processor type: {type(integration.processor).__name__}')

        if integration.tokenizer:
            print('✓ Tokenizer loaded successfully')
            print(f'  Tokenizer type: {type(integration.tokenizer).__name__}')

        print()
        print('✓ All components loaded successfully!')
        print('Qwen3-Omni is ready for use!')

    else:
        print('❌ Model loading failed')
        exit(1)

except Exception as e:
    print(f'❌ Error during model loading: {e}')
    import traceback
    traceback.print_exc()
    input('Press Enter to exit...')
    exit(1)
"
if %errorlevel% neq 0 (
    echo [ERROR] Model loading test failed!
    echo.
    echo This could be due to:
    echo 1. Insufficient RAM/VRAM
    echo 2. Model files corrupted
    echo 3. Missing dependencies
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Qwen3-Omni model is working perfectly!
echo.
echo You can now run the full system with:
echo - START_DUCKBOT_DEBUG.bat
echo - START_ELECTRON_LAUNCHER.bat
echo.
pause