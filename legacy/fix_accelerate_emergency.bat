@echo off
title Emergency Accelerate Fix
color 0E
cls

echo ===============================================
echo  🚨 Emergency Accelerate Package Fix
echo ===============================================
echo.
echo The accelerate package is corrupted and returning None version.
echo This will completely reinstall the package.
echo.

cd /d "%~dp0"

echo [1/4] Completely removing accelerate...
"%~dp0python_embeded\python.exe" -m pip uninstall accelerate -y
if exist "%~dp0python_embeded\Lib\site-packages\accelerate" (
    echo Removing leftover files...
    rmdir /s /q "%~dp0python_embeded\Lib\site-packages\accelerate" 2>nul
)

echo [2/4] Clearing pip cache...
"%~dp0python_embeded\python.exe" -m pip cache purge

echo [3/4] Installing fresh accelerate...
"%~dp0python_embeded\python.exe" -m pip install accelerate --force-reinstall --no-cache-dir

echo [4/4] Verifying installation...
"%~dp0python_embeded\python.exe" -c "import accelerate; print('Accelerate version:', accelerate.__version__)" 2>&1

if errorlevel 1 (
    echo.
    echo ❌ Accelerate fix failed. Trying alternative approach...
    echo Installing specific version...
    "%~dp0python_embeded\python.exe" -m pip install "accelerate>=0.20.0,<1.0.0" --force-reinstall --no-cache-dir
)

echo.
echo ===============================================
echo  ✅ Accelerate Fix Complete!
echo ===============================================
echo.
echo Now testing ComfyUI startup...
echo.

REM Test ComfyUI startup
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0

echo Starting ComfyUI test (will timeout after 20 seconds)...
timeout 20 "%~dp0python_embeded\python.exe" "%~dp0ComfyUI\main.py" --cpu --listen 127.0.0.1 --port 8188

echo.
echo If no errors appeared above, ComfyUI should now work!
echo Run launch_ultra_lowvram.bat for full GPU mode.
echo.
pause