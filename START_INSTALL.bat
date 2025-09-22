@echo off
REM ==============================================================================
REM  📦 DUCKBOT INSTALL LAUNCHER v4.2
REM  Automatic Dependency Installation and Setup
REM ==============================================================================

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot Install Mode
color 0A
cls

cd /d "%~dp0"

echo.
echo ================================================================================
echo  📦 DUCKBOT INSTALL MODE v4.2
echo ================================================================================
echo.
echo 📦 INSTALLATION FEATURES:
echo   ✅ Auto-install missing components
echo   ✅ Python packages and system tools
echo   ✅ Configuration file creation
echo   ✅ Environment setup
echo.
echo 🚀 STARTING AUTOMATIC INSTALLATION...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from: https://www.python.org/downloads/
    echo 💡 During installation, make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python installation verified
echo 📦 Starting comprehensive installation...
echo.

echo [1/6] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ❌ Failed to upgrade pip
    pause
    exit /b 1
)
echo ✅ pip upgraded successfully

echo [2/6] Installing core requirements...
if exist "requirements.txt" (
    echo 📦 Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install from requirements.txt
        echo 💡 Continuing with individual package installation...
    ) else (
        echo ✅ Requirements installed successfully
    )
) else (
    echo ⚠️  requirements.txt not found, will install individual packages
)

echo [3/6] Installing essential DuckBot dependencies...
echo    - FastAPI (Web framework)
python -m pip install --upgrade fastapi uvicorn aiohttp python-multipart jinja2
echo    - HTTP and networking
python -m pip install --upgrade requests httpx aiohttp websockets websocket-client
echo    - System monitoring
python -m pip install --upgrade psutil GPUtil
echo    - Data processing
python -m pip install --upgrade numpy pillow opencv-python
echo    - Configuration handling
python -m pip install --upgrade pyyaml jsonpickle python-dotenv

echo [4/6] Installing AI and ML libraries...
echo    - Core ML framework
python -m pip install --upgrade torch transformers accelerate
echo    - Additional AI tools (optional)
python -m pip install --upgrade langchain openai anthropic
echo    - Web automation (optional)
python -m pip install --upgrade selenium beautifulsoup4 playwright

echo [5/6] Installing enhanced features...
echo    - Web UI frameworks
python -m pip install --upgrade streamlit gradio flask
echo    - Terminal interface
python -m pip install --upgrade rich typer click
echo    - Database and storage
python -m pip install --upgrade sqlite3 aiofiles
echo    - Communication tools
python -m pip install --upgrade discord.py slack-sdk

echo [6/6] Creating configuration files...
if not exist ".env" (
    echo ⚙️ Creating .env configuration file...
    echo # DuckBot v4.2 Configuration > .env
    echo # AI Provider Configuration >> .env
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here >> .env
    echo ANTHROPIC_API_KEY=your_anthropic_api_key_here >> .env
    echo DISCORD_TOKEN=your_discord_token_here >> .env
    echo # System Configuration >> .env
    echo DUCKBOT_WEBUI_HOST=127.0.0.1 >> .env
    echo DUCKBOT_WEBUI_PORT=8787 >> .env
    echo AI_CONFIDENCE_MIN=0.75 >> .env
    echo AI_LOCAL_CONF_MIN=0.68 >> .env
    echo MAX_MEMORY_THRESHOLD=85.0 >> .env
    echo # Local AI Configuration >> .env
    echo LM_STUDIO_URL=http://localhost:1234/v1 >> .env
    echo OLLAMA_URL=http://localhost:11434 >> .env
    echo ✅ .env configuration file created
)

if not exist "requirements.txt" (
    echo 📝 Creating requirements.txt file...
    echo fastapi>=0.104.0 > requirements.txt
    echo uvicorn[standard]>=0.24.0 >> requirements.txt
    echo aiohttp>=3.9.0 >> requirements.txt
    echo requests>=2.31.0 >> requirements.txt
    echo psutil>=5.9.0 >> requirements.txt
    echo websockets>=12.0 >> requirements.txt
    echo pillow>=10.0.0 >> requirements.txt
    echo numpy>=1.24.0 >> requirements.txt
    echo pyyaml>=6.0 >> requirements.txt
    echo python-dotenv>=1.0.0 >> requirements.txt
    echo rich>=13.0.0 >> requirements.txt
    echo typer>=0.9.0 >> requirements.txt
    echo ✅ requirements.txt file created
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "test_results" mkdir test_results
if not exist "config" mkdir config
if not exist "temp" mkdir temp
echo ✅ Directories created

echo.
echo ================================================================================
echo  📦 INSTALLATION COMPLETE
echo ================================================================================
echo.
echo ✅ All essential components have been installed
echo 💡 Your DuckBot system is ready to use!
echo.
echo 🚀 Quick Start Options:
echo   - START_LOCAL_ONLY.bat    (Privacy mode)
echo   - START_ENHANCED_DUCKBOT.bat (Full features)
echo   - START_QUICK.bat         (Fast startup)
echo   - launcher/CONSOLIDATED_DUCKBOT_LAUNCHER.bat (All options)
echo.
echo ⚙️ Configuration:
echo   - Edit .env file to set your API keys
echo   - Use START_DOCTOR.bat for system diagnostics
echo   - Use START_KILL.bat for emergency shutdown
echo.
pause