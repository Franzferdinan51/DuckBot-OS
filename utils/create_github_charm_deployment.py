#!/usr/bin/env python3
"""
Create Complete GitHub Deployment Package for DuckBot Enhanced v4.2
Includes complete Charm ecosystem integration and all required files
"""

import os
import zipfile
import json
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """Create complete deployment package with all required files"""
    
    # Package info
    package_name = "DuckBot-Enhanced-v4.2-Charm-Ecosystem-Complete"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{package_name}-{timestamp}.zip"
    
    # Current directory
    source_dir = Path.cwd()
    
    # Essential files and directories for deployment
    include_files = [
        # Core Python files
        "ai_ecosystem_manager.py",
        "start_ecosystem.py",
        "call_agent.py",
        "create_github_package.py",
        
        # Documentation
        "README.md",
        "CLAUDE.md",
        "CRUSH.md",
        "AGENTS.md",
        "AVATAR_API_GUIDE.md",
        "GITHUB_PACKAGE_SUMMARY.md",
        "INTEGRATION_ENHANCEMENT_SUMMARY.md",
        
        # Requirements and config
        "requirements.txt",
        "requirements-core.txt", 
        "requirements-extras.txt",
        "enhanced_config.json",
        "hardware_config.json",
        "provider_config.json",
        
        # Startup scripts
        "START_ENHANCED_DUCKBOT.bat",
        "START_DUCKBOT.bat",
        "START_DUCKBOT_OS.bat",
        "START_DUCKBOT_OS_ONLY.bat",
        "START_HEADLESS_LOCAL.bat",
        "START_OPEN_WEBUI.bat",
        "START_OPENWEBUI_CLAUDE_ROUTER.bat",
        "START_OPENWEBUI_OPENROUTER_FREE.bat",
        "QWEN_SETUP_AND_START.bat",
        "QUICK_FIX_DEPENDENCIES.bat",
        
        # OpenWebUI integration files
        "duckbot_openwebui_function.json",
        "duckbot_openwebui_function.py",
        "openwebui_duckbot_complete_all_features.py",
        "openwebui_duckbot_tool.py",
        "OPENWEBUI_INSTALL_GUIDE.md",
        "INSTALL_OPENWEBUI_TOOL.md",
        "WORKSPACE_TOOL_INSTALL.md",
        
        # Test files
        "test_duckbot_os.py",
        "test_hardware_detection.py",
        "test_integration.py",
        "test_enhanced_system.bat",
        
        # HTML/JS files
        "DuckBotOS-Complete.html",
        "DuckBotOS-Complete.js",
        "robot_companion_fixed.html",
        
        # Workflow files
        "ChatBot-DuckBot.json",
        "ChatBot-DuckBot-Safe.json",
        "trading-news-video-workflow_i2v_fix (1).json",
    ]
    
    include_directories = [
        "duckbot",
        "scripts", 
        "config",
        "docs",
        "tools",
        "utilities",
        "startup",
        "tests",
        "workflows",
        "open-notebook",
        "duckbot-os",
        "interactive-3d-talking-robot",
        "integrations",
    ]
    
    print(f"Creating deployment package: {zip_name}")
    print("=" * 60)
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        
        # Add individual files
        for file_name in include_files:
            file_path = source_dir / file_name
            if file_path.exists():
                zipf.write(file_path, file_name)
                print(f"[OK] Added file: {file_name}")
                files_added += 1
            else:
                print(f"[WARN] Missing file: {file_name}")
        
        # Add directories
        for dir_name in include_directories:
            dir_path = source_dir / dir_name
            if dir_path.exists():
                dir_files = 0
                for root, dirs, files in os.walk(dir_path):
                    # Skip certain directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
                    
                    for file in files:
                        # Skip certain file types
                        if file.endswith(('.pyc', '.pyo', '.log', '.tmp', '.cache')):
                            continue
                        
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(source_dir)
                        zipf.write(file_path, str(arc_path))
                        dir_files += 1
                
                print(f"[OK] Added directory: {dir_name} ({dir_files} files)")
                files_added += dir_files
            else:
                print(f"[WARN] Missing directory: {dir_name}")
        
        # Create deployment info file
        deployment_info = {
            "package_name": package_name,
            "version": "4.2",
            "created_at": datetime.now().isoformat(),
            "features": [
                "Complete Charm Ecosystem Integration",
                "GitHub Spec-Kit Integration", 
                "8 Charm CLI Tools with Python Wrappers",
                "Interactive Terminal UI Components",
                "Spec-Driven Development Workflows",
                "3D Interactive Avatar",
                "Chrome OS-like Desktop Environment",
                "OpenWebUI Integration",
                "Enterprise AI Router",
                "Cost Analytics Dashboard"
            ],
            "charm_tools": [
                "gum - Interactive shell components",
                "glow - Markdown rendering", 
                "mods - AI-powered commands",
                "skate - Key-value storage",
                "crush - AI coding agent",
                "charm - Backend system",
                "freeze - Code screenshots", 
                "vhs - Terminal recording"
            ],
            "requirements": [
                "Windows 10/11",
                "Python 3.8+",
                "Go 1.20+ (for Charm tools)",
                "4GB RAM minimum",
                "2GB disk space"
            ],
            "setup_instructions": [
                "1. Extract package to desired location",
                "2. Run START_ENHANCED_DUCKBOT.bat",
                "3. Choose Option 1 for complete experience", 
                "4. Copy token URL from terminal",
                "5. Paste in browser for instant access"
            ],
            "total_files": files_added
        }
        
        zipf.writestr("DEPLOYMENT_INFO.json", json.dumps(deployment_info, indent=2))
        
        # Create setup verification script
        setup_script = '''#!/usr/bin/env python3
"""
DuckBot Enhanced v4.2 Setup Verification Script
Verifies all components are properly installed
"""

import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[EMOJI] Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"[EMOJI] Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def check_go():
    """Check Go installation"""
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[EMOJI] {result.stdout.strip()} - OK")
            return True
    except FileNotFoundError:
        pass
    print("[EMOJI] Go not found - Required for Charm tools")
    return False

def check_charm_tools():
    """Check Charm tools installation"""
    tools = ['gum', 'glow', 'mods', 'skate', 'crush', 'charm', 'freeze', 'vhs']
    available = []
    
    go_bin = Path.home() / 'go' / 'bin'
    
    for tool in tools:
        tool_path = go_bin / f"{tool}.exe"  # Windows
        if not tool_path.exists():
            tool_path = go_bin / tool  # Linux/Mac
        
        if tool_path.exists():
            available.append(tool)
            print(f"[EMOJI] {tool} - Available")
        else:
            print(f"[EMOJI] {tool} - Missing")
    
    print(f"\\nCharm Tools: {len(available)}/{len(tools)} available")
    return len(available) == len(tools)

def check_duckbot_integration():
    """Check DuckBot Charm integration"""
    try:
        sys.path.append('.')
        from duckbot.charm_tools_integration import get_charm_status
        status = get_charm_status()
        print(f"[EMOJI] DuckBot Charm Integration: {status['total_tools']} tools integrated")
        return status['total_tools'] > 0
    except ImportError:
        print("[EMOJI] DuckBot Charm Integration - Import failed")
        return False
    except Exception as e:
        print(f"[EMOJI] DuckBot Charm Integration - Error: {e}")
        return False

def main():
    print("DuckBot Enhanced v4.2 - Setup Verification")
    print("=" * 50)
    
    checks = [
        check_python(),
        check_go(),
        check_charm_tools(),
        check_duckbot_integration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print("\\n" + "=" * 50)
    print(f"Setup Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("[SUCCESS] All systems ready! Run START_ENHANCED_DUCKBOT.bat to begin.")
    else:
        print("⚠ Some components need attention. Check the output above.")
        print("[EMOJI] See README.md for complete setup instructions.")

if __name__ == "__main__":
    main()
'''
        
        zipf.writestr("verify_setup.py", setup_script)
        
        print(f"\\n[OK] Created deployment info and setup verification script")
        files_added += 2
    
    # Create summary
    print("\\n" + "=" * 60)
    print(f"DEPLOYMENT PACKAGE CREATED: {zip_name}")
    print(f"Total files included: {files_added}")
    print(f"Package size: {os.path.getsize(zip_name) / (1024*1024):.1f} MB")
    print("\\nREADY FOR GITHUB DISTRIBUTION!")
    print("\\nNext Steps:")
    print("1. Upload to GitHub repository")
    print("2. Create release tag (v4.2)")
    print("3. Add release notes with Charm ecosystem features")
    print("4. Test installation on clean system")
    
    return zip_name

if __name__ == "__main__":
    create_deployment_package()