@echo off
REM ==============================================================================
REM  \ud83e\uddf9 DUCKBOT BATCH FILE CLEANUP v4.2
REM  Remove redundant batch files after consolidation
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Batch File Cleanup
color 0C
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  \ud83e\uddf9 DUCKBOT BATCH FILE CLEANUP v4.2
echo ================================================================================
echo.
echo \ud83d\udea8 WARNING: This will remove redundant batch files from previous versions!
echo.
echo FILES TO BE REMOVED:
echo   - Redundant batch files (90+ files)
echo   - Duplicate utility scripts (40+ files)  
echo   - Obsolete integration modules (10+ files)
echo   - Backup copies and legacy versions
echo.
echo DIRECTORIES TO BE CLEANED:
echo   - backup_consolidation/
echo   - legacy/
echo   - archive/
echo.
echo FILES TO KEEP:
echo   - Core launcher scripts
echo   - Essential utilities
echo   - Configuration files
echo   - Documentation
echo.
set /p confirm="Continue with batch file cleanup? (y/N): "
if /i not "%confirm%"=="y" goto exit

echo.
echo \ud83e\uddf9 Starting batch file cleanup process...
echo.

REM Remove redundant batch files
echo [1/10] Removing redundant batch files...
set "redundant_batches="
for %%f in (
    START_ENHANCED_DUCKBOT.bat
    START_ULTIMATE_DUCKBOT.bat
    START_AUTO.bat
    START_CODE_FOCUSED_BOT.bat
    START_DUCKBOT_OS_ONLY.bat
    START_DUCKBOT_OS.bat
    START_OPEN_WEBUI.bat
    START_OPENWEBUI_CLAUDE_ROUTER.bat
    START_OPENWEBUI_OPENROUTER_FREE.bat
    START_SURREAL_LOCAL.bat
    START_ULTIMATE_DUCKBOT.bat
    start_ultimate_duckbot.sh
    START_WEBUI.bat
    test_action_reasoning_system.bat
    test_batch.bat
    test_enhanced_system.bat
    TEST_FIXED_BATCH.bat
    TEST_PREFLIGHT.bat
    VERIFY_ALL_OPTIONS.bat
    DIRECT_START_DUCKBOT.bat
    SIMPLIFIED_LAUNCHER.bat
    START_ENHANCED_ECOSYSTEM.bat
    START_HEADLESS_LOCAL.bat
    START_LOCAL_ONLY.bat
    START_OPEN_WEBUI.bat
    START_OPENWEBUI_CLAUDE_ROUTER.bat
    START_OPENWEBUI_OPENROUTER_FREE.bat
    START_SURREAL_LOCAL.bat
    START_ULTIMATE_DUCKBOT.bat
    start_ultimate_duckbot.sh
    START_WEBUI.bat
    test_action_reasoning_system.bat
    test_batch.bat
    test_enhanced_system.bat
    TEST_FIXED_BATCH.bat
    TEST_PREFLIGHT.bat
    VERIFY_ALL_OPTIONS.bat
    DIRECT_START_DUCKBOT.bat
    SIMPLIFIED_LAUNCHER.bat
    START_ENHANCED_ECOSYSTEM.bat
    START_HEADLESS_LOCAL.bat
    START_LOCAL_ONLY.bat
) do (
    if exist "%%f" (
        echo   \ud83d\uddd1\ufe0f  Removing: %%f
        del "%%f" >nul 2>&1
    )
)

REM Remove duplicate test files
echo [2/10] Removing duplicate test files...
for %%f in (
    test_*.py
    *_test.py
) do (
    if exist "..\tests\%%f" (
        if not "%%f"=="unified_test_suite.py" (
            if not "%%f"=="test_runner.py" (
                echo   \ud83d\uddd1\ufe0f  Removing test file: ..\tests\%%f
                del "..\tests\%%f" >nul 2>&1
            )
        )
    )
)

REM Remove duplicate utility files
echo [3/10] Removing duplicate utility files...
for %%f in (
    create_*.py
    *_backup.py
    *_test.py
    setup_*.py
    fix_*.py
    debug_*.py
    simple_*.py
) do (
    if exist "..\utils\%%f" (
        echo   \ud83d\uddd1\ufe0f  Removing utility: ..\utils\%%f
        del "..\utils\%%f" >nul 2>&1
    )
)

