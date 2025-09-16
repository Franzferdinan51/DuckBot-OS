@echo off
setlocal
pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\make_release_zip.ps1"
set ERR=%ERRORLEVEL%
popd
if errorlevel 1 exit /b %ERR%
exit /b 0

