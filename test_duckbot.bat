@echo off
REM Test script to start DuckBot WebSocket server and Electron launcher

echo Starting DuckBot WebSocket server...
start "DuckBot WebSocket Server" /wait python simple_websocket_server.py

echo Starting DuckBot Electron Launcher...
cd /d electron-launcher
npm start