@echo off
echo ========================================
echo DuckBot-OS v4.2 GitHub Push Script
echo ========================================
echo.

REM Navigate to Desktop
cd /d C:\Users\Ryan\Desktop

REM Check if DuckBot-OS directory exists, if not clone it
if not exist "DuckBot-OS" (
    echo Cloning repository...
    git clone https://github.com/Franzferdinan51/DuckBot-OS.git
    if errorlevel 1 (
        echo ERROR: Failed to clone repository
        pause
        exit /b 1
    )
)

cd DuckBot-OS

echo.
echo Current directory: %CD%
echo.

REM Copy essential files from source directory
set SOURCE_DIR=C:\Users\Ryan\Desktop\DuckBot-Consolidated-v4.2

echo Copying updated files...

REM Copy key files
copy "%SOURCE_DIR%\README.md" . /y
copy "%SOURCE_DIR%\.gitignore" . /y
copy "%SOURCE_DIR%\GITHUB_UPLOAD_GUIDE.md" . /y
copy "%SOURCE_DIR%\CLAUDE.md" . /y
copy "%SOURCE_DIR%\requirements.txt" . /y
copy "%SOURCE_DIR%\START_ENHANCED_DUCKBOT.bat" . /y

REM Copy duckbot directory (the most important)
if exist "duckbot" rmdir /s /q duckbot
xcopy "%SOURCE_DIR%\duckbot" duckbot\ /e /i /y

REM Copy other essential directories
if exist "config" rmdir /s /q config
xcopy "%SOURCE_DIR%\config" config\ /e /i /y /q

if exist "docs" rmdir /s /q docs  
xcopy "%SOURCE_DIR%\docs" docs\ /e /i /y /q

echo.
echo Files copied successfully!
echo.

REM Git commands
echo Adding files to git...
git add .

echo.
echo Committing changes...
git commit -m "v4.2: Complete Consolidation with LiveKit & VibeVoice Integration

🌟 MAJOR UPDATE - COMPLETE CONSOLIDATION & NEW INTEGRATIONS:
- Consolidated all DuckBot versions into single clean codebase
- LiveKit WebRTC integration for real-time audio/video conferencing
- Complete Discord bot with VibeVoice TTS and LiveKit commands
- Enhanced audio/video capabilities with VibeVoice + LiveKit bridge
- Modern Discord slash commands with embed support
- Cost tracking integration for AI usage monitoring

🎙️ VIBEVOICE ENHANCEMENTS:
- Multi-speaker voice generation (Alice, Carter, David, Emily)
- Natural sounding TTS with proper intonation
- Conversation mode for dialogues and podcasts
- Custom voice profile creation and training
- Real-time audio generation and export

📹 LIVEKIT WEBRTC FEATURES:
- Real-time video conferencing with WebRTC
- Multi-participant rooms (up to 50+ users)
- End-to-end encryption for secure communications
- Discord integration for voice room management
- Low latency audio/video streaming
- Cross-platform support (web, mobile, desktop)

🤖 DISCORD BOT INTEGRATION:
- Modern slash command interface
- VibeVoice voice generation commands
- LiveKit voice room creation and management
- Real-time bot status and system monitoring
- Interactive help system with embeds
- Cost tracking and usage summaries

🔧 TECHNICAL IMPROVEMENTS:
- New: duckbot/livekit_integration.py - Complete WebRTC functionality
- New: duckbot/discord_bot.py - Full Discord bot with all integrations
- Updated: requirements.txt - LiveKit dependencies added
- New: livekit_config.yaml - LiveKit server configuration
- Updated: README.md - Comprehensive v4.2 documentation
- Consolidated: All versions merged into DuckBot-Consolidated-v4.2

🚀 FEATURES:
- VibeVoice TTS + LiveKit WebRTC working together
- Complete Discord bot with modern interface
- Consolidated architecture for easy maintenance
- Enhanced audio/video communication capabilities
- Real-time system monitoring and cost tracking

Generated with Claude Code - https://claude.ai/code
Co-Authored-By: Claude <noreply@anthropic.com>"

if errorlevel 1 (
    echo ERROR: Git commit failed
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
git push origin main

if errorlevel 1 (
    echo ERROR: Git push failed
    echo This might be due to authentication issues.
    echo Please check your GitHub credentials and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! DuckBot-OS v4.2 Consolidated pushed to GitHub!
echo Repository: https://github.com/Franzferdinan51/DuckBot-OS.git
echo Features: VibeVoice TTS + LiveKit WebRTC + Discord Bot
echo ========================================
echo.
pause