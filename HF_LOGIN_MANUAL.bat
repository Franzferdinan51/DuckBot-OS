@echo off
REM Manual Hugging Face Login - Open browser and show commands
echo.
echo ================================================================================
echo  MANUAL HUGGING FACE LOGIN
echo ================================================================================
echo.
echo This will open the Hugging Face website and show you the commands to run.
echo.
echo [STEP 1] Opening Hugging Face tokens page...
start https://huggingface.co/settings/tokens
echo.
echo [STEP 2] If you don't have a token, create one:
echo.
echo - Click "New token"
echo - Name it something like "duckbot-qwen3"
echo - Set role to "write" (recommended)
echo - Click "Generate a token"
echo - Copy the token (it starts with "hf_")
echo.
echo [STEP 3] Login using Python command:
echo.
echo Run this command in a terminal:
echo python -c "from huggingface_hub import login; login('YOUR_TOKEN_HERE')"
echo.
echo Replace YOUR_TOKEN_HERE with your actual token.
echo.
echo [STEP 4] Alternative: Create a login script...
echo @echo off > temp_login.bat
echo python -c "from huggingface_hub import login; login('%%1')" >> temp_login.bat
echo echo Login complete! >> temp_login.bat
echo pause >> temp_login.bat
echo.
echo Created temp_login.bat - run it with: temp_login.bat YOUR_TOKEN
echo.
echo [STEP 5] Testing login...
python -c "from huggingface_hub import whoami; print('Currently logged in as:', whoami()['name'])" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [OK] You are already logged in!
    python -c "from huggingface_hub import whoami; info = whoami(); print('Username:', info['name']); print('Email:', info.get('email', 'Not available'))"
) else (
    echo.
    echo [INFO] Not currently logged in.
)
echo.
pause