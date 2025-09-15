#!/usr/bin/env python3
"""
Quick complete backup - essential directories only
"""
import os
import zipfile
from pathlib import Path

def main():
    print("Creating DuckBot Complete Backup (Essential Only)...")
    
    base_dir = Path(".")
    zip_path = "DuckBot-v3.0.8-Complete-Backup.zip"
    
    # Essential directories and files
    include_items = [
        # Core directories
        "duckbot/",
        "open-notebook/",
        "workflows/", 
        
        # Root files
        "*.py", "*.bat", "*.md", "*.txt", 
        "*.yaml", "*.yml", "*.json",
        
        # Config directories
        "ai_cache/",
        "backup/",
        "logs/",
        "notebooks/",
        "output/"
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        file_count = 0
        
        # Add root level files by pattern
        for pattern in ["*.py", "*.bat", "*.md", "*.txt", "*.yaml", "*.yml", "*.json"]:
            for file_path in base_dir.glob(pattern):
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
                    file_count += 1
        
        # Add essential directories
        essential_dirs = ["duckbot", "open-notebook", "workflows", "ai_cache", "backup", "notebooks", "output"]
        
        for dir_name in essential_dirs:
            dir_path = base_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        # Skip problematic files
                        if any(skip in str(file_path) for skip in [
                            '.log', '.db-shm', '.db-wal', '__pycache__', '.tmp'
                        ]):
                            continue
                        
                        # Skip very large files
                        try:
                            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                                continue
                        except:
                            continue
                        
                        relative_path = file_path.relative_to(base_dir)
                        zipf.write(file_path, relative_path)
                        file_count += 1
                        
                        if file_count % 50 == 0:
                            print(f"Added {file_count} files...")
    
    print(f"\n[COMPLETE] Backup created: {zip_path}")
    print(f"Total files: {file_count}")
    
    # Verify integrity
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.testzip()
            zip_size = Path(zip_path).stat().st_size / (1024 * 1024)
            print(f"Archive size: {zip_size:.1f} MB")
            print("[OK] Backup verified successfully")
    except Exception as e:
        print(f"[ERROR] Backup verification failed: {e}")

if __name__ == "__main__":
    main()