@echo off
REM Generate Open WebUI Extension Files for DuckBot Integration

echo ================================================================
echo  DuckBot Open WebUI Extension Generator
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not available. Please install Python 3.8+.
    pause
    exit /b 1
)

echo [INFO] Generating Open WebUI extension files...
echo.

REM Run the extension generator
python -c "from open_webui_extension import duckbot_extension; duckbot_extension.generate_extension_files('.')"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Open WebUI extension files generated successfully!
    echo.
    echo Generated files:
    echo   - duckbot_extension.json (extension manifest)
    echo   - duckbot_extension.js (JavaScript extension)
    echo   - duckbot_extension.css (styles)
    echo   - INSTALL.md (installation instructions)
    echo.
    echo [INFO] Copy these files to your Open WebUI extensions directory
    echo [INFO] Typical locations:
    echo   - Local: ./extensions/
    echo   - Docker: /var/lib/open-webui/extensions/
    echo.
    echo [INFO] Restart Open WebUI after installing the extension
) else (
    echo.
    echo [ERROR] Failed to generate extension files
    echo [ERROR] Check if DuckBot modules are available
)

echo.
pause