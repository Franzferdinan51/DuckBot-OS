#!/usr/bin/env python3
"""
Emergency bypass for accelerate version issue in ComfyUI
This patches the transformers import to handle the None version error
"""

import sys
import os
from pathlib import Path

def patch_accelerate_version():
    """Patch the accelerate version detection to prevent None errors"""
    
    # Find the transformers import_utils.py file
    python_path = Path(sys.executable).parent
    import_utils_path = python_path / "Lib" / "site-packages" / "transformers" / "utils" / "import_utils.py"
    
    if not import_utils_path.exists():
        print("Could not find transformers import_utils.py")
        return False
        
    print(f"Patching: {import_utils_path}")
    
    # Read the file
    with open(import_utils_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already patched
    if "# DUCKBOT ACCELERATE PATCH" in content:
        print("Already patched!")
        return True
    
    # Create backup
    backup_path = import_utils_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # Apply patch - fix the None version issue
    original_line = "return _accelerate_available and version.parse(_accelerate_version) >= version.parse(min_version)"
    patched_line = """# DUCKBOT ACCELERATE PATCH - Fix None version issue
    try:
        return _accelerate_available and _accelerate_version and version.parse(_accelerate_version) >= version.parse(min_version)
    except (TypeError, ValueError) as e:
        print(f"Warning: Accelerate version issue bypassed: {e}")
        return _accelerate_available  # Return basic availability if version parsing fails"""
    
    if original_line in content:
        content = content.replace(original_line, patched_line)
        
        # Write patched file
        with open(import_utils_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Patch applied successfully!")
        return True
    else:
        print("Could not find target line to patch")
        return False

def main():
    print("=" * 50)
    print("Emergency Accelerate Version Bypass")
    print("=" * 50)
    print()
    
    if patch_accelerate_version():
        print()
        print("SUCCESS: Patch complete! ComfyUI should now start.")
        print("NEXT: Run launch_ultra_lowvram.bat to test")
    else:
        print()
        print("ERROR: Patch failed. Try fix_accelerate_emergency.bat instead")
    
    print()
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()