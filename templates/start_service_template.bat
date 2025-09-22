@echo off
REM DuckBot Service Launcher Template
REM Uses centralized configuration management system

REM Set environment (development, production, local)
set "DUCKBOT_ENV=%1"
if "%DUCKBOT_ENV%"=="" set "DUCKBOT_ENV=development"

REM Service to start (webui, monitoring, terminal, etc.)
set "SERVICE_NAME=%2"
if "%SERVICE_NAME%"=="" (
    echo Usage: %0 [environment] [service_name]
    echo Example: %0 development webui
    exit /b 1
)

REM Change to project root
cd /d "%~dp0.."

REM Select best Python launcher
set "PY_CMD=python"
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

echo.
echo ================================================================================
echo  DUCKBOT SERVICE LAUNCHER
echo ================================================================================
echo    Environment: %DUCKBOT_ENV%
echo    Service: %SERVICE_NAME%
echo    Python: %PY_CMD%
echo ================================================================================
echo.

REM Start service using configuration manager
%PY_CMD% -c "
import os
import sys
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager
env = Environment(os.environ.get('DUCKBOT_ENV', 'development'))
cm = get_config_manager(environment=env)

# Get service configuration
service_name = os.environ.get('SERVICE_NAME')
service = cm.get_service_config(service_name)

if not service:
    print(f'ERROR: Service {service_name} not found in configuration')
    sys.exit(1)

if not service.enabled:
    print(f'ERROR: Service {service_name} is disabled')
    sys.exit(1)

print(f'Starting service: {service.name}')

try:
    # Allocate port
    port = cm.allocate_port(service_name)
    print(f'Allocated port: {port}')

    # Set environment variables
    env_vars = cm.get_service_environment(service_name)
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f'Environment: {key}={value}')

    # Start service
    if service.startup_script:
        import subprocess

        cmd = [sys.executable, '-m', service.startup_script]

        print(f'Executing: {\" \".join(cmd)}')
        print(f'Service URL: {cm.get_service_url(service_name)}')
        print()

        # Run service
        subprocess.run(cmd)

    else:
        print(f'ERROR: No startup script defined for service {service_name}')
        sys.exit(1)

except Exception as e:
    print(f'ERROR: Failed to start service: {e}')
    sys.exit(1)
"

if %errorlevel% neq 0 (
    echo [ERROR] Service startup failed
    pause
    exit /b 1
)

echo [SUCCESS] Service completed
pause