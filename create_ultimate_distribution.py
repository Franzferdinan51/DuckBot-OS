#!/usr/bin/env python3
"""
DuckBot v3.1.0+ Ultimate Distribution Creator
Creates a complete, distributable package with all integrations and enhancements
Ready for GitHub upload or direct distribution
"""

import os
import shutil
import zipfile
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateDistributionCreator:
    """Create ultimate DuckBot distribution package"""
    
    def __init__(self, source_dir: str = None, output_dir: str = None):
        self.source_dir = Path(source_dir) if source_dir else Path.cwd()
        self.output_dir = Path(output_dir) if output_dir else self.source_dir.parent
        self.package_name = f"DuckBot-v3.1.0-Ultimate-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.temp_dir = self.output_dir / f"temp_{self.package_name}"
        
        # Essential files that MUST be included
        self.essential_files = {
            # Core startup scripts
            'START_ULTIMATE_DUCKBOT.bat',
            'start_ultimate_duckbot.sh',
            'START_LOCAL_ONLY.bat',
            'SETUP_AND_START.bat',
            'EMERGENCY_KILL.bat',
            
            # Core Python files
            'start_ecosystem.py',
            'start_local_ecosystem.py',
            'ai_ecosystem_manager.py',
            'model_status.py',
            'chat_with_ai.py',
            'organize_duckbot.py',
            
            # Configuration files
            '.env',
            '.env.local', 
            'ecosystem_config.yaml',
            'ai_config.json',
            'requirements.txt',
            
            # Documentation
            'README.md',
            'CLAUDE.md',
            'DUCKBOT_OS_README.md',
            
            # Enhanced components
            'create_ultimate_distribution.py'
        }
        
        # Essential folders that must be included
        self.essential_folders = {
            'duckbot',
            'logs',
            'workflows',
            'scripts'
        }
        
        # Files and folders to exclude
        self.exclude_patterns = {
            '__pycache__',
            '.python_cache',
            '.pytest_cache',
            'node_modules',
            '.git',
            '.gitignore',
            '.vscode',
            '.idea',
            '*.pyc',
            '*.pyo',
            '*.log',
            'logs/*.log',
            'ai_cache',
            '*.db',
            '.webui_secret_key',
            'backup_*',
            'temp_*',
            '*.tmp',
            '*~',
            '.DS_Store',
            'Thumbs.db'
        }
        
        # Platform-specific file mappings
        self.platform_files = {
            'windows': [
                'START_ULTIMATE_DUCKBOT.bat',
                'START_LOCAL_ONLY.bat', 
                'EMERGENCY_KILL.bat',
                'QUICK_KILL.bat',
                'CHECK_MODEL_STATUS.bat'
            ],
            'linux': [
                'start_ultimate_duckbot.sh'
            ]
        }
    
    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded"""
        path_str = str(path)
        
        for pattern in self.exclude_patterns:
            if pattern.endswith('*'):
                if path_str.startswith(pattern[:-1]):
                    return True
            elif pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif '*' in pattern:
                # Simple wildcard matching
                parts = pattern.split('*')
                if all(part in path_str for part in parts):
                    return True
            else:
                if pattern in path_str:
                    return True
        
        return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return "unknown"
    
    def create_file_manifest(self, package_dir: Path) -> Dict:
        """Create a manifest of all files in the package"""
        manifest = {
            "package_name": self.package_name,
            "version": "3.1.0+",
            "created": datetime.now().isoformat(),
            "total_files": 0,
            "total_size": 0,
            "files": {},
            "checksums": {}
        }
        
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(package_dir)
                file_size = file_path.stat().st_size
                file_hash = self.calculate_file_hash(file_path)
                
                manifest["files"][str(rel_path)] = {
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                manifest["checksums"][str(rel_path)] = file_hash
                manifest["total_files"] += 1
                manifest["total_size"] += file_size
        
        return manifest
    
    def copy_essential_files(self, package_dir: Path):
        """Copy essential files to the package directory"""
        logger.info("Copying essential files...")
        
        copied_count = 0
        missing_files = []
        
        for file_name in self.essential_files:
            source_path = self.source_dir / file_name
            if source_path.exists():
                dest_path = package_dir / file_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                copied_count += 1
                logger.debug(f"Copied: {file_name}")
            else:
                missing_files.append(file_name)
                logger.warning(f"Missing essential file: {file_name}")
        
        logger.info(f"Copied {copied_count} essential files")
        
        if missing_files:
            logger.warning(f"Missing files: {missing_files}")
            # Create placeholder files for critical missing files
            for missing_file in ['README.md', 'requirements.txt']:
                if missing_file in missing_files:
                    self.create_placeholder_file(package_dir / missing_file, missing_file)
    
    def copy_essential_folders(self, package_dir: Path):
        """Copy essential folders to the package directory"""
        logger.info("Copying essential folders...")
        
        copied_count = 0
        
        for folder_name in self.essential_folders:
            source_path = self.source_dir / folder_name
            if source_path.exists() and source_path.is_dir():
                dest_path = package_dir / folder_name
                
                # Copy folder contents, excluding unwanted files
                self.copy_folder_selective(source_path, dest_path)
                copied_count += 1
                logger.debug(f"Copied folder: {folder_name}")
            else:
                logger.warning(f"Missing essential folder: {folder_name}")
                # Create empty folder with README
                dest_path = package_dir / folder_name
                dest_path.mkdir(parents=True, exist_ok=True)
                self.create_folder_readme(dest_path, folder_name)
        
        logger.info(f"Copied {copied_count} essential folders")
    
    def copy_folder_selective(self, source_dir: Path, dest_dir: Path):
        """Copy folder contents while respecting exclusion patterns"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.iterdir():
            if self.should_exclude(item):
                continue
            
            dest_item = dest_dir / item.name
            
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                self.copy_folder_selective(item, dest_item)
    
    def create_placeholder_file(self, file_path: Path, file_type: str):
        """Create placeholder for missing essential files"""
        placeholders = {
            'README.md': f"""# DuckBot v3.1.0+ Ultimate Edition

This is a placeholder README. The original file was missing during packaging.

## Quick Start

Run the appropriate startup script:
- Windows: `START_ULTIMATE_DUCKBOT.bat`
- Linux/WSL: `./start_ultimate_duckbot.sh`

Generated: {datetime.now().isoformat()}
""",
            'requirements.txt': """# DuckBot v3.1.0+ Requirements (Placeholder)
# Install actual requirements with: pip install -r requirements.txt

fastapi>=0.104.0
uvicorn[standard]>=0.24.0
discord.py>=2.3.0
psutil>=5.9.0
httpx>=0.25.0
"""
        }
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(placeholders.get(file_type, f"# Placeholder for {file_type}\n"))
        logger.info(f"Created placeholder: {file_path.name}")
    
    def create_folder_readme(self, folder_path: Path, folder_name: str):
        """Create README for missing folders"""
        readme_content = f"""# {folder_name.title()} Folder

This folder was missing during packaging and has been created as a placeholder.

Folder purpose:
- `duckbot/` - Main Python module with all integrations
- `logs/` - Application logs and monitoring data
- `workflows/` - n8n workflow definitions
- `scripts/` - Utility and helper scripts

Generated: {datetime.now().isoformat()}
"""
        
        readme_path = folder_path / "README.md"
        readme_path.write_text(readme_content)
    
    def create_installation_guide(self, package_dir: Path):
        """Create comprehensive installation guide"""
        install_guide = f"""# DuckBot v3.1.0+ Ultimate Edition - Installation Guide

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), or WSL2
- **Python**: 3.8 or higher with pip
- **RAM**: 4GB (8GB+ recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for cloud features (optional)

### Recommended Setup
- **GPU**: NVIDIA GPU with CUDA support (for acceleration)
- **RAM**: 16GB+ for optimal performance  
- **WSL**: Windows Subsystem for Linux (for cross-platform features)
- **Docker**: For containerized services (optional)

## Quick Installation

### Windows Users
1. Extract the DuckBot package to your desired location
2. Double-click `START_ULTIMATE_DUCKBOT.bat`
3. Follow the interactive setup prompts
4. Access the WebUI at http://127.0.0.1:8787

### Linux/WSL Users  
1. Extract the package: `unzip DuckBot-v3.1.0-Ultimate-*.zip`
2. Navigate to the folder: `cd DuckBot-*/`
3. Make script executable: `chmod +x start_ultimate_duckbot.sh`
4. Run the launcher: `./start_ultimate_duckbot.sh`

## Manual Installation Steps

### 1. Python Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# For GPU acceleration (NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For image/video processing
pip install opencv-python Pillow imageio
```

### 2. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (optional for local-only mode)
nano .env
```

### 3. System Integration
```bash
# Windows: Enable WSL (run as Administrator)
wsl --install

# Linux: Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv
```

## Configuration Options

### AI Provider Setup
- **Local Only**: No API keys needed - uses LM Studio
- **Cloud + Local**: Add OpenRouter API key to .env
- **Discord Bot**: Add Discord token for bot features

### Feature Toggles
Edit `.env` file to enable/disable features:
```bash
# Core settings
AI_LOCAL_ONLY_MODE=true          # Privacy mode
ENABLE_ENHANCED_WEBUI=true       # Modern WebUI
ENABLE_WSL_INTEGRATION=true      # Linux integration
ENABLE_DESKTOP_AUTOMATION=true   # ByteBot features

# Optional services  
ENABLE_VIDEO_FEATURES=false      # Video generation
ENABLE_VOICE_FEATURES=true       # Voice synthesis
ENABLE_NOTEBOOK_FEATURES=true    # Jupyter integration
```

## Launch Modes

### Ultimate Enhanced Mode (Recommended)
- All features enabled
- Best performance and capabilities
- Requires more system resources

### Local-First Privacy Mode  
- Complete offline operation
- Zero external API calls
- Lower system requirements
- Full feature parity with cloud mode

### Hybrid Cloud+Local Mode
- Best of both worlds
- Local models preferred for privacy
- Cloud fallback for advanced features
- Optimal cost efficiency

## Troubleshooting

### Common Issues

**Python not found**
- Install Python 3.8+ from https://python.org
- Ensure Python is added to system PATH

**Permission errors (Windows)**
- Run command prompt as Administrator
- Check antivirus software settings

**WSL not available**
- Enable WSL feature in Windows Features
- Install Ubuntu from Microsoft Store
- Restart system after installation

**Dependencies failed to install**
- Upgrade pip: `python -m pip install --upgrade pip`
- Use virtual environment: `python -m venv duckbot_env`
- Install with --user flag: `pip install --user -r requirements.txt`

**GPU not detected**
- Install NVIDIA drivers
- Install CUDA toolkit
- Verify with: `nvidia-smi`

### Getting Help

1. Check the logs in `logs/` folder
2. Run diagnostics: Choose option 'S' in launcher  
3. Review documentation in `docs/` folder
4. Check GitHub issues for known problems

## Advanced Configuration

### Custom AI Models
1. Install LM Studio from https://lmstudio.ai
2. Download compatible models (Qwen, Gemma, etc.)  
3. Start local server on port 1234
4. DuckBot will automatically detect and use local models

### Docker Deployment
```bash
# Build container (if Dockerfile provided)
docker build -t duckbot:ultimate .

# Run with GPU support
docker run --gpus all -p 8787:8787 duckbot:ultimate
```

### Development Setup
```bash
# Clone for development
git clone <repository-url>
cd duckbot

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **Network**: WebUI binds to localhost by default
- **Logs**: Check logs don't contain sensitive information
- **Updates**: Keep dependencies updated for security patches

## Performance Optimization

### For Limited Resources
- Use Local-First Privacy Mode
- Disable video features
- Reduce AI model sizes
- Close unnecessary services

### For High Performance  
- Enable GPU acceleration
- Use SSD storage
- Increase system RAM
- Use wired network connection

---

**Support**: For additional help, consult the documentation or community resources.
**Version**: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        install_path = package_dir / "INSTALLATION_GUIDE.md"
        install_path.write_text(install_guide)
        logger.info("Created comprehensive installation guide")
    
    def create_package_info(self, package_dir: Path) -> Dict:
        """Create package information file"""
        package_info = {
            "name": "DuckBot Ultimate Edition",
            "version": "3.1.0+", 
            "build": datetime.now().strftime('%Y%m%d_%H%M%S'),
            "description": "Enhanced AI ecosystem with ByteBot, Archon, and Charm integrations",
            "features": [
                "Multi-agent AI orchestration (Archon-inspired)",
                "Desktop automation (ByteBot integration)",
                "Beautiful terminal interfaces (Charm-inspired)",
                "Windows/Linux/WSL cross-platform support",
                "Real-time WebUI with monitoring",
                "Privacy-first local-only mode",
                "Hybrid cloud+local AI routing",
                "Advanced system monitoring"
            ],
            "integrations": {
                "ByteBot": "Desktop automation and control",
                "Archon": "Multi-agent orchestration system", 
                "Charm Crush": "Terminal UI components",
                "ChromiumOS": "System-level features",
                "OpenWebUI": "Web interface integration"
            },
            "platforms": ["Windows", "Linux", "WSL"],
            "requirements": {
                "python": ">=3.8",
                "memory": "4GB+ (8GB+ recommended)",
                "storage": "2GB+ free space",
                "gpu": "Optional but recommended"
            },
            "startup_scripts": {
                "windows": "START_ULTIMATE_DUCKBOT.bat",
                "linux": "start_ultimate_duckbot.sh"
            },
            "webui_url": "http://127.0.0.1:8787",
            "created": datetime.now().isoformat(),
            "packager": "DuckBot Ultimate Distribution Creator"
        }
        
        info_path = package_dir / "PACKAGE_INFO.json"
        with open(info_path, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        logger.info("Created package information file")
        return package_info
    
    def create_zip_package(self, package_dir: Path) -> Path:
        """Create ZIP archive of the package"""
        zip_path = self.output_dir / f"{self.package_name}.zip"
        
        logger.info(f"Creating ZIP package: {zip_path.name}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        # Get zip file size
        zip_size = zip_path.stat().st_size
        zip_size_mb = zip_size / (1024 * 1024)
        
        logger.info(f"ZIP package created: {zip_size_mb:.1f}MB")
        return zip_path
    
    def create_github_ready_package(self, package_dir: Path):
        """Create GitHub-ready package structure"""
        logger.info("Preparing GitHub-ready package...")
        
        # Create .gitignore
        gitignore_content = """# DuckBot .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# DuckBot specific
