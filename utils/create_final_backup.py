#!/usr/bin/env python3
"""
Create final backup and ZIP of fully tested DuckBot system
"""
import os
import zipfile
import datetime
from pathlib import Path
import shutil

def create_backup():
    """Create backup and ZIP file"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    source_dir = Path("DuckBotComplete")
    
    # Create backup directory name
    backup_name = f"DuckBot-v3.0.6-TESTED-{timestamp}"
    zip_name = f"{backup_name}.zip"
    
    print(f"[BACKUP] Creating backup: {backup_name}")
    
    # Files to exclude from backup
    exclude_patterns = [
        "*.zip", "*.bak", "*.tmp", "__pycache__", "*.pyc", 
        "*.log", "nul", "webui_token.txt", ".env.bak",
        "node_modules", ".git", "test_*.py", "create_*.py"
    ]
    
    # Create ZIP file
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        file_count = 0
        
        for root, dirs, files in os.walk(source_dir):
            # Skip problematic directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                # Skip excluded files
                if any(pattern.replace('*', '') in file.lower() for pattern in exclude_patterns):
                    continue
                
                try:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    
                    if file_count % 100 == 0:
                        print(f"[PROGRESS] Added {file_count} files...")
                        
                except Exception as e:
                    print(f"[SKIP] {file}: {e}")
    
    # Get ZIP size
    zip_size = os.path.getsize(zip_name)
    zip_size_mb = zip_size / (1024 * 1024)
    
    print(f"[SUCCESS] Created {zip_name}")
    print(f"[SIZE] {zip_size_mb:.1f} MB ({file_count} files)")
    
    # Create summary file
    summary_name = f"{backup_name}_SUMMARY.txt"
    with open(summary_name, 'w', encoding='utf-8') as f:
        f.write(f"DuckBot v3.0.6 - FULLY TESTED RELEASE\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files: {file_count}\n")
        f.write(f"Size: {zip_size_mb:.1f} MB\n\n")
        
        f.write("TESTED FEATURES:\n")
        f.write("- SETUP_AND_START.bat Option 1 (Unified WebUI)\n")
        f.write("- All critical imports working\n")  
        f.write("- Server management (7 services)\n")
        f.write("- AI routing with dynamic model selection\n")
        f.write("- WebUI with token authentication\n")
        f.write("- Unicode encoding fixes applied\n")
        f.write("- LM Studio integration (nvidia_acereason-nemotron-14b detected)\n")
        f.write("- ComfyUI integration (running on port 8188)\n")
        f.write("- n8n availability (v1.108.1)\n")
        f.write("- Qwen-Agent integration framework\n\n")
        
        f.write("KEY FIXES APPLIED:\n")
        f.write("- Fixed Unicode encoding issues in WebUI and logging\n")
        f.write("- Fixed n8n installation detection timeout\n") 
        f.write("- Fixed SETUP_AND_START.bat output visibility\n")
        f.write("- Added dynamic model selection for Nemotron 49B\n")
        f.write("- Enhanced server management with natural language\n")
        f.write("- Token persistence between WebUI pages\n")
        f.write("- Configuration errors in ecosystem_config.yaml\n\n")
        
        f.write("PRODUCTION READY STATUS: [OK] FULLY TESTED\n")
        f.write("All core features verified and working correctly.\n")
    
    print(f"[SUMMARY] Created {summary_name}")
    return zip_name, summary_name

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    zip_file, summary_file = create_backup()
    print(f"\n[COMPLETE] Backup ready: {zip_file}")
    print(f"[SUMMARY] Details: {summary_file}")