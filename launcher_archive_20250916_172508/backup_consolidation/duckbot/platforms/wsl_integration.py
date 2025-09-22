#!/usr/bin/env python3
"""
Real WSL Integration for DuckBot
Provides actual Windows Subsystem for Linux integration
"""

import os
import subprocess
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shlex

logger = logging.getLogger(__name__)

class WSLIntegration:
    """Real WSL integration with Windows OS"""
    
    def __init__(self):
        self.available_distros = {}
        self.default_distro = None
        self.wsl_available = False
        
    async def initialize(self) -> bool:
        """Initialize WSL integration"""
        try:
            # Check Windows system info first
            windows_info = await self._get_windows_system_info()
            logger.info(f"Windows System: {windows_info.get('os', 'Unknown')} - {windows_info.get('version', 'Unknown')}")
            
            # Check if WSL is available
            result = await self._run_command("wsl --version", shell=True)
            if result['success']:
                self.wsl_available = True
                await self._discover_distros()
                logger.info(f"WSL integration initialized - Available distros: {list(self.available_distros.keys())}")
                logger.info(f"Default distribution: {self.default_distro}")
                return True
            else:
                logger.warning("WSL not available on this system")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize WSL integration: {e}")
            return False
    
    async def _get_windows_system_info(self) -> Dict[str, str]:
        """Get Windows system information"""
        try:
            # Get Windows version info
            result = await self._run_command('systeminfo | findstr /B /C:"OS Name" /C:"OS Version"', shell=True)
            info = {}
            
            if result['success']:
                lines = result['output'].strip().split('\n')
                for line in lines:
                    if 'OS Name' in line:
                        info['os'] = line.split(':')[1].strip()
                    elif 'OS Version' in line:
                        info['version'] = line.split(':')[1].strip()
            
            # Get additional system info
            hostname_result = await self._run_command('hostname', shell=True)
            if hostname_result['success']:
                info['hostname'] = hostname_result['output'].strip()
            
            return info
        except Exception as e:
            logger.error(f"Failed to get Windows system info: {e}")
            return {}
    
    async def _discover_distros(self):
        """Discover available WSL distributions"""
        try:
            result = await self._run_command("wsl --list --verbose", shell=True)
            if result['success']:
                lines = result['output'].strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0].replace('*', '').strip()
                        state = parts[1].strip()
                        version = parts[2].strip()
                        
                        self.available_distros[name] = {
                            'state': state,
                            'version': version,
                            'default': '*' in line
                        }
                        
                        if '*' in line or self.default_distro is None:
                            self.default_distro = name
        except Exception as e:
            logger.error(f"Failed to discover WSL distributions: {e}")
    
    async def _run_command(self, command: str, distro: str = None, shell: bool = False, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command (WSL or Windows)"""
        try:
            if distro and not shell:
                # WSL command
                full_command = f"wsl -d {distro} -- {command}"
            elif not shell:
                # Default WSL
                full_command = f"wsl -- {command}"
            else:
                # Windows command
                full_command = command
            
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return {
                    'success': process.returncode == 0,
                    'output': stdout.decode('utf-8', errors='ignore'),
                    'error': stderr.decode('utf-8', errors='ignore'),
                    'returncode': process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'success': False,
                    'output': '',
                    'error': f'Command timed out after {timeout} seconds',
                    'returncode': -1
                }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
    
    async def execute_wsl_command(self, command: str, distro: str = None) -> Dict[str, Any]:
        """Execute a command in WSL"""
        if not self.wsl_available:
            return {
                'success': False,
                'error': 'WSL not available',
                'output': ''
            }
        
        target_distro = distro or self.default_distro
        result = await self._run_command(command, target_distro)
        
        return {
            'success': result['success'],
            'output': result['output'],
            'error': result['error'],
            'distro': target_distro,
            'command': command
        }
    
    async def start_distro(self, distro: str) -> Dict[str, Any]:
        """Start a WSL distribution"""
        if distro not in self.available_distros:
            return {
                'success': False,
                'error': f'Distribution {distro} not found'
            }
        
        # Starting WSL automatically happens when running a command
        result = await self.execute_wsl_command('echo "WSL Started"', distro)
        if result['success']:
            await self._discover_distros()  # Update status
        
        return result
    
    async def stop_distro(self, distro: str) -> Dict[str, Any]:
        """Stop a WSL distribution"""
        result = await self._run_command(f"wsl --terminate {distro}", shell=True)
        if result['success']:
            await self._discover_distros()  # Update status
        
        return result
    
    async def install_package(self, package: str, distro: str = None) -> Dict[str, Any]:
        """Install a package using apt (Ubuntu/Debian)"""
        command = f"sudo apt update && sudo apt install -y {shlex.quote(package)}"
        return await self.execute_wsl_command(command, distro)
    
    async def check_docker(self, distro: str = None) -> Dict[str, Any]:
        """Check Docker installation and status"""
        docker_check = await self.execute_wsl_command("docker --version", distro)
        
        if docker_check['success']:
            # Check if Docker daemon is running
            daemon_check = await self.execute_wsl_command("docker ps", distro)
            return {
                'success': True,
                'docker_installed': True,
                'daemon_running': daemon_check['success'],
                'version': docker_check['output'].strip(),
                'error': daemon_check['error'] if not daemon_check['success'] else None
            }
        else:
            return {
                'success': True,
                'docker_installed': False,
                'daemon_running': False,
                'version': None,
                'error': 'Docker not installed'
            }
    
    async def start_docker(self, distro: str = None) -> Dict[str, Any]:
        """Start Docker service"""
        return await self.execute_wsl_command("sudo service docker start", distro)
    
    async def list_containers(self, distro: str = None) -> Dict[str, Any]:
        """List Docker containers"""
        result = await self.execute_wsl_command("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", distro)
        return result
    
    async def get_system_info(self, distro: str = None) -> Dict[str, Any]:
        """Get WSL system information"""
        commands = {
            'os_release': 'cat /etc/os-release',
            'kernel': 'uname -r',
            'memory': 'free -h',
            'disk': 'df -h /',
            'cpu': 'lscpu | head -10'
        }
        
        info = {}
        for key, command in commands.items():
            result = await self.execute_wsl_command(command, distro)
            info[key] = {
                'output': result['output'] if result['success'] else 'N/A',
                'success': result['success']
            }
        
        return {
            'success': True,
            'distro': distro or self.default_distro,
            'info': info
        }
    
    async def file_operations(self, operation: str, path: str = None, content: str = None, distro: str = None) -> Dict[str, Any]:
        """Perform file operations in WSL"""
        if operation == 'ls':
            command = f"ls -la {shlex.quote(path) if path else '~'}"
        elif operation == 'pwd':
            command = "pwd"
        elif operation == 'cat' and path:
            command = f"cat {shlex.quote(path)}"
        elif operation == 'mkdir' and path:
            command = f"mkdir -p {shlex.quote(path)}"
        elif operation == 'write' and path and content:
            # Write content to file
            escaped_content = shlex.quote(content)
            command = f"echo {escaped_content} > {shlex.quote(path)}"
        else:
            return {
                'success': False,
                'error': f'Invalid file operation: {operation}'
            }
        
        return await self.execute_wsl_command(command, distro)
    
    async def get_network_info(self, distro: str = None) -> Dict[str, Any]:
        """Get network information"""
        commands = {
            'ip': 'ip addr show',
            'routes': 'ip route show',
            'dns': 'cat /etc/resolv.conf'
        }
        
        network_info = {}
        for key, command in commands.items():
            result = await self.execute_wsl_command(command, distro)
            network_info[key] = result['output'] if result['success'] else 'N/A'
        
        return {
            'success': True,
            'network_info': network_info
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get WSL integration status"""
        return {
            'wsl_available': self.wsl_available,
            'available_distros': self.available_distros,
            'default_distro': self.default_distro
        }
    
    async def start_service(self):
        """Start WSL as a background service"""
        logger.info("Starting WSL integration service...")
        await self.initialize()
        
        if not self.wsl_available:
            print("WARNING: WSL not available on this system.")
            print("Install WSL with: wsl --install")
            return
        
        print("[WSL] WSL Integration Service Active!")
        print(f"Available distributions: {list(self.available_distros.keys())}")
        print(f"Default distribution: {self.default_distro}")
        
        # Run service loop
        while True:
            try:
                await asyncio.sleep(30)  # Service heartbeat every 30 seconds
                logger.debug("WSL service running...")
            except KeyboardInterrupt:
                logger.info("WSL service stopped")
                break
            except Exception as e:
                logger.error(f"WSL service error: {e}")
                await asyncio.sleep(10)
    
    async def start_interactive_mode(self):
        """Start WSL in interactive mode"""
        logger.info("Starting WSL Interactive Mode...")
        await self.initialize()
        
        if not self.wsl_available:
            print("WARNING: WSL not available on this system.")
            print("To install WSL:")
            print("  1. Run as administrator: wsl --install")
            print("  2. Restart your computer")
            print("  3. Complete Ubuntu setup")
            return
        
        print("[WSL] WSL Integration Active!")
        print(f"Available distributions: {list(self.available_distros.keys())}")
        print(f"Default distribution: {self.default_distro}")
        print("\nCommands:")
        print("  - 'distros' - List distributions")
        print("  - 'status' - Show WSL status")
        print("  - 'exec <command>' - Execute command in default distro")
        print("  - 'exec <distro> <command>' - Execute in specific distro")
        print("  - 'shell' - Open interactive shell")
        print("  - 'help' - Show all commands")
        print("  - 'quit' - Exit WSL integration")
        
        while True:
            try:
                command = input("\nWSL> ").strip()
                
                if command.lower() in ['quit', 'exit']:
                    break
                elif command.lower() == 'help':
                    await self._show_help()
                elif command.lower() == 'distros':
                    await self._show_distros()
                elif command.lower() == 'status':
                    status = self.get_status()
                    print(f"WSL Status: {json.dumps(status, indent=2)}")
                elif command.startswith('exec '):
                    exec_command = command[5:]  # Remove 'exec '
                    parts = exec_command.split(' ', 1)
                    
                    if len(parts) == 2 and parts[0] in self.available_distros:
                        # Execute in specific distro
                        distro, cmd = parts
                        result = await self.execute_wsl_command(cmd, distro)
                    else:
                        # Execute in default distro
                        result = await self.execute_wsl_command(exec_command)
                    
                    if result.get('success'):
                        print(f"Output:\n{result.get('output', 'No output')}")
                        if result.get('error'):
                            print(f"Errors:\n{result['error']}")
                    else:
                        print(f"Command failed: {result.get('error', 'Unknown error')}")
                        
                elif command.lower() == 'shell':
                    print("Opening WSL shell...")
                    print("Type 'exit' to return to WSL integration mode")
                    os.system(f"wsl -d {self.default_distro}")
                elif command:
                    # Treat as WSL command
                    result = await self.execute_wsl_command(command)
                    if result.get('success'):
                        print(f"Output:\n{result.get('output', 'No output')}")
                        if result.get('error'):
                            print(f"Errors:\n{result['error']}")
                    else:
                        print(f"Command failed: {result.get('error', 'Unknown error')}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("WSL Interactive Mode ended.")
    
    async def _show_help(self):
        """Show detailed help information"""
        help_text = """
[WSL] WSL Integration Commands:

Basic Commands:
  distros                  - List available distributions
  status                   - Show WSL status and configuration
  exec <command>           - Execute command in default distribution
  exec <distro> <command>  - Execute command in specific distribution
  shell                    - Open interactive WSL shell
  help                     - Show this help
  quit/exit               - Exit WSL integration

Distribution Management:
  - Ubuntu (default)       - Most common Linux distribution
  - Debian                 - Stable, reliable distribution  
  - SUSE                   - Enterprise Linux distribution
  - Kali Linux             - Security and penetration testing

Command Examples:
  WSL> exec ls -la
  WSL> exec Ubuntu pwd
  WSL> exec apt update && apt upgrade
  WSL> exec python3 --version
  WSL> shell

Advanced Features:
  - Cross-platform file operations
  - Network configuration and management
  - Docker container integration
  - Development environment setup
  - Package management across distributions
        """
        print(help_text)
    
    async def _show_distros(self):
        """Show available distributions"""
        print("\n[WSL] Available WSL Distributions:")
        if not self.available_distros:
            print("  No distributions found")
            return
            
        for name, info in self.available_distros.items():
            default_marker = " (default)" if name == self.default_distro else ""
            print(f"  - {name}{default_marker}")
            print(f"    Version: {info.get('version', 'Unknown')}")
            print(f"    State: {info.get('state', 'Unknown')}")
        
        print(f"\nTotal distributions: {len(self.available_distros)}")

# Global instance
wsl_integration = WSLIntegration()

async def initialize_wsl() -> bool:
    """Initialize WSL integration"""
    return await wsl_integration.initialize()

async def execute_wsl_command(command: str, distro: str = None) -> Dict[str, Any]:
    """Execute WSL command interface"""
    return await wsl_integration.execute_wsl_command(command, distro)

def is_wsl_available() -> bool:
    """Check if WSL is available"""
    return wsl_integration.wsl_available

def get_wsl_status() -> Dict[str, Any]:
    """Get WSL status"""
    return wsl_integration.get_status()