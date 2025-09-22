@echo off
echo ================================================================================
echo  DUCKBOT DIRECT START - NO CHECKS, JUST RUN
echo ================================================================================
echo.
echo Starting DuckBot directly...
echo Current directory: %CD%
echo.

echo [1] Starting Enhanced WebUI...
start "Enhanced WebUI" python -m duckbot.enhanced_webui --host 0.0.0.0 --port 8787
timeout /t 3 >nul

echo [2] Starting main ecosystem...
python start_ecosystem.py

echo.
echo DuckBot startup completed.
echo Enhanced WebUI should be available at: http://127.0.0.1:8787
echo.
pause