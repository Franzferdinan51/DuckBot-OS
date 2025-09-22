@echo off
REM DuckBot Enhanced Launcher with Configuration Management
REM Uses centralized configuration system

chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v4.2 - Enhanced Configuration Management
color 0A

REM Change to script directory
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

REM Set environment from parameter or default
set "DUCKBOT_ENV=%1"
if "%DUCKBOT_ENV%"=="" set "DUCKBOT_ENV=development"

echo.
echo ================================================================================
echo  DUCKBOT v4.2 ENHANCED CONFIGURATION MANAGEMENT
echo ================================================================================
echo    Environment: %DUCKBOT_ENV%
echo    Configuration: Centralized YAML-based system
echo    Python Command: %PY_CMD%
echo ================================================================================
echo.

REM Validate configuration
echo [STEP 1] Validating configuration...
%PY_CMD% -c "from config.config_manager import get_config_manager; cm = get_config_manager(); issues = cm.validate_config(); [print(f'  [WARN] {issue}') for issue in issues] or print('  [OK] Configuration validation passed')"

if %errorlevel% neq 0 (
    echo [ERROR] Configuration validation failed
    pause
    exit /b 1
)

REM Show system information
echo [STEP 2] Loading system information...
%PY_CMD% -c "from config.config_manager import get_config_manager; cm = get_config_manager(); info = cm.get_system_info(); print(f'  Environment: {info[\"environment\"]}'); print(f'  Enabled Services: {info[\"enabled_services\"]}'); print(f'  Configuration File: {info[\"config_path\"]}')"

echo.
echo LAUNCH MODES:
echo.
echo 1. [ENHANCED] Complete Enhanced Mode
echo    All enabled services with configuration management
echo.
echo 2. [WEBUI] WebUI Only Mode
echo    Start only the WebUI service
echo.
echo 3. [MONITORING] Monitoring Only Mode
echo    Start only the monitoring service
echo.
echo 4. [LOCAL] Local-Only Mode
echo    Offline mode with local AI only
echo.
echo 5. [CONFIG] Configuration Management
echo    View and manage configuration settings
echo.
echo 6. [VALIDATE] Validate Configuration
echo    Run comprehensive configuration validation
echo.
echo 7. [EXPORT] Export Configuration
echo    Export current configuration to different formats
echo.
echo 8. [INFO] System Information
echo    Display detailed system and configuration information
echo.
echo 9. [EXIT] Exit
echo.

set /p choice="Select mode (1-9): "

if "%choice%"=="1" goto enhanced_mode
if "%choice%"=="2" goto webui_mode
if "%choice%"=="3" goto monitoring_mode
if "%choice%"=="4" goto local_mode
if "%choice%"=="5" goto config_management
if "%choice%"=="6" goto validate_config
if "%choice%"=="7" goto export_config
if "%choice%"=="8" goto system_info
if "%choice%"=="9" goto exit

echo [ERROR] Invalid choice
pause
goto main_menu

:enhanced_mode
echo [START] Starting Enhanced Mode...
set "DUCKBOT_ENV=%DUCKBOT_ENV%"
%PY_CMD% -c "
import os
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager
env = Environment(os.environ.get('DUCKBOT_ENV', 'development'))
cm = get_config_manager(environment=env)

# Get enabled services
services = cm.get_enabled_services()
print(f'Starting {len(services)} services...')

# Start each service
for service_name, service in services.items():
    if not service.external_service:
        print(f'  Starting {service_name}...')
        try:
            # Allocate port
            port = cm.allocate_port(service_name)

            # Set environment variables
            env_vars = cm.get_service_environment(service_name)
            for key, value in env_vars.items():
                os.environ[key] = value

            # Start service
            if service.startup_script:
                import subprocess
                import sys

                cmd = [sys.executable, '-m', service.startup_script]

                # Run in background for non-blocking startup
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                print(f'    [OK] {service_name} started on port {port}')

        except Exception as e:
            print(f'    [ERROR] Failed to start {service_name}: {e}')

print('Enhanced mode startup completed!')
"
pause
goto main_menu

:webui_mode
echo [START] Starting WebUI Only Mode...
set "DUCKBOT_ENV=%DUCKBOT_ENV%"
%PY_CMD% -c "
import os
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager
env = Environment(os.environ.get('DUCKBOT_ENV', 'development'))
cm = get_config_manager(environment=env)

