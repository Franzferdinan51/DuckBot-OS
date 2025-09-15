#!/usr/bin/env python3
"""
Quick backup creation excluding ComfyUI
"""
import os
import zipfile
from pathlib import Path

def create_backup():
    """Create DuckBot backup excluding ComfyUI"""
    print("Creating DuckBot Complete Backup...")
    
    base_dir = Path(".")
    zip_path = "DuckBot-v3.0.8-Complete-Backup.zip"
    
    # Major exclusions 
    skip_dirs = {
        'ComfyUI', 'ComfyUI_windows_portable_nvidia', 
        'python_embeded', '__pycache__', '.git', 
        'backup', 'logs', 'temp', 'cache'
    }
    
    # Skip file types
    skip_extensions = {'.log', '.pyc', '.pyo', '.db-shm', '.db-wal'}
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                # Skip excluded file types
                if any(file.endswith(ext) for ext in skip_extensions):
                    continue
                    
                file_path = Path(root) / file
                
                # Skip very large files
                try:
                    if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                        continue
                except:
                    continue
                
                relative_path = file_path.relative_to(base_dir)
                zipf.write(file_path, relative_path)
                
    print(f"[OK] Created: {zip_path}")
    return zip_path

def create_github_package():
    """Create minimal GitHub package"""
    print("Creating GitHub Update Package...")
    
    base_dir = Path(".")
    zip_path = "DuckBot-v3.0.8-GitHub-Update.zip"
    
    # Essential files only
    essential_files = [
        "*.py", "*.bat", "*.md", "*.txt", "*.yaml", "*.yml", "*.json"
    ]
    
    essential_dirs = {
        "duckbot", "workflows", "open-notebook"
    }
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        # Add root level essential files
        for pattern in essential_files:
            for file_path in base_dir.glob(pattern):
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
        
        # Add essential directories
        for dir_name in essential_dirs:
            dir_path = base_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and not any(
                        skip in str(file_path) for skip in 
                        ['.log', '.db', '.pyc', '__pycache__', 'egg-info']
                    ):
                        relative_path = file_path.relative_to(base_dir)
                        zipf.write(file_path, relative_path)
    
    print(f"[OK] Created: {zip_path}")
    return zip_path

if __name__ == "__main__":
    print("[CREATING] DuckBot packages...")
    
    # Create packages
    backup = create_backup()
    github = create_github_package()
    
    print(f"\n[COMPLETE] Packages created:")
    print(f"Backup: {backup}")
    print(f"GitHub: {github}")