#!/usr/bin/env python3
"""
Unicode Encoding Fix for DuckBot
Fixes Windows console encoding issues that prevent system startup
"""
import os
import sys
import re
from pathlib import Path

def fix_unicode_in_file(file_path):
    """Fix Unicode emojis in a single file by replacing with ASCII equivalents"""
    
    # Unicode emoji to ASCII replacements
    replacements = {
        '[EMOJI]': '[BRAIN]',
        '[OK]': '[OK]', 
        '[FAIL]': '[ERROR]',
        '[WARN]': '[WARNING]',
        '[EMOJI]': '[GPU]',
        '[EMOJI][EMOJI]': '[PROTECTED]',
        '[CHART]': '[METRICS]',
        '[EMOJI]': '[LOADING]',
        '⏳': '[WAITING]',
        '[SAVE]': '[SAVE]',
        '[TARGET]': '[TARGET]',
        '[LAUNCH]': '[START]',
        '[EMOJI]': '[LOCAL]',
        '[GLOBE]': '[CLOUD]',
        '[EMOJI]': '[SECURE]',
        '[ART]': '[COMFYUI]',
        '[EMOJI]': '[DUCKBOT]',
        '[EMOJI]': '[NOTEBOOK]',
        '[AI]': '[AI]',
        '[EMOJI]': '[TIP]',
        '[STOP]': '[STOP]',
        '⚡': '[FAST]',
        '[EMOJI]': '[SEARCH]',
        '[FOLDER]': '[FILES]',
        '[COMPUTER]': '[SYSTEM]',
        '[EMOJI]': '[FEATURE]',
        '[EMOJI]': '[STATS]',
        '⭐': '[STAR]',
        '[TARGET]': '[FOCUS]',
    }
    
    try:
        # Read file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Track if any changes were made
        original_content = content
        
        # Replace Unicode emojis with ASCII equivalents
        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)
        
        # Also handle any remaining high Unicode characters
        content = re.sub(r'[\U00010000-\U0010FFFF]', '[EMOJI]', content)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed Unicode issues in: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix Unicode issues in all Python files"""
    print("DuckBot Unicode Encoding Fix")
    print("=" * 50)
    
    base_path = Path(__file__).parent
    fixed_count = 0
    
    # Find all Python files that might have Unicode issues
    python_files = [
        base_path / "duckbot" / "dynamic_model_manager.py",
        base_path / "duckbot" / "ai_router_gpt.py", 
        base_path / "duckbot" / "webui.py",
        base_path / "model_status.py",
        base_path / "start_ai_ecosystem.py",
        base_path / "direct_launch.py",
        base_path / "test_every_feature.py",
    ]
    
    # Also scan all files in duckbot directory
    duckbot_dir = base_path / "duckbot"
    if duckbot_dir.exists():
        for py_file in duckbot_dir.glob("*.py"):
            if py_file not in python_files:
                python_files.append(py_file)
    
    # Process each file
    for file_path in python_files:
        if file_path.exists():
            if fix_unicode_in_file(file_path):
                fixed_count += 1
    
    print(f"\nFixed Unicode issues in {fixed_count} files")
    
    # Create a sitecustomize.py to force UTF-8 encoding
    sitecustomize_content = '''# DuckBot Unicode Encoding Fix
import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    # Set environment variables for Python processes
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    
    # Try to reconfigure stdout/stderr for current process
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
'''
    
    sitecustomize_path = base_path / "sitecustomize.py"
    with open(sitecustomize_path, 'w', encoding='utf-8') as f:
        f.write(sitecustomize_content)
    
    print(f"Created sitecustomize.py for automatic encoding fix")
    
    print("\n" + "=" * 50)
    print("Unicode fix completed!")
    print("The system should now start without encoding errors.")
    print("=" * 50)

if __name__ == "__main__":
    main()