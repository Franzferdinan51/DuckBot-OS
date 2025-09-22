@echo off
REM ==============================================================================
REM  🎮 ENHANCED DISCORD BOT STARTUP SCRIPT v4.2
REM  Discord Bot with Entertainment Commands and AI Integration
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Enhanced Discord Bot - DuckBot Integration
color 0A
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Version and build info
set "DISCORDBOT_VERSION=1.0.0"
set "BUILD_DATE=2025-09-17"

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
echo  🎮 ENHANCED DISCORD BOT v%DISCORDBOT_VERSION%
echo ================================================================================
echo    Discord Bot with Entertainment Commands and AI Integration
echo    [BUILD] %BUILD_DATE% - Enhanced Edition
echo ================================================================================
echo.

echo 🚀 LAUNCHING: Enhanced Discord Bot
echo.

REM Pre-flight checks
call :check_python
if errorlevel 1 goto :eof

call :install_dependencies_if_needed
if errorlevel 1 goto :eof

call :check_discord_token
if errorlevel 1 goto :eof

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo.
echo 📋 STARTUP INFORMATION:
echo   - Bot Name: DuckBot Enhanced
echo   - Status: Online and Ready
echo   - Log file: logs/discord.log
echo   - Prefix: ! (configurable)
echo.

echo 🎮 ENTERTAINMENT FEATURES:
echo   - Games: Trivia, Word Games, Number Guessing
echo   - Music: Voice channel music playback
echo   - Fun Commands: Jokes, Quotes, Facts, Meme Generator
echo   - Utilities: Translation, Calculator, Weather
echo   - Moderation: Auto-moderation tools
echo   - AI Integration: Chat with AI directly in Discord
echo.

echo 🤖 AI FEATURES:
echo   - Natural language conversations
echo   - Multiple AI provider support
echo   - Context-aware responses
echo   - Voice channel integration
echo   - Custom commands and responses
echo.

echo 🎛️  CONTROL COMMANDS:
echo   - !help - Show all available commands
echo   - !ai - Chat with AI assistant
echo   - !play - Play music in voice channels
echo   - !trivia - Start trivia game
echo   - !joke - Get a random joke
echo   - !weather - Get weather information
echo   - !translate - Translate text
echo.

REM Check if Discord bot module is available
echo [CHECK] Checking Discord bot integration...
%PY_CMD% -c "import importlib; importlib.import_module('duckbot.discord_bot')" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Discord bot integration not found!
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo   1. Ensure duckbot/discord_bot.py exists
    echo   2. Check that all dependencies are installed
    echo   3. Verify the Discord bot module is properly configured
    echo.
    pause
    exit /b 1
)

echo [LAUNCHING] Starting Enhanced Discord Bot...
echo       Press Ctrl+C to stop the bot
echo.

REM Start the Discord bot with logging
start "Enhanced Discord Bot" %PY_CMD% -c "from duckbot.discord_bot import DiscordBot; import asyncio; asyncio.run(DiscordBot().start_service())" > logs\discord.log 2>&1

REM Wait a moment and check if it started
timeout /t 5 >nul

REM Check if the process is running
tasklist /FI "WINDOWTITLE eq Enhanced Discord Bot*" 2>nul | find "python" >nul
if %errorlevel% equ 0 (
    echo [OK] Enhanced Discord Bot started successfully!
    echo [INFO] Bot is now online and ready to accept commands
    echo [INFO] Check your Discord server for the bot's presence
    echo.
    echo 🎮 GETTING STARTED:
    echo   1. Invite the bot to your Discord server
    echo   2. Use !help command to see all available features
    echo   3. Try !ai to start chatting with the AI
    echo   4. Join a voice channel and use !play for music
    echo.
    echo 📋 LOGS: Bot activity is being logged to logs\discord.log
    echo 💡 STOP: Press Ctrl+C in the bot window to stop the service
) else (
    echo [ERROR] Failed to start Enhanced Discord Bot!
    echo [DEBUG] Check logs\discord.log for error details
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo   1. Verify your Discord bot token is correct
    echo   2. Check bot permissions in Discord Developer Portal
    echo   3. Ensure Discord.py is properly installed
    echo   4. Check your internet connection
    echo   5. Verify bot intents are enabled in Developer Portal
    echo.
)

echo.
pause
goto :eof

REM =============================================================================
REM SUPPORT FUNCTIONS
REM ==============================================================================

:check_python
echo 🐍 Checking Python installation...
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    echo 📝 During installation, make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ Python installation verified
exit /b 0

:install_dependencies_if_needed
echo 📦 Checking dependencies...
%PY_CMD% -c "import discord, asyncio, aiohttp, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing required dependencies...
    %PY_CMD% -m pip install discord.py aiohttp requests python-dotenv
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        echo 💡 Try manually: pip install discord.py aiohttp requests python-dotenv
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ All dependencies are available
)

REM Check for optional dependencies
echo 🎮 Checking optional dependencies...
%PY_CMD% -c "import youtube_dl, spotipy, pytz" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Installing optional dependencies...
    %PY_CMD% -m pip install yt-dlp spotipy pytz
    if %errorlevel% neq 0 (
        echo [WARN] Some optional dependencies failed to install
        echo [INFO] Basic functionality will still work
    )
)

echo ✅ Dependencies check completed
exit /b 0

:check_discord_token
echo 🔑 Checking Discord bot token...
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr "DISCORD_TOKEN"') do (
        if "%%b"=="" (
            echo [ERROR] DISCORD_TOKEN is not set in .env file!
            echo.
            echo 🔧 CONFIGURATION:
            echo   1. Open .env file
            echo   2. Add: DISCORD_TOKEN=your_discord_bot_token_here
            echo   3. Replace with your actual bot token from Discord Developer Portal
            echo   4. Save the file and try again
            echo.
            pause
            exit /b 1
        ) else (
            echo [OK] Discord bot token found
        )
    )
) else (
    echo [ERROR] .env file not found!
    echo.
    echo 🔧 CONFIGURATION:
    echo   1. Create .env file in the project root
    echo   2. Add: DISCORD_TOKEN=your_discord_bot_token_here
    echo   3. Replace with your actual bot token from Discord Developer Portal
    echo   4. Save the file and try again
    echo.
    pause
    exit /b 1
)
exit /b 0