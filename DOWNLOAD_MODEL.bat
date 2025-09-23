@echo off
REM Model Download Script for Qwen3-Omni-30B-A3B-Instruct
echo.
echo ================================================================================
echo  QWEN3-OMNI MODEL DOWNLOADER
echo ================================================================================
echo.
echo This will help you download the Qwen3-Omni-30B-A3B-Instruct model
echo from: https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct
echo.
echo The model will be saved to: ./models/Qwen3-Omni-30B-A3B-Instruct
echo.
echo WARNING: This is a 30B parameter model - it's very large!
echo - Download size: ~60GB+
echo - Required disk space: ~100GB+
echo - Recommended: 32GB+ RAM, GPU with 24GB+ VRAM
echo.
echo Options:
echo 1. Download full model (recommended for full experience)
echo 2. Download 4-bit quantized version (smaller, faster)
echo 3. Setup instructions for manual download
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto FULL_DOWNLOAD
if "%choice%"=="2" goto QUANTIZED_DOWNLOAD
if "%choice%"=="3" goto MANUAL_INSTRUCTIONS
if "%choice%"=="4" goto EXIT

:FULL_DOWNLOAD
echo.
echo [OPTION 1] Downloading full Qwen3-Omni-30B-A3B-Instruct model...
echo.
echo IMPORTANT: This model requires Hugging Face authentication!
echo.
echo First, let's check if you're logged in to Hugging Face...
echo.
python -c "from huggingface_hub import whoami; print('✓ Already logged in as:', whoami()['name'])" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Not logged in to Hugging Face.
    echo.
    echo Please authenticate first:
    echo 1. Install Hugging Face CLI: pip install huggingface_hub
    echo 2. Login: huggingface-cli login
    echo 3. OR use token: huggingface-cli login --token YOUR_TOKEN
    echo 4. Get your token from: https://huggingface.co/settings/tokens
    echo.
    echo Trying to login with token...
    echo.
    set /p hf_token="Enter your Hugging Face token (or press Enter to skip): "
    if not "%hf_token%"=="" (
        python -c "from huggingface_hub import login; login('%hf_token%'); print('✓ Login successful!')"
        if %errorlevel% neq 0 (
            echo [ERROR] Login failed. Please check your token.
            pause
            cd ..
            exit /b 1
        )
    )
)

echo.
echo This will download the complete 30B parameter model.
echo Make sure you have:
echo - Hugging Face account with access to Qwen3-Omni-30B-A3B-Instruct
echo - Stable internet connection
echo - ~100GB free disk space
echo - Patience (this may take several hours)
echo.
pause

echo Creating model directory...
if not exist "models" mkdir models
cd models

echo Downloading Qwen3-Omni-30B-A3B-Instruct...
echo This may take several hours depending on your internet speed...
echo.

echo [INFO] Downloading model using Hugging Face Hub...
echo This method uses your Hugging Face login automatically...
echo.

python -c "
from huggingface_hub import snapshot_download
import os

try:
    print('Checking Hugging Face login...')
    from huggingface_hub import whoami
    user_info = whoami()
    print(f'✓ Logged in as: {user_info.get(\"name\", \"Unknown\")}')

    print('Downloading Qwen3-Omni-30B-A3B-Instruct...')
    snapshot_download(
        repo_id='Qwen/Qwen3-Omni-30B-A3B-Instruct',
        local_dir='./Qwen3-Omni-30B-A3B-Instruct',
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=['*.json', '*.bin', '*.txt', '*.py']
    )
    print('✓ Download completed successfully!')

except Exception as e:
    print(f'❌ Download failed: {e}')
    if '401' in str(e):
        print('Authentication error. Please run HF_LOGIN.bat first.')
    elif '403' in str(e):
        print('Access denied. You may need to accept the model\'s terms on Hugging Face.')
    else:
        print('Network or connection error. Please check your internet connection.')
    input('Press Enter to continue...')
"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download failed!
    echo.
    echo Possible solutions:
    echo 1. Install Git LFS: git lfs install
    echo 2. Check your internet connection
    echo 3. Check disk space
    echo 4. Try manual download option
    echo.
    pause
    cd ..
    exit /b 1
)

