@echo off
REM List all files in model directory
echo.
echo ================================================================================
echo  LISTING MODEL DIRECTORY CONTENTS
echo ================================================================================
echo.
cd /d "%~dp0"

if not exist "models\Qwen3-Omni-30B-A3B-Instruct" (
    echo [ERROR] Model directory not found!
    pause
    exit /b 1
)

echo Showing all files in models\Qwen3-Omni-30B-A3B-Instruct\
echo.
dir "models\Qwen3-Omni-30B-A3B-Instruct" /b /s

echo.
echo ================================================================================
echo.
echo Showing file types and sizes:
echo.
dir "models\Qwen3-Omni-30B-A3B-Instruct\*.json" /b
echo.
dir "models\Qwen3-Omni-30B-A3B-Instruct\*.bin" /b
echo.
dir "models\Qwen3-Omni-30B-A3B-Instruct\*.txt" /b
echo.
dir "models\Qwen3-Omni-30B-A3B-Instruct\*.py" /b
echo.

echo ================================================================================
echo.
echo Checking for specific essential files:
echo.
if exist "models\Qwen3-Omni-30B-A3B-Instruct\config.json" (
    echo [✓] config.json - EXISTS
) else (
    echo [❌] config.json - MISSING
)

if exist "models\Qwen3-Omni-30B-A3B-Instruct\pytorch_model.bin" (
    echo [✓] pytorch_model.bin - EXISTS
) else (
    echo [❌] pytorch_model.bin - MISSING
)

if exist "models\Qwen3-Omni-30B-A3B-Instruct\tokenizer.json" (
    echo [✓] tokenizer.json - EXISTS
) else (
    echo [❌] tokenizer.json - MISSING
)

if exist "models\Qwen3-Omni-30B-A3B-Instruct\model.safetensors" (
    echo [✓] model.safetensors - EXISTS
) else (
    echo [❌] model.safetensors - MISSING
)

echo.
pause