# Get WebUI service
webui_service = cm.get_service_config('webui')
if webui_service and webui_service.enabled:
    # Allocate port
    port = cm.allocate_port('webui')

    # Set environment variables
    env_vars = cm.get_service_environment('webui')
    for key, value in env_vars.items():
        os.environ[key] = value

    # Start WebUI
    import subprocess
    import sys

    cmd = [sys.executable, '-m', webui_service.startup_script]
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    print(f'WebUI started on http://localhost:{port}')
    print(f'Access WebUI at: http://localhost:{port}')
else:
    print('WebUI service is not enabled in configuration')
"
pause
goto main_menu

:monitoring_mode
echo [START] Starting Monitoring Only Mode...
set "DUCKBOT_ENV=%DUCKBOT_ENV%"
%PY_CMD% -c "
import os
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager
env = Environment(os.environ.get('DUCKBOT_ENV', 'development'))
cm = get_config_manager(environment=env)

# Get monitoring service
monitoring_service = cm.get_service_config('monitoring')
if monitoring_service and monitoring_service.enabled:
    # Allocate port
    port = cm.allocate_port('monitoring')

    # Set environment variables
    env_vars = cm.get_service_environment('monitoring')
    for key, value in env_vars.items():
        os.environ[key] = value

    # Start monitoring
    import subprocess
    import sys

    cmd = [sys.executable, '-m', monitoring_service.startup_script]
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    print(f'Monitoring started on http://localhost:{port}')
    print(f'Access monitoring at: http://localhost:{port}')
else:
    print('Monitoring service is not enabled in configuration')
"
pause
goto main_menu

:local_mode
echo [START] Starting Local-Only Mode...
set "DUCKBOT_ENV=local"
%PY_CMD% -c "
import os
from config.config_manager import get_config_manager, Environment

# Initialize configuration manager for local mode
cm = get_config_manager(environment=Environment.LOCAL)

# Check if LM Studio is required and available
lm_studio_service = cm.get_service_config('lm_studio')
if lm_studio_service and lm_studio_service.required:
    print('Checking LM Studio availability...')
    if cm.is_service_available('lm_studio'):
        print('  [OK] LM Studio is available')
    else:
        print('  [ERROR] LM Studio is required but not available')
        print('  Please start LM Studio with local server enabled (localhost:1234)')
        exit(1)

# Get enabled local services
services = cm.get_enabled_services()
print(f'Starting {len(services)} local services...')

# Start each service
for service_name, service in services.items():
    if not service.external_service:
        print(f'  Starting {service_name}...')
        try:
            # Allocate port
            port = cm.allocate_port(service_name)

            # Set environment variables
            env_vars = cm.get_service_environment(service_name)
            for key, value in env_vars.items():
                os.environ[key] = value

            # Start service
            if service.startup_script:
                import subprocess
                import sys

                cmd = [sys.executable, '-m', service.startup_script]
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                print(f'    [OK] {service_name} started on port {port}')

        except Exception as e:
            print(f'    [ERROR] Failed to start {service_name}: {e}')

print('Local mode startup completed!')
print('All services running in offline mode')
"
pause
goto main_menu

:config_management
echo [CONFIG] Configuration Management
echo.
echo 1. View Configuration
echo 2. List Services
echo 3. Check Service Status
echo 4. View Feature Flags
echo 5. Test Configuration
echo 6. Back to Main Menu
echo.

set /p config_choice="Select option (1-6): "

if "%config_choice%"=="1" goto view_config
if "%config_choice%"=="2" goto list_services
if "%config_choice%"=="3" goto check_status
if "%config_choice%"=="4" goto view_features
if "%config_choice%"=="5" goto test_config
if "%config_choice%"=="6" goto main_menu

echo [ERROR] Invalid choice
pause
goto config_management

:view_config
echo [CONFIG] Current Configuration
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
info = cm.get_system_info()
print(f'Environment: {info[\"environment\"]}')
print(f'Config Path: {info[\"config_path\"]}')
print(f'Enabled Services: {info[\"enabled_services\"]}')
print(f'Total Services: {info[\"total_services\"]}')
print(f'Validation Issues: {len(info[\"validation_issues\"])}')
for issue in info['validation_issues']:
    print(f'  - {issue}')
"
pause
goto config_management

:list_services
echo [SERVICES] Available Services
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
services = cm.get_all_services()
print(f'Total Services: {len(services)}')
print()
for name, service in services.items():
    status = 'ENABLED' if service.enabled else 'DISABLED'
    port = service.current_port or service.default_port
    print(f'{name}: {status} (Port: {port})')
"
pause
goto config_management

