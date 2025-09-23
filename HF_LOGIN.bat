@echo off
REM Hugging Face Login Helper
echo.
echo ================================================================================
echo  HUGGING FACE LOGIN HELPER
echo ================================================================================
echo.
echo This script will help you log in to Hugging Face to download the Qwen3-Omni model.
echo.
echo Steps:
echo 1. Get your Hugging Face token from: https://huggingface.co/settings/tokens
echo 2. Make sure you have accepted the model's terms of use
echo 3. Enter your token when prompted
echo.
echo [STEP 1] Checking if huggingface_hub is installed...
python -c "import huggingface_hub" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing huggingface_hub...
    pip install huggingface_hub
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install huggingface_hub!
        pause
        exit /b 1
    )
)

echo [OK] huggingface_hub is installed
echo.

echo [STEP 2] Checking if you're already logged in...
python -c "from huggingface_hub import whoami; print('Logged in as:', whoami()['name'])" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] You are already logged in to Hugging Face!
    echo.
    python -c "from huggingface_hub import whoami; info = whoami(); print('Username:', info['name']); print('Email:', info.get('email', 'Not available'))"
    echo.
    set /p continue="Do you want to continue with this account? (y/n): "
    if /i "%continue%"=="n" goto LOGIN_NEW
    goto DONE
)

:LOGIN_NEW
echo [STEP 3] Please log in to Hugging Face...
echo.
echo You can:
echo 1. Enter your Hugging Face token directly
echo 2. Use interactive login (opens browser)
echo.
set /p login_method="Choose login method (1 or 2): "

if "%login_method%"=="1" goto TOKEN_LOGIN
if "%login_method%"=="2" goto INTERACTIVE_LOGIN
echo [ERROR] Invalid choice. Please enter 1 or 2.
pause
goto LOGIN_NEW

:TOKEN_LOGIN
echo.
set /p hf_token="Enter your Hugging Face token: "
if "%hf_token%"=="" (
    echo [ERROR] Token cannot be empty!
    pause
    goto LOGIN_NEW
)

echo [INFO] Logging in with token...
python -c "from huggingface_hub import login; login('%hf_token%'); print('✓ Login successful!')"
if %errorlevel% neq 0 (
    echo [ERROR] Login failed! Please check your token.
    pause
    goto LOGIN_NEW
)
goto DONE

:INTERACTIVE_LOGIN
echo.
echo [INFO] Starting interactive login...
echo This will open your browser for authentication.
echo.
python -c "from huggingface_hub import login; login(add_to_git_credential=True)"
if %errorlevel% neq 0 (
    echo [ERROR] Interactive login failed!
    echo Please try option 1 (token login) instead.
    pause
    goto LOGIN_NEW
)
goto DONE

:DONE
echo.
echo [STEP 4] Verifying login...
python -c "from huggingface_hub import whoami; info = whoami(); print('✓ Successfully logged in!'); print('Username:', info['name']); print('Email:', info.get('email', 'Not available'))"
if %errorlevel% neq 0 (
    echo [ERROR] Login verification failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Hugging Face login completed!
echo.
echo Now you can download the Qwen3-Omni model using DOWNLOAD_MODEL.bat
echo.
pause