echo.
echo [SUCCESS] Model downloaded successfully!
echo Model saved to: ./models/Qwen3-Omni-30B-A3B-Instruct
echo.
cd ..
pause
goto EXIT

:QUANTIZED_DOWNLOAD
echo.
echo [OPTION 2] Downloading 4-bit quantized version...
echo.
echo This will download smaller, optimized versions of the model.
echo Requirements:
echo - ~20GB free disk space
echo - 16GB+ RAM
echo - GPU with 8GB+ VRAM recommended
echo.
pause

echo Creating model directory...
if not exist "models" mkdir models
cd models

echo Checking existing directories...
if exist "Qwen3-Omni-30B-A3B-Instruct-GGUF" (
    echo [INFO] GGUF directory exists, checking contents...
    dir "Qwen3-Omni-30B-A3B-Instruct-GGUF" | findstr /c:".bin" >nul
    if %errorlevel% equ 0 (
        echo [OK] GGUF files already exist!
    ) else (
        echo [INFO] GGUF directory exists but is empty, redownloading...
        rmdir /s /q "Qwen3-Omni-30B-A3B-Instruct-GGUF"
    )
)

if exist "Qwen3-Omni-30B-A3B-Instruct-AWQ" (
    echo [INFO] AWQ directory exists, checking contents...
    dir "Qwen3-Omni-30B-A3B-Instruct-AWQ" | findstr /c:".bin" >nul
    if %errorlevel% equ 0 (
        echo [OK] AWQ files already exist!
    ) else (
        echo [INFO] AWQ directory exists but is empty, redownloading...
        rmdir /s /q "Qwen3-Omni-30B-A3B-Instruct-AWQ"
    )
)

echo Downloading 4-bit quantized versions using Hugging Face Hub...
echo.

python -c "
from huggingface_hub import snapshot_download
import os

try:
    print('Checking Hugging Face login...')
    from huggingface_hub import whoami
    user_info = whoami()
    print(f'✓ Logged in as: {user_info.get(\"name\", \"Unknown\")}')

    print('Downloading GGUF quantized version...')
    snapshot_download(
        repo_id='Qwen/Qwen3-Omni-30B-A3B-Instruct-GGUF',
        local_dir='./Qwen3-Omni-30B-A3B-Instruct-GGUF',
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=['*.gguf', '*.json', '*.txt']
    )
    print('✓ GGUF download completed!')

    print('Downloading AWQ quantized version...')
    snapshot_download(
        repo_id='Qwen/Qwen3-Omni-30B-A3B-Instruct-AWQ',
        local_dir='./Qwen3-Omni-30B-A3B-Instruct-AWQ',
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=['*.awq', '*.json', '*.txt', '*.bin']
    )
    print('✓ AWQ download completed!')

    print('')
    print('🎉 All quantized models downloaded successfully!')
    print('')
    print('Available models:')
    print('- GGUF version (good for CPU inference)')
    print('- AWQ version (good for GPU inference)')
    print('')

except Exception as e:
    print(f'❌ Download failed: {e}')
    if '401' in str(e):
        print('Authentication error. Please run HF_LOGIN.bat first.')
    elif '403' in str(e):
        print('Access denied. You may need to accept the model\'s terms on Hugging Face.')
    else:
        print('Network or connection error. Please check your internet connection.')
    input('Press Enter to continue...')
"

:MANUAL_INSTRUCTIONS
echo.
echo [OPTION 3] Manual Download Instructions
echo.
echo To download the model manually:
echo.
echo 1. Visit: https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct
echo 2. Click "Files and versions"
echo 3. Download all files (or use Git LFS)
echo 4. Save them in: ./models/Qwen3-Omni-30B-A3B-Instruct/
echo.
echo Alternative sources:
echo - GGUF quantized versions:
echo   https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct-GGUF
echo - AWQ quantized versions:
echo   https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct-AWQ
echo.
echo After downloading, run START_SIMPLE_QWEN.bat to test the model.
echo.
pause
goto EXIT

:EXIT
echo.
echo Thank you for downloading Qwen3-Omni!
echo After downloading the model, you can run:
echo - START_SIMPLE_QWEN.bat (test the model)
echo - START_DUCKBOT_DEBUG.bat (full system with debug)
echo - START_ELECTRON_LAUNCHER.bat (normal startup)
echo.
pause