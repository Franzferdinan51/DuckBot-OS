@echo off
REM Test script to start DuckBot WebSocket server and Electron launcher

echo Starting DuckBot WebSocket server...
start "DuckBot WebSocket Server" /min python simple_websocket_server.py

echo Waiting for server to start...
timeout /t 5 /nobreak >nul

echo Starting DuckBot Electron Launcher...
cd /d electron-launcher
npm start