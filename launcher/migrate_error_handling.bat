@echo off
REM ==============================================================================
REM  🔄 DUCKBOT ERROR HANDLING MIGRATION TOOL v4.2
REM  Automated Migration of Existing Batch Files to Standardized Error Handling
REM ==============================================================================
REM
REM This script automates the migration of existing batch files to use
REM the standardized error handling framework. It analyzes batch files
REM and suggests or applies improvements to ensure consistency.
REM
REM USAGE:
REM   migrate_error_handling.bat analyze     [Analyze current error handling]
REM   migrate_error_handling.bat suggest     [Suggest improvements]
REM   migrate_error_handling.bat apply       [Apply improvements]
REM   migrate_error_handling.bat backup      [Create backup before migration]
REM   migrate_error_handling.bat restore     [Restore from backup]
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Error Handling Migration Tool
color 0A
cls

REM Initialize error handling
call "%~dp0error_handling_config.bat"
if %errorlevel% neq 0 (
    echo [❌] Failed to initialize error handling
    pause
    exit /b 1
)

REM Configuration
set "BACKUP_DIR=backup_error_handling_migration"
set "ANALYSIS_REPORT=error_handling_analysis.txt"
set "MIGRATION_LOG=migration_log.txt"

:main
echo.
echo ================================================================================
echo  🔄 DUCKBOT ERROR HANDLING MIGRATION TOOL v4.2
echo ================================================================================
echo.
echo 🔧 AUTOMATED ERROR HANDLING STANDARDIZATION
echo.
echo Select operation:
echo.
echo 1. 🔍 ANALYZE - Analyze current error handling patterns
echo 2. 💡 SUGGEST - Suggest improvements for batch files
echo 3. 🚀 APPLY - Apply standardized error handling
echo 4. 💾 BACKUP - Create backup before migration
echo 5. 🔄 RESTORE - Restore from backup
echo 6. 📊 REPORT - Generate comprehensive report
echo 7. ❓ HELP - Show help and documentation
echo 8. 🚪 EXIT - Exit migration tool
echo.
set /p choice="[MIGRATION] Enter your choice: "

if "%choice%"=="1" goto analyze_files
if "%choice%"=="2" goto suggest_improvements
if "%choice%"=="3" goto apply_improvements
if "%choice%"=="4" goto create_backup
if "%choice%"=="5" goto restore_backup
if "%choice%"=="6" goto generate_report
if "%choice%"=="7" goto show_help
if "%choice%"=="8" goto exit_tool

echo [❌] Invalid choice: %choice%
timeout /t 2 >nul
goto main

:analyze_files
echo.
echo ================================================================================
echo  🔍 ANALYZING ERROR HANDLING PATTERNS
echo ================================================================================
echo.

REM Create analysis report
echo [%date% %time%] ERROR HANDLING ANALYSIS REPORT > "%ANALYSIS_REPORT%"
echo ==================================================== >> "%ANALYSIS_REPORT%"
echo. >> "%ANALYSIS_REPORT%"

REM Find all batch files
set "file_count=0"
set "total_inconsistencies=0"

for %%f in (*.bat) do (
    if /i not "%%f"=="error_handler.bat" (
        if /i not "%%f"=="error_handling_config.bat" (
            if /i not "%%f"=="error_handling_template.bat" (
                if /i not "%%f"=="migrate_error_handling.bat" (
                    set /a file_count+=1
                    echo [📁] Analyzing: %%f

                    REM Analyze file for error handling patterns
                    call :analyze_single_file "%%f" >> "%ANALYSIS_REPORT%"

                    REM Count inconsistencies
                    set /a total_inconsistencies+=%inconsistencies_found%
                )
            )
        )
    )
)

echo.
echo [%date% %time%] ANALYSIS SUMMARY >> "%ANALYSIS_REPORT%"
echo Files analyzed: %file_count% >> "%ANALYSIS_REPORT%"
echo Total inconsistencies found: %total_inconsistencies% >> "%ANALYSIS_REPORT%"
echo. >> "%ANALYSIS_REPORT%"

echo.
echo [✅] Analysis completed!
echo [📊] %file_count% files analyzed
echo [⚠️]  %total_inconsistencies% inconsistencies found
echo [📋] Report saved to: %ANALYSIS_REPORT%
echo.
pause
goto main

