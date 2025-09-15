@echo off
echo Testing menu display...
echo.

:main_menu
cls
echo.
echo ================================================================================
echo  DUCKBOT MENU TEST
echo ================================================================================
echo.
echo LAUNCH MODES:
echo.
echo 1. [ULTIMATE] Complete Ultimate Enhanced Mode - RECOMMENDED!
echo.
echo 2. [ENHANCED-WEBUI] Enhanced WebUI Dashboard
echo.
echo 3. [CHARM-TERMINAL] Charm Terminal Interface
echo.
echo 4. [STATUS] Quick System Status
echo.
echo 5. [TEST] Test All Integrations
echo.
echo 6. [INSTALL] Auto-Install Missing Components
echo.
echo Q. [QUIT] Exit Launcher
echo.

echo DEBUG: About to show input prompt
set /p choice="Enter your choice (1-6 or Q): "

echo.
echo DEBUG: You entered: [%choice%]
echo.

if /i "%choice%"=="Q" goto exit
if /i "%choice%"=="q" goto exit

echo You selected option: %choice%
echo This proves the menu is working!
echo.
pause
goto main_menu

:exit
echo Exiting menu test.
exit /b 0