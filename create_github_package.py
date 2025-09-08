#!/usr/bin/env python3
"""
GitHub Package Creator for DuckBot v3.1.0+
Creates a complete ZIP package ready for GitHub upload
Includes all files from organized and unorganized structure
"""

import os
import shutil
import zipfile
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Set, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubPackageCreator:
    """Create a complete GitHub-ready package"""
    
    def __init__(self, source_dir: str = None):
        self.source_dir = Path(source_dir) if source_dir else Path.cwd()
        self.package_name = f"DuckBot-v3.1.0-Ultimate-GitHub-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Files and folders to exclude
        self.exclude_patterns = {
            '__pycache__',
            '.python_cache', 
            '.pytest_cache',
            'node_modules',
            '.git',
            '.vscode',
            '.idea',
            '*.pyc',
            '*.pyo',
            'logs/*.log',
            '*.db',
            '.webui_secret_key',
            'backup_*',
            'temp_*',
            '*.tmp',
            '*~',
            '.DS_Store',
            'Thumbs.db',
            'ai_cache',
            'cost_tracking.db',
            'duckbot_context.db',
            'duckbot_learning.db',
            'ecosystem_state.db'
        }
        
        # Essential files that must be included
        self.essential_files = [
            'START_ENHANCED_DUCKBOT.bat',
            'START_ULTIMATE_DUCKBOT.bat', 
            'start_ultimate_duckbot.sh',
            'requirements.txt',
            'create_ultimate_distribution.py',
            'create_github_package.py',
            'INTEGRATION_ENHANCEMENT_SUMMARY.md'
        ]
    
    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded"""
        path_str = str(path).replace('\\', '/')
        name = path.name
        
        # Check if it's a temporary or cache directory
        for pattern in self.exclude_patterns:
            if pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif '*' in pattern:
                # Handle patterns like "logs/*.log"
                if '/' in pattern:
                    dir_part, file_part = pattern.split('/', 1)
                    if dir_part in path_str and file_part.replace('*', '') in name:
                        return True
                else:
                    if pattern.replace('*', '') in name:
                        return True
            else:
                if pattern in name or pattern in path_str:
                    return True
        
        return False
    
    def collect_all_files(self) -> List[Path]:
        """Collect all files that should be included"""
        all_files = []
        
        logger.info("Scanning directory structure...")
        
        for item in self.source_dir.rglob('*'):
            if item.is_file():
                if not self.should_exclude(item):
                    all_files.append(item)
                    logger.debug(f"Including: {item.relative_to(self.source_dir)}")
                else:
                    logger.debug(f"Excluding: {item.relative_to(self.source_dir)}")
        
        logger.info(f"Found {len(all_files)} files to include")
        return all_files
    
    def create_github_ready_structure(self, temp_dir: Path):
        """Create GitHub-ready package structure"""
        logger.info("Creating GitHub-ready structure...")
        
        # Copy all valid files
        all_files = self.collect_all_files()
        
        for file_path in all_files:
            rel_path = file_path.relative_to(self.source_dir)
            dest_path = temp_dir / rel_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            try:
                shutil.copy2(file_path, dest_path)
                logger.debug(f"Copied: {rel_path}")
            except Exception as e:
                logger.warning(f"Failed to copy {rel_path}: {e}")
        
        # Create essential GitHub files
        self.create_github_files(temp_dir)
        
        return len(all_files)
    
    def create_github_files(self, package_dir: Path):
        """Create essential GitHub files"""
        
        # Create comprehensive README.md
        readme_content = f"""# DuckBot v3.1.0+ Ultimate Edition

**The Complete AI Integration Suite - Enhanced with ByteBot, Archon, Charm, and ChromiumOS Features**

