#!/usr/bin/env python3
"""
Backup script for DuckBot v4.2 with PyBoy integration
Handles Windows reserved device names and creates comprehensive backup
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup():
    """Create comprehensive backup of DuckBot system"""

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"DuckBot-v4.2-PyBoy-Backup-{timestamp}"
    backup_dir = Path(backup_name)
    backup_dir.mkdir(exist_ok=True)

    logger.info(f"Creating backup in: {backup_dir}")

    # Key directories to backup
    backup_dirs = [
        "duckbot",
        "core_ai",
        "launcher",
        "config",
        "docs",
        "tests",
        "diagnostics",
        "utils"
    ]

    # Key files to backup
    backup_files = [
        "requirements.txt",
        "README.md",
        "CLAUDE.md",
        "QWEN.md",
        "START_LOCAL_ONLY.bat",
        "start_ecosystem.py",
        "ai_ecosystem_manager.py",
        "chat_with_ai.py",
        "test_pyboy_integration.py",
        "demo_pyboy_features.py",
        "PYBOY_INTEGRATION_COMPLETE.md"
    ]

    # Copy directories
    for dir_name in backup_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists():
            dst_dir = backup_dir / dir_name
            logger.info(f"Copying directory: {dir_name}")

            try:
                shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'node_modules', '.env', '.env.local', 'nul'))
                logger.info(f"✅ Copied {dir_name}")
            except Exception as e:
                logger.error(f"❌ Failed to copy {dir_name}: {e}")
        else:
            logger.warning(f"Directory not found: {dir_name}")

    # Copy files
    for file_name in backup_files:
        src_file = Path(file_name)
        if src_file.exists():
            dst_file = backup_dir / file_name
            logger.info(f"Copying file: {file_name}")
            try:
                shutil.copy2(src_file, dst_file)
                logger.info(f"✅ Copied {file_name}")
            except Exception as e:
                logger.error(f"❌ Failed to copy {file_name}: {e}")
        else:
            logger.warning(f"File not found: {file_name}")

    # Create backup info file
    info_file = backup_dir / "BACKUP_INFO.txt"
    with open(info_file, 'w') as f:
        f.write(f"DuckBot v4.2 PyBoy Integration Backup\n")
        f.write(f"Created: {datetime.now().isoformat()}\n")
        f.write(f"Backup includes:\n")
        f.write(f"- Complete PyBoy Game Boy emulator integration\n")
        f.write(f"- Service manager integration\n")
        f.write(f"- WebUI interface with REST API\n")
        f.write(f"- AI agent framework for game automation\n")
        f.write(f"- Test suite and documentation\n")
        f.write(f"\nKey Features:\n")
        f.write(f"- Game Boy ROM loading and management\n")
        f.write(f"- AI-powered game automation\n")
        f.write(f"- Base64 frame streaming for web interface\n")
        f.write(f"- Save/load game state functionality\n")
        f.write(f"- Performance monitoring and statistics\n")

    # Create ZIP archive
    zip_file = Path(f"{backup_name}.zip")
    logger.info(f"Creating ZIP archive: {zip_file}")

    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in backup_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(backup_dir)
                zipf.write(file_path, arcname)

    logger.info(f"✅ Backup completed successfully!")
    logger.info(f"Backup directory: {backup_dir}")
    logger.info(f"ZIP archive: {zip_file}")

    return backup_dir, zip_file

if __name__ == "__main__":
    try:
        backup_dir, zip_file = create_backup()
        print(f"\n🎉 Backup created successfully!")
        print(f"📁 Directory: {backup_dir}")
        print(f"📦 Archive: {zip_file}")
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        print(f"❌ Backup failed: {e}")