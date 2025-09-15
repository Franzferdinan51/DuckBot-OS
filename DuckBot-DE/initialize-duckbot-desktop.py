#!/usr/bin/env python3
"""
DuckBot Desktop Environment - Initialization Script
Initializes complete DuckBot integration with desktop environment
"""

import asyncio
import sys
import os
import logging
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DuckBotDesktopInitializer:
    """Complete DuckBot Desktop Environment Initializer"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.duckbot_source = Path('/home/user/Desktop/DuckBot-v3.1.0-VibeVoice-Ready-20250829_191017 (1)')
        self.install_path = Path('/usr/share/duckbot-de')
        self.config_path = Path.home() / '.duckbot'
        
        # Initialize paths
        self.config_path.mkdir(exist_ok=True)
        
    async def initialize_complete_desktop_environment(self):
        """Initialize complete DuckBot desktop environment"""
        logger.info("[DUCKBOT] Starting DuckBot Desktop Environment Initialization...")
        
        try:
            # Phase 1: System Setup
            await self._setup_system_integration()
            
            # Phase 2: Copy DuckBot Core
            await self._setup_duckbot_core()
            
            # Phase 3: Setup Desktop Services
            await self._setup_desktop_services()
            
            # Phase 4: Initialize Integrations
            await self._initialize_all_integrations()
            
            # Phase 5: Setup System Services
            await self._setup_system_services()
            
            # Phase 6: Configure Desktop Session
            await self._configure_desktop_session()
            
            # Phase 7: Setup GNOME Extension
            await self._setup_gnome_extension()
            
            # Phase 8: Finalize Configuration
            await self._finalize_configuration()
            
            logger.info("[OK] DuckBot Desktop Environment initialization complete!")
            await self._print_success_summary()
            
        except Exception as e:
            logger.error(f"[FAIL] Initialization failed: {e}")
            raise
            
    async def _setup_system_integration(self):
        """Setup system-level integration"""
        logger.info("[CONFIG] Setting up system integration...")
        
        # Create installation directory
        self.install_path.mkdir(parents=True, exist_ok=True)
        
        # Copy desktop environment files
        if self.base_path.exists():
            shutil.copytree(
                self.base_path,
                self.install_path,
                dirs_exist_ok=True
            )
            logger.info(f"[OK] Copied DuckBot-DE to {self.install_path}")
        
        # Setup system paths
        bashrc_path = Path.home() / '.bashrc'
        duckbot_paths = [
            'export DUCKBOT_DE_PATH="/usr/share/duckbot-de"',
            'export PATH="$PATH:/usr/share/duckbot-de/bin"',
            'export PYTHONPATH="$PYTHONPATH:/usr/share/duckbot-de"'
        ]
        
        # Add to bashrc if not already present
        if bashrc_path.exists():
            bashrc_content = bashrc_path.read_text()
            for path_export in duckbot_paths:
                if path_export not in bashrc_content:
                    with open(bashrc_path, 'a') as f:
                        f.write(f'\n# DuckBot Desktop Environment\n{path_export}\n')
        
        logger.info("[OK] System integration configured")
        
    async def _setup_duckbot_core(self):
        """Setup DuckBot core components"""
        logger.info("[BRAIN] Setting up DuckBot core...")
        
        if not self.duckbot_source.exists():
            logger.warning(f"[WARN] DuckBot source not found at {self.duckbot_source}")
            return
            
        # Copy core DuckBot components
        core_components = [
            'duckbot',
            'core',
            'open-notebook',
            'tests',
            'workflows',
            'ComfyUI',
            'logs'
        ]
        
        for component in core_components:
            source = self.duckbot_source / component
            target = self.install_path / component
            
            if source.exists():
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
                logger.info(f"[OK] Copied {component}")
            else:
                logger.warning(f"[WARN] Component {component} not found")
                
        # Copy essential files
        essential_files = [
            'requirements.txt',
            '.env.example',
            'ecosystem_config.yaml',
            'ai_config.json',
            'CLAUDE.md'
        ]
        
        for file in essential_files:
            source = self.duckbot_source / file
            target = self.install_path / file
            
            if source.exists():
                shutil.copy2(source, target)
                logger.info(f"[OK] Copied {file}")
                
        logger.info("[OK] DuckBot core setup complete")
        
    async def _setup_desktop_services(self):
        """Setup desktop-specific services"""
        logger.info("[DESKTOP] Setting up desktop services...")
        
        services_path = self.install_path / 'duckbot-desktop-services'
        services_path.mkdir(exist_ok=True)
        
        # Create systemd service files
        await self._create_systemd_services()
        
        # Setup D-Bus configuration
        await self._setup_dbus_configuration()
        
        # Create launcher scripts
        await self._create_launcher_scripts()
        
        logger.info("[OK] Desktop services configured")
        
    async def _create_systemd_services(self):
        """Create systemd service files"""
        logger.info("[LIST] Creating systemd services...")
        
        services = {
            'duckbot-window-manager': {
                'description': 'DuckBot Intelligent Window Manager',
                'script': 'intelligent-window-manager.py'
            },
            'duckbot-app-launcher': {
                'description': 'DuckBot Predictive Application Launcher',
                'script': 'predictive-app-launcher.py'
            },
            'duckbot-workflows': {
                'description': 'DuckBot Context-Aware Workflows',
                'script': 'context-aware-workflows.py'
            },
            'duckbot-coordinator': {
                'description': 'DuckBot Multi-Agent Coordinator',
                'script': 'multi-agent-coordinator.py'
            },
            'duckbot-integration': {
                'description': 'DuckBot Complete Integration Service',
                'script': 'complete-duckbot-integration.py'
            }
        }
        
        systemd_path = Path.home() / '.config' / 'systemd' / 'user'
        systemd_path.mkdir(parents=True, exist_ok=True)
        
        for service_name, config in services.items():
            service_content = f"""[Unit]
