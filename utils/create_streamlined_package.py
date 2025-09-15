#!/usr/bin/env python3
"""
Create streamlined DuckBot package without ComfyUI and Open Notebook
Keeps: Agent tools, Discord bot, n8n workflows, WebUI, core AI features
"""
import os
import sys
import zipfile
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

def create_streamlined_package():
    """Create a streamlined DuckBot package without ComfyUI and Open Notebook."""
    
    # Get current directory
    base_dir = Path.cwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"DuckBot-Streamlined-{timestamp}.zip"
    
    print(f"[DUCKBOT] Creating streamlined DuckBot package: {package_name}")
    print("[EXCLUDE] Excluding: ComfyUI and Open Notebook")
    print("[INCLUDE] Including: Agent tools, Discord bot, n8n workflows, WebUI, core AI")
    
    # Create temporary directory for staging
    with tempfile.TemporaryDirectory() as temp_dir:
        staging_dir = Path(temp_dir) / "DuckBot-Streamlined"
        staging_dir.mkdir()
        
        # Essential files and directories to include
        essential_items = [
            # Core files
            "*.py",
            "*.bat", 
            "*.md",
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.env*",
            
            # Core directories
            "duckbot/",
            "logs/",
            "ai_cache/",
            "scripts/",
            "backup/",
            
            # Discord bot
            "DuckBot-v2.3.0-Trading-Video-Enhanced.py",
            
            # Workflows (excluding ComfyUI specific ones)
            "workflows/",
            "workflow/n8n/",
            "workflow/codex/",
            
            # n8n specific
            "DiscordBotAI/",  # Contains Discord bot versions
            
            # Required dependencies
            "requirements*.txt",
            "python_embeded/",  # Keep embedded Python
        ]
        
        # Items to explicitly exclude
        exclude_patterns = [
            "*ComfyUI*",
            "*comfyui*", 
            "*open-notebook*",
            "*open_notebook*",
            "DuckBot Parts/ComfyUI*",
            "workflow/ComfyUI/",
            "ComfyUI_*/",
            "*.mp4",  # Large video files
            "*.zip",  # Existing zip files
            "__pycache__/",
            ".git/",
            "node_modules/",
        ]
        
        print(f"\n[COPY] Copying essential files to staging area...")
        
        # Copy files and directories
        for item in base_dir.rglob("*"):
            if item.is_file():
                # Check if item should be excluded
                item_str = str(item.relative_to(base_dir)).lower()
                should_exclude = any(
                    exclude_pattern.lower().replace("*", "") in item_str 
                    for exclude_pattern in exclude_patterns
                )
                
                if should_exclude:
                    continue
                
                # Check if item matches essential patterns
                relative_path = item.relative_to(base_dir)
                should_include = False
                
                for pattern in essential_items:
                    if pattern.endswith("/"):
                        # Directory pattern
                        if str(relative_path).startswith(pattern):
                            should_include = True
                            break
                    elif "*" in pattern:
                        # Wildcard pattern
                        if item.name.endswith(pattern[1:]) or pattern[:-1] in item.name:
                            should_include = True
                            break
                    else:
                        # Exact match
                        if item.name == pattern:
                            should_include = True
                            break
                
                if should_include:
                    dest_path = staging_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(item, dest_path)
                        if len(str(relative_path)) < 80:
                            print(f"  [OK] {relative_path}")
                    except Exception as e:
                        print(f"  [WARN] Failed to copy {relative_path}: {e}")
        
        # Create the zip package
        print(f"\n[ZIP] Creating zip package: {package_name}")
        with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for file_path in staging_dir.rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(staging_dir)
                    zipf.write(file_path, arc_name)
        
        # Get package info
        package_size_mb = os.path.getsize(package_name) / (1024 * 1024)
        file_count = len([f for f in staging_dir.rglob("*") if f.is_file()])
        
        print(f"\n[SUCCESS] Streamlined DuckBot package created successfully!")
        print(f"[PACKAGE] Package: {package_name}")
        print(f"[SIZE] Size: {package_size_mb:.1f} MB")
        print(f"[FILES] Files: {file_count}")
        
        print(f"\n[INCLUDED] INCLUDED COMPONENTS:")
        print(f"  [AI] AI Agent and tools")
        print(f"  [DISCORD] Discord bot (all versions)")
        print(f"  [N8N] n8n workflows")
        print(f"  [WEBUI] WebUI dashboard")
        print(f"  [CORE] Core AI routing and management")
        print(f"  [COST] Cost tracking and analytics")
        print(f"  [PYTHON] Python embedded environment")
        print(f"  [CONFIG] Configuration files")
        print(f"  [SCRIPTS] Scripts and utilities")
        
        print(f"\n[EXCLUDED] EXCLUDED COMPONENTS:")
        print(f"  [COMFYUI] ComfyUI (image/video generation)")
        print(f"  [NOTEBOOK] Open Notebook")
        print(f"  [VIDEO] Large video files")
        print(f"  [BACKUP] Existing backup zips")
        
        print(f"\n[VOICE] READY FOR VIBE VOICE INTEGRATION!")
        print(f"  This streamlined package is optimized for voice features")
        print(f"  No image generation conflicts with TTS systems")
        
        return package_name

if __name__ == "__main__":
    try:
        package_name = create_streamlined_package()
        print(f"\n[DUCKBOT] DuckBot streamlined package ready: {package_name}")
    except Exception as e:
        print(f"[ERROR] Error creating package: {e}")
        raise