:check_status
echo [STATUS] Service Status Check
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
services = cm.get_enabled_services()
print('Checking service availability...')
print()
for name in services.keys():
    available = cm.is_service_available(name)
    status = 'AVAILABLE' if available else 'UNAVAILABLE'
    url = cm.get_service_url(name)
    print(f'{name}: {status}')
    if url:
        print(f'  URL: {url}')
"
pause
goto config_management

:view_features
echo [FEATURES] Feature Flags
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
features = cm.config_data.get('features', {})
print('Feature Flags:')
print()
for name, enabled in features.items():
    status = 'ENABLED' if enabled else 'DISABLED'
    print(f'{name}: {status}')
"
pause
goto config_management

:test_config
echo [TEST] Configuration Test
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
print('Testing configuration system...')
print()

# Test service allocation
try:
    port = cm.allocate_port('test_service')
    print(f'✓ Port allocation test passed: {port}')
    cm.release_port(port)
except Exception as e:
    print(f'✗ Port allocation test failed: {e}')

# Test service environment
env_vars = cm.get_service_environment('webui')
print(f'✓ Service environment test: {len(env_vars)} variables')

# Test feature flags
feature = cm.get_feature_flag('webui_enabled')
print(f'✓ Feature flag test: webui_enabled = {feature}')

# Test AI provider config
provider = cm.get_ai_provider_config('lm_studio')
print(f'✓ AI provider config test: lm_studio = {len(provider)} settings')

print('Configuration test completed!')
"
pause
goto config_management

:validate_config
echo [VALIDATE] Configuration Validation
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
print('Running comprehensive configuration validation...')
print()

issues = cm.validate_config()
if issues:
    print(f'Found {len(issues)} validation issues:')
    for issue in issues:
        print(f'  ✗ {issue}')
else:
    print('✓ All validation checks passed!')

print()
print('Additional system checks:')
info = cm.get_system_info()
print(f'  Environment: {info[\"environment\"]}')
print(f'  Enabled Services: {info[\"enabled_services\"]}')
print(f'  Required Services: {info[\"required_services\"]}')
print(f'  Allocated Ports: {len(info[\"allocated_ports\"])}')
"
pause
goto main_menu

:export_config
echo [EXPORT] Configuration Export
echo.
echo 1. Export to JSON
echo 2. Save Current Configuration
echo 3. Back to Main Menu
echo.

set /p export_choice="Select option (1-3): "

if "%export_choice%"=="1" goto export_json
if "%export_choice%"=="2" goto save_config
if "%export_choice%"=="3" goto main_menu

echo [ERROR] Invalid choice
pause
goto export_config

:export_json
echo [EXPORT] Exporting configuration to JSON...
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
cm.export_config_json('config/duckbot_config_export.json')
print('Configuration exported to: config/duckbot_config_export.json')
"
pause
goto export_config

:save_config
echo [SAVE] Saving current configuration...
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
cm.save_config()
print('Configuration saved successfully!')
"
pause
goto export_config

:system_info
echo [INFO] System Information
%PY_CMD% -c "
from config.config_manager import get_config_manager
cm = get_config_manager()
info = cm.get_system_info()

print('=== DUCKBOT SYSTEM INFORMATION ===')
print()
print('Configuration:')
print(f'  Environment: {info[\"environment\"]}')
print(f'  Config Path: {info[\"config_path\"]}')
print(f'  Version: {info[\"features\"].get(\"version\", \"Unknown\")}')
print()

print('Services:')
print(f'  Total Services: {info[\"total_services\"]}')
print(f'  Enabled Services: {info[\"enabled_services\"]}')
print(f'  Required Services: {info[\"required_services\"]}')
print()

print('Resources:')
hw = info['hardware']
print(f'  Min RAM: {hw[\"min_ram_gb\"]}GB')
print(f'  Recommended RAM: {hw[\"recommended_ram_gb\"]}GB')
print(f'  Max Concurrent Services: {hw[\"max_concurrent_services\"]}')
print(f'  GPU Enabled: {hw[\"gpu_enabled\"]}')
print()

print('Features:')
features = info['features']
for name, enabled in features.items():
    print(f'  {name}: {\"Enabled\" if enabled else \"Disabled\"}')
print()

if info['validation_issues']:
    print('Validation Issues:')
    for issue in info['validation_issues']:
        print(f'  ✗ {issue}')
else:
    print('✓ No validation issues')
"
pause
goto main_menu

:exit
echo [EXIT] Thank you for using DuckBot Enhanced Configuration Management!
pause
exit /b 0

:main_menu
cls
goto :EOF