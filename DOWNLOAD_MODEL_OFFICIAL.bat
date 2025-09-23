@echo off
REM Official Hugging Face CLI Model Downloader
echo.
echo ================================================================================
echo  OFFICIAL QWEN3-OMNI MODEL DOWNLOADER
echo ================================================================================
echo.
echo This uses the official Hugging Face CLI to download the model.
echo.
echo Steps:
echo 1. Check/install Hugging Face CLI
echo 2. Verify login
echo 3. Download model using official CLI
echo.

cd /d "%~dp0"

REM Step 1: Check/install Hugging Face CLI
echo [STEP 1] Checking Hugging Face CLI...
python -c "import huggingface_hub" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing Hugging Face CLI...
    pip install -U "huggingface_hub[cli]"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Hugging Face CLI!
        pause
        exit /b 1
    )
)
echo [OK] Hugging Face CLI is installed
echo.

REM Step 2: Check Git LFS
echo [STEP 2] Checking Git LFS...
git lfs version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git LFS not found!
    echo Please install Git LFS from: https://git-lfs.com
    pause
    exit /b 1
)
echo [OK] Git LFS is installed
echo.

REM Step 3: Check login
echo [STEP 3] Checking Hugging Face login...
python -c "from huggingface_hub import whoami; print('Logged in as:', whoami()['name'])" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Not logged in to Hugging Face.
    echo.
    echo Please login first:
    echo 1. Run HF_LOGIN.bat
    echo 2. Or use: huggingface-cli login
    echo 3. Get token from: https://huggingface.co/settings/tokens
    echo.
    pause
    exit /b 1
)
python -c "from huggingface_hub import whoami; info = whoami(); print('✓ Logged in as:', info['name'])"
echo.

REM Step 4: Choose download method
echo [STEP 4] Choose download method:
echo.
echo 1. Full model (using huggingface-cli download) - Recommended
echo 2. Git clone method
echo 3. Quantized versions only
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto HF_CLI_DOWNLOAD
if "%choice%"=="2" goto GIT_CLONE_DOWNLOAD
if "%choice%"=="3" goto QUANTIZED_DOWNLOAD
if "%choice%"=="4" goto EXIT

:HF_CLI_DOWNLOAD
echo.
echo [OPTION 1] Downloading using Hugging Face CLI...
echo.
echo Creating models directory...
if not exist "models" mkdir models
cd models

echo Downloading Qwen3-Omni-30B-A3B-Instruct...
echo This may take several hours...
echo.

huggingface-cli download Qwen/Qwen3-Omni-30B-A3B-Instruct --local-dir Qwen3-Omni-30B-A3B-Instruct

if %errorlevel% neq 0 (
    echo [ERROR] Download failed!
    echo.
    echo Alternative command:
    echo python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-Omni-30B-A3B-Instruct', local_dir='Qwen3-Omni-30B-A3B-Instruct')"
    echo.
    cd ..
    pause
    exit /b 1
)

echo [SUCCESS] Model downloaded successfully!
echo Model saved to: models\Qwen3-Omni-30B-A3B-Instruct
cd ..
pause
goto EXIT

:GIT_CLONE_DOWNLOAD
echo.
echo [OPTION 2] Downloading using Git clone...
echo.
echo Creating models directory...
if not exist "models" mkdir models
cd models

echo Installing Git LFS...
git lfs install

echo Cloning repository...
echo This may take several hours and requires good Git LFS setup...
echo.

git clone https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct

if %errorlevel% neq 0 (
    echo [ERROR] Git clone failed!
    echo.
    echo Troubleshooting:
    echo 1. Check Git LFS installation: git lfs version
    echo 2. Check Hugging Face login: huggingface-cli whoami
    echo 3. Try Option 1 instead
    echo.
    cd ..
    pause
    exit /b 1
)

echo [SUCCESS] Model downloaded successfully!
cd ..
pause
goto EXIT

:QUANTIZED_DOWNLOAD
echo.
echo [OPTION 3] Downloading quantized versions...
echo.
echo Creating models directory...
if not exist "models" mkdir models
cd models

echo Downloading GGUF version (CPU optimized)...
huggingface-cli download Qwen/Qwen3-Omni-30B-A3B-Instruct-GGUF --local-dir Qwen3-Omni-30B-A3B-Instruct-GGUF --include "*.gguf *.json *.txt"

echo Downloading AWQ version (GPU optimized)...
huggingface-cli download Qwen/Qwen3-Omni-30B-A3B-Instruct-AWQ --local-dir Qwen3-Omni-30B-A3B-Instruct-AWQ --include "*.awq *.json *.txt *.bin"

echo [SUCCESS] Quantized models downloaded!
echo.
echo Available models:
echo - GGUF version (good for CPU inference)
echo - AWQ version (good for GPU inference)
cd ..
pause
goto EXIT

:EXIT
echo.
echo Download completed!
echo.
echo After downloading, you can test the model with:
echo - START_SIMPLE_QWEN.bat
echo - START_DUCKBOT_DEBUG.bat
echo.
pause