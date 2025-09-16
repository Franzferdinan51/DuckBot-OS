@echo off
echo Testing SETUP_AND_START.bat Option 1 (Unified AI-Enhanced WebUI)
echo.

cd /d "%~dp0"

REM Set Unicode encoding
set PYTHONIOENCODING=utf-8

echo [TEST] Running core validation tests first...
python test_simple.py

if errorlevel 1 (
    echo [ERROR] Core tests failed - cannot continue
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Core tests passed - proceeding with Option 1 test
echo.

REM Now test the imports that Option 1 would test
echo [STEP 1] Testing imports...
python -c "from duckbot.service_detector import ServiceDetector; print('[PASS] Service detector works')"
python -c "import start_ai_ecosystem; print('[PASS] AI ecosystem import works')"  
python -c "from duckbot.webui import app; print('[PASS] WebUI import works')"

echo.
echo [STEP 2] Testing service detection...
python -c "
from duckbot.service_detector import ServiceDetector
detector = ServiceDetector()
recommendations = detector.get_startup_recommendations()
print('[SCAN] Service detection results:')
for service_name, rec in recommendations.items():
    if not rec['can_start']:
        print(f'  OK {service_name}: {rec[\"reason\"]}')
    else:
        print(f'  Available {service_name}: Available to start')
print('[SUCCESS] Service detection completed')
"

echo.
echo [STEP 3] Starting WebUI (15 second test)...
echo [INFO] This should show the token and URL, then timeout after 15 seconds
echo [INFO] Look for: WebUI URL and Token in output
echo.

timeout 15 python -m duckbot.webui

echo.
echo [COMPLETED] Option 1 simulation complete!
echo [INFO] If you saw the WebUI token and URL above, Option 1 is working correctly.
echo.
pause