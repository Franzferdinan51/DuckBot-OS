@echo off
REM Check if model files exist
echo.
echo ================================================================================
echo  CHECKING MODEL FILES
echo ================================================================================
echo.
cd /d "%~dp0"

echo Checking if model directory exists...
if exist "models\Qwen3-Omni-30B-A3B-Instruct" (
    echo [OK] Model directory found
    echo.
    echo Checking model files...
    echo.

    echo Looking for config.json...
    if exist "models\Qwen3-Omni-30B-A3B-Instruct\config.json" (
        echo [✓] config.json found
    ) else (
        echo [❌] config.json missing
    )

    echo Looking for model files...
    dir "models\Qwen3-Omni-30B-A3B-Instruct\*.bin" | find /c ".bin" >nul
    if %errorlevel% equ 0 (
        echo [✓] Model binary files found
        dir "models\Qwen3-Omni-30B-A3B-Instruct\*.bin" | find ".bin"
    ) else (
        echo [❌] No model binary files found
    )

    echo.
    echo Looking for tokenizer files...
    if exist "models\Qwen3-Omni-30B-A3B-Instruct\tokenizer.json" (
        echo [✓] tokenizer.json found
    ) else (
        echo [❌] tokenizer.json missing
    )

    echo.
    echo Total files in model directory:
    dir "models\Qwen3-Omni-30B-A3B-Instruct" | find "File(s)"

) else (
    echo [❌] Model directory not found
    echo Please download the model first using DOWNLOAD_MODEL_OFFICIAL.bat
)

echo.
echo Checking model size...
if exist "models\Qwen3-Omni-30B-A3B-Instruct" (
    for /f "delims=" %%D in ('dir "models\Qwen3-Omni-30B-A3B-Instruct" /s /a-d ^| find "File(s)"') do (
        echo Model directory size: %%D
    )
)

echo.
pause