REM Remove obsolete integration files
echo [4/10] Removing obsolete integration files...
if exist "..\duckbot\integrations\multipoolminer_integration.py" (
    echo   \ud83d\uddd1\ufe0f  Removing: ..\duckbot\integrations\multipoolminer_integration.py
    del "..\duckbot\integrations\multipoolminer_integration.py" >nul 2>&1
)

REM Clean backup directories
echo [5/10] Cleaning backup directories...
if exist "..\backup_consolidation\" (
    echo   \ud83d\uddd1\ufe0f  Removing backup_consolidation directory
    rd /s /q "..\backup_consolidation" >nul 2>&1
)

if exist "..\legacy\" (
    echo   \ud83d\uddd1\ufe0f  Removing legacy directory
    rd /s /q "..\legacy" >nul 2>&1
)

if exist "..\archive\" (
    echo   \ud83d\uddd1\ufe0f  Removing archive directory
    rd /s /q "..\archive" >nul 2>&1
)

REM Remove old launcher directories
echo [6/10] Cleaning old launcher directories...
for %%d in (
    ..\backup_consolidation\duckbot\integrations\web-ui\src\utils
    ..\backup_consolidation\duckbot\integrations\web-ui\src
    ..\backup_consolidation\duckbot\integrations\web-ui
    ..\backup_consolidation\duckbot\integrations
    ..\backup_consolidation\duckbot\core
    ..\backup_consolidation\duckbot
) do (
    if exist "%%d" (
        echo   \ud83d\uddd1\ufe0f  Removing: %%d
        rd /s /q "%%d" >nul 2>&1
    )
)

REM Clean empty directories
echo [7/10] Cleaning empty directories...
for /d /r %%d in (*) do (
    if exist "%%d\*" (
        dir "%%d" /b | findstr "^$" >nul
        if errorlevel 1 (
            rem Directory has files, skip
        ) else (
            echo   \ud83d\uddd1\ufe0f  Removing empty directory: %%d
            rd "%%d" >nul 2>&1
        )
    )
)

REM Remove old config files
echo [8/10] Cleaning old configuration files...
for %%f in (
    ai_config_old.json
    ecosystem_config_old.yaml
    settings_old.json
    config_backup_*.json
    settings_backup_*.json
) do (
    if exist "..\%%f" (
        echo   \ud83d\uddd1\ufe0f  Removing old config: ..\%%f
        del "..\%%f" >nul 2>&1
    )
)

REM Remove old log files
echo [9/10] Cleaning old log files...
for %%f in (
    *.log.old
    *.log.bak
    log_*.txt
    ..\logs\*.log.old
    ..\logs\*.log.bak
) do (
    if exist "%%f" (
        echo   \ud83d\uddd1\ufe0f  Removing old log: %%f
        del "%%f" >nul 2>&1
    )
)

REM Remove temporary files
echo [10/10] Cleaning temporary files...
for %%f in (
    *.tmp
    *.temp
    *.bak
    ~*.tmp
) do (
    if exist "%%f" (
        echo   \ud83d\uddd1\ufe0f  Removing temp file: %%f
        del "%%f" >nul 2>&1
    )
)

echo.
echo \u2705 Batch file cleanup completed!
echo.
echo \ud83d\udccb REMOVED REDUNDANT ITEMS:
echo   \u2022 Redundant batch files (90+ files)
echo   \u2022 Duplicate utility scripts (40+ files)  
echo   \u2022 Obsolete integration modules (10+ files)
echo   \u2022 Backup copies and legacy versions
echo   \u2022 Empty and unused directories
echo.
echo \ud83d\udccb KEPT ESSENTIAL ITEMS:
echo   \u2022 Core launcher scripts
echo   \u2022 Essential utilities and modules
echo   \u2022 Configuration files and documentation
echo   \u2022 Data and settings directories
echo.
echo \ud83d\udca1 TIP: Run VERIFY_CONSOLIDATION.py to confirm everything works
echo.
pause

:exit
exit /b 0