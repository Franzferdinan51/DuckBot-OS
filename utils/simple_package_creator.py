#!/usr/bin/env python3
"""
Create final deployment package for DuckBot v3.1.0 with VibeVoice
Simple and effective packaging
"""
import os
import zipfile
from pathlib import Path
from datetime import datetime

def create_package():
    """Create deployment package."""
    
    base_dir = Path.cwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"DuckBot-v3.1.0-VibeVoice-Ready-{timestamp}.zip"
    
    print(f"Creating deployment package: {package_name}")
    
    # Essential files to include
    include_patterns = [
        "*.py", "*.bat", "*.md", "*.txt", "*.json", "*.yaml", "*.yml", ".env*"
    ]
    
    # Essential directories
    include_dirs = [
        "duckbot/",
        "workflows/", 
        "workflow/n8n/",
        "ai_cache/",
        "logs/",
        "scripts/"
    ]
    
    # Exclude patterns
    exclude_patterns = [
        "DuckBot-v3.0.6-FINAL", "DiscordBotAI", "DuckBot Parts", "Training",
        "python_embeded", "*.zip", "*.mp4", "*.backup", "__pycache__",
        ".git", "ComfyUI", "open-notebook", "*.log"
    ]
    
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        file_count = 0
        
        # Add root files
        for pattern in include_patterns:
            for file_path in base_dir.glob(pattern):
                if file_path.is_file():
                    # Check exclude patterns
                    should_exclude = any(excl.lower() in str(file_path).lower() for excl in exclude_patterns)
                    if not should_exclude:
                        zipf.write(file_path, file_path.name)
                        file_count += 1
                        if file_count % 20 == 0:
                            print(f"  Added {file_count} files...")
        
        # Add directories
        for dir_pattern in include_dirs:
            dir_path = base_dir / dir_pattern.rstrip('/')
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Check exclude patterns
                        should_exclude = any(excl.lower() in str(file_path).lower() for excl in exclude_patterns)
                        if not should_exclude:
                            rel_path = file_path.relative_to(base_dir)
                            zipf.write(file_path, rel_path)
                            file_count += 1
                            if file_count % 20 == 0:
                                print(f"  Added {file_count} files...")
    
    # Get package info
    package_size_mb = os.path.getsize(package_name) / (1024 * 1024)
    
    print(f"\nDEPLOYMENT PACKAGE READY!")
    print(f"Package: {package_name}")
    print(f"Size: {package_size_mb:.1f} MB")
    print(f"Files: {file_count}")
    
    print(f"\nINCLUDED:")
    print(f"  - DuckBot v3.1.0 with VibeVoice integration")
    print(f"  - Discord bot with voice commands")  
    print(f"  - Professional WebUI dashboard")
    print(f"  - n8n workflows")
    print(f"  - Configuration files and scripts")
    print(f"  - Complete documentation")
    
    print(f"\nEXCLUDED:")
    print(f"  - ComfyUI (image generation)")
    print(f"  - Open Notebook")
    print(f"  - Old versions and backups") 
    print(f"  - Large embedded Python")
    print(f"  - Training data and media files")
    
    print(f"\nREADY FOR DEPLOYMENT ON ANY SYSTEM!")
    print(f"Users need to: 1) Extract 2) pip install -r requirements.txt 3) Configure .env 4) Run SETUP_AND_START.bat")
    
    return package_name

if __name__ == "__main__":
    try:
        package = create_package()
        print(f"\nSuccess! Package: {package}")
    except Exception as e:
        print(f"Error: {e}")