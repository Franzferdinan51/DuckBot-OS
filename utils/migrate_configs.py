#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Configuration Migration Script
Migrates from legacy configuration files to the unified configuration system
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from config.unified_config import get_config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main migration function"""
    print("DuckBot Configuration Migration Tool")
    print("=" * 40)
    print()

    # Initialize config manager
    config_manager = get_config_manager()

    # Check for legacy config files
    legacy_files = [
        "ai_config.json",
        "enhanced_config.json",
        "provider_config.json",
        "hardware_config.json",
        "ecosystem_config.yaml",
        "livekit_config.yaml"
    ]

    found_legacy = []
    for filename in legacy_files:
        if Path(filename).exists():
            found_legacy.append(filename)

    if not found_legacy:
        print("✅ No legacy configuration files found")
        print("   Unified configuration system is already active")
        return

    print(f"Found {len(found_legacy)} legacy configuration files:")
    for filename in found_legacy:
        print(f"   - {filename}")
    print()

    # Confirm migration
    response = input("Proceed with migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Migration cancelled")
        return

    print()
    print("Migrating configurations...")

    try:
        # Load current config (creates default if needed)
        config = config_manager.load_config()

        # Migrate legacy files
        config_manager.migrate_legacy_configs()

        print()
        print("✅ Migration completed successfully!")
        print()
        print("What happened:")
        print("   - Legacy configuration files have been migrated")
        print("   - Old files have been moved to config/archived/")
        print("   - New unified configuration saved to config/unified_config.json")
        print()
        print("To use the new configuration system:")
        print("   from config.unified_config import get_config")
        print("   config = get_config()")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print()
        print("❌ Migration failed!")
        print(f"   Error: {e}")
        print("   Check the logs for details")

if __name__ == "__main__":
    main()