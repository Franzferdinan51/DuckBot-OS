#!/usr/bin/env python3
"""
DuckBot Monitoring System Startup Script
Launches the comprehensive monitoring system with dashboard
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import monitoring components
from duckbot.core.monitoring_system import (
    get_monitoring, start_monitoring, stop_monitoring, DuckBotMonitoring
)
from duckbot.services.enhanced_monitoring_dashboard import EnhancedMonitoringDashboard
from duckbot.analytics.monitoring_analytics import get_analytics
from duckbot.integrations.monitoring_integration import get_monitoring_integration
# from duckbot.core.logging_setup import setup_logging

# Simple logging setup
def setup_logging(level=logging.INFO):
    """Setup basic logging"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('monitoring.log')
        ]
    )

# Global variables
monitoring_instance = None
dashboard_instance = None
analytics_instance = None
running = True

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        global running
        print(f"\nReceived signal {signum}, shutting down...")
        running = False
        cleanup()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def cleanup():
    """Clean up resources"""
    global monitoring_instance, dashboard_instance

    print("Cleaning up monitoring system...")

    try:
        # Stop monitoring
        if monitoring_instance:
            monitoring_instance.stop()
            print("✅ Monitoring stopped")

        # Dashboard will be stopped automatically when the process ends
        if dashboard_instance:
            print("✅ Dashboard cleanup initiated")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def start_background_monitoring(metrics_interval: float = 5.0, health_check_interval: float = 30.0):
    """Start background monitoring"""
    global monitoring_instance

    try:
        print("🚀 Starting background monitoring system...")
        monitoring_instance = start_monitoring(metrics_interval, health_check_interval)
        print(f"✅ Background monitoring started (metrics: {metrics_interval}s, health: {health_check_interval}s)")

        # Record startup event
        monitoring_instance.record_agent_interaction(
            agent_id="monitoring_system",
            agent_type="system_startup",
            response_time_ms=0,
            success=True,
            model_used="monitoring_core",
            tokens_used=0
        )

        return monitoring_instance

    except Exception as e:
        print(f"❌ Failed to start background monitoring: {e}")
        return None

def start_dashboard(host: str = "127.0.0.1", port: int = 8790):
    """Start monitoring dashboard"""
    global dashboard_instance

    try:
        print(f"🚀 Starting monitoring dashboard on {host}:{port}...")
        dashboard_instance = EnhancedMonitoringDashboard(host=host, port=port)

        # Start dashboard in a separate thread to keep the main thread responsive
        import threading
        dashboard_thread = threading.Thread(
            target=dashboard_instance.start,
            daemon=True
        )
        dashboard_thread.start()
        print(f"✅ Dashboard started on http://{host}:{port}")

        # Record dashboard startup event
        if monitoring_instance:
            monitoring_instance.record_agent_interaction(
                agent_id="monitoring_dashboard",
                agent_type="dashboard_startup",
                response_time_ms=0,
                success=True,
                model_used="web_ui",
                tokens_used=0
            )

        return dashboard_instance

    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None

def generate_startup_report():
    """Generate and display startup report"""
    global analytics_instance

    try:
        print("\n📊 Generating startup report...")
        analytics_instance = get_analytics()

        # Get system status
        if monitoring_instance:
            status = monitoring_instance.get_system_status()
            print("\n📈 System Status:")
            print(f"  CPU Usage: {status.get('system_metrics', {}).get('cpu_percent', 0):.1f}%")
            print(f"  Memory Usage: {status.get('system_metrics', {}).get('memory_percent', 0):.1f}%")
            print(f"  Disk Usage: {status.get('system_metrics', {}).get('disk_percent', 0):.1f}%")
            print(f"  Active Alerts: {status.get('alerts', {}).get('total_active', 0)}")

        # Get recent activity
        activity_summary = analytics_instance.get_user_activity_report(AnalyticsPeriod.HOUR)
        print(f"\n📊 Recent Activity (Last Hour):")
        print(f"  Total Activities: {activity_summary.get('total_activities', 0)}")
        print(f"  Avg Response Time: {activity_summary.get('avg_response_time', 0):.1f}ms")
        print(f"  Avg Satisfaction: {activity_summary.get('avg_satisfaction', 0):.1f}/5")

        print("\n✅ Startup report completed")

    except Exception as e:
        print(f"❌ Error generating startup report: {e}")

