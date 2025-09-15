@echo off
echo === DUCKBOT QUICK DIAGNOSTIC ===
echo Directory: %CD%
echo Python: 
python --version 2>&1
echo.
echo Files:
if exist start_ecosystem.py (echo [OK] start_ecosystem.py) else (echo [MISSING] start_ecosystem.py)
if exist duckbot (echo [OK] duckbot directory) else (echo [MISSING] duckbot directory)  
if exist requirements.txt (echo [OK] requirements.txt) else (echo [MISSING] requirements.txt)
echo.
echo Testing python import:
python -c "print('Python basic test: OK')" 2>&1
echo.
echo === DIAGNOSTIC COMPLETE ===
echo.
echo To run DuckBot manually try:
echo   python start_ecosystem.py
echo   or
echo   python -m duckbot.enhanced_webui --port 8787
echo.