:analyze_single_file
set "filename=%~1"
set "inconsistencies_found=0"
set "has_error_handling=0"
set "has_consistent_patterns=0"
set "uses_exit_codes=0"
set "has_error_logging=0"

echo. >> "%ANALYSIS_REPORT%"
echo File: %filename% >> "%ANALYSIS_REPORT%"
echo ---------------------------------------- >> "%ANALYSIS_REPORT%"

REM Check for various error handling patterns
findstr /i "if errorlevel" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    set /a has_error_handling+=1
    echo [✓] Found errorlevel checking >> "%ANALYSIS_REPORT%"
)

findstr /i "if %errorlevel%" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    set /a has_error_handling+=1
    echo [✓] Found %errorlevel% checking >> "%ANALYSIS_REPORT%"
)

findstr /i "exit /b" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    set /a uses_exit_codes+=1
    echo [✓] Found exit /b statements >> "%ANALYSIS_REPORT%"
)

findstr /i "echo.*❌" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    set /a has_error_logging+=1
    echo [✓] Found error message formatting >> "%ANALYSIS_REPORT%"
)

REM Check for inconsistencies
if %has_error_handling% gtr 1 (
    echo [⚠️] Mixed error checking patterns detected >> "%ANALYSIS_REPORT%"
    set /a inconsistencies_found+=1
)

if %has_error_handling% equ 0 (
    echo [❌] No error handling found >> "%ANALYSIS_REPORT%"
    set /a inconsistencies_found+=1
)

if %uses_exit_codes% equ 0 (
    echo [❌] No exit codes found >> "%ANALYSIS_REPORT%"
    set /a inconsistencies_found+=1
)

if %has_error_logging% equ 0 (
    echo [❌] No error message formatting >> "%ANALYSIS_REPORT%"
    set /a inconsistencies_found+=1
)

REM Check for error handler import
findstr /i "error_handler" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Already uses error handler framework >> "%ANALYSIS_REPORT%"
) else (
    echo [❌] Does not use error handler framework >> "%ANALYSIS_REPORT%"
    set /a inconsistencies_found+=1
)

echo Inconsistencies found: %inconsistencies_found% >> "%ANALYSIS_REPORT%"
exit /b %inconsistencies_found%

:suggest_improvements
echo.
echo ================================================================================
echo  💡 SUGGESTING ERROR HANDLING IMPROVEMENTS
echo ================================================================================
echo.

if not exist "%ANALYSIS_REPORT%" (
    echo [❌] Analysis report not found. Please run analysis first.
    pause
    goto main
)

echo [📋] Generating improvement suggestions...
echo.

REM Create suggestions file
set "SUGGESTIONS_FILE=error_handling_suggestions.txt"
echo [%date% %time%] ERROR HANDLING IMPROVEMENT SUGGESTIONS > "%SUGGESTIONS_FILE%"
echo ==================================================== >> "%SUGGESTIONS_FILE%"
echo. >> "%SUGGESTIONS_FILE%"

REM Parse analysis report and generate suggestions
for %%f in (*.bat) do (
    if /i not "%%f"=="error_handler.bat" (
        if /i not "%%f"=="error_handling_config.bat" (
            if /i not "%%f"=="error_handling_template.bat" (
                if /i not "%%f"=="migrate_error_handling.bat" (
                    echo [📁] Processing suggestions for: %%f
                    call :generate_suggestions "%%f" >> "%SUGGESTIONS_FILE%"
                    echo. >> "%SUGGESTIONS_FILE%"
                )
            )
        )
    )
)

echo.
echo [✅] Suggestions generated!
echo [📋] Suggestions saved to: %SUGGESTIONS_FILE%
echo.
pause
goto main

:generate_suggestions
set "filename=%~1"
echo File: %filename% >> "%SUGGESTIONS_FILE%"
echo ---------------------------------------- >> "%SUGGESTIONS_FILE%"

