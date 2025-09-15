#!/usr/bin/env python3
"""
Create DuckBot backup zip excluding AI models
"""

import zipfile
import os
from pathlib import Path
import time

def should_exclude(path_str):
    """Check if a path should be excluded from backup"""
    exclude_patterns = [
        # AI Model directories
        '/models/',
        '\\models\\',
        '/checkpoints/',
        '\\checkpoints\\',
        '/lora/',
        '\\lora\\',
        '/vae/',
        '\\vae\\',
        '/embeddings/',
        '\\embeddings\\',
        '/controlnet/',
        '\\controlnet\\',
        # Model file extensions
        '.ckpt',
        '.safetensors',
        '.pt',
        '.pth',
        '.bin',
        # Large cache/temp files
        '__pycache__',
        '.pyc',
        '.pyo',
        'node_modules',
        '.git',
        '.gitignore',
        # Log files and temp data
        '.log',
        '.tmp',
        '.temp',
        '/temp/',
        '\\temp\\',
        '/logs/',
        '\\logs\\',
        # Virtual environments
        '/venv/',
        '\\venv\\',
        '/env/',
        '\\env\\',
        # IDE files
        '.vscode',
        '.idea',
        # Large datasets
        '/datasets/',
        '\\datasets\\',
    ]
    
    path_lower = path_str.lower()
    return any(pattern.lower() in path_lower for pattern in exclude_patterns)

def create_backup_zip():
    """Create comprehensive backup zip"""
    source_dir = Path(r"C:\Users\Duck1\Desktop\DuckBotComplete")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    zip_path = Path(r"C:\Users\Duck1\Desktop") / f"DuckBot-v3.0.5-Complete-Backup-{timestamp}.zip"
    
    try:
        print(f"[COMPRESS]  Creating DuckBot backup: {zip_path.name}")
        print(f"[FOLDER] Source: {source_dir}")
        print("[NO] Excluding: AI models, caches, logs, temp files")
    except UnicodeEncodeError:
        print(f"[ZIP] Creating DuckBot backup: {zip_path.name}")
        print(f"[SRC] Source: {source_dir}")
        print("[EXCL] Excluding: AI models, caches, logs, temp files")
    print()
    
    included_count = 0
    excluded_count = 0
    total_size = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if should_exclude(file_path):
                    excluded_count += 1
                    continue
                
                try:
                    # Get relative path for zip
                    rel_path = os.path.relpath(file_path, source_dir)
                    
                    # Add to zip
                    zipf.write(file_path, rel_path)
                    included_count += 1
                    
                    # Track size
                    total_size += os.path.getsize(file_path)
                    
                    if included_count % 100 == 0:
                        try:
                            print(f"[PACKAGE] Processed {included_count} files...")
                        except UnicodeEncodeError:
                            print(f"[PROC] Processed {included_count} files...")
                        
                except Exception as e:
                    try:
                        print(f"[WARN]  Warning: Could not add {file_path}: {e}")
                    except UnicodeEncodeError:
                        print(f"[WARN] Warning: Could not add {file_path}: {e}")
                    excluded_count += 1
    
    print()
    try:
        print("[OK] Backup created successfully!")
        print(f"[CHART] Statistics:")
        print(f"   • Included files: {included_count:,}")
        print(f"   • Excluded files: {excluded_count:,}")
        print(f"   • Total size: {total_size / (1024*1024):.1f} MB")
        print(f"   • Zip file: {zip_path}")
        print(f"   • Zip size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
        print()
        print("[LIST] Backup includes:")
        print("   [OK] All Python code and configuration")
        print("   [OK] ComfyUI framework (no models)")
        print("   [OK] WebUI interface and templates")
        print("   [OK] AI router and server management")
        print("   [OK] Custom nodes and extensions")
        print("   [OK] Batch files and launchers")
        print("   [OK] Documentation and setup files")
        print()
        print("[NO] Backup excludes:")
        print("   [FAIL] AI model files (*.ckpt, *.safetensors, etc.)")
        print("   [FAIL] Cache and temp files")
        print("   [FAIL] Log files")
        print("   [FAIL] Virtual environments")
        print()
        print(f"[DIR] Ready to distribute: {zip_path}")
    except UnicodeEncodeError:
        print("[SUCCESS] Backup created successfully!")
        print(f"[STATS] Statistics:")
        print(f"   - Included files: {included_count:,}")
        print(f"   - Excluded files: {excluded_count:,}")
        print(f"   - Total size: {total_size / (1024*1024):.1f} MB")
        print(f"   - Zip file: {zip_path}")
        print(f"   - Zip size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
        print()
        print("[INCLUDES] Backup includes:")
        print("   + All Python code and configuration")
        print("   + ComfyUI framework (no models)")
        print("   + WebUI interface and templates")
        print("   + AI router and server management")
        print("   + Custom nodes and extensions")
        print("   + Batch files and launchers")
        print("   + Documentation and setup files")
        print()
        print("[EXCLUDES] Backup excludes:")
        print("   - AI model files (*.ckpt, *.safetensors, etc.)")
        print("   - Cache and temp files")
        print("   - Log files")
        print("   - Virtual environments")
        print()
        print(f"[READY] Ready to distribute: {zip_path}")

if __name__ == "__main__":
    create_backup_zip()