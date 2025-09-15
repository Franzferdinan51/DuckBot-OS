#!/usr/bin/env python3
"""
Cleanup script for legacy DuckBot test files

This script helps remove the scattered test files that have been
consolidated into the comprehensive test suite.

USE WITH CAUTION - This will permanently delete files!
"""

import os
import shutil
from pathlib import Path

def backup_legacy_tests():
    """Create a backup of legacy test files before deletion"""
    backup_dir = Path("legacy_tests_backup")
    backup_dir.mkdir(exist_ok=True)

    legacy_files = [
        # Python test files
        "test_ai_mode_detection.py",
        "test_duckbot_os.py",
        "test_duckbot_simple.py",
        "test_enhanced_webui.py",
        "test_hardware_detection.py",
        "test_integration.py",
        "test_service_detection.py",
        "test_simple.py",
        "test_vibevoice.py",
        "test_webui_detection.py",
        "test_consolidation.py",
        "test_mining_integration.py",
        "test_ui_tars_mcp_integration.py",

        # Batch test files
        "test_action_reasoning_system.bat",
        "test_enhanced_system.bat",
        "test_batch.bat",
        "TEST_FIXED_BATCH.bat",
        "TEST_PREFLIGHT.bat",

        # PowerShell test files
        "test_option1.ps1",

        # Test helper files (can be removed)
        "simple_module_test.py",
        "test_duckbot_modules.py",
    ]

    backed_up_files = []

    for file_path in legacy_files:
        source = Path(file_path)
        if source.exists():
            dest = backup_dir / source.name
            shutil.copy2(source, dest)
            backed_up_files.append(file_path)
            print(f"Backed up: {file_path}")

    return backed_up_files, backup_dir

def delete_legacy_tests(backup_dir):
    """Delete legacy test files after confirmation"""
    legacy_files = [
        "test_ai_mode_detection.py",
        "test_duckbot_os.py",
        "test_duckbot_simple.py",
        "test_enhanced_webui.py",
        "test_hardware_detection.py",
        "test_integration.py",
        "test_service_detection.py",
        "test_simple.py",
        "test_vibevoice.py",
        "test_webui_detection.py",
        "test_consolidation.py",
        "test_mining_integration.py",
        "test_ui_tars_mcp_integration.py",
        "test_action_reasoning_system.bat",
        "test_enhanced_system.bat",
        "test_batch.bat",
        "TEST_FIXED_BATCH.bat",
        "TEST_PREFLIGHT.bat",
        "test_option1.ps1",
        "simple_module_test.py",
        "test_duckbot_modules.py",
    ]

    deleted_files = []

    for file_path in legacy_files:
        source = Path(file_path)
        if source.exists():
            try:
                source.unlink()
                deleted_files.append(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

    # Remove tests directory if empty
    tests_dir = Path("tests")
    if tests_dir.exists() and tests_dir.is_dir():
        try:
            # Check if it contains only test files or README
            contents = list(tests_dir.iterdir())
            readme_only = all(f.name == "README.md" for f in contents)

            if readme_only or len(contents) == 0:
                shutil.rmtree(tests_dir)
                print(f"Removed empty tests directory")
        except Exception as e:
            print(f"Could not remove tests directory: {e}")

    return deleted_files

def main():
    """Main cleanup function"""
    print("DuckBot Legacy Test Files Cleanup")
    print("=" * 50)
    print()
    print("This script will:")
    print("1. Backup legacy test files to 'legacy_tests_backup/'")
    print("2. Delete the original legacy test files")
    print("3. Remove empty 'tests/' directory")
    print()
    print("⚠️  WARNING: This will permanently delete files!")
    print("Make sure you have tested the new comprehensive test suite first.")
    print()

    response = input("Do you want to continue? (yes/no): ").strip().lower()

    if response != "yes":
        print("Cleanup cancelled.")
        return

    print()
    print("Step 1: Creating backup...")
    backed_up_files, backup_dir = backup_legacy_tests()

    if not backed_up_files:
        print("No legacy test files found to backup.")
        return

    print(f"Backed up {len(backed_up_files)} files to: {backup_dir}")
    print()

    print("Step 2: Deleting legacy files...")
    deleted_files = delete_legacy_tests(backup_dir)

    print(f"Deleted {len(deleted_files)} legacy test files.")
    print()

    print("Step 3: Creating cleanup summary...")
    summary_file = Path("cleanup_summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("DuckBot Legacy Test Files Cleanup Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Date: {Path().cwd()}\n")
        f.write(f"Backup location: {backup_dir}\n")
        f.write(f"Files backed up: {len(backed_up_files)}\n")
        f.write(f"Files deleted: {len(deleted_files)}\n\n")
        f.write("Backed up files:\n")
        for file_path in backed_up_files:
            f.write(f"  - {file_path}\n")
        f.write("\nDeleted files:\n")
        for file_path in deleted_files:
            f.write(f"  - {file_path}\n")

    print(f"Cleanup summary saved to: {summary_file}")
    print()
    print("✅ Legacy test files cleanup completed!")
    print()
    print("Your DuckBot directory is now clean with:")
    print("- practical_test_suite.py (new comprehensive test suite)")
    print("- comprehensive_test_suite.py (advanced reference)")
    print("- COMPREHENSIVE_TEST_SUITE_README.md (documentation)")
    print()
    print("The consolidated test suite provides:")
    print("- Single command to run all tests")
    print("- Comprehensive coverage of all system aspects")
    print("- Detailed reporting and analysis")
    print("- Easy maintenance and extension")

if __name__ == "__main__":
    main()