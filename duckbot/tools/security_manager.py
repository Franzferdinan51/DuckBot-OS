#!/usr/bin/env python3
"""
DuckBot Security Management CLI Tool

Command-line tool for managing DuckBot security features including:
- User and role management
- Security configuration
- Audit log viewing
- Security monitoring
- Compliance reporting
- System hardening

Usage: python security_manager.py <command> [options]

Author: Security Framework Module
Version: 1.0.0
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Add duckbot to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.security_integration import SecurityIntegration
from core.security_framework import Permission, ResourceType, SecurityEventType
from core.audit_logger import ComplianceStandard

class SecurityManagerCLI:
    """Security Manager CLI"""

    def __init__(self):
        self.security_integration = None

    async def initialize(self):
        """Initialize security integration"""
        self.security_integration = SecurityIntegration()
        await self.security_integration.initialize()

    async def user_commands(self, args):
        """Handle user management commands"""
        if args.action == "create":
            await self.create_user(args)
        elif args.action == "list":
            await self.list_users(args)
        elif args.action == "update":
            await self.update_user(args)
        elif args.action == "delete":
            await self.delete_user(args)
        elif args.action == "reset-password":
            await self.reset_password(args)
        elif args.action == "enable-mfa":
            await self.enable_mfa(args)
        elif args.action == "disable-mfa":
            await self.disable_mfa(args)

    async def create_user(self, args):
        """Create new user"""
        try:
            user = await self.security_integration.auth_system.create_user(
                username=args.username,
                email=args.email,
                password=args.password,
                roles=args.roles.split(',') if args.roles else ['user']
            )

            print(f"✓ User '{args.username}' created successfully")
            print(f"  User ID: {user['id']}")
            print(f"  Email: {user['email']}")
            print(f"  Roles: {', '.join(user['roles'])}")

        except Exception as e:
            print(f"✗ Failed to create user: {e}")
            sys.exit(1)

    async def list_users(self, args):
        """List all users"""
        try:
            # This would typically query the user database
            print("Users:")
            print("-" * 50)
            print("No users found (database integration needed)")

        except Exception as e:
            print(f"✗ Failed to list users: {e}")
            sys.exit(1)

    async def update_user(self, args):
        """Update user"""
        try:
            print(f"Updating user '{args.username}'...")
            print("User update functionality requires database integration")

        except Exception as e:
            print(f"✗ Failed to update user: {e}")
            sys.exit(1)

    async def delete_user(self, args):
        """Delete user"""
        try:
            print(f"Deleting user '{args.username}'...")
            print("User deletion functionality requires database integration")

        except Exception as e:
            print(f"✗ Failed to delete user: {e}")
            sys.exit(1)

    async def reset_password(self, args):
        """Reset user password"""
        try:
            success = await self.security_integration.auth_system.change_password(
                user_id=args.user_id,
                current_password=args.current_password,
                new_password=args.new_password
            )

            if success:
                print(f"✓ Password reset successfully for user {args.user_id}")
            else:
                print("✗ Password reset failed - check current password")
                sys.exit(1)

        except Exception as e:
            print(f"✗ Failed to reset password: {e}")
            sys.exit(1)

    async def enable_mfa(self, args):
        """Enable MFA for user"""
        try:
            mfa_setup = await self.security_integration.auth_system.setup_mfa(args.user_id)

            print(f"✓ MFA setup initiated for user {args.user_id}")
            print(f"  Secret: {mfa_setup['secret']}")
            print(f"  Backup codes: {', '.join(mfa_setup['backup_codes'])}")
            print(f"  QR Code data available in base64 format")
            print("  Please scan the QR code with your authenticator app")
            print("  Then run 'security-manager mfa verify' to complete setup")

        except Exception as e:
            print(f"✗ Failed to enable MFA: {e}")
            sys.exit(1)

    async def disable_mfa(self, args):
        """Disable MFA for user"""
        try:
            success = await self.security_integration.auth_system.disable_mfa(args.user_id, args.password)

            if success:
                print(f"✓ MFA disabled for user {args.user_id}")
            else:
                print("✗ Failed to disable MFA - check password")
                sys.exit(1)

        except Exception as e:
            print(f"✗ Failed to disable MFA: {e}")
            sys.exit(1)

    async def role_commands(self, args):
        """Handle role management commands"""
        if args.action == "create":
            await self.create_role(args)
        elif args.action == "list":
            await self.list_roles(args)
        elif args.action == "update":
            await self.update_role(args)
        elif args.action == "delete":
            await self.delete_role(args)

    async def create_role(self, args):
        """Create new role"""
        try:
            from core.security_framework import Role

            permissions = [Permission(p.strip()) for p in args.permissions.split(',') if p.strip()]

            role = Role(
                name=args.name.lower(),
                description=args.description,
                permissions=permissions
            )

            self.security_integration.security_manager.roles[role.name] = role

            print(f"✓ Role '{args.name}' created successfully")
            print(f"  Description: {args.description}")
            print(f"  Permissions: {', '.join([p.value for p in permissions])}")

        except Exception as e:
            print(f"✗ Failed to create role: {e}")
            sys.exit(1)

    async def list_roles(self, args):
        """List all roles"""
        try:
            roles = self.security_integration.security_manager.roles

            print("Roles:")
            print("-" * 80)
            print(f"{'Name':<20} {'Description':<30} {'Permissions':<30}")
            print("-" * 80)

            for role in roles.values():
                permissions_str = ', '.join([p.value for p in role.permissions[:3]])
                if len(role.permissions) > 3:
                    permissions_str += f" (+{len(role.permissions) - 3} more)"

                print(f"{role.name:<20} {role.description[:30]:<30} {permissions_str:<30}")

        except Exception as e:
            print(f"✗ Failed to list roles: {e}")
            sys.exit(1)

    async def update_role(self, args):
        """Update role"""
        try:
            print(f"Updating role '{args.name}'...")
            print("Role update functionality needs database integration")

        except Exception as e:
            print(f"✗ Failed to update role: {e}")
            sys.exit(1)

    async def delete_role(self, args):
        """Delete role"""
        try:
            if args.name in self.security_integration.security_manager.roles:
                del self.security_integration.security_manager.roles[args.name]
                print(f"✓ Role '{args.name}' deleted successfully")
            else:
                print(f"✗ Role '{args.name}' not found")
                sys.exit(1)

        except Exception as e:
            print(f"✗ Failed to delete role: {e}")
            sys.exit(1)

    async def audit_commands(self, args):
        """Handle audit log commands"""
        if args.action == "view":
            await self.view_audit_log(args)
        elif args.action == "export":
            await self.export_audit_log(args)
        elif args.action == "compliance":
            await self.generate_compliance_report(args)

    async def view_audit_log(self, args):
        """View audit log"""
        try:
            from core.audit_logger import AuditFilter
            from datetime import datetime, timedelta

            filter_criteria = AuditFilter()

            if args.user:
                filter_criteria.username = args.user

            if args.event_type:
                try:
                    filter_criteria.event_type = SecurityEventType(args.event_type)
                except ValueError:
                    print(f"✗ Invalid event type: {args.event_type}")
                    sys.exit(1)

            if args.hours:
                filter_criteria.start_date = datetime.utcnow() - timedelta(hours=args.hours)

            if args.limit:
                filter_criteria.limit = args.limit

            events = await self.security_integration.audit_logger.query_events(filter_criteria)

            print(f"Audit Log Events ({len(events)} found):")
            print("-" * 100)
            print(f"{'Timestamp':<20} {'User':<15} {'Event Type':<20} {'Action':<40}")
            print("-" * 100)

            for event in events[:args.limit or 50]:
                timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                username = event.username or "system"
                event_type = event.event_type.value
                action = event.action[:40] if event.action else ""

                print(f"{timestamp:<20} {username:<15} {event_type:<20} {action:<40}")

        except Exception as e:
            print(f"✗ Failed to view audit log: {e}")
            sys.exit(1)

    async def export_audit_log(self, args):
        """Export audit log"""
        try:
            output_file = await self.security_integration.audit_logger.export_audit_log(
                output_format=args.format,
                output_file=args.output
            )

            print(f"✓ Audit log exported to: {output_file}")

        except Exception as e:
            print(f"✗ Failed to export audit log: {e}")
            sys.exit(1)

    async def generate_compliance_report(self, args):
        """Generate compliance report"""
        try:
            standard = ComplianceStandard(args.standard.upper())
            period_start = datetime.utcnow() - timedelta(days=args.days)
            period_end = datetime.utcnow()

            report = await self.security_integration.generate_compliance_report(
                standard, period_start, period_end
            )

            print(f"Compliance Report - {standard.value}")
            print("=" * 50)
            print(f"Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
            print(f"Total Events: {report.total_events}")
            print(f"Security Events: {report.security_events}")
            print(f"Data Access Events: {report.data_access_events}")
            print(f"Admin Actions: {report.admin_actions}")
            print(f"Failed Authentications: {report.failed_authentications}")
            print(f"Unique Users: {report.unique_users}")
            print(f"Compliance Score: {report.compliance_score:.1f}%")

            if report.findings:
                print("\nFindings:")
                for finding in report.findings:
                    print(f"  [{finding['severity'].upper()}] {finding['category']}")
                    print(f"    {finding['description']}")
                    print(f"    Recommendation: {finding['recommendation']}")
                    print()

        except Exception as e:
            print(f"✗ Failed to generate compliance report: {e}")
            sys.exit(1)

    async def monitor_commands(self, args):
        """Handle monitoring commands"""
        if args.action == "status":
            await self.show_security_status(args)
        elif args.action == "alerts":
            await self.show_alerts(args)
        elif args.action == "metrics":
            await self.show_metrics(args)
        elif args.action == "report":
            await self.generate_security_report(args)

    async def show_security_status(self, args):
        """Show security status"""
        try:
            status = await self.security_integration.get_security_status()

            print("Security Status")
            print("=" * 50)
            print(f"Security Enabled: {status['security_enabled']}")
            print(f"Framework Status: {status['framework_status']}")
            print(f"Components Protected: {status['components_protected']}")
            print(f"Active Sessions: {status['active_sessions']}")
            print(f"Recent Threats: {status['recent_threats']}")
            print(f"System Health: {status['system_health']}")
            print(f"Last Updated: {status['last_updated']}")

        except Exception as e:
            print(f"✗ Failed to show security status: {e}")
            sys.exit(1)

    async def show_alerts(self, args):
        """Show security alerts"""
        try:
            from core.security_monitoring import AlertStatus, ThreatLevel

            alerts = self.security_integration.security_monitor.get_alerts(
                status=AlertStatus(args.status) if args.status else None,
                limit=args.limit
            )

            print(f"Security Alerts ({len(alerts)} found):")
            print("-" * 100)
            print(f"{'ID':<10} {'Severity':<10} {'Type':<20} {'Status':<12} {'Title'}")
            print("-" * 100)

            for alert in alerts:
                alert_id = alert.id[:8]
                severity = alert.severity.value
                threat_type = alert.threat_type.value
                status = alert.status.value
                title = alert.title[:50]

                print(f"{alert_id:<10} {severity:<10} {threat_type:<20} {status:<12} {title}")

        except Exception as e:
            print(f"✗ Failed to show alerts: {e}")
            sys.exit(1)

    async def show_metrics(self, args):
        """Show security metrics"""
        try:
            stats = await self.security_integration.get_security_statistics()

            print("Security Metrics")
            print("=" * 50)

            # Security Manager Stats
            sm_stats = stats["security_manager"]
            print(f"Total Users: {sm_stats['total_users']}")
            print(f"Active Users: {sm_stats['active_users']}")
            print(f"Locked Accounts: {sm_stats['locked_accounts']}")
            print(f"Failed Logins (24h): {sm_stats['failed_logins_24h']}")

            print()

            # Monitor Stats
            monitor_stats = stats["security_monitor"]
            print(f"Total Events: {monitor_stats['total_events']}")
            print(f"Total Alerts: {monitor_stats['total_alerts']}")
            print(f"Critical Alerts: {monitor_stats['critical_alerts']}")
            print(f"High Alerts: {monitor_stats['high_alerts']}")

            print()

            # Integration Stats
            print(f"Active Sessions: {stats['active_sessions']}")
            print(f"Protected Components: {stats['protected_components']}")

        except Exception as e:
            print(f"✗ Failed to show metrics: {e}")
            sys.exit(1)

    async def generate_security_report(self, args):
        """Generate security report"""
        try:
            output_file = await self.security_integration.export_security_report(
                format=args.format,
                hours=args.hours
            )

            print(f"✓ Security report exported to: {output_file}")

        except Exception as e:
            print(f"✗ Failed to generate security report: {e}")
            sys.exit(1)

    async def config_commands(self, args):
        """Handle configuration commands"""
        if args.action == "show":
            await self.show_config(args)
        elif args.action == "update":
            await self.update_config(args)
        elif args.action == "reset":
            await self.reset_config(args)

    async def show_config(self, args):
        """Show security configuration"""
        try:
            config = self.security_integration.config

            print("Security Configuration")
            print("=" * 50)

            for section, settings in config.items():
                print(f"\n[{section}]")
                for key, value in settings.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {key}: {value}")

        except Exception as e:
            print(f"✗ Failed to show configuration: {e}")
            sys.exit(1)

    async def update_config(self, args):
        """Update security configuration"""
        try:
            print(f"Updating configuration setting '{args.key}' to '{args.value}'...")
            print("Configuration update functionality needs file persistence")

        except Exception as e:
            print(f"✗ Failed to update configuration: {e}")
            sys.exit(1)

    async def reset_config(self, args):
        """Reset security configuration to defaults"""
        try:
            if args.confirm.lower() != "yes":
                print("✗ Configuration reset requires confirmation: --confirm=yes")
                sys.exit(1)

            print("Resetting configuration to defaults...")
            print("Configuration reset functionality needs file persistence")

        except Exception as e:
            print(f"✗ Failed to reset configuration: {e}")
            sys.exit(1)

    async def harden_commands(self, args):
        """Handle system hardening commands"""
        if args.action == "scan":
            await self.security_scan(args)
        elif args.action == "headers":
            await self.show_security_headers(args)
        elif args.action == "test":
            await self.security_test(args)

    async def security_scan(self, args):
        """Perform security scan"""
        try:
            print("Performing security scan...")
            print("Security scan functionality needs integration with vulnerability scanners")

        except Exception as e:
            print(f"✗ Failed to perform security scan: {e}")
            sys.exit(1)

    async def show_security_headers(self, args):
        """Show security headers"""
        try:
            headers = self.security_integration.get_security_headers()

            print("Security Headers")
            print("=" * 50)
            for header, value in headers.items():
                print(f"{header}: {value}")

        except Exception as e:
            print(f"✗ Failed to show security headers: {e}")
            sys.exit(1)

    async def security_test(self, args):
        """Test security features"""
        try:
            print("Testing security features...")

            # Test input validation
            test_result = await self.security_integration.validate_and_sanitize_input(
                "test<script>alert('xss')</script>",
                self.security_integration.auth_system.InputType.HTML
            )

            print(f"Input validation test: {'✓' if test_result.is_valid else '✗'}")
            if not test_result.is_valid:
                print(f"  Error: {test_result.error_message}")

            # Test rate limiting
            rate_limit_result = self.security_integration.security_hardening.check_rate_limit("test_user")
            print(f"Rate limiting test: {'✓' if rate_limit_result else '✗'}")

            print("Security tests completed")

        except Exception as e:
            print(f"✗ Failed to test security features: {e}")
            sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="DuckBot Security Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # User management commands
    user_parser = subparsers.add_parser('user', help='User management')
    user_subparsers = user_parser.add_subparsers(dest='action', help='User actions')

    user_create = user_subparsers.add_parser('create', help='Create new user')
    user_create.add_argument('--username', required=True, help='Username')
    user_create.add_argument('--email', required=True, help='Email address')
    user_create.add_argument('--password', required=True, help='Password')
    user_create.add_argument('--roles', help='Comma-separated list of roles')

    user_list = user_subparsers.add_parser('list', help='List users')

    user_update = user_subparsers.add_parser('update', help='Update user')
    user_update.add_argument('--username', required=True, help='Username')
    user_update.add_argument('--email', help='New email address')
    user_update.add_argument('--roles', help='Comma-separated list of roles')

    user_delete = user_subparsers.add_parser('delete', help='Delete user')
    user_delete.add_argument('--username', required=True, help='Username')

    user_password = user_subparsers.add_parser('reset-password', help='Reset user password')
    user_password.add_argument('--user-id', required=True, help='User ID')
    user_password.add_argument('--current-password', required=True, help='Current password')
    user_password.add_argument('--new-password', required=True, help='New password')

    user_mfa_enable = user_subparsers.add_parser('enable-mfa', help='Enable MFA for user')
    user_mfa_enable.add_argument('--user-id', required=True, help='User ID')

    user_mfa_disable = user_subparsers.add_parser('disable-mfa', help='Disable MFA for user')
    user_mfa_disable.add_argument('--user-id', required=True, help='User ID')
    user_mfa_disable.add_argument('--password', required=True, help='User password')

    # Role management commands
    role_parser = subparsers.add_parser('role', help='Role management')
    role_subparsers = role_parser.add_subparsers(dest='action', help='Role actions')

    role_create = role_subparsers.add_parser('create', help='Create new role')
    role_create.add_argument('--name', required=True, help='Role name')
    role_create.add_argument('--description', required=True, help='Role description')
    role_create.add_argument('--permissions', required=True, help='Comma-separated list of permissions')

    role_list = role_subparsers.add_parser('list', help='List roles')

    role_update = role_subparsers.add_parser('update', help='Update role')
    role_update.add_argument('--name', required=True, help='Role name')
    role_update.add_argument('--description', help='New description')
    role_update.add_argument('--permissions', help='Comma-separated list of permissions')

    role_delete = role_subparsers.add_parser('delete', help='Delete role')
    role_delete.add_argument('--name', required=True, help='Role name')

    # Audit commands
    audit_parser = subparsers.add_parser('audit', help='Audit logging')
    audit_subparsers = audit_parser.add_subparsers(dest='action', help='Audit actions')

    audit_view = audit_subparsers.add_parser('view', help='View audit log')
    audit_view.add_argument('--user', help='Filter by username')
    audit_view.add_argument('--event-type', help='Filter by event type')
    audit_view.add_argument('--hours', type=int, help='Show events from last N hours')
    audit_view.add_argument('--limit', type=int, default=50, help='Limit number of events')

    audit_export = audit_subparsers.add_parser('export', help='Export audit log')
    audit_export.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    audit_export.add_argument('--output', help='Output file path')

    audit_compliance = audit_subparsers.add_parser('compliance', help='Generate compliance report')
    audit_compliance.add_argument('--standard', choices=['GDPR', 'HIPAA', 'PCI_DSS', 'SOX', 'ISO27001', 'NIST'], required=True, help='Compliance standard')
    audit_compliance.add_argument('--days', type=int, default=30, help='Number of days to analyze')

    # Monitoring commands
    monitor_parser = subparsers.add_parser('monitor', help='Security monitoring')
    monitor_subparsers = monitor_parser.add_subparsers(dest='action', help='Monitoring actions')

    monitor_status = monitor_subparsers.add_parser('status', help='Show security status')

    monitor_alerts = monitor_subparsers.add_parser('alerts', help='Show security alerts')
    monitor_alerts.add_argument('--status', choices=['open', 'investigating', 'resolved'], help='Filter by status')
    monitor_alerts.add_argument('--limit', type=int, default=20, help='Limit number of alerts')

    monitor_metrics = monitor_subparsers.add_parser('metrics', help='Show security metrics')

    monitor_report = monitor_subparsers.add_parser('report', help='Generate security report')
    monitor_report.add_argument('--format', choices=['json', 'csv'], default='json', help='Report format')
    monitor_report.add_argument('--hours', type=int, default=24, help='Number of hours to analyze')

    # Configuration commands
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='action', help='Configuration actions')

    config_show = config_subparsers.add_parser('show', help='Show current configuration')

    config_update = config_subparsers.add_parser('update', help='Update configuration')
    config_update.add_argument('--key', required=True, help='Configuration key')
    config_update.add_argument('--value', required=True, help='Configuration value')

    config_reset = config_subparsers.add_parser('reset', help='Reset configuration to defaults')
    config_reset.add_argument('--confirm', required=True, help='Confirm reset (must be "yes")')

    # Hardening commands
    harden_parser = subparsers.add_parser('harden', help='System hardening')
    harden_subparsers = harden_parser.add_subparsers(dest='action', help='Hardening actions')

    harden_scan = harden_subparsers.add_parser('scan', help='Perform security scan')

    harden_headers = harden_subparsers.add_parser('headers', help='Show security headers')

    harden_test = harden_subparsers.add_parser('test', help='Test security features')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create CLI instance and run command
    cli = SecurityManagerCLI()

    async def run_command():
        await cli.initialize()

        if args.command == 'user':
            await cli.user_commands(args)
        elif args.command == 'role':
            await cli.role_commands(args)
        elif args.command == 'audit':
            await cli.audit_commands(args)
        elif args.command == 'monitor':
            await cli.monitor_commands(args)
        elif args.command == 'config':
            await cli.config_commands(args)
        elif args.command == 'harden':
            await cli.harden_commands(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)

    # Run the command
    asyncio.run(run_command())

if __name__ == '__main__':
    main()