#!/usr/bin/env python3
"""
Create simple streamlined DuckBot package without ComfyUI and Open Notebook
"""
import os
import zipfile
from datetime import datetime
from pathlib import Path

def create_simple_zip():
    """Create a simple streamlined DuckBot package."""
    
    base_dir = Path.cwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"DuckBot-Streamlined-{timestamp}.zip"
    
    print(f"Creating streamlined package: {package_name}")
    
    # Essential files to include
    include_patterns = [
        "*.py", "*.bat", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"
    ]
    
    # Essential directories
    include_dirs = [
        "duckbot/",
        "logs/", 
        "ai_cache/",
        "scripts/",
        "workflows/",
        "workflow/n8n/",
        "DiscordBotAI/"
    ]
    
    # Exclude patterns
    exclude_patterns = [
        "comfyui", "open-notebook", "open_notebook", ".mp4", ".zip",
        "__pycache__", ".git", "node_modules", "python_embeded"
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
                        if file_count % 10 == 0:
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
                            if file_count % 50 == 0:
                                print(f"  Added {file_count} files...")
    
    # Get package info
    package_size_mb = os.path.getsize(package_name) / (1024 * 1024)
    
    print(f"\nSuccess! Created: {package_name}")
    print(f"Size: {package_size_mb:.1f} MB")
    print(f"Files: {file_count}")
    
    print(f"\nINCLUDED:")
    print(f"  - Core DuckBot AI system")
    print(f"  - Discord bot")  
    print(f"  - n8n workflows")
    print(f"  - WebUI dashboard")
    print(f"  - Configuration files")
    
    print(f"\nEXCLUDED:")
    print(f"  - ComfyUI (image generation)")
    print(f"  - Open Notebook") 
    print(f"  - Large embedded Python")
    print(f"  - Video files")
    
    print(f"\nReady for Vibe Voice integration!")
    
    return package_name

if __name__ == "__main__":
    try:
        package_name = create_simple_zip()
        print(f"\nPackage ready: {package_name}")
    except Exception as e:
        print(f"Error: {e}")
        raise