logs/*.log
ai_cache/
*.db
.webui_secret_key
cost_tracking.db
duckbot_context.db
duckbot_learning.db
ecosystem_state.db

# Temporary files
temp_*/
backup_*/
*.tmp
"""
        
        gitignore_path = package_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content)
        
        # Create LICENSE file
        license_content = """MIT License

Copyright (c) 2024 DuckBot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        
        license_path = package_dir / "LICENSE"
        license_path.write_text(license_content)
        
        logger.info("GitHub-ready files created")
    
    def create_distribution_package(self) -> Dict:
        """Create the complete distribution package"""
        logger.info("Starting ultimate distribution creation...")
        
        try:
            # Create temporary directory
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            package_dir = self.temp_dir / "DuckBot-v3.1.0-Ultimate"
            package_dir.mkdir(exist_ok=True)
            
            # Copy essential files and folders
            self.copy_essential_files(package_dir)
            self.copy_essential_folders(package_dir)
            
            # Create documentation and guides
            self.create_installation_guide(package_dir)
            package_info = self.create_package_info(package_dir)
            
            # Create GitHub-ready package
            self.create_github_ready_package(package_dir)
            
            # Create file manifest
            manifest = self.create_file_manifest(package_dir)
            manifest_path = package_dir / "FILE_MANIFEST.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create ZIP package
            zip_path = self.create_zip_package(package_dir)
            
            # Create distribution report
            distribution_report = {
                "success": True,
                "package_name": self.package_name,
                "version": "3.1.0+",
                "created": datetime.now().isoformat(),
                "zip_file": str(zip_path),
                "zip_size_mb": zip_path.stat().st_size / (1024 * 1024),
                "total_files": manifest["total_files"],
                "total_size_mb": manifest["total_size"] / (1024 * 1024),
                "package_info": package_info,
                "ready_for": [
                    "Direct distribution",
                    "GitHub upload",
                    "User deployment"
                ]
            }
            
            # Save distribution report
            report_path = self.output_dir / f"{self.package_name}_DISTRIBUTION_REPORT.json"
            with open(report_path, 'w') as f:
                json.dump(distribution_report, f, indent=2)
            
            # Clean up temporary directory
            shutil.rmtree(self.temp_dir)
            
            logger.info("Ultimate distribution package created successfully!")
            logger.info(f"Package: {zip_path}")
            logger.info(f"Size: {distribution_report['zip_size_mb']:.1f}MB")
            logger.info(f"Files: {distribution_report['total_files']}")
            logger.info(f"Report: {report_path}")
            
            return distribution_report
            
        except Exception as e:
            logger.error(f"Distribution creation failed: {e}")
            # Clean up on failure
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create DuckBot Ultimate Distribution Package')
    parser.add_argument('--source', help='Source directory (default: current directory)')
    parser.add_argument('--output', help='Output directory (default: parent of source)')
    parser.add_argument('--organize-first', action='store_true', help='Run organization before packaging')
    parser.add_argument('--info-only', action='store_true', help='Show package info without creating')
    
    args = parser.parse_args()
    
    # Run organization first if requested
    if args.organize_first:
        print("Running folder organization first...")
        from organize_duckbot import DuckBotOrganizer
        organizer = DuckBotOrganizer(args.source)
        organizer.run_organization()
        print("Organization completed!")
    
    # Create distribution
    creator = UltimateDistributionCreator(args.source, args.output)
    
    if args.info_only:
        print(f"Package Name: {creator.package_name}")
        print(f"Source: {creator.source_dir}")
        print(f"Output: {creator.output_dir}")
        print(f"Essential Files: {len(creator.essential_files)}")
        print(f"Essential Folders: {len(creator.essential_folders)}")
        return
    
    try:
        report = creator.create_distribution_package()
        
        print("\nDistribution Package Created Successfully!")
        print(f"Package: {report['zip_file']}")
        print(f"Size: {report['zip_size_mb']:.1f}MB")
        print(f"Files: {report['total_files']}")
        print(f"Version: {report['version']}")
        print("\nReady for distribution and GitHub upload!")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()