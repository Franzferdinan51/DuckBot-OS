#!/usr/bin/env python3
"""
DuckBot v3.0.7 Complete Package Creator (Simple Version)
Creates comprehensive zip package with all features except ComfyUI installation
"""

import os
import shutil
import zipfile
import time
from pathlib import Path
from datetime import datetime

def create_package():
    """Create comprehensive DuckBot package"""
    
    version = "3.0.7"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"DuckBot-v{version}-Complete-{timestamp}"
    
    print(f"Creating DuckBot v{version} Complete Package...")
    print(f"Package: {package_name}")
    print("="*60)
    
    base_dir = Path(__file__).parent
    temp_dir = base_dir / f"{package_name}_temp"
    zip_path = base_dir / f"{package_name}.zip"
    
    # Clean up any existing temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    temp_dir.mkdir()
    
    # Core DuckBot files and directories to include
    include_items = [
        # Core system
        ("duckbot", "dir"),
        ("ai_cache", "dir"),
        ("logs", "dir"),
        ("notebooks", "dir"),
        ("output", "dir"),
        ("workflows", "dir"),
        ("open-notebook", "dir"),
        ("python_embeded", "dir"),
        
        # Documentation
        ("CLAUDE.md", "file"),
        ("README.md", "file"),
        ("QUICKSTART.md", "file"),
        ("QWEN.md", "file"),
        ("COMFYUI_SETUP.md", "file"),
        ("AI-Information.md", "file"),
        ("AGENTS.md", "file"),
        ("FIXES_CHANGELOG.md", "file"),
        ("FINAL_IMPROVEMENTS_SUMMARY.md", "file"),
        ("qwen_system_prompt.md", "file"),
        ("ecosystem_config.yaml", "file"),
        
        # Scripts
        ("SETUP_AND_START.bat", "file"),
        ("SETUP_AND_START_ENHANCED.bat", "file"),
        ("START_DUCKBOT.bat", "file"),
        ("START_COMFYUI.bat", "file"),
        ("launch_ultra_lowvram.bat", "file"),
        ("EMERGENCY_KILL.bat", "file"),
        ("QUICK_KILL.bat", "file"),
        ("install_missing_services.bat", "file"),
        
        # Test scripts
        ("test_enhanced_system.bat", "file"),
        ("test_action_reasoning_system.bat", "file"),
        ("test_all_features.py", "file"),
        ("test_every_feature.py", "file"),
        ("test_simple.py", "file"),
        
        # Python scripts
        ("start_ecosystem.py", "file"),
        ("start_ai_ecosystem.py", "file"),
        ("ai_ecosystem_manager.py", "file"),
        ("direct_launch.py", "file"),
        ("start_comfyui.py", "file"),
        ("start_cost_dashboard.py", "file"),
        ("chat_with_ai.py", "file"),
        ("setup_ai_provider.py", "file"),
        
        # Config files
        ("ai_config.json", "file"),
        ("requirements.txt", "file"),
        ("requirements-core.txt", "file"), 
        ("requirements-extras.txt", "file"),
        ("sitecustomize.py", "file"),
        
        # Workflows
        ("ChatBot-DuckBot.json", "file"),
        ("ChatBot-DuckBot-Safe.json", "file"), 
        ("DuckBot-Audio-DuckTown-Integration.json", "file"),
        
        # Database files
        ("ecosystem_state.db", "file"),
        ("cost_tracking.db", "file"),
    ]
    
    print("[COPY] Copying core files and directories...")
    copied_count = 0
    
    for item, item_type in include_items:
        src_path = base_dir / item
        if src_path.exists():
            dest_path = temp_dir / item
            
            if item_type == "dir" and src_path.is_dir():
                print(f"  [DIR] Copying: {item}")
                # Copy with exclusions
                def ignore_func(dir, files):
                    ignored = []
                    for f in files:
                        if (f.startswith('.') or f.endswith(('.pyc', '.pyo', '.tmp')) or 
                            f in ('__pycache__', 'ComfyUI', 'ComfyUI_windows_portable')):
                            ignored.append(f)
                    return ignored
                
                shutil.copytree(src_path, dest_path, ignore=ignore_func)
                copied_count += 1
                
            elif item_type == "file" and src_path.is_file():
                print(f"  [FILE] Copying: {item}")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                copied_count += 1
        else:
            print(f"  [SKIP] Not found: {item}")
    
    print(f"\n[OK] Copied {copied_count} items")
    
    # Create package documentation
    create_docs(temp_dir, version)
    
    # Create the zip package
    print(f"\n[ZIP] Creating package: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(temp_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                # Skip certain files
                if file.endswith(('.pyc', '.pyo', '.tmp')) or file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                arc_name = file_path.relative_to(temp_dir)
                zf.write(file_path, arc_name)
                
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    # Get final package size
    package_size = zip_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n[SUCCESS] Package created!")
    print(f"[FILE] {zip_path.name}")
    print(f"[SIZE] {package_size:.1f} MB")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create summary
    create_summary(zip_path, version, package_size)
    
    return zip_path

def create_docs(temp_dir, version):
    """Create package documentation"""
    
    readme_content = f"""# DuckBot v{version} Complete Package

## Professional AI-Powered Crypto Analysis & Broadcasting System

### New in v{version} - Action & Reasoning System
- Comprehensive AI decision tracking with full reasoning
- Automatic fallback logging (Qwen -> GLM 4.5 Air -> Local)
- Rate limiting intelligence with separate buckets  
- Server management logging with timing analysis
- Professional WebUI dashboard with real-time updates
- Enterprise SQLite database with performance indexing

### Core Features
- Enhanced AI routing with automatic fallbacks
- Separate rate limits for chat/background tasks
- Professional WebUI with action logs and cost analysis
- Intelligent server management with auto-start
- Discord integration with crypto analysis
- Cost tracking with detailed breakdowns
- Jupyter notebook integration
- Voice features (TTS/STT)

### Quick Start
1. Extract package to desired location
2. Run SETUP_AND_START.bat (Windows)
3. Choose option 1 for full AI-enhanced experience
4. Follow setup wizard for API configuration
5. Access WebUI at http://localhost:8787

### Package Contents
- Complete DuckBot ecosystem
- Action & reasoning logging system
- Enhanced AI router with fallbacks
- Professional WebUI dashboard
- ComfyUI workflows (ComfyUI installation separate)
- Comprehensive documentation and tests
- Setup and configuration wizards

### Requirements
- Python 3.8+ (portable version included)
- Node.js (auto-installed by setup)
- ComfyUI (separate - workflows included)
- API keys (OpenRouter, Anthropic, etc.)

### Support
- Documentation: CLAUDE.md, README.md files
- Testing: Run test_enhanced_system.bat
- Troubleshooting: Use doctor mode (option 4)
- Logs: Structured logging in /logs directory

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(temp_dir / "PACKAGE_README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    install_guide = f"""# DuckBot v{version} Installation Guide

## Quick Installation
1. Extract package to C:\\DuckBot\\ (or preferred location)
2. Run SETUP_AND_START.bat as Administrator  
3. Choose option 1: "AI-Enhanced WebUI Dashboard"
4. Follow setup wizard for API keys and configuration
5. Access dashboard at http://localhost:8787

## Validation
Run comprehensive tests:
- test_enhanced_system.bat (complete system test)
- test_action_reasoning_system.bat (action logging test)
- python test_all_features.py (feature validation)

## Key URLs
- WebUI Dashboard: http://localhost:8787
- Action Logs: http://localhost:8787/action-logs  
- Cost Analysis: http://localhost:8787/cost
- Settings: http://localhost:8787/settings

## Troubleshooting
1. Run doctor mode: Choose option 4 in setup menu
2. Check logs in /logs directory
3. Use emergency kill: EMERGENCY_KILL.bat

For detailed documentation, see CLAUDE.md and README.md files.
"""
    
    with open(temp_dir / "INSTALLATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(install_guide)

def create_summary(zip_path, version, package_size):
    """Create package summary"""
    
    summary_file = zip_path.with_suffix('.txt')
    summary_content = f"""DuckBot v{version} Complete Package Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PACKAGE DETAILS:
- Name: {zip_path.name}
- Size: {package_size:.1f} MB
- Version: {version}
- Type: Complete Package (excludes ComfyUI installation)

NEW FEATURES v{version}:
[+] Action & Reasoning Log System
    - Comprehensive AI decision tracking with full context
    - Automatic fallback logging (Qwen -> GLM -> Local)
    - Rate limiting intelligence with separate buckets
    - Server management logging with timing analysis
    - Professional WebUI dashboard with real-time updates
    - Enterprise SQLite database with performance indexing

[+] Enhanced AI Routing System  
    - Smart model selection with automatic fallbacks
    - No more timeout errors shown to users
    - Separate rate limits: Chat (30/min), Background (30/min)
    - Smart model rotation prevents OpenRouter limits
    - Circuit breaker patterns for reliability

[+] Fixed WebUI Issues
    - Resolved infinite "waiting for background tasks" loop
    - Removed problematic Unicode characters
    - Enhanced lifespan management with timeouts
    - Improved error handling and graceful shutdowns

CORE FEATURES:
[+] Professional WebUI Dashboard
    - Beautiful responsive interface
    - Action logs viewer at /action-logs
    - Cost analysis dashboard at /cost  
    - Settings management at /settings
    - Real-time monitoring and updates

[+] Server Management System
    - Intelligent ComfyUI startup with GPU optimization
    - Auto-installation scripts for missing services
    - Service health monitoring and auto-restart
    - Comprehensive logging of all operations

[+] Complete Ecosystem
    - Discord bot integration
    - Jupyter notebook support
    - n8n workflow automation
    - Open Notebook AI interface
    - Cost tracking and visualization
    - Voice features (TTS/STT)

INSTALLATION:
1. Extract package to desired location
2. Run SETUP_AND_START.bat (Windows)
3. Choose option 1 for full AI-enhanced experience
4. Follow setup wizard for configuration
5. Access WebUI at http://localhost:8787

VALIDATION:
- test_enhanced_system.bat (complete system test)
- test_action_reasoning_system.bat (action logging test)
- Doctor mode (option 4) for diagnostics

This package represents the complete DuckBot v{version} system with all
enhancements, fixes, and new features. Ready for production deployment
with enterprise-grade reliability and comprehensive decision tracking.
"""
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_content)
    
    print(f"[DOCS] Summary created: {summary_file.name}")

if __name__ == "__main__":
    try:
        package_path = create_package()
        print(f"\n[FINAL] DuckBot Complete Package ready: {package_path.name}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create package: {e}")
        import traceback
        traceback.print_exc()