Description={config['description']}
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/share/duckbot-de/duckbot-desktop-services/{config['script']}
Restart=always
RestartSec=10
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%i/bus

[Install]
WantedBy=default.target
"""
            
            service_file = systemd_path / f'{service_name}.service'
            service_file.write_text(service_content)
            logger.info(f"[OK] Created {service_name}.service")
            
        logger.info("[OK] Systemd services created")
        
    async def _setup_dbus_configuration(self):
        """Setup D-Bus configuration"""
        logger.info("[SERVICE] Setting up D-Bus configuration...")
        
        dbus_path = Path.home() / '.local' / 'share' / 'dbus-1' / 'services'
        dbus_path.mkdir(parents=True, exist_ok=True)
        
        dbus_services = [
            'org.duckbot.WindowManager',
            'org.duckbot.AppLauncher', 
            'org.duckbot.ContextWorkflows',
            'org.duckbot.MultiAgentCoordinator',
            'org.duckbot.DesktopService'
        ]
        
        for service in dbus_services:
            service_content = f"""[D-BUS Service]
Name={service}
Exec=/usr/bin/python3 /usr/share/duckbot-de/duckbot-desktop-services/complete-duckbot-integration.py
User=user
"""
            
            service_file = dbus_path / f'{service}.service'
            service_file.write_text(service_content)
            logger.info(f"[OK] Created D-Bus service {service}")
            
        logger.info("[OK] D-Bus configuration complete")
        
    async def _create_launcher_scripts(self):
        """Create launcher scripts"""
        logger.info("[START] Creating launcher scripts...")
        
        bin_path = self.install_path / 'bin'
        bin_path.mkdir(exist_ok=True)
        
        # Main launcher
        launcher_content = """#!/bin/bash
# DuckBot Desktop Environment Launcher

export DUCKBOT_DE_PATH="/usr/share/duckbot-de"
export PYTHONPATH="$PYTHONPATH:/usr/share/duckbot-de"

# Start all DuckBot desktop services
echo "[DUCKBOT] Starting DuckBot Desktop Environment..."

# Start systemd services
systemctl --user start duckbot-window-manager
systemctl --user start duckbot-app-launcher
systemctl --user start duckbot-workflows
systemctl --user start duckbot-coordinator
systemctl --user start duckbot-integration

echo "[OK] DuckBot Desktop Environment started"
"""
        
        launcher_file = bin_path / 'start-duckbot-desktop'
        launcher_file.write_text(launcher_content)
        launcher_file.chmod(0o755)
        
        # Terminal launcher
        terminal_content = """#!/usr/bin/python3
# DuckBot AI Terminal Launcher

import sys
import os
sys.path.append('/usr/share/duckbot-de')

