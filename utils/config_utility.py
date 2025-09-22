#!/usr/bin/env python3
"""
DuckBot Configuration Utility
Command-line tool for managing DuckBot configuration
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import (
    get_config_manager,
    initialize_config,
    Environment,
    ServiceStatus
)

class ConfigUtility:
    """Configuration management utility"""

    def __init__(self):
        self.config_manager = get_config_manager()

    def show_config(self, args: argparse.Namespace) -> None:
        """Show current configuration"""
        info = self.config_manager.get_system_info()

        print("=== DuckBot Configuration ===")
        print(f"Environment: {info['environment']}")
        print(f"Config Path: {info['config_path']}")
        print(f"Version: {self.config_manager.config_data.get('system', {}).get('version', 'Unknown')}")
        print()

        print("Services:")
        services = self.config_manager.get_all_services()
        for name, service in services.items():
            status = "ENABLED" if service.enabled else "DISABLED"
            port = service.current_port or service.default_port
            print(f"  {name}: {status} (Port: {port})")
        print()

        print("Feature Flags:")
        features = self.config_manager.config_data.get('features', {})
        for name, enabled in features.items():
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  {name}: {status}")
        print()

        if info['validation_issues']:
            print("Validation Issues:")
            for issue in info['validation_issues']:
                print(f"  X {issue}")
        else:
            print("PASS: No validation issues")

    def list_services(self, args: argparse.Namespace) -> None:
        """List all services"""
        services = self.config_manager.get_all_services()

        print(f"{'Service':<20} {'Status':<10} {'Port':<6} {'Required':<10} {'URL'}")
        print("-" * 80)

        for name, service in services.items():
            status = "ENABLED" if service.enabled else "DISABLED"
            port = service.current_port or service.default_port
            required = "YES" if service.required else "NO"
            url = self.config_manager.get_service_url(name) or ""

            print(f"{name:<20} {status:<10} {port:<6} {required:<10} {url}")

    def check_status(self, args: argparse.Namespace) -> None:
        """Check service status"""
        services = self.config_manager.get_enabled_services()

        print("Service Status Check:")
        print(f"{'Service':<20} {'Status':<12} {'Port':<6} {'Health'}")
        print("-" * 60)

        for name in services.keys():
            available = self.config_manager.is_service_available(name)
            status = "AVAILABLE" if available else "UNAVAILABLE"
            service = self.config_manager.get_service_config(name)
            port = service.current_port or service.default_port
            health = "PASS" if available else "FAIL"

            print(f"{name:<20} {status:<12} {port:<6} {health}")

    def validate_config(self, args: argparse.Namespace) -> None:
        """Validate configuration"""
        issues = self.config_manager.validate_config()

        print("Configuration Validation:")
        print("=" * 50)

        if issues:
            print(f"Found {len(issues)} validation issues:")
            for issue in issues:
                print(f"  X {issue}")
            sys.exit(1)
        else:
            print("PASS: All validation checks passed!")

    def export_config(self, args: argparse.Namespace) -> None:
        """Export configuration"""
        output_path = args.output or "config/duckbot_config_export.json"

        if args.format == "json":
            self.config_manager.export_config_json(output_path)
            print(f"Configuration exported to: {output_path}")
        elif args.format == "yaml":
            self.config_manager.save_config(output_path)
            print(f"Configuration saved to: {output_path}")

    def test_ports(self, args: argparse.Namespace) -> None:
        """Test port allocation"""
        print("Testing port allocation...")

        try:
            # Test port allocation
            port = self.config_manager.allocate_port("webui")
            print(f"PASS: Port allocated: {port}")

            # Test port availability check
            available = self.config_manager._is_port_available(port + 1)
            print(f"PASS: Port {port + 1} available: {available}")

            # Release port
            self.config_manager.release_port(port)
            print("PASS: Port released successfully")

        except Exception as e:
            print(f"FAIL: Port test failed: {e}")

    def start_service(self, args: argparse.Namespace) -> None:
        """Start a specific service"""
        service_name = args.service
        service = self.config_manager.get_service_config(service_name)

        if not service:
            print(f"Service '{service_name}' not found")
            return

        if not service.enabled:
            print(f"Service '{service_name}' is disabled")
            return

        print(f"Starting service: {service_name}")

        try:
            # Allocate port
            port = self.config_manager.allocate_port(service_name)
            print(f"Allocated port: {port}")

            # Set environment variables
            env_vars = self.config_manager.get_service_environment(service_name)
            for key, value in env_vars.items():
                os.environ[key] = value
                print(f"Set environment: {key}={value}")

            # Start service
            if service.startup_script:
                import subprocess
                import sys

                cmd = [sys.executable, "-m", service.startup_script]

                if args.background:
                    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                    print(f"Service started in background")
                else:
                    subprocess.run(cmd)
                    print(f"Service completed")

                print(f"Service URL: {self.config_manager.get_service_url(service_name)}")

        except Exception as e:
            print(f"Failed to start service: {e}")

    def set_environment(self, args: argparse.Namespace) -> None:
        """Set runtime environment"""
        env_name = args.environment.lower()

        try:
            env = Environment(env_name)
            # Reinitialize config manager with new environment
            self.config_manager = initialize_config(environment=env)
            print(f"Environment set to: {env_name}")
        except ValueError:
            print(f"Invalid environment: {env_name}")
            print(f"Valid environments: {[e.value for e in Environment]}")

    def show_features(self, args: argparse.Namespace) -> None:
        """Show feature flags"""
        features = self.config_manager.config_data.get('features', {})

        print("Feature Flags:")
        print(f"{'Feature':<30} {'Status':<10}")
        print("-" * 45)

        for name, enabled in features.items():
            status = "ENABLED" if enabled else "DISABLED"
            print(f"{name:<30} {status:<10}")

    def toggle_feature(self, args: argparse.Namespace) -> None:
        """Toggle a feature flag"""
        feature_name = args.feature
        features = self.config_manager.config_data.get('features', {})

        if feature_name not in features:
            print(f"Feature '{feature_name}' not found")
            return

        current_value = features[feature_name]
        new_value = not current_value

        features[feature_name] = new_value
        self.config_manager.config_data['features'] = features

        print(f"Feature '{feature_name}' toggled: {'ENABLED' if new_value else 'DISABLED'}")

        if args.save:
            self.config_manager.save_config()
            print("Configuration saved")

    def create_backup(self, args: argparse.Namespace) -> None:
        """Create configuration backup"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"config/backup_config_{timestamp}.yaml"

        # Copy current config to backup
        import shutil
        shutil.copy2(self.config_manager.config_path, backup_path)

        print(f"Configuration backup created: {backup_path}")

    def restore_backup(self, args: argparse.Namespace) -> None:
        """Restore configuration from backup"""
        backup_path = args.backup

        if not os.path.exists(backup_path):
            print(f"Backup file not found: {backup_path}")
            return

        # Restore from backup
        import shutil
        shutil.copy2(backup_path, self.config_manager.config_path)

        # Reinitialize config manager
        self.config_manager = initialize_config()

        print(f"Configuration restored from: {backup_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DuckBot Configuration Utility")
    parser.add_argument("--env", choices=["development", "production", "local"],
                       help="Runtime environment")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Show configuration
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    show_parser.set_defaults(func="show_config")

    # List services
    list_parser = subparsers.add_parser("list", help="List all services")
    list_parser.set_defaults(func="list_services")

    # Check status
    status_parser = subparsers.add_parser("status", help="Check service status")
    status_parser.set_defaults(func="check_status")

    # Validate configuration
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.set_defaults(func="validate_config")

    # Export configuration
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument("--output", help="Output file path")
    export_parser.add_argument("--format", choices=["json", "yaml"], default="json",
                              help="Export format")
    export_parser.set_defaults(func="export_config")

    # Test ports
    test_parser = subparsers.add_parser("test-ports", help="Test port allocation")
    test_parser.set_defaults(func="test_ports")

    # Start service
    start_parser = subparsers.add_parser("start", help="Start a specific service")
    start_parser.add_argument("service", help="Service name")
    start_parser.add_argument("--background", action="store_true",
                             help="Start service in background")
    start_parser.set_defaults(func="start_service")

    # Set environment
    env_parser = subparsers.add_parser("set-env", help="Set runtime environment")
    env_parser.add_argument("environment", choices=["development", "production", "local"],
                           help="Environment name")
    env_parser.set_defaults(func="set_environment")

    # Show features
    features_parser = subparsers.add_parser("features", help="Show feature flags")
    features_parser.set_defaults(func="show_features")

    # Toggle feature
    toggle_parser = subparsers.add_parser("toggle", help="Toggle feature flag")
    toggle_parser.add_argument("feature", help="Feature name")
    toggle_parser.add_argument("--save", action="store_true",
                              help="Save configuration after toggle")
    toggle_parser.set_defaults(func="toggle_feature")

    # Create backup
    backup_parser = subparsers.add_parser("backup", help="Create configuration backup")
    backup_parser.set_defaults(func="create_backup")

    # Restore backup
    restore_parser = subparsers.add_parser("restore", help="Restore configuration from backup")
    restore_parser.add_argument("backup", help="Backup file path")
    restore_parser.set_defaults(func="restore_backup")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize config manager with environment if specified
    if args.env:
        initialize_config(environment=Environment(args.env))
    else:
        initialize_config()

    # Create utility instance
    utility = ConfigUtility()

    # Execute command
    func_name = args.func.replace('-', '_')
    func = getattr(utility, func_name)
    func(args)

if __name__ == "__main__":
    main()