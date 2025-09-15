#!/usr/bin/env python3
"""
Create DuckBot backup zip excluding AI models - NO EMOJIS VERSION
"""

import zipfile
import os
from pathlib import Path
import time

def should_exclude(path_str):
    """Check if a path should be excluded from backup"""
    exclude_patterns = [
        # AI Model directories and files
        '/models/', '\\models\\', '/checkpoints/', '\\checkpoints\\',
        '/lora/', '\\lora\\', '/vae/', '\\vae\\', '/embeddings/', '\\embeddings\\',
        '/controlnet/', '\\controlnet\\',
        '.ckpt', '.safetensors', '.pt', '.pth', '.bin',
        # Cache and temp files
        '__pycache__', '.pyc', '.pyo', 'node_modules', '.git',
        '.log', '.tmp', '.temp', '/temp/', '\\temp\\', '/logs/', '\\logs\\',
        # Virtual environments and IDE
        '/venv/', '\\venv\\', '/env/', '\\env\\', '.vscode', '.idea',
        # Large datasets
        '/datasets/', '\\datasets\\',
        # Exclude most ComfyUI directories except workflows
        '/ComfyUI/models/', '\\ComfyUI\\models\\',
        '/ComfyUI/output/', '\\ComfyUI\\output\\',
        '/ComfyUI/input/', '\\ComfyUI\\input\\',
        '/ComfyUI/temp/', '\\ComfyUI\\temp\\',
        '/ComfyUI/web/', '\\ComfyUI\\web\\',
        '/ComfyUI/tests/', '\\ComfyUI\\tests\\',
        '/comfyui/models/', '\\comfyui\\models\\',
        '/comfyui/output/', '\\comfyui\\output\\',
        '/comfyui/input/', '\\comfyui\\input\\',
        '/comfyui/temp/', '\\comfyui\\temp\\',
        '/comfyui/web/', '\\comfyui\\web\\',
        '/comfyui/tests/', '\\comfyui\\tests\\',
    ]
    
    path_lower = path_str.lower()
    return any(pattern.lower() in path_lower for pattern in exclude_patterns)

def create_backup_zip():
    """Create comprehensive backup zip"""
    source_dir = Path(r"C:\Users\Duck1\Desktop\DuckBotComplete")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    zip_path = Path(r"C:\Users\Duck1\Desktop") / f"DuckBot-v3.0.5-Complete-Backup-{timestamp}.zip"
    
    print(f"Creating DuckBot backup: {zip_path.name}")
    print(f"Source: {source_dir}")
    print("Excluding: AI models, caches, logs, temp files")
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
                    
                    if included_count % 500 == 0:
                        print(f"Processed {included_count} files...")
                        
                except Exception as e:
                    print(f"Warning: Could not add {file_path}: {e}")
                    excluded_count += 1
    
    print()
    print("SUCCESS: Backup created successfully!")
    print(f"Statistics:")
    print(f"  - Included files: {included_count:,}")
    print(f"  - Excluded files: {excluded_count:,}")
    print(f"  - Total size: {total_size / (1024*1024):.1f} MB")
    print(f"  - Zip file: {zip_path}")
    print(f"  - Zip size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
    print()
    print("Backup includes:")
    print("  + All Python code and configuration")
    print("  + ComfyUI workflows and custom nodes only")
    print("  + WebUI interface and templates") 
    print("  + AI router and server management")
    print("  + Batch files and launchers")
    print("  + Documentation and setup files")
    print()
    print("Backup excludes:")
    print("  - AI model files (*.ckpt, *.safetensors, etc.)")
    print("  - ComfyUI models, output, input, temp, web directories")
    print("  - Cache and temp files")
    print("  - Log files")
    print("  - Virtual environments")
    print()
    print(f"Ready to distribute: {zip_path}")

if __name__ == "__main__":
    create_backup_zip()