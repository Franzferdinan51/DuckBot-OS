#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User interface module for the modular launcher
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class LauncherUI:
    """User interface for the modular launcher"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent

    def show_welcome(self):
        """Display welcome message"""
        self.clear_screen()
        print("=" * 80)
        print("DUCKBOT MODULAR LAUNCHER v4.2")
        print("=" * 80)
        print("Welcome to the new modular launcher architecture!")
        print("This replaces the monolithic 5,888-line batch file with a clean,")
        print("maintainable Python-based system.")
        print()
        print("Features:")
        print("[✓] Modular service management")
        print("[✓] Intelligent port allocation")
        print("[✓] Comprehensive error handling")
        print("[✓] Real-time service monitoring")
        print("[✓] Dependency resolution")
        print("[✓] Auto-recovery capabilities")
        print("=" * 80)
        print()

    def show_main_menu(self, available_modes: List[str]) -> str:
        """Display main menu and get user choice"""
        self.clear_screen()

        print("DUCKBOT LAUNCHER - MAIN MENU")
        print("=" * 60)
        print()

        # Show launch modes
        print("🚀 AVAILABLE LAUNCH MODES:")
        for i, mode in enumerate(available_modes[:8], 1):  # Show top 8 modes
            print(f"  {i}. {mode.replace('_', ' ').title()}")

        print()
        print("🔧 MANAGEMENT OPTIONS:")
        print("  s. System Status")
        print("  x. Stop All Services")
        print("  e. Export Configuration")
        print("  h. Help")
        print("  q. Quit")
        print()

        while True:
            choice = input("Select an option: ").strip().lower()

            # Map numeric choices to mode names
            if choice.isdigit() and 1 <= int(choice) <= len(available_modes[:8]):
                return available_modes[int(choice) - 1]
            elif choice == 's':
                return "status"
            elif choice == 'x':
                return "stop"
            elif choice == 'e':
                return "export"
            elif choice == 'h':
                return "help"
            elif choice == 'q':
                return "exit"
            else:
                print("❌ Invalid choice. Please try again.")

    def show_status(self, status_data: Dict[str, Any]):
        """Display comprehensive system status"""
        self.clear_screen()

        print("📊 DUCKBOT SYSTEM STATUS")
        print("=" * 60)
        print()

        # Launcher status
        launcher_info = status_data.get("launcher", {})
        uptime = launcher_info.get("uptime", 0)
        uptime_str = self._format_uptime(uptime)

        print("🏠 LAUNCHER STATUS:")
        print(f"  State: {launcher_info.get('state', {}).get('current_mode', 'unknown')}")
        print(f"  Uptime: {uptime_str}")
        print(f"  Active Services: {len(launcher_info.get('state', {}).get('active_services', []))}")
        print()

        # Service status
        services = status_data.get("services", {})
        running_services = [s for s in services.values() if s.get("state") == "running"]
        stopped_services = [s for s in services.values() if s.get("state") == "stopped"]
        error_services = [s for s in services.values() if s.get("state") == "error"]

        print("🔧 SERVICE STATUS:")
        print(f"  ✅ Running: {len(running_services)}")
        print(f"  ⏹️  Stopped: {len(stopped_services)}")
        print(f"  ❌ Error: {len(error_services)}")
        print()

        # Show running services
        if running_services:
            print("🟢 RUNNING SERVICES:")
            for service in running_services[:5]:  # Show top 5
                name = service.get("display_name", service.get("name", "Unknown"))
                uptime = self._format_uptime(service.get("uptime", 0))
                health = "✅" if service.get("health", {}).get("is_healthy", False) else "⚠️"
                print(f"    {health} {name} ({uptime})")
            if len(running_services) > 5:
                print(f"    ... and {len(running_services) - 5} more")
            print()

        # Port status
        ports = status_data.get("ports", {})
        used_ports = [p for p in ports.values() if p.get("in_use")]
        available_ports = [p for p in ports.values() if not p.get("in_use")]

        print("🌐 PORT STATUS:")
        print(f"  🟢 In Use: {len(used_ports)}")
        print(f"  ⚪ Available: {len(available_ports)}")
        print()

        # Show port conflicts
        conflicts = [p for p in used_ports if not p.get("health_status", True)]
        if conflicts:
            print("⚠️  PORT CONFLICTS:")
            for port in conflicts[:3]:
                port_num = port.get("port", "Unknown")
                service = port.get("service_name", "Unknown")
                print(f"    Port {port_num} ({service}) - Not responding")
            print()

        # Environment status
        env = status_data.get("environment", {})
        env_status = env.get("status", "unknown")

        print("🌍 ENVIRONMENT STATUS:")
        status_icon = "✅" if env_status == "ready" else "❌"
        print(f"  {status_icon} {env_status.title()}")
        print(f"  Python: {env.get('python_command', 'Not found')}")
        print(f"  Working Directory: {env.get('working_directory', 'Unknown')}")
        print()

    def show_launch_success(self, mode_name: str):
        """Display launch success message"""
        print(f"✅ SUCCESS: {mode_name.replace('_', ' ').title()} launched successfully!")
        print()
        print("🌐 Access URLs:")
        print("  Enhanced WebUI:     http://localhost:8787")
        print("  Enhanced Dashboard: http://localhost:8788")
        print("  System Monitoring:  http://localhost:8789")
        print("  Open WebUI:         http://localhost:3000")
        print("  Modern WebUI:       http://localhost:8790")
        print()
        print("📝 Logs are available in the 'logs/' directory")
        print()

    def show_launch_failed(self, mode_name: str, error_message: str):
        """Display launch failure message"""
        print(f"❌ FAILED: {mode_name.replace('_', ' ').title()} launch failed!")
        print()
        print(f"Error: {error_message}")
        print()
        print("💡 Troubleshooting:")
        print("  1. Check the logs in 'logs/' directory")
        print("  2. Verify Python installation")
        print("  3. Check port conflicts")
        print("  4. Run with 'status' option for diagnostics")
        print()

    def show_services_stopped(self):
        """Display services stopped message"""
        print("🛑 All services have been stopped.")
        print()
        print("✅ System is now in idle state.")
        print()

    def show_goodbye(self):
        """Display goodbye message"""
        self.clear_screen()
        print("👋 GOODBYE FROM DUCKBOT!")
        print("=" * 60)
        print()
        print("Thank you for using DuckBot Modular Launcher!")
        print()
        print("📝 Note: Some services may still be running in the background.")
        print("   Check your task manager if you need to stop them manually.")
        print()
        print("🚀 See you next time!")
        print("=" * 60)

    def show_invalid_choice(self):
        """Display invalid choice message"""
        print("❌ Invalid choice. Please select a valid option.")

    def show_help(self):
        """Display help information"""
        self.clear_screen()
        print("📖 DUCKBOT LAUNCHER HELP")
        print("=" * 60)
        print()

        print("🚀 LAUNCH MODES:")
        print("  ultimate        - Complete enhanced mode with all integrations")
        print("  enhanced_webui  - Modern web interface with real-time updates")
        print("  monitoring      - Real-time system metrics and performance")
        print("  local_only      - Complete offline operation with LM Studio")
        print("  hybrid          - Intelligent local/cloud AI routing")
        print("  duckbot_os      - AI web operating system")
        print("  minimal         - Essential services for low-resource systems")
        print("  developer       - Full debugging and development tools")
        print()

        print("🔧 MANAGEMENT OPTIONS:")
        print("  status          - Show comprehensive system status")
        print("  stop            - Stop all running services")
        print("  export          - Export current configuration")
        print("  help            - Show this help message")
        print("  quit            - Exit the launcher")
        print()

        print("🔍 TROUBLESHOOTING:")
        print("  • Check 'logs/' directory for detailed service logs")
        print("  • Use 'status' to see port conflicts and service health")
        print("  • Verify Python 3.8+ is installed and accessible")
        print("  • Ensure LM Studio is running for local-only mode")
        print("  • Check for port conflicts if services fail to start")
        print()

        print("⚙️  CONFIGURATION:")
        print("  • Service configs: config/services.json")
        print("  • Mode configs: config/launch_modes.json")
        print("  • Environment: .env files")
        print()

        input("Press Enter to continue...")

    def show_mode_details(self, mode_name: str, mode_config: Any):
        """Show detailed information about a launch mode"""
        self.clear_screen()
        print(f"📋 {mode_config.display_name}")
        print("=" * 60)
        print()

        print(f"Description: {mode_config.description}")
        print()

        print("🔧 Services:")
        for service_name in mode_config.services:
            print(f"  • {service_name.replace('_', ' ').title()}")
        print()

        if mode_config.env_vars:
            print("🌍 Environment Variables:")
            for key, value in mode_config.env_vars.items():
                print(f"  • {key} = {value}")
            print()

        if mode_config.pre_launch:
            print("⚡ Pre-launch Commands:")
            for cmd in mode_config.pre_launch:
                print(f"  • {cmd}")
            print()

        if mode_config.post_launch:
            print("🔄 Post-launch Commands:")
            for cmd in mode_config.post_launch:
                print(f"  • {cmd}")
            print()

        input("Press Enter to continue...")

    def show_port_conflicts(self, conflicts: List[Dict[str, Any]]):
        """Display port conflict information"""
        if not conflicts:
            return

        print("⚠️  PORT CONFLICTS DETECTED")
        print("=" * 60)
        print()

        for conflict in conflicts:
            port = conflict.get("port", "Unknown")
            service = conflict.get("service", "Unknown")
            issue = conflict.get("issue", "Unknown issue")

            print(f"❌ Port {port} ({service}): {issue}")

        print()
        print("💡 Solutions:")
        print("  1. Stop the conflicting service")
        print("  2. Change the port configuration")
        print("  3. Use 'status' to see detailed port information")
        print()

    def show_service_logs(self, service_name: str, log_lines: int = 20):
        """Show recent log lines for a service"""
        log_file = self.project_root / "logs" / f"{service_name}.log"

        if not log_file.exists():
            print(f"❌ Log file not found: {log_file}")
            return

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            print(f"📝 RECENT LOGS: {service_name}")
            print("=" * 60)
            print()

            # Show last N lines
            for line in lines[-log_lines:]:
                print(line.rstrip())

        except Exception as e:
            print(f"❌ Error reading log file: {e}")

        input("\nPress Enter to continue...")

    def show_configuration_export(self, export_path: str):
        """Show configuration export result"""
        print(f"✅ Configuration exported to: {export_path}")
        print()
        print("📋 Export includes:")
        print("  • Service configurations")
        print("  • Launch mode definitions")
        print("  • Current system state")
        print()
        input("Press Enter to continue...")

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}d {hours}h"

    def show_progress(self, message: str, duration: float = 2.0):
        """Show a simple progress indicator"""
        print(f"⏳ {message}", end="", flush=True)

        import time
        start_time = time.time()
        while time.time() - start_time < duration:
            for char in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏":
                print(f"\r⏳ {message} {char}", end="", flush=True)
                time.sleep(0.1)

        print(f"\r✅ {message}      ")

    def prompt_confirmation(self, message: str) -> bool:
        """Prompt for yes/no confirmation"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes', 'Y']:
                return True
            elif response in ['n', 'no', 'N']:
                return False
            else:
                print("Please enter 'y' or 'n'.")

    def prompt_input(self, message: str, default: str = None) -> str:
        """Prompt for user input with optional default"""
        if default:
            response = input(f"{message} [{default}]: ").strip()
            return response if response else default
        else:
            return input(f"{message}: ").strip()

    def show_error_details(self, error_info: Dict[str, Any]):
        """Show detailed error information"""
        print("❌ ERROR DETAILS")
        print("=" * 60)
        print()

        print(f"Category: {error_info.get('category', 'Unknown')}")
        print(f"Level: {error_info.get('level', 'Unknown')}")
        print(f"Message: {error_info.get('message', 'No message')}")
        print()

        if error_info.get('timestamp'):
            timestamp = error_info['timestamp']
            if isinstance(timestamp, (int, float)):
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                print(f"Time: {time_str}")

        if error_info.get('details'):
            print("Details:")
            for key, value in error_info['details'].items():
                print(f"  {key}: {value}")

        if error_info.get('stack_trace'):
            print("\nStack Trace:")
            print(error_info['stack_trace'])

        print()

    def show_banner(self, text: str, width: int = 60):
        """Show a formatted banner"""
        padding = (width - len(text) - 4) // 2
        print("=" * width)
        print(f"{' ' * padding} {text} {' ' * padding}")
        print("=" * width)
        print()