def run_monitoring_cli():
    """Run monitoring CLI interface"""
    global running

    print("\n🎯 DuckBot Monitoring System CLI")
    print("Commands:")
    print("  status    - Show system status")
    print("  alerts    - Show active alerts")
    print("  services  - Show service status")
    print("  agents    - Show agent performance")
    print("  activity  - Show user activity")
    print("  export    - Export data")
    print("  report    - Generate report")
    print("  help      - Show this help")
    print("  quit/exit - Exit monitoring system")

    while running:
        try:
            command = input("\n🔧 monitoring> ").strip().lower()

            if command in ["quit", "exit"]:
                running = False
                break
            elif command == "status":
                show_system_status()
            elif command == "alerts":
                show_active_alerts()
            elif command == "services":
                show_service_status()
            elif command == "agents":
                show_agent_performance()
            elif command == "activity":
                show_user_activity()
            elif command == "export":
                export_data_cli()
            elif command == "report":
                generate_report_cli()
            elif command == "help":
                show_help()
            elif command == "":
                continue
            else:
                print(f"❓ Unknown command: {command}")
                print("   Type 'help' for available commands")

        except KeyboardInterrupt:
            running = False
            break
        except EOFError:
            running = False
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def show_system_status():
    """Show current system status"""
    try:
        if monitoring_instance:
            status = monitoring_instance.get_system_status()
            print("\n📊 System Status:")
            print(f"  Timestamp: {status.get('timestamp', 'N/A')}")
            print(f"  CPU Usage: {status.get('system_metrics', {}).get('cpu_percent', 0):.1f}%")
            print(f"  Memory Usage: {status.get('system_metrics', {}).get('memory_percent', 0):.1f}%")
            print(f"  Disk Usage: {status.get('system_metrics', {}).get('disk_percent', 0):.1f}%")
            print(f"  Active Processes: {status.get('system_metrics', {}).get('active_processes', 0)}")
            print(f"  Active Alerts: {status.get('alerts', {}).get('total_active', 0)}")
        else:
            print("❌ Monitoring system not available")
    except Exception as e:
        print(f"❌ Error getting system status: {e}")

def show_active_alerts():
    """Show active alerts"""
    try:
        if monitoring_instance:
            alerts = monitoring_instance.database.get_active_alerts()
            print(f"\n🚨 Active Alerts ({len(alerts)}):")
            if alerts:
                for alert in alerts:
                    print(f"  [{alert['level'].upper()}] {alert['title']}: {alert['message']}")
                    print(f"    Source: {alert['source']} | Time: {alert['timestamp']}")
            else:
                print("  ✅ No active alerts")
        else:
            print("❌ Monitoring system not available")
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")

def show_service_status():
    """Show service status"""
    try:
        from duckbot.services.server_manager import server_manager

        services = server_manager.get_all_service_status()
        print(f"\n🔧 Service Status ({len(services)} services):")

        for name, service in services.items():
            status_icon = "🟢" if service.status.value == "running" else "🔴"
            print(f"  {status_icon} {service.display_name} ({name})")
            print(f"     Status: {service.status.value}")
            if service.port:
                print(f"     Port: {service.port}")
            if service.url:
                print(f"     URL: {service.url}")
            print()

    except Exception as e:
        print(f"❌ Error getting service status: {e}")

def show_agent_performance():
    """Show agent performance"""
    try:
        if monitoring_instance:
            performance = monitoring_instance.agent_monitor.get_agent_performance_summary()
            print(f"\n🤖 Agent Performance ({len(performance)} agents):")

            for agent_id, metrics in performance.items():
                success_rate = (metrics.get('successful_requests', 0) /
                              max(metrics.get('total_requests', 1), 1)) * 100
                print(f"  📊 {agent_id}")
                print(f"     Requests: {metrics.get('total_requests', 0)}")
                print(f"     Success Rate: {success_rate:.1f}%")
                print(f"     Avg Response Time: {metrics.get('avg_response_time', 0):.1f}ms")
                print(f"     Total Tokens: {metrics.get('total_tokens', 0)}")
                print()

        else:
            print("❌ Monitoring system not available")
    except Exception as e:
        print(f"❌ Error getting agent performance: {e}")

def show_user_activity():
    """Show user activity"""
    try:
        if analytics_instance:
            activity = analytics_instance.get_user_activity_report(AnalyticsPeriod.HOUR)
            print(f"\n👥 User Activity (Last Hour):")
            print(f"  Total Activities: {activity.get('total_activities', 0)}")
            print(f"  Avg Response Time: {activity.get('avg_response_time', 0):.1f}ms")
            print(f"  Avg Satisfaction: {activity.get('avg_satisfaction', 0):.1f}/5")

            if activity.get('by_activity_type'):
                print("  Activity Types:")
                for activity_type, count in activity['by_activity_type'].items():
                    print(f"    {activity_type}: {count}")

            if activity.get('by_feature'):
                print("  Feature Usage:")
                for feature, count in activity['by_feature'].items():
                    print(f"    {feature}: {count}")

        else:
            print("❌ Analytics system not available")
    except Exception as e:
        print(f"❌ Error getting user activity: {e}")