from duckbot_applications.ai_terminal.duckbot_terminal import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        terminal_file = bin_path / 'duckbot-terminal'
        terminal_file.write_text(terminal_content)
        terminal_file.chmod(0o755)
        
        logger.info("[OK] Launcher scripts created")
        
    async def _initialize_all_integrations(self):
        """Initialize all DuckBot integrations"""
        logger.info("[PLUGIN] Initializing all integrations...")
        
        try:
            # Add paths for import
            sys.path.insert(0, str(self.install_path))
            sys.path.insert(0, str(self.install_path / 'duckbot-desktop-services'))
            
            # Import and initialize
            from complete_duckbot_integration import initialize_complete_duckbot_integration
            
            results = await initialize_complete_duckbot_integration()
            
            successful = sum(1 for status in results.values() if status.initialized)
            total = len(results)
            
            logger.info(f"[OK] Integrations initialized: {successful}/{total}")
            
        except Exception as e:
            logger.error(f"[FAIL] Integration initialization failed: {e}")
            # Continue with setup even if some integrations fail
            
    async def _setup_system_services(self):
        """Setup and enable system services"""
        logger.info("[SETTINGS] Setting up system services...")
        
        try:
            # Reload systemd
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
            
            # Enable services
            services = [
                'duckbot-window-manager',
                'duckbot-app-launcher',
                'duckbot-workflows',
                'duckbot-coordinator',
                'duckbot-integration'
            ]
            
            for service in services:
                try:
                    subprocess.run(['systemctl', '--user', 'enable', service], check=True)
                    logger.info(f"[OK] Enabled {service}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"[WARN] Failed to enable {service}: {e}")
                    
            logger.info("[OK] System services configured")
            
        except Exception as e:
            logger.error(f"[FAIL] System services setup failed: {e}")
            
    async def _configure_desktop_session(self):
        """Configure desktop session"""
        logger.info("[HOME] Configuring desktop session...")
        
        # Create DuckBot session
        sessions_path = Path('/usr/share/xsessions')
        if not sessions_path.exists():
            sessions_path = Path.home() / '.local' / 'share' / 'xsessions'
            sessions_path.mkdir(parents=True, exist_ok=True)
            
        session_content = """[Desktop Entry]
Name=DuckBot AI Desktop
Comment=AI-Enhanced Desktop Environment powered by DuckBot
Exec=gnome-session --session=duckbot
TryExec=gnome-session
Type=Application
Keywords=GNOME;DuckBot;AI;Desktop;
"""
        
        session_file = sessions_path / 'duckbot-desktop.desktop'
        try:
            session_file.write_text(session_content)
            logger.info("[OK] Desktop session configured")
        except PermissionError:
            logger.warning("[WARN] Could not write system session file - manual configuration required")
            
        # Create GNOME session configuration
        gnome_sessions_path = Path('/usr/share/gnome-session/sessions')
        if not gnome_sessions_path.exists():
            gnome_sessions_path = Path.home() / '.local' / 'share' / 'gnome-session' / 'sessions'
            gnome_sessions_path.mkdir(parents=True, exist_ok=True)
            
        gnome_session_content = """[GNOME Session]
Name=DuckBot AI Desktop
RequiredComponents=org.gnome.Shell;org.gnome.SettingsDaemon;
RequiredProviders=windowmanager;panel;
DefaultProvider-windowmanager=org.gnome.Shell
DefaultProvider-panel=org.gnome.Shell
"""
        
        gnome_session_file = gnome_sessions_path / 'duckbot.session'
        try:
            gnome_session_file.write_text(gnome_session_content)
            logger.info("[OK] GNOME session configured")
        except PermissionError:
            logger.warning("[WARN] Could not write GNOME session file - manual configuration required")
            
    async def _setup_gnome_extension(self):
        """Setup GNOME Shell extension"""
        logger.info("[CONFIG] Setting up GNOME Shell extension...")
        
        # Copy extension
        extensions_path = Path.home() / '.local' / 'share' / 'gnome-shell' / 'extensions'
        extensions_path.mkdir(parents=True, exist_ok=True)
        
        extension_path = extensions_path / 'duckbot-ai@duckbot.ai'
        source_extension = self.install_path / 'duckbot-shell-extension'
        
        if source_extension.exists():
            shutil.copytree(source_extension, extension_path, dirs_exist_ok=True)
            logger.info("[OK] GNOME extension installed")
            
            # Try to enable extension
            try:
                subprocess.run([
                    'gnome-extensions', 'enable', 'duckbot-ai@duckbot.ai'
                ], check=True)
                logger.info("[OK] GNOME extension enabled")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("[WARN] Could not enable extension automatically - enable manually")
        else:
            logger.warning("[WARN] GNOME extension source not found")
            
    async def _finalize_configuration(self):
        """Finalize configuration"""
        logger.info("[TARGET] Finalizing configuration...")
        
        # Create desktop launchers
        desktop_path = Path.home() / 'Desktop'
        desktop_path.mkdir(exist_ok=True)
        
        # DuckBot Terminal launcher
        terminal_launcher = """[Desktop Entry]
Version=1.0
Type=Application
Name=DuckBot AI Terminal
Comment=AI-Enhanced Terminal with Charm Integration
Exec=/usr/share/duckbot-de/bin/duckbot-terminal
Icon=terminal
Terminal=false
Categories=System;TerminalEmulator;AI;
Keywords=terminal;command;shell;ai;duckbot;
"""
        
        terminal_file = desktop_path / 'DuckBot Terminal.desktop'
        terminal_file.write_text(terminal_launcher)
        terminal_file.chmod(0o755)
        
        # DuckBot System Monitor launcher (native desktop integration)
        monitor_launcher = """[Desktop Entry]
Version=1.0
Type=Application
Name=DuckBot System Monitor
Comment=DuckBot AI System Status and Control
Exec=gnome-system-monitor
Icon=utilities-system-monitor
Terminal=false
Categories=System;Monitor;AI;
Keywords=duckbot;ai;system;monitor;status;
"""
        
        monitor_file = desktop_path / 'DuckBot System Monitor.desktop'
        monitor_file.write_text(monitor_launcher)
        monitor_file.chmod(0o755)
        
        # Create documentation
        docs_path = self.install_path / 'docs'
        docs_path.mkdir(exist_ok=True)
        
        readme_content = """# DuckBot Desktop Environment

## Welcome to the World's First AI-Native Desktop Environment!

DuckBot-DE transforms your Ubuntu desktop into an intelligent, AI-enhanced workspace that learns from your behavior and assists with your tasks.

## Quick Start

1. **Log out of your current session**
2. **Select "DuckBot AI Desktop" from the login screen**
3. **Log in to experience the future of computing**

## Features

### [EMOJI] Intelligent Window Management
- AI learns your window preferences
- Automatic layout optimization
- Context-aware organization

### [START] Predictive Application Launching  
- Suggests apps based on your patterns
- Learns from your usage habits
- Intelligent recommendations

### [EMOJI] Context-Aware Workflows
- Detects workflow patterns
- Suggests automation opportunities
- Streamlines repetitive tasks

### [AI] Multi-Agent Coordination
- Deploy specialized AI agents
- Collaborative task execution
- Intelligent task distribution

## Getting Help

- Open DuckBot AI Terminal from desktop
- Type `help` for available commands
- Use voice commands: "DuckBot, help me with..."

## System Requirements

- Ubuntu 20.04+ with GNOME
- 8GB+ RAM (16GB+ recommended)
- Modern GPU with 4GB+ VRAM (optional but recommended)
- Internet connection for cloud AI features

Enjoy your AI-enhanced desktop experience! [DUCKBOT][STAR]
"""
        
        readme_file = docs_path / 'README.md'
        readme_file.write_text(readme_content)
        
        logger.info("[OK] Configuration finalized")
        
    async def _print_success_summary(self):
        """Print success summary"""
        print("\n" + "="*60)
        print("[DUCKBOT] DuckBot Desktop Environment Installation Complete! [DUCKBOT]")
        print("="*60)
        print()
        print("[SUCCESS] The world's first AI-native desktop environment is ready!")
        print()
        print("[LIST] Next Steps:")
        print("1. Log out of your current session")
        print("2. Select 'DuckBot AI Desktop' from login screen")
        print("3. Log in to experience AI-enhanced computing")
        print()
        print("[START] Features Available:")
        print("• Intelligent Window Management")
        print("• Predictive Application Launching")  
        print("• Context-Aware Workflows")
        print("• Multi-Agent Coordination")
        print("• AI-Enhanced Terminal")
        print("• Voice Control Integration")
        print("• Complete DuckBot AI Ecosystem")
        print()
        print("[TOOLS] Quick Commands:")
        print("• duckbot-terminal  - Launch AI terminal")
        print("• start-duckbot-desktop - Start all services")
        print()
        print("[DOCS] Documentation: /usr/share/duckbot-de/docs/")
        print("[CONFIG] Configuration: ~/.duckbot/")
        print()
        print("Welcome to the future of computing! [START]")
        print("="*60)

async def main():
    """Main initialization function"""
    try:
        initializer = DuckBotDesktopInitializer()
        await initializer.initialize_complete_desktop_environment()
        return 0
        
    except KeyboardInterrupt:
        print("\n[FAIL] Installation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"[FAIL] Installation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))