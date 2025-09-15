#!/usr/bin/env python3
"""
Simple backup creation - just essential files
"""
import os
import zipfile
from pathlib import Path

def main():
    print("Creating DuckBot GitHub Update Package...")
    
    base_dir = Path(".")
    zip_path = "DuckBot-v3.0.8-GitHub-Update.zip"
    
    # Essential files to include
    essential_files = [
        # Root Python files
        "ai_ecosystem_manager.py",
        "start_ecosystem.py", 
        "start_local_ecosystem.py",
        "model_status.py",
        "chat_with_ai.py",
        
        # Configuration files
        "ecosystem_config.yaml",
        "ai_config.json", 
        "requirements.txt",
        "requirements-core.txt",
        
        # Documentation
        "CLAUDE.md",
        "README.md",
        "QUICKSTART.md",
        "OPEN_NOTEBOOK_SUCCESS.md",
        
        # Scripts
        "START_LOCAL_ONLY.bat",
        "SETUP_AND_START.bat",
        "START_DUCKBOT.bat",
        "EMERGENCY_KILL.bat"
    ]
    
    # Essential directories (limited to avoid timeout)
    essential_dirs = [
        "duckbot",
        "workflows"
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add essential root files
        for filename in essential_files:
            file_path = base_dir / filename
            if file_path.exists():
                zipf.write(file_path, filename)
                print(f"Added: {filename}")
        
        # Add essential directories
        for dir_name in essential_dirs:
            dir_path = base_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Skip log files and cache
                        if any(skip in str(file_path) for skip in ['.log', '.db', '.pyc', '__pycache__']):
                            continue
                        relative_path = file_path.relative_to(base_dir)
                        zipf.write(file_path, relative_path)
                        print(f"Added: {relative_path}")
    
    print(f"\n[COMPLETE] GitHub package created: {zip_path}")
    
    # Show zip contents
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        print(f"Package contains {len(zipf.filelist)} files")

if __name__ == "__main__":
    main()