def export_data_cli():
    """Export data through CLI"""
    try:
        if not analytics_instance:
            print("❌ Analytics system not available")
            return

        print("\n💾 Export Data")
        print("Available data types:")
        print("  1. System Metrics")
        print("  2. Agent Metrics")
        print("  3. Alerts")

        data_type_choice = input("Select data type (1-3): ").strip()

        data_types = {
            "1": "system_metrics",
            "2": "agent_metrics",
            "3": "alerts"
        }

        if data_type_choice not in data_types:
            print("❌ Invalid choice")
            return

        data_type = data_types[data_type_choice]

        print("Available periods:")
        print("  1. Last Hour")
        print("  2. Last Day")
        print("  3. Last Week")

        period_choice = input("Select period (1-3): ").strip()

        periods = {
            "1": AnalyticsPeriod.HOUR,
            "2": AnalyticsPeriod.DAY,
            "3": AnalyticsPeriod.WEEK
        }

        if period_choice not in periods:
            print("❌ Invalid choice")
            return

        period = periods[period_choice]

        print("Available formats:")
        print("  1. CSV")
        print("  2. JSON")
        print("  3. Excel")

        format_choice = input("Select format (1-3): ").strip()

        formats = {
            "1": ReportFormat.CSV,
            "2": ReportFormat.JSON,
            "3": ReportFormat.EXCEL
        }

        if format_choice not in formats:
            print("❌ Invalid choice")
            return

        format_type = formats[format_choice]

        print(f"Exporting {data_type} for {period.value} as {format_type.value}...")

        export_path = analytics_instance.export_data(data_type, period, format_type)
        print(f"✅ Data exported to: {export_path}")

    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def generate_report_cli():
    """Generate report through CLI"""
    try:
        if not analytics_instance:
            print("❌ Analytics system not available")
            return

        print("\n📊 Generate Report")
        print("Available periods:")
        print("  1. Last Hour")
        print("  2. Last Day")
        print("  3. Last Week")

        period_choice = input("Select period (1-3): ").strip()

        periods = {
            "1": AnalyticsPeriod.HOUR,
            "2": AnalyticsPeriod.DAY,
            "3": AnalyticsPeriod.WEEK
        }

        if period_choice not in periods:
            print("❌ Invalid choice")
            return

        period = periods[period_choice]

        print(f"Generating report for {period.value}...")

        report_path = analytics_instance.generate_report(period)
        print(f"✅ Report generated: {report_path}")

    except Exception as e:
        print(f"❌ Error generating report: {e}")

def show_help():
    """Show help information"""
    print("\n📚 DuckBot Monitoring System Help")
    print("=====================================")
    print("This monitoring system provides comprehensive real-time monitoring")
    print("and analytics for DuckBot components.")
    print()
    print("Features:")
    print("  • Real-time system metrics collection")
    print("  • AI agent performance monitoring")
    print("  • Service health monitoring")
    print("  • User activity analytics")
    print("  • Alert management and notifications")
    print("  • Data export and reporting")
    print("  • Web-based dashboard")
    print()
    print("Dashboard Access:")
    print("  • Open http://localhost:8790 in your web browser")
    print("  • Real-time metrics and charts")
    print("  • Service control interface")
    print("  • Alert management")
    print()
    print("API Access:")
    print("  • System status: GET /api/status")
    print("  • Metrics: GET /api/metrics/system")
    print("  • Services: GET /api/services")
    print("  • Alerts: GET /api/alerts")
    print("  • Activity: GET /api/activity")
    print()
    print("Configuration:")
    print("  • Database: monitoring.db (SQLite)")
    print("  • Export directory: exports/")
    print("  • Report directory: reports/")
    print("  • Log files: Check logs/ directory")

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(
        description="DuckBot Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_monitoring_system.py                    # Start with defaults
  python start_monitoring_system.py --cli              # CLI mode only
  python start_monitoring_system.py --host 0.0.0.0     # Listen on all interfaces
  python start_monitoring_system.py --port 8800       # Use custom port
  python start_monitoring_system.py --metrics 2       # Faster metrics collection
  python start_monitoring_system.py --debug            # Enable debug logging
        """
    )

    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8790, help="Dashboard port (default: 8790)")
    parser.add_argument("--metrics-interval", type=float, default=5.0, help="Metrics collection interval in seconds (default: 5.0)")
    parser.add_argument("--health-interval", type=float, default=30.0, help="Health check interval in seconds (default: 30.0)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode only (no dashboard)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-dashboard", action="store_true", help="Don't start web dashboard")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)

    # Setup signal handlers
    setup_signal_handlers()

    print("🚀 Starting DuckBot Monitoring System")
    print("=" * 50)

    # Start background monitoring
    monitoring_instance = start_background_monitoring(
        metrics_interval=args.metrics_interval,
        health_check_interval=args.health_interval
    )

    if not monitoring_instance:
        print("❌ Failed to start monitoring system")
        sys.exit(1)

    # Start dashboard if requested
    if not args.cli and not args.no_dashboard:
        dashboard_instance = start_dashboard(host=args.host, port=args.port)
        if not dashboard_instance:
            print("⚠️  Dashboard failed to start, but monitoring continues")

    # Generate startup report
    generate_startup_report()

    # Show access information
    if not args.cli:
        print(f"\n🌐 Dashboard Access:")
        print(f"   URL: http://{args.host}:{args.port}")
        print(f"   API: http://{args.host}:{args.port}/api/status")
        print()

    print("🎯 Monitoring system is now running!")
    print("   Use Ctrl+C to stop")

    try:
        if args.cli:
            # Run CLI interface
            run_monitoring_cli()
        else:
            # Keep running until signal received
            while running:
                time.sleep(1)

    except KeyboardInterrupt:
        running = False
    finally:
        cleanup()

    print("\n👋 DuckBot Monitoring System stopped")

if __name__ == "__main__":
    main()