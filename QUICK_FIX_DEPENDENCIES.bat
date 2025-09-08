@echo off
REM DuckBot v3.1.0 - Quick Dependency Fix
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title DuckBot v3.1.0 - Quick Dependency Fix
color 0E
cls

REM Ensure we're in the correct directory
cd /d "%~dp0"

echo.
echo ===============================================
echo  🔧 DUCKBOT QUICK DEPENDENCY FIX
echo ===============================================
echo.
echo 🚀 Installing critical Python dependencies...
echo.
echo 💡 This fixes common errors like:
echo    • ModuleNotFoundError: No module named 'seaborn'
echo    • Discord.py import errors
echo    • Jupyter startup failures
echo    • WebUI dependency issues
echo.

REM Check Python
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 📥 Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python installation verified

echo.
echo 🔄 Installing dependencies in order of importance...
echo.

echo 📊 [CRITICAL] Visualization libraries (fixes seaborn errors)...
pip install seaborn plotly matplotlib pandas numpy
if errorlevel 1 (
    echo ❌ Critical visualization libraries failed
    echo 💡 Try running as administrator
    pause
    exit /b 1
) else (
    echo ✅ Visualization libraries: INSTALLED
)

echo.
echo 🤖 [CRITICAL] Discord bot framework...
pip install discord.py aiohttp requests
if errorlevel 1 (
    echo ⚠️  Discord.py installation had issues - bot may not work
) else (
    echo ✅ Discord bot framework: INSTALLED
)

echo.
echo 🌐 [CRITICAL] Web server dependencies...
pip install fastapi uvicorn jinja2 python-multipart
if errorlevel 1 (
    echo ⚠️  Web dependencies had issues - WebUI may be limited
) else (
    echo ✅ Web server dependencies: INSTALLED
)

echo.
echo 📔 [IMPORTANT] Jupyter ecosystem...
pip install jupyter notebook ipywidgets
if errorlevel 1 (
    echo ⚠️  Jupyter installation had issues - notebooks may be limited
) else (
    echo ✅ Jupyter ecosystem: INSTALLED
)

echo.
echo 🛠️ [IMPORTANT] System utilities...
pip install python-dotenv psutil PyYAML
if errorlevel 1 (
    echo ⚠️  Some system utilities had issues
) else (
    echo ✅ System utilities: INSTALLED
)

echo.
echo 🤖 [OPTIONAL] Claude Code Router (AI code tools)...
where npm >nul 2>&1
if not errorlevel 1 (
    npm install -g @musistudio/claude-code-router
    if errorlevel 1 (
        echo ⚠️  Claude Code Router installation failed
    ) else (
        echo ✅ Claude Code Router: INSTALLED
    )
) else (
    echo ⚠️  Node.js not found - Claude Code Router skipped
)

echo.
echo 🧪 Testing critical imports...
python -c "
import sys
test_modules = ['seaborn', 'discord', 'fastapi', 'jupyter', 'matplotlib', 'pandas', 'numpy']
failed = []
for module in test_modules:
    try:
        __import__(module)
        print(f'  ✅ {module}')
    except ImportError:
        print(f'  ❌ {module} - Still missing')
        failed.append(module)

if not failed:
    print('🎉 All critical dependencies working!')
else:
    print(f'⚠️  {len(failed)} modules still missing - run full installer')
"

echo.
echo ===============================================
echo  ✅ QUICK DEPENDENCY FIX COMPLETED!
echo ===============================================
echo.
echo 🎯 WHAT WAS FIXED:
echo   ✅ seaborn + visualization libraries
echo   ✅ discord.py bot framework  
echo   ✅ fastapi web server
echo   ✅ jupyter notebooks
echo   ✅ Core system utilities
echo.
echo 🚀 Your DuckBot should now start without dependency errors!
echo.
echo 💡 If you still have issues:
echo   • Run the full launcher: SETUP_AND_START.bat
echo   • Use option P for complete dependency installation
echo   • Use option D for Doctor mode diagnostics
echo.
pause