REM Check if file needs error handler import
findstr /i "error_handler" "%filename%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SUGGESTION 1] Add error handler import at beginning: >> "%SUGGESTIONS_FILE%"
    echo   @echo off >> "%SUGGESTIONS_FILE%"
    echo   call "%%~dp0error_handling_config.bat" >> "%SUGGESTIONS_FILE%"
    echo   if %%errorlevel%% neq 0 exit /b 1 >> "%SUGGESTIONS_FILE%"
    echo. >> "%SUGGESTIONS_FILE%"
)

REM Check for inconsistent error checking
findstr /i "if errorlevel" "%filename%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUGGESTION 2] Standardize error checking patterns: >> "%SUGGESTIONS_FILE%"
    echo   Replace 'if errorlevel 1' with 'if %%errorlevel%% neq 0' >> "%SUGGESTIONS_FILE%"
    echo   Use call :handle_error function for consistent error handling >> "%SUGGESTIONS_FILE%"
    echo. >> "%SUGGESTIONS_FILE%"
)

REM Check for missing exit codes
findstr /i "exit /b" "%filename%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SUGGESTION 3] Add proper exit codes: >> "%SUGGESTIONS_FILE%"
    echo   Add 'exit /b %%errorlevel%%' after failed operations >> "%SUGGESTIONS_FILE%"
    echo   Use standardized error codes (1-10) >> "%SUGGESTIONS_FILE%"
    echo. >> "%SUGGESTIONS_FILE%"
)

REM Check for inconsistent error message formatting
findstr /i "echo.*❌" "%filename%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SUGGESTION 4] Standardize error message formatting: >> "%SUGGESTIONS_FILE%"
    echo   Use %%ERROR_PREFIX%% for error messages >> "%SUGGESTIONS_FILE%"
    echo   Use %%SUCCESS_PREFIX%% for success messages >> "%SUGGESTIONS_FILE%"
    echo   Use %%WARNING_PREFIX%% for warnings >> "%SUGGESTIONS_FILE%"
    echo. >> "%SUGGESTIONS_FILE%"
)

echo [SUGGESTION 5] Add comprehensive error handling: >> "%SUGGESTIONS_FILE%"
echo   - Call error_handler.bat init at beginning >> "%SUGGESTIONS_FILE%"
echo   - Use call error_handler.bat check for commands >> "%SUGGESTIONS_FILE%"
echo   - Use call error_handler.bat log for error messages >> "%SUGGESTIONS_FILE%"
echo   - Use call error_handler.bat exit for clean exit >> "%SUGGESTIONS_FILE%"
echo. >> "%SUGGESTIONS_FILE%"

exit /b 0

:apply_improvements
echo.
echo ================================================================================
echo  🚀 APPLYING STANDARDIZED ERROR HANDLING
echo ================================================================================
echo.
echo ⚠️  WARNING: This will modify batch files automatically!
echo.
set /p confirm="Are you sure you want to apply improvements? (y/N): "
if /i not "%confirm%"=="y" (
    echo [❌] Migration cancelled
    pause
    goto main
)

echo [🔄] Creating backup before applying changes...
call :create_backup

echo [🚀] Applying standardized error handling...

REM Apply improvements to all batch files
for %%f in (*.bat) do (
    if /i not "%%f"=="error_handler.bat" (
        if /i not "%%f"=="error_handling_config.bat" (
            if /i not "%%f"=="error_handling_template.bat" (
                if /i not "%%f"=="migrate_error_handling.bat" (
                    echo [📁] Migrating: %%f
                    call :apply_single_migration "%%f"
                )
            )
        )
    )
)

echo.
echo [✅] Migration completed!
echo [💾] Backup saved to: %BACKUP_DIR%
echo [📋] Migration log saved to: %MIGRATION_LOG%
echo.
pause
goto main

:apply_single_migration
set "filename=%~1"
set "temp_file=%filename%.tmp"

REM Create backup of original file
copy "%filename%" "%BACKUP_DIR%\%filename%.bak" >nul 2>&1

REM Apply migration transformations
REM 1. Add error handler import at beginning
echo @echo off > "%temp_file%"
echo REM Migrated by error handling migration tool >> "%temp_file%"
echo call "%%~dp0error_handling_config.bat" >> "%temp_file%"
echo if %%errorlevel%% neq 0 exit /b 1 >> "%temp_file%"
echo. >> "%temp_file%"

REM 2. Copy rest of file (skip first line if it's @echo off)
set "skip_line=0"
findstr /i "@echo off" "%filename%" >nul 2>&1
if %errorlevel% equ 0 set "skip_line=1"

REM Copy remaining content
if %skip_line% equ 1 (
    more +1 "%filename%" >> "%temp_file%"
) else (
    type "%filename%" >> "%temp_file%"
)

REM Replace original file
move /y "%temp_file%" "%filename%" >nul 2>&1

REM Log migration
echo [%date% %time%] Migrated: %filename% >> "%MIGRATION_LOG%"
exit /b 0

:create_backup
echo.
echo ================================================================================
echo  💾 CREATING BACKUP
echo ================================================================================
echo.

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [💾] Creating backup of batch files...
copy *.bat "%BACKUP_DIR%\" >nul 2>&1

echo [💾] Creating backup of configuration files...
if exist "config\*.json" copy "config\*.json" "%BACKUP_DIR%\config\" >nul 2>&1
if exist "*.env" copy "*.env" "%BACKUP_DIR%\" >nul 2>&1

echo [✅] Backup completed!
echo [📁] Backup location: %BACKUP_DIR%
echo.
pause
goto main

:restore_backup
echo.
echo ================================================================================
echo  🔄 RESTORING FROM BACKUP
echo ================================================================================
echo.

if not exist "%BACKUP_DIR%" (
    echo [❌] Backup directory not found: %BACKUP_DIR%
    pause
    goto main
)

echo ⚠️  WARNING: This will overwrite current files with backup!
echo.
set /p confirm="Are you sure you want to restore from backup? (y/N): "
if /i not "%confirm%"=="y" (
    echo [❌] Restore cancelled
    pause
    goto main
)

echo [🔄] Restoring files from backup...
copy "%BACKUP_DIR%\*.bat" . >nul 2>&1
if exist "%BACKUP_DIR%\config\*.json" copy "%BACKUP_DIR%\config\*.json" "config\" >nul 2>&1
if exist "%BACKUP_DIR%\*.env" copy "%BACKUP_DIR%\*.env" . >nul 2>&1

echo [✅] Restore completed!
echo.
pause
goto main

:generate_report
echo.
echo ================================================================================
echo  📊 GENERATING COMPREHENSIVE REPORT
echo ================================================================================
echo.

echo [📊] Generating comprehensive error handling report...

REM Create comprehensive report
set "COMPREHENSIVE_REPORT=error_handling_comprehensive_report.txt"
echo [%date% %time%] COMPREHENSIVE ERROR HANDLING REPORT > "%COMPREHENSIVE_REPORT%"
echo =============================================================== >> "%COMPREHENSIVE_REPORT%"
echo. >> "%COMPREHENSIVE_REPORT%"

REM System information
echo [SYSTEM INFORMATION] >> "%COMPREHENSIVE_REPORT%"
echo Date: %date% >> "%COMPREHENSIVE_REPORT%"
echo Time: %time% >> "%COMPREHENSIVE_REPORT%"
echo User: %USERNAME% >> "%COMPREHENSIVE_REPORT%"
echo Computer: %COMPUTERNAME% >> "%COMPREHENSIVE_REPORT%"
echo Directory: %CD% >> "%COMPREHENSIVE_REPORT%"
echo. >> "%COMPREHENSIVE_REPORT%"

REM Count files
set "total_files=0"
set "files_with_error_handling=0"
set "files_without_error_handling=0"

for %%f in (*.bat) do (
    set /a total_files+=1
    findstr /i "if errorlevel\|if %errorlevel%" "%%f" >nul 2>&1
    if %errorlevel% equ 0 (
        set /a files_with_error_handling+=1
    ) else (
        set /a files_without_error_handling+=1
    )
)

echo [STATISTICS] >> "%COMPREHENSIVE_REPORT%"
echo Total batch files: %total_files% >> "%COMPREHENSIVE_REPORT%"
echo Files with error handling: %files_with_error_handling% >> "%COMPREHENSIVE_REPORT%"
echo Files without error handling: %files_without_error_handling% >> "%COMPREHENSIVE_REPORT%"
echo. >> "%COMPREHENSIVE_REPORT%"

REM Error handling patterns
echo [ERROR HANDLING PATTERNS] >> "%COMPREHENSIVE_REPORT%"
findstr /i "if errorlevel" *.bat | wc -l >> "%COMPREHENSIVE_REPORT%" 2>nul
findstr /i "if %errorlevel%" *.bat | wc -l >> "%COMPREHENSIVE_REPORT%" 2>nul
findstr /i "exit /b" *.bat | wc -l >> "%COMPREHENSIVE_REPORT%" 2>nul
findstr /i "echo.*❌" *.bat | wc -l >> "%COMPREHENSIVE_REPORT%" 2>nul
echo. >> "%COMPREHENSIVE_REPORT%"

REM Recommendations
echo [RECOMMENDATIONS] >> "%COMPREHENSIVE_REPORT%"
if %files_without_error_handling% gtr 0 (
    echo - %files_without_error_handling% files need error handling implementation >> "%COMPREHENSIVE_REPORT%"
)
echo - Standardize error checking patterns across all files >> "%COMPREHENSIVE_REPORT%"
echo - Implement consistent error message formatting >> "%COMPREHENSIVE_REPORT%"
echo - Add proper exit codes for all error conditions >> "%COMPREHENSIVE_REPORT%"
echo - Implement logging for all error conditions >> "%COMPREHENSIVE_REPORT%"
echo. >> "%COMPREHENSIVE_REPORT%"

echo [✅] Comprehensive report generated!
echo [📋] Report saved to: %COMPREHENSIVE_REPORT%
echo.
pause
goto main

:show_help
echo.
echo ================================================================================
echo  ❓ ERROR HANDLING MIGRATION TOOL HELP
echo ================================================================================
echo.
echo 🔧 TOOL OVERVIEW:
echo   This tool helps standardize error handling across all DuckBot batch files.
echo   It analyzes existing patterns, suggests improvements, and can automatically
echo   apply standardized error handling to ensure consistency.
echo.
echo 📋 AVAILABLE OPERATIONS:
echo.
echo   1. 🔍 ANALYZE
echo      - Analyzes all batch files for error handling patterns
echo      - Identifies inconsistencies and missing error handling
echo      - Generates detailed analysis report
echo.
echo   2. 💡 SUGGEST
echo      - Suggests specific improvements for each file
echo      - Provides code snippets for implementation
echo      - Prioritizes critical issues
echo.
echo   3. 🚀 APPLY
echo      - Automatically applies standardized error handling
echo      - Modifies batch files to use error handler framework
echo      - Creates backup before making changes
echo.
echo   4. 💾 BACKUP
echo      - Creates backup of all batch files
echo      - Safely stores current state before migration
echo      - Allows easy restoration if needed
echo.
echo   5. 🔄 RESTORE
echo      - Restores files from backup
echo      - Reverts migration if issues occur
echo      - Returns to previous state
echo.
echo   6. 📊 REPORT
echo      - Generates comprehensive migration report
echo      - Includes statistics and recommendations
echo      - Provides detailed analysis summary
echo.
echo ⚠️  IMPORTANT NOTES:
echo   - Always create backup before applying changes
echo   - Test migrated files thoroughly
echo   - Review applied changes manually
echo   - Keep backup until confident with migration
echo.
echo 🛡️  ERROR HANDLING FRAMEWORK:
echo   - error_handler.bat: Core error handling functions
echo   - error_handling_config.bat: Configuration and utilities
echo   - error_handling_template.bat: Template for new scripts
echo.
echo 📁 FILES CREATED:
echo   - error_handling_analysis.txt: Analysis results
echo   - error_handling_suggestions.txt: Improvement suggestions
echo   - error_handling_comprehensive_report.txt: Detailed report
echo   - migration_log.txt: Migration operations log
echo   - backup_error_handling_migration\: Backup directory
echo.
pause
goto main

:exit_tool
echo.
echo ================================================================================
echo  🚪 EXITING MIGRATION TOOL
echo ================================================================================
echo.
echo 🔄 Error handling migration tool completed.
echo 📋 Check generated reports for details.
echo 🛡️  Remember to test migrated files thoroughly.
echo.
echo [✅] Tool session ended
echo.
timeout /t 3 >nul
exit /b 0