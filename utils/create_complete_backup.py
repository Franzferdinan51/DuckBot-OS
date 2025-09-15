#!/usr/bin/env python3
"""
Complete backup excluding ComfyUI and large files
"""
import os
import zipfile
from pathlib import Path

def main():
    print("Creating DuckBot Complete Backup...")
    
    base_dir = Path(".")
    zip_path = "DuckBot-v3.0.8-Complete-Backup.zip"
    
    # Directories to completely exclude
    exclude_dirs = {
        'ComfyUI', 
        'ComfyUI_windows_portable_nvidia',
        'python_embeded',
        '__pycache__',
        '.git',
        'backup',
        'temp',
        'cache'
    }
    
    # File extensions to skip
    skip_extensions = {'.log', '.pyc', '.pyo', '.db-shm', '.db-wal'}
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        file_count = 0
        for root, dirs, files in os.walk(base_dir):
            # Remove excluded directories from traversal
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # Skip excluded file types
                if any(file.endswith(ext) for ext in skip_extensions):
                    continue
                    
                file_path = Path(root) / file
                
                # Skip very large files (over 50MB)
                try:
                    if file_path.stat().st_size > 50 * 1024 * 1024:
                        print(f"Skipping large file: {file_path}")
                        continue
                except:
                    continue
                
                relative_path = file_path.relative_to(base_dir)
                zipf.write(file_path, relative_path)
                file_count += 1
                
                # Print progress every 100 files
                if file_count % 100 == 0:
                    print(f"Added {file_count} files...")
    
    print(f"\n[COMPLETE] Complete backup created: {zip_path}")
    print(f"Total files: {file_count}")
    
    # Show zip size
    zip_size = Path(zip_path).stat().st_size / (1024 * 1024)
    print(f"Archive size: {zip_size:.1f} MB")

if __name__ == "__main__":
    main()