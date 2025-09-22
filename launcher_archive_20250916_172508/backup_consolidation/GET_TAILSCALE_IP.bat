@echo off
echo ================================================================================
echo  TAILSCALE IP DETECTION AND DUCKBOT ACCESS INFORMATION
echo ================================================================================
echo.
echo Detecting Tailscale IP address...
echo.

REM Method 1: Try tailscale ip command
tailscale ip --4 2>nul
if %errorlevel% equ 0 (
    echo Tailscale IP detected via 'tailscale ip' command
    for /f %%i in ('tailscale ip --4 2^>nul') do set TAILSCALE_IP=%%i
    goto :show_info
)

REM Method 2: Parse ipconfig for Tailscale adapter
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "tailscale" -A 5 ^| findstr "IPv4"') do (
    set TAILSCALE_IP=%%i
    set TAILSCALE_IP=!TAILSCALE_IP: =!
    goto :show_info
)

REM Method 3: Check common Tailscale IP ranges
for /f "tokens=14" %%i in ('ipconfig ^| findstr "100\."') do (
    set TAILSCALE_IP=%%i
    goto :show_info
)

echo Tailscale IP not detected. Possible reasons:
echo - Tailscale is not installed
echo - Tailscale is not running
echo - Device is not connected to Tailscale network
echo.
echo Install Tailscale from: https://tailscale.com/download
echo.
pause
exit /b 1

:show_info
if defined TAILSCALE_IP (
    echo ✓ Tailscale IP Address: %TAILSCALE_IP%
    echo.
    echo ================================================================================
    echo  DUCKBOT TAILSCALE ACCESS URLS
    echo ================================================================================
    echo.
    echo Use these URLs to access DuckBot from any device on your Tailscale network:
    echo.
    echo PRIMARY INTERFACES:
    echo   Enhanced WebUI Dashboard:     http://%TAILSCALE_IP%:8787
    echo   System Monitoring Dashboard:  http://%TAILSCALE_IP%:8789
    echo.
    echo ALTERNATIVE INTERFACES:
    echo   Charm WebUI (if running):     http://%TAILSCALE_IP%:8788
    echo   Developer Mode (if running):  http://%TAILSCALE_IP%:8787
    echo.
    echo NOTES:
    echo   - These URLs work from any device connected to your Tailscale network
    echo   - No port forwarding or firewall configuration needed
    echo   - Secure encrypted connection via Tailscale
    echo   - Services must be started with host 0.0.0.0 (not 127.0.0.1)
    echo.
    echo TROUBLESHOOTING:
    echo   - If URLs don't work, ensure services are running with --host 0.0.0.0
    echo   - Check Windows Firewall allows Python through
    echo   - Verify Tailscale is connected on both devices
    echo.
) else (
    echo Tailscale IP detection failed
)

echo ================================================================================
pause