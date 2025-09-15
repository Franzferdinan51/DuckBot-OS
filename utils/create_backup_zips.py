#!/usr/bin/env python3
"""
Create DuckBot Complete backup and GitHub update packages
Excludes ComfyUI folders but includes ComfyUI workflows
"""
import os
import zipfile
import shutil
from pathlib import Path

def create_backup_zip():
    """Create complete backup excluding ComfyUI folders"""
    print("Creating DuckBot Complete Backup...")
    
    base_dir = Path("C:/Users/Duck1/Desktop/DuckBotComplete")
    backup_name = "DuckBot-v3.0.8-Complete-Backup"
    zip_path = base_dir / f"{backup_name}.zip"
    
    # Exclusion patterns for backup
    exclude_patterns = [
        'ComfyUI/',
        'ComfyUI_windows_portable_nvidia/',
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.log',
        '.git/',
        'node_modules/',
        'temp/',
        'cache/',
        '.pytest_cache/',
        '.mypy_cache/'
    ]
    
    # Always include these important files
    force_include = [
        'workflows/',
        'ComfyUI/workflows/',  # Include workflows from ComfyUI if they exist
        '*.json',
        '*.yaml', 
        '*.yml',
        '*.md',
        '*.txt',
        '*.bat',
        '*.py'
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.rstrip('/') in d for pattern in exclude_patterns)]
            
            relative_root = Path(root).relative_to(base_dir)
            
            # Skip if in excluded pattern
            if any(pattern.rstrip('/') in str(relative_root) for pattern in exclude_patterns):
                continue
                
            for file in files:
                file_path = Path(root) / file
                relative_path = Path(root).relative_to(base_dir) / file
                
                # Skip excluded files
                if any(pattern.lstrip('*') in file or pattern.rstrip('/') in str(relative_path) for pattern in exclude_patterns):
                    continue
                
                # Add to zip
                zipf.write(file_path, relative_path)
                
    print(f"[OK] Backup created: {zip_path}")
    return zip_path

def create_github_zip():
    """Create GitHub update package with essential files only"""
    print("Creating GitHub Update Package...")
    
    base_dir = Path("C:/Users/Duck1/Desktop/DuckBotComplete")
    github_name = "DuckBot-v3.0.8-GitHub-Update"
    zip_path = base_dir / f"{github_name}.zip"
    
    # Essential files for GitHub
    github_files = [
        # Core Python files
        "*.py",
        "duckbot/",
        "workflows/",
        
        # Configuration files
        "*.yaml", "*.yml", "*.json",
        "requirements*.txt",
        "ecosystem_config.yaml",
        "ai_config.json",
        
        # Documentation
        "*.md",
        "CLAUDE.md",
        "README.md",
        "QUICKSTART.md",
        
        # Scripts
        "*.bat",
        
        # Open Notebook (without large files)
        "open-notebook/*.py",
        "open-notebook/*.md", 
        "open-notebook/*.yml",
        "open-notebook/*.yaml",
        "open-notebook/*.json",
        "open-notebook/api/",
        "open-notebook/pages/",
        "open-notebook/commands/",
        "open-notebook/migrations/",
        
        # Templates and static files
        "duckbot/templates/",
        "duckbot/static/"
    ]
    
    # Exclusions for GitHub
    exclude_from_github = [
        '*.log', '*.db', '*.db-*',
        'python_embeded/',
        'ComfyUI/',
        'ComfyUI_windows_portable_nvidia/',
        '__pycache__/',
        '*.pyc', '*.pyo',
        'backup/',
        'logs/',
        'temp/',
        'cache/',
        '.pytest_cache/',
        '.mypy_cache/',
        'open_notebook.egg-info/',
        'uv.lock'
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if not any(excl.rstrip('/') in d for excl in exclude_from_github)]
            
            relative_root = Path(root).relative_to(base_dir)
            
            # Skip excluded directories
            if any(excl.rstrip('/') in str(relative_root) for excl in exclude_from_github):
                continue
                
            for file in files:
                file_path = Path(root) / file
                relative_path = relative_root / file
                
                # Skip excluded files  
                if any(excl.lstrip('*') in file for excl in exclude_from_github if excl.startswith('*')):
                    continue
                if any(excl.rstrip('/') in str(relative_path) for excl in exclude_from_github):
                    continue
                
                # Only include essential files
                include_file = (
                    file.endswith(('.py', '.md', '.txt', '.bat', '.yaml', '.yml', '.json', '.html', '.css', '.js')) or
                    'duckbot' in str(relative_path) or
                    'workflows' in str(relative_path) or
                    'open-notebook' in str(relative_path) and not any(excl in str(relative_path) for excl in exclude_from_github)
                )
                
                if include_file:
                    zipf.write(file_path, relative_path)
                    
    print(f"[OK] GitHub package created: {zip_path}")
    return zip_path

if __name__ == "__main__":
    print("[ROCKET] Creating DuckBot Complete packages...")
    
    # Create both packages
    backup_zip = create_backup_zip()
    github_zip = create_github_zip()
    
    print("\n[PACKAGE] Package Summary:")
    print(f"[FOLDER] Complete Backup: {backup_zip}")
    print(f"[GITHUB] GitHub Update: {github_zip}")
    print("\n[OK] All packages created successfully!")