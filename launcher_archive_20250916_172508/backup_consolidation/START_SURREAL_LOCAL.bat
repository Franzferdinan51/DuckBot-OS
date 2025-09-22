@echo off
setlocal ENABLEDELAYEDEXPANSION
pushd "%~dp0"

echo === Starting SurrealDB locally (no Docker) ===

set "SURREAL_BIN=surreal.exe"
where %SURREAL_BIN% >nul 2>&1
if NOT %ERRORLEVEL%==0 (
  if exist "open-notebook\bin\surreal.exe" (
    set "SURREAL_BIN=\"%~dp0open-notebook\bin\surreal.exe\""
  ) else (
    echo SurrealDB binary not found.
    echo Download Windows x64 zip from: https://github.com/surrealdb/surrealdb/releases
    echo Place surreal.exe into open-notebook\bin and rerun this script.
    goto :done
  )
)

set "DB_PATH=%~dp0open-notebook\surreal_single_data\mydatabase.db"
if not exist "%~dp0open-notebook\surreal_single_data" mkdir "%~dp0open-notebook\surreal_single_data"

echo Launching SurrealDB at ws://localhost:8000/rpc
start "SurrealDB" /min %SURREAL_BIN% start --log info --user root --pass root rocksdb:"%DB_PATH%"
echo Started (minimized). If port 8000 is busy, close other instances.

:done
popd
endlocal