![DuckBot Logo](https://img.shields.io/badge/DuckBot-v3.1.0+-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20WSL-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 Features

### Ultimate Integration Suite
- **🤖 ByteBot Desktop Automation** - Complete computer control and task automation
- **🧠 Archon Multi-Agent System** - Advanced orchestration and knowledge management
- **💻 Charm Terminal Interface** - Beautiful, interactive command-line experience  
- **🌐 ChromiumOS System Features** - Advanced OS-level integration and security
- **🐧 WSL Integration** - Full Windows Subsystem for Linux support
- **🎨 Enhanced WebUI** - Modern real-time dashboard with WebSocket updates

### AI Capabilities
- **Multi-Model AI Routing** - Intelligent local/cloud hybrid processing
- **Real-Time Monitoring** - Live system metrics and performance tracking
- **Provider Abstraction** - Zero-code switching between AI providers
- **Intelligent Agents** - Adaptive decision-making and learning
- **Context Management** - Learning from experience and interactions
- **Visual Workflow Designer** - Figma-like canvas for AI workflows

## 🎯 Quick Start

### Windows Users
```batch
# Download and extract the package
# Run the enhanced launcher
START_ENHANCED_DUCKBOT.bat
```

### Linux/WSL Users
```bash
# Make scripts executable
chmod +x start_ultimate_duckbot.sh

# Run the cross-platform launcher  
./start_ultimate_duckbot.sh
```

### Ultimate Mode (Recommended)
Choose option **1. [ULTIMATE]** from the launcher menu for the complete experience with all integrations active.

## 🛠️ Installation

### System Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), or WSL2
- **Python**: 3.8 or higher with pip
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for cloud features (optional)

### Automatic Installation
The launcher will automatically install missing dependencies. For manual installation:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install enhanced integration dependencies  
pip install psutil fastapi uvicorn websockets pillow opencv-python numpy rich typer
```

## 🎮 Usage Modes

### 🏆 Ultimate Modes
- **[1] ULTIMATE** - Complete integration suite (Recommended)
- **[2] ENHANCED-WEBUI** - Modern web interface with real-time updates
- **[3] CHARM-TERMINAL** - Beautiful terminal interface
- **[4] DESKTOP-AUTO** - ByteBot desktop automation
- **[5] MULTI-AGENT** - Archon multi-agent orchestration
- **[6] WSL-MODE** - WSL integration interface

### 🔧 Classic Modes  
- **[7] CLASSIC-ENHANCED** - Original DuckBot with new integrations
- **[8] LOCAL-PRIVACY** - Complete offline operation
- **[9] HYBRID-CLOUD** - Intelligent local/cloud routing

### ⚙️ Management Tools
- **[T] TEST-ALL** - Comprehensive integration testing
- **[S] STATUS** - System health checks and diagnostics  
- **[C] CONFIG** - Interactive configuration manager
- **[I] INSTALL** - Auto-install missing components
- **[P] PACKAGE** - Create distribution packages

## 🔧 Configuration

### Environment Setup
The system supports multiple configuration modes:
- **Local-Only**: Complete privacy with LM Studio integration
- **Cloud+Local**: Hybrid mode with intelligent routing
- **Ultimate**: All features enabled with maximum capabilities

### AI Provider Configuration
```bash
# Edit configuration
.env              # Cloud + Local mode settings
.env.local        # Local-only mode settings  
ai_config.json    # AI routing configuration
```

## 📚 Documentation

### Core Documentation
- **[CLAUDE.md](docs/CLAUDE.md)** - Development and technical guide
- **[INTEGRATION_ENHANCEMENT_SUMMARY.md](INTEGRATION_ENHANCEMENT_SUMMARY.md)** - Complete feature overview
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Comprehensive setup instructions

### Integration Guides
- **ByteBot Integration** - Desktop automation capabilities
- **Archon Multi-Agent** - Agent orchestration and knowledge management
- **Charm Terminal** - Beautiful command-line interfaces
- **WSL Integration** - Cross-platform Linux support

## 🏗️ Architecture

### Integration Components
```
DuckBot Ultimate/
├── 🚀 ByteBot Desktop Automation
├── 🧠 Archon Multi-Agent System  
├── 💻 Charm Terminal Interface
├── 🌐 ChromiumOS System Features
├── 🐧 WSL Cross-Platform Support
├── 🎨 Enhanced Real-Time WebUI
├── 🤖 Multi-Model AI Routing
└── 📊 Advanced System Monitoring
```

### Service Architecture
- **Enhanced WebUI** (Port 8787) - Main dashboard interface
- **Charm Terminal** - Interactive command-line interface
- **ByteBot API** - Desktop automation endpoints
- **Archon Agents** - Multi-agent coordination system
- **WSL Integration** - Linux subsystem management

## 🧪 Testing

### Automated Testing
```bash
# Run comprehensive integration tests
# Choose option T from the launcher menu
# Or run directly:
python test_enhanced_duckbot.py
```

### Integration Validation
The system includes comprehensive testing for:
- ✅ All integration components
- ✅ Cross-platform compatibility  
- ✅ AI provider connectivity
- ✅ System resource requirements
- ✅ Performance benchmarks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone the repository
git clone https://github.com/your-username/duckbot-ultimate.git
cd duckbot-ultimate

# Install development dependencies
pip install -r requirements.txt

# Run in development mode
# Choose option D from the launcher menu
```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB
- **Storage**: 2GB free space
- **OS**: Windows 10+ or Linux (Ubuntu 18.04+)

### Recommended Configuration
- **CPU**: 4+ cores with GPU acceleration
- **RAM**: 8GB+
- **Storage**: 5GB+ SSD
- **OS**: Windows 11 or Ubuntu 22.04+
- **GPU**: NVIDIA GPU with CUDA support (optional)

## 🐛 Troubleshooting

### Common Issues

**Python not found**
```bash
# Install Python 3.8+ from https://python.org
# Ensure "Add Python to PATH" is checked during installation
```

**WSL not available**
```bash
# Install WSL on Windows
wsl --install
# Restart system after installation
```

**Dependencies failed**
```bash
# Use the automatic installer
# Choose option I from the launcher menu
# Or install manually:
pip install --upgrade pip
pip install -r requirements.txt
```

### Getting Help
- Check the `logs/` directory for detailed error information
- Use option **S** from the launcher for system diagnostics
- Review the **[INTEGRATION_ENHANCEMENT_SUMMARY.md](INTEGRATION_ENHANCEMENT_SUMMARY.md)** for feature details

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Integration Projects
- **[ByteBot](https://github.com/bytebot-ai/bytebot)** - Desktop automation framework
- **[Archon](https://github.com/coleam00/Archon)** - Multi-agent orchestration system  
- **[Charm](https://github.com/charmbracelet/crush)** - Terminal UI components
- **ChromiumOS** - System-level integration features

### Technologies
- **Python** - Core programming language
- **FastAPI** - Modern web framework
- **WebSockets** - Real-time communication
- **Rich** - Beautiful terminal formatting
- **OpenAI/Anthropic** - AI model providers

## 🚀 What's New in v3.1.0+

### Major Enhancements
- ✅ Complete ByteBot desktop automation integration
- ✅ Archon multi-agent orchestration system
- ✅ Charm-inspired terminal interfaces  
- ✅ Enhanced WebUI with real-time updates
- ✅ Cross-platform WSL integration
- ✅ Advanced system monitoring and analytics
- ✅ Professional distribution packaging
- ✅ Comprehensive testing and validation

### Technical Improvements
- ✅ Enhanced error handling and diagnostics
- ✅ Smart system requirement detection
- ✅ Cross-platform compatibility improvements
- ✅ Real-time WebSocket-based updates
- ✅ Professional logging and monitoring
- ✅ Automated dependency management

---

**Made with ❤️ for the AI community**

*DuckBot v3.1.0+ Ultimate Edition - The Complete AI Integration Suite*
"""
        
        readme_path = package_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
        
        # Create .gitignore
        gitignore_content = """# Python
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
        
        # Create LICENSE
        license_content = """MIT License

Copyright (c) 2024 DuckBot Ultimate Team

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
        
        # Create CONTRIBUTING.md
        contributing_content = """# Contributing to DuckBot Ultimate

Thank you for considering contributing to DuckBot Ultimate! This document provides guidelines for contributing to this project.

## Development Setup

1. Fork and clone the repository
2. Install Python 3.8+ and dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the system in developer mode:
   ```bash
   # Windows
   START_ENHANCED_DUCKBOT.bat
   # Choose option D for Developer Mode
   
   # Linux/WSL  
   ./start_ultimate_duckbot.sh
   # Choose option D for Developer Mode
   ```

## Integration Guidelines

### Adding New Integrations
1. Create integration module in `duckbot/integrations/`
2. Follow the existing integration patterns
3. Add comprehensive testing
4. Update documentation
5. Add to the main launcher menu

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to all public functions
- Maintain cross-platform compatibility

## Testing

Run comprehensive tests before submitting:
```bash
# From the launcher menu, choose option T
# Or run directly:
python test_enhanced_duckbot.py
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Update documentation as needed
4. Submit pull request with detailed description
5. Ensure all CI checks pass

## Integration Opportunities

Current integration focus areas:
- **Desktop Automation** - Extend ByteBot capabilities
- **Multi-Agent Systems** - Enhance Archon orchestration
- **Terminal Interfaces** - Improve Charm UI components
- **System Integration** - Expand ChromiumOS features
- **Cross-Platform** - Strengthen WSL support

## Questions?

Feel free to open an issue for questions or discussions about contributing.
"""
        
        contributing_path = package_dir / "CONTRIBUTING.md"
        contributing_path.write_text(contributing_content)
        
        logger.info("Created GitHub-ready files: README.md, .gitignore, LICENSE, CONTRIBUTING.md")
    
    def create_package_manifest(self, package_dir: Path, file_count: int) -> dict:
        """Create package manifest"""
        manifest = {
            "package_name": self.package_name,
            "version": "3.1.0+",
            "created": datetime.now().isoformat(),
            "total_files": file_count,
            "description": "DuckBot Ultimate Edition - Complete AI Integration Suite",
            "integrations": [
                "ByteBot Desktop Automation",
                "Archon Multi-Agent System", 
                "Charm Terminal Interface",
                "ChromiumOS System Features",
                "WSL Cross-Platform Support",
                "Enhanced Real-Time WebUI"
            ],
            "platforms": ["Windows", "Linux", "WSL"],
            "requirements": {
                "python": ">=3.8",
                "memory": "4GB+ (8GB+ recommended)",
                "storage": "2GB+ free space"
            },
            "startup_scripts": {
                "windows": "START_ENHANCED_DUCKBOT.bat",
                "linux": "start_ultimate_duckbot.sh"
            },
            "github_ready": True,
            "distribution_type": "complete"
        }
        
        manifest_path = package_dir / "PACKAGE_MANIFEST.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest
    
    def create_github_package(self) -> dict:
        """Create the complete GitHub package"""
        logger.info("Creating GitHub-ready DuckBot package...")
        
        # Create temporary directory
        output_dir = self.source_dir.parent
        temp_dir = output_dir / f"temp_{self.package_name}"
        package_dir = temp_dir / "DuckBot-v3.1.0-Ultimate"
        
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files and create structure
            file_count = self.create_github_ready_structure(package_dir)
            
            # Create package manifest
            manifest = self.create_package_manifest(package_dir, file_count)
            
            # Create ZIP file
            zip_path = output_dir / f"{self.package_name}.zip"
            
            logger.info(f"Creating ZIP archive: {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            # Get final size
            zip_size = zip_path.stat().st_size
            zip_size_mb = zip_size / (1024 * 1024)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            result = {
                "success": True,
                "package_name": self.package_name,
                "zip_path": str(zip_path),
                "zip_size_mb": zip_size_mb,
                "total_files": file_count,
                "manifest": manifest,
                "github_ready": True
            }
            
            logger.info(f"GitHub package created successfully!")
            logger.info(f"Package: {zip_path}")
            logger.info(f"Size: {zip_size_mb:.1f}MB")
            logger.info(f"Files: {file_count}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create GitHub package: {e}")
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create GitHub-ready DuckBot package')
    parser.add_argument('--source', help='Source directory (default: current directory)')
    
    args = parser.parse_args()
    
    try:
        creator = GitHubPackageCreator(args.source)
        result = creator.create_github_package()
        
        print("\nGitHub Package Created Successfully!")
        print(f"Package: {result['zip_path']}")
        print(f"Size: {result['zip_size_mb']:.1f}MB")
        print(f"Files: {result['total_files']}")
        print(f"Version: {result['manifest']['version']}")
        print("\nReady for GitHub upload!")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()