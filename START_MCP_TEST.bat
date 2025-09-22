@echo off
echo Starting MCP Server for WebSocket Testing...
echo ====================================================

cd /d "%~dp0"

echo Starting MCP Server on port 8790...
start "MCP Server Test" cmd /k "python start_mcp_server.py --host 0.0.0.0 --port 8790 --mcp-only"

echo.
echo Waiting for MCP server to start...
timeout /t 5 /nobreak

echo Testing server connectivity...
python test_mcp_connections.py

echo.
echo Test completed. Press any key to close MCP server and exit...
pause >nul

taskkill /f /im python.exe /fi "WINDOWTITLE eq MCP Server Test*" 2>nul
echo MCP server stopped.
pause