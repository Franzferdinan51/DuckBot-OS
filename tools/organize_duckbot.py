#!/usr/bin/env python3
"""
DuckBot v3.1.0+ Folder Organization Script
Clean up and optimize the folder structure for distribution
Organize files by category and remove unnecessary clutter
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DuckBotOrganizer:
    """Organize DuckBot files and folders for optimal distribution"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.backup_dir = self.root_dir / "backup_before_organization"
        
        # File categories for organization
        self.file_categories = {
            'core_scripts': [
                'start_ecosystem.py',
                'start_local_ecosystem.py', 
                'ai_ecosystem_manager.py',
                'start_ai_ecosystem.py',
                'model_status.py',
                'chat_with_ai.py'
            ],
            'startup_scripts': [
                'START_ULTIMATE_DUCKBOT.bat',
                'start_ultimate_duckbot.sh',
                'START_LOCAL_ONLY.bat',
                'START_ENHANCED_ECOSYSTEM.bat',
                'SETUP_AND_START.bat'
            ],
            'utility_scripts': [
                'EMERGENCY_KILL.bat',
                'QUICK_KILL.bat', 
                'CHECK_MODEL_STATUS.bat',
                'TEST_LOCAL_PARITY.bat'
            ],
            'test_scripts': [
                'test_every_feature.py',
                'test_enhanced_duckbot.py',
                'test_local_feature_parity.py',
                'test_dynamic_model.py',
                'test_all_features.py'
            ],
            'config_files': [
                '.env',
                '.env.local',
                'ecosystem_config.yaml',
                'ai_config.json',
                'provider_config.json',
                'hardware_config.json',
                'vibevoice_config.yaml'
            ],
            'documentation': [
                'README.md',
                'CLAUDE.md',
                'DUCKBOT_OS_README.md',
                'QUICKSTART.md',
                'QWEN.md',
                'GEMINI.md',
                'AI-Information.md',
                'DEPLOYMENT_READY.md',
                'VIBEVOICE_INTEGRATION_COMPLETE.md',
                'INTEGRATION_COMPLETE_SUMMARY.md',
                'FINAL_IMPROVEMENTS_SUMMARY.md',
                'FIXES_CHANGELOG.md'
            ],
            'openwebui_integration': [
                'openwebui_duckbot_adapter.py',
                'openwebui_duckbot_complete.py',
                'openwebui_integration_config.py',
                'OPENWEBUI_INTEGRATION_GUIDE.md',
                'START_OPENWEBUI_DUCKBOT_ADAPTER.bat'
            ],
            'package_creators': [
                'create_deployment_package.py',
                'create_duckbot_complete_package.py',
                'create_duckbot_os_deployment.py',
                'CREATE_DEPLOYMENT_PACKAGE.bat',
                'organize_duckbot.py'
            ],
            'legacy_files': [
                'DuckBot-v2.3.0-Trading-Video-Enhanced.py',
                'bytebot_enhanced_adapter.py',
                'test_batch_option1.bat',
                'fix_accelerate_emergency.bat',
                'launch_ultra_lowvram.bat'
            ]
        }
        
        # Folders to organize
        self.folder_structure = {
            'core': 'Core system files and main scripts',
            'startup': 'Startup and launcher scripts',  
            'utilities': 'Utility and management scripts',
            'tests': 'Test and validation scripts',
            'config': 'Configuration files',
            'docs': 'Documentation and guides',
            'integrations': 'Third-party integrations',
            'tools': 'Development and packaging tools',
            'legacy': 'Legacy and backup files'
        }
        
        # Files and folders to exclude from distribution
        self.exclude_from_distribution = {
            '__pycache__',
            '.python_cache',
            '.pytest_cache', 
            'node_modules',
            '.git',
            '.vscode',
            '.idea',
            '*.pyc',
            '*.pyo',
            '*.log',
            'logs',
            'ai_cache',
            'cost_tracking.db',
            'duckbot_context.db',
            'duckbot_learning.db',
            'ecosystem_state.db',
            '.webui_secret_key'
        }
    
    def create_backup(self):
        """Create a backup before reorganization"""
        logger.info("Creating backup before reorganization...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup important files
        important_files = [
            '.env', '.env.local', 
            'ecosystem_config.yaml',
            'ai_config.json',
            'requirements.txt'
        ]
        
        for file in important_files:
            file_path = self.root_dir / file
            if file_path.exists():
                shutil.copy2(file_path, self.backup_dir)
                logger.info(f"Backed up: {file}")
    
    def create_folder_structure(self):
        """Create organized folder structure"""
        logger.info("Creating organized folder structure...")
        
        for folder, description in self.folder_structure.items():
            folder_path = self.root_dir / folder
            folder_path.mkdir(exist_ok=True)
            
            # Create a README for each folder
            readme_path = folder_path / "README.md"
            if not readme_path.exists():
                with open(readme_path, 'w') as f:
                    f.write(f"# {folder.title()} Folder\n\n{description}\n")
            
            logger.info(f"Created folder: {folder}/")
    
    def organize_files(self):
        """Organize files into appropriate folders"""
        logger.info("Organizing files by category...")
        
        # Map categories to folders
        category_to_folder = {
            'core_scripts': 'core',
            'startup_scripts': 'startup',
            'utility_scripts': 'utilities', 
            'test_scripts': 'tests',
            'config_files': 'config',
            'documentation': 'docs',
            'openwebui_integration': 'integrations/openwebui',
            'package_creators': 'tools',
            'legacy_files': 'legacy'
        }
        
        # Create integration subfolders
        (self.root_dir / "integrations" / "openwebui").mkdir(parents=True, exist_ok=True)
        
        moved_files = []
        
        for category, files in self.file_categories.items():
            target_folder = category_to_folder.get(category, 'misc')
            target_path = self.root_dir / target_folder
            
            for file in files:
                source_path = self.root_dir / file
                if source_path.exists() and source_path.is_file():
                    dest_path = target_path / file
                    
                    # Don't move if already in correct location
                    if source_path.parent == target_path:
                        continue
                    
                    try:
                        shutil.move(str(source_path), str(dest_path))
                        moved_files.append(f"{file} -> {target_folder}/")
                        logger.info(f"Moved: {file} -> {target_folder}/")
                    except Exception as e:
                        logger.error(f"Failed to move {file}: {e}")
        
        return moved_files
    
    def organize_duckbot_module(self):
        """Ensure duckbot module is properly organized"""
        duckbot_dir = self.root_dir / "duckbot"
        
        if not duckbot_dir.exists():
            logger.warning("duckbot module directory not found!")
            return
        
        logger.info("Organizing duckbot module...")
        
        # Create submodules for better organization
        submodules = {
            'ui': ['webui.py', 'enhanced_webui.py', 'charm_terminal_ui.py', 'web_dashboard.py'],
            'integrations': ['wsl_integration.py', 'bytebot_integration.py', 'archon_integration.py', 'chromium_integration.py'],
            'ai': ['ai_router_gpt.py', 'dynamic_model_manager.py', 'local_feature_parity.py'],
            'core': ['server_manager.py', 'service_detector.py', 'settings_gpt.py']
        }
        
        for submodule, files in submodules.items():
            submodule_dir = duckbot_dir / submodule
            submodule_dir.mkdir(exist_ok=True)
            
            # Create __init__.py if it doesn't exist
            init_file = submodule_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# DuckBot submodule\n")
            
            logger.info(f"Organized submodule: duckbot/{submodule}")
    
    def clean_up_files(self):
        """Clean up unnecessary files"""
        logger.info("Cleaning up unnecessary files...")
        
        cleaned_files = []
        
        # Remove temporary and cache files
        for pattern in ['*.pyc', '*.pyo', '*.tmp', '*~']:
            for file in self.root_dir.rglob(pattern):
                try:
                    file.unlink()
                    cleaned_files.append(str(file.name))
                    logger.debug(f"Removed: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to remove {file}: {e}")
        
        # Remove empty directories
        for folder in self.root_dir.iterdir():
            if folder.is_dir() and not any(folder.iterdir()):
                try:
                    folder.rmdir()
                    cleaned_files.append(f"Empty folder: {folder.name}/")
                    logger.info(f"Removed empty folder: {folder.name}/")
                except Exception as e:
                    logger.debug(f"Could not remove {folder}: {e}")
        
        return cleaned_files
    
    def update_requirements(self):
        """Update and organize requirements.txt"""
        logger.info("Updating requirements.txt...")
        
        requirements_file = self.root_dir / "requirements.txt"
        
        # Enhanced requirements with all new integrations
        enhanced_requirements = [
            "# DuckBot v3.1.0+ Enhanced Requirements",
            "# Core Dependencies",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "discord.py>=2.3.0",
            "asyncio-mqtt>=0.13.0",
            "psutil>=5.9.0",
            "httpx>=0.25.0",
            "aiohttp>=3.8.0",
            "",
            "# AI and ML", 
            "openai>=1.3.0",
            "anthropic>=0.5.0",
            "transformers>=4.35.0",
            "torch>=2.0.0",
            "numpy>=1.24.0",
            "",
            "# Web and UI",
            "jinja2>=3.1.0",
            "websockets>=11.0.0",
            "rich>=13.5.0",
            "typer>=0.9.0",
            "",
            "# Database and Storage", 
            "sqlite3",  # Built-in
            "sqlalchemy>=2.0.0",
            "aiosqlite>=0.19.0",
            "",
            "# Image and Video Processing",
            "Pillow>=10.0.0",
            "opencv-python>=4.8.0",
            "imageio>=2.31.0",
            "",
            "# System Integration",
            "pywin32>=306; platform_system=='Windows'",
            "python-dotenv>=1.0.0",
            "pyyaml>=6.0.0",
            "toml>=0.10.0",
            "",
            "# Optional: Enhanced Features",
            "# jupyter>=1.0.0",
            "# notebook>=7.0.0", 
            "# streamlit>=1.28.0",
            "",
            "# Development and Testing",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0"
        ]
        
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(enhanced_requirements))
        
        logger.info("Requirements.txt updated with enhanced dependencies")
    
    def create_distribution_info(self):
        """Create distribution information and metadata"""
        logger.info("Creating distribution metadata...")
        
        # Create distribution info
        dist_info = {
            "name": "DuckBot",
            "version": "3.1.0+",
            "description": "Enhanced AI ecosystem with ByteBot, Archon, and Charm integrations",
            "author": "DuckBot Team",
            "license": "MIT",
            "requires_python": ">=3.8",
            "platforms": ["Windows", "Linux", "WSL"],
            "features": [
                "Multi-agent AI orchestration",
                "Desktop automation (ByteBot)",
                "Beautiful terminal interfaces (Charm)",
                "WSL integration", 
                "Real-time WebUI",
                "Local-first privacy mode",
                "Hybrid cloud+local AI routing"
            ],
            "integrations": [
                "ByteBot - Desktop automation",
                "Archon - Multi-agent systems", 
                "Charm Crush - Terminal UI",
                "ChromiumOS - System features",
                "OpenWebUI - Web interface"
            ],
            "created": datetime.now().isoformat(),
            "organized": True
        }
        
        # Save distribution info
        with open(self.root_dir / "distribution_info.json", 'w') as f:
            json.dump(dist_info, f, indent=2)
        
        # Create enhanced README for distribution
        readme_content = f"""# DuckBot v3.1.0+ Ultimate Edition

**Enhanced AI ecosystem with advanced integrations**

## Features

- 🚀 **Ultimate Enhanced Mode** - All features enabled
- 🏠 **Local-First Privacy** - Complete offline experience  
- 🌐 **Hybrid Cloud+Local** - Best of both worlds
- 🤖 **Multi-Agent Orchestration** - Archon-inspired coordination
- 🖥️ **Desktop Automation** - ByteBot integration
- 💻 **Beautiful Terminal UI** - Charm-inspired interfaces
- 🐧 **WSL Integration** - Native Linux subsystem support
- 🎨 **Enhanced WebUI** - Modern real-time dashboard

## Quick Start

### Windows
```bash
START_ULTIMATE_DUCKBOT.bat
```

### Linux/WSL
```bash
./start_ultimate_duckbot.sh
```

## File Organization

- `core/` - Core system files and main scripts
- `startup/` - Startup and launcher scripts  
- `utilities/` - Utility and management scripts
- `tests/` - Test and validation scripts
- `config/` - Configuration files
- `docs/` - Documentation and guides
- `integrations/` - Third-party integrations
- `tools/` - Development and packaging tools
- `duckbot/` - Main Python module

## Requirements

- Python 3.8+ with pip
- Windows 10/11 or Linux (WSL supported)
- 4GB+ RAM (8GB+ recommended)
- GPU acceleration (optional but recommended)

## Installation

1. Clone or extract the DuckBot package
2. Run the appropriate startup script
3. Follow the interactive setup
4. Access WebUI at http://127.0.0.1:8787

## Documentation

See the `docs/` folder for detailed documentation:
- `CLAUDE.md` - Development guide
- `DUCKBOT_OS_README.md` - OS integration
- `INTEGRATION_COMPLETE_SUMMARY.md` - Feature overview

## License

MIT License - see LICENSE file for details

---

*DuckBot v3.1.0+ - Enhanced with ByteBot, Archon, ChromiumOS, and Charm integrations*
"""
        
        with open(self.root_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        logger.info("Distribution metadata created")
    
    def generate_organization_report(self, moved_files: List[str], cleaned_files: List[str]):
        """Generate organization report"""
        report_content = f"""# DuckBot v3.1.0+ Organization Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total files moved**: {len(moved_files)}
- **Files cleaned up**: {len(cleaned_files)}
- **Folder structure**: Organized into {len(self.folder_structure)} categories

## Moved Files

```
{chr(10).join(moved_files) if moved_files else 'No files moved'}
```

## Cleaned Files

```
{chr(10).join(cleaned_files) if cleaned_files else 'No files cleaned'}
```

## Folder Structure

{chr(10).join([f'- `{folder}/` - {desc}' for folder, desc in self.folder_structure.items()])}

## Next Steps

1. Test the organized structure
2. Create deployment package
3. Distribute to users

---

Organization completed successfully!
"""
        
        with open(self.root_dir / "ORGANIZATION_REPORT.md", 'w') as f:
            f.write(report_content)
        
        logger.info("Organization report generated")
    
    def run_organization(self):
        """Run the complete organization process"""
        logger.info("Starting DuckBot folder organization...")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Create folder structure
            self.create_folder_structure()
            
            # Step 3: Organize files
            moved_files = self.organize_files()
            
            # Step 4: Organize duckbot module
            self.organize_duckbot_module()
            
            # Step 5: Clean up
            cleaned_files = self.clean_up_files()
            
            # Step 6: Update requirements
            self.update_requirements()
            
            # Step 7: Create distribution info
            self.create_distribution_info()
            
            # Step 8: Generate report
            self.generate_organization_report(moved_files, cleaned_files)
            
            logger.info("✅ DuckBot organization completed successfully!")
            logger.info(f"📁 Organized into {len(self.folder_structure)} categories")
            logger.info(f"📦 Ready for distribution packaging")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Organization failed: {e}")
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize DuckBot folder structure')
    parser.add_argument('--root', help='Root directory (default: current directory)')
    parser.add_argument('--backup', action='store_true', help='Create backup only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    organizer = DuckBotOrganizer(args.root)
    
    if args.backup:
        organizer.create_backup()
        print("✅ Backup created successfully!")
        return
    
    if args.dry_run:
        print("🔍 Dry run mode - showing organization plan:")
        print(f"📁 Root directory: {organizer.root_dir}")
        print(f"📦 Will organize {sum(len(files) for files in organizer.file_categories.values())} files")
        print(f"🗂️ Into {len(organizer.folder_structure)} categories")
        return
    
    # Run organization
    success = organizer.run_organization()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()