#!/usr/bin/env python3
"""
DuckBot Health Maintenance System Launcher
Standalone launcher for health checks and predictive maintenance
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Local imports
from duckbot.integrations.health_maintenance_integration import (
    HealthMaintenanceIntegration, health_maintenance_integration,
    HealthMaintenanceHooks, start_health_maintenance_standalone
)
from duckbot.core.health_predictive_maintenance import (
    HealthMaintenanceManager, health_maintenance_manager
)
from duckbot.core.health_analytics_dashboard import health_dashboard_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_maintenance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class HealthMaintenanceLauncher:
    """Main launcher for health maintenance system"""

    def __init__(self):
        self.integration = health_maintenance_integration
        self.args = None

    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description='DuckBot Health Maintenance System',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python start_health_maintenance.py --standalone
  python start_health_maintenance.py --check
  python start_health_maintenance.py --dashboard
  python start_health_maintenance.py --maintenance
  python start_health_maintenance.py --predictions
  python start_health_maintenance.py --trends day
            """
        )

        parser.add_argument(
            '--standalone', '-s',
            action='store_true',
            help='Run in standalone mode (continuous operation)'
        )

        parser.add_argument(
            '--check', '-c',
            action='store_true',
            help='Run immediate health check'
        )

        parser.add_argument(
            '--dashboard', '-d',
            action='store_true',
            help='Show system health dashboard'
        )

        parser.add_argument(
            '--maintenance', '-m',
            action='store_true',
            help='Show maintenance recommendations'
        )

        parser.add_argument(
            '--predictions', '-p',
            action='store_true',
            help='Show prediction insights'
        )

        parser.add_argument(
            '--trends', '-t',
            choices=['hour', 'day', 'week', 'month'],
            help='Show health trends for specified timeframe'
        )

        parser.add_argument(
            '--analytics', '-a',
            choices=['hour', 'day', 'week', 'month'],
            help='Show analytics report for specified timeframe'
        )

        parser.add_argument(
            '--config',
            help='Configuration file path'
        )

        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )

        parser.add_argument(
            '--web-port',
            type=int,
            default=8790,
            help='Web dashboard port (default: 8790)'
        )

        self.args = parser.parse_args()

        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    async def run_standalone_mode(self):
        """Run in standalone mode"""
        print("🚀 Starting DuckBot Health Maintenance System (Standalone Mode)")
        print("=" * 60)

        # Initialize integration
        success = await self.integration.initialize_integration()
        if not success:
            print("❌ Failed to initialize Health Maintenance System")
            return

        print("✅ Health Maintenance System initialized successfully")
        print("📊 Dashboard available at: http://localhost:{}".format(self.args.web_port))
        print("⏰ Running continuous health monitoring...")
        print("Press Ctrl+C to stop")

        try:
            # Keep running with periodic status updates
            while True:
                await asyncio.sleep(300)  # 5 minutes
                status = self.integration.get_integration_status()
                print(f"🟢 System healthy - Uptime: {status['statistics']['system_uptime']:.0f}s")

        except KeyboardInterrupt:
            print("\n🛑 Stopping Health Maintenance System...")
            await self.integration.shutdown_integration()
            print("✅ Health Maintenance System stopped")

    async def run_health_check(self):
        """Run immediate health check"""
        print("🔍 Running Comprehensive Health Check...")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            results = await self.integration.run_comprehensive_health_check()

            if 'error' in results:
                print(f"❌ Error: {results['error']}")
                return

            print(f"📊 Overall Health Score: {results['overall_score']:.2%}")
            print(f"⏰ Check Time: {results['timestamp']}")
            print(f"🚨 Action Required: {'Yes' if results['action_required'] else 'No'}")

            print("\n📋 Component Results:")
            for component, data in results['component_results'].items():
                status_icon = "✅" if data['score'] > 0.8 else "⚠️" if data['score'] > 0.5 else "❌"
                print(f"  {status_icon} {component}: {data['score']:.2%} ({data['status']})")

            if results['recommendations']:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(results['recommendations'], 1):
                    print(f"  {i}. {rec}")

        finally:
            await self.integration.shutdown_integration()

    async def show_dashboard(self):
        """Show system health dashboard"""
        print("📊 System Health Dashboard")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            dashboard = await self.integration.get_system_health_dashboard()

            if 'error' in dashboard:
                print(f"❌ Error: {dashboard['error']}")
                return

            # System Overview
            health_summary = dashboard.get('health_summary', {})
            print(f"🏥 Overall Health: {health_summary.get('overall_status', 'Unknown').upper()}")
            print(f"📈 Health Score: {health_summary.get('overall_score', 0):.2%}")
            print(f"🔧 Components: {health_summary.get('total_components', 0)} total")
            print(f"✅ Healthy: {health_summary.get('healthy_components', 0)}")
            print(f"⚠️  Degraded: {health_summary.get('degraded_components', 0)}")
            print(f"❌ Unhealthy: {health_summary.get('unhealthy_components', 0)}")
            print(f"🚨 Critical Issues: {health_summary.get('critical_issues', 0)}")

            # Real-time Metrics
            print(f"\n📊 Real-time Metrics:")
            metrics = dashboard.get('real_time_metrics', [])
            for metric in metrics:
                trend_icon = "📈" if metric.get('trend', 0) > 0 else "📉" if metric.get('trend', 0) < 0 else "➡️"
                print(f"  {metric.get('name', 'Unknown')}: {metric.get('current_value', 0):.1f}{metric.get('unit', '')} {trend_icon}")

            # Predictions
            predictions = dashboard.get('prediction_insights', {})
            print(f"\n🔮 Predictions:")
            print(f"  Total Predictions: {predictions.get('total_predictions', 0)}")
            print(f"  High Risk: {predictions.get('high_risk_predictions', 0)}")
            if predictions.get('urgent_actions'):
                print(f"  Urgent Actions: {len(predictions['urgent_actions'])}")

            # Maintenance
            maintenance = dashboard.get('maintenance_dashboard', {})
            print(f"\n🔧 Maintenance:")
            print(f"  Pending Actions: {maintenance.get('pending_actions', 0)}")
            print(f"  Automation: {'✅ Active' if maintenance.get('automation_status') else '❌ Inactive'}")

        finally:
            await self.integration.shutdown_integration()

    async def show_maintenance_recommendations(self):
        """Show maintenance recommendations"""
        print("🔧 Maintenance Recommendations")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            recommendations = await self.integration.get_maintenance_recommendations()

            if 'error' in recommendations:
                print(f"❌ Error: {recommendations['error']}")
                return

            # Predictions
            predictions = recommendations.get('predictions', [])
            print(f"🔮 Recent Predictions ({len(predictions)}):")
            for pred in predictions[:5]:  # Show top 5
                print(f"  • {pred.get('component', 'Unknown')}: {pred.get('prediction_type', 'Unknown')} "
                      f"({pred.get('probability', 0):.1%} confidence)")

            # Pending Maintenance
            pending = recommendations.get('pending_maintenance', [])
            print(f"\n⏳ Pending Maintenance ({len(pending)}):")
            for action in pending[:5]:  # Show top 5
                print(f"  • {action.get('name', 'Unknown')} ({action.get('priority', 'low')} priority)")

            # Analytics Insights
            analytics = recommendations.get('analytics_insights', {})
            if analytics.get('recommendations'):
                print(f"\n💡 Analytics Recommendations:")
                for i, rec in enumerate(analytics['recommendations'][:3], 1):
                    print(f"  {i}. {rec}")

            # Automation Status
            automation = recommendations.get('automation_status', {})
            print(f"\n🤖 Automation Status:")
            print(f"  Active: {'✅' if automation.get('active') else '❌'}")
            print(f"  Completed Actions: {automation.get('completed_actions', 0)}")

        finally:
            await self.integration.shutdown_integration()

    async def show_predictions(self):
        """Show prediction insights"""
        print("🔮 Prediction Insights")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            insights = await self.integration.get_maintenance_recommendations()

            if 'error' in insights:
                print(f"❌ Error: {insights['error']}")
                return

            predictions = insights.get('predictions', [])
            if not predictions:
                print("✅ No high-risk predictions detected")
                return

            print(f"📊 Found {len(predictions)} predictions:")

            # Group by risk level
            high_risk = [p for p in predictions if p.get('probability', 0) > 0.8]
            medium_risk = [p for p in predictions if 0.5 < p.get('probability', 0) <= 0.8]
            low_risk = [p for p in predictions if p.get('probability', 0) <= 0.5]

            if high_risk:
                print(f"\n🚨 HIGH RISK PREDICTIONS ({len(high_risk)}):")
                for pred in high_risk:
                    print(f"  • {pred.get('component', 'Unknown')}")
                    print(f"    Type: {pred.get('prediction_type', 'Unknown')}")
                    print(f"    Probability: {pred.get('probability', 0):.1%}")
                    print(f"    Timeframe: {pred.get('timeframe', 'Unknown')}")
                    print(f"    Recommended Actions:")
                    for action in json.loads(pred.get('recommended_actions', '[]')):
                        print(f"      - {action}")
                    print()

            if medium_risk:
                print(f"⚠️  MEDIUM RISK PREDICTIONS ({len(medium_risk)}):")
                for pred in medium_risk[:5]:  # Show first 5
                    print(f"  • {pred.get('component', 'Unknown')}: {pred.get('prediction_type', 'Unknown')} "
                          f"({pred.get('probability', 0):.1%})")

            if low_risk:
                print(f"ℹ️  LOW RISK PREDICTIONS ({len(low_risk)}):")
                for pred in low_risk[:3]:  # Show first 3
                    print(f"  • {pred.get('component', 'Unknown')}: {pred.get('prediction_type', 'Unknown')} "
                          f"({pred.get('probability', 0):.1%})")

        finally:
            await self.integration.shutdown_integration()

    async def show_trends(self, timeframe: str):
        """Show health trends"""
        print(f"📈 Health Trends - {timeframe.upper()}")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            trends = await self.integration.get_health_trends(timeframe)

            if 'error' in trends:
                print(f"❌ Error: {trends['error']}")
                return

            print(f"Timeframe: {trends.get('timeframe', timeframe)}")
            print()

            trends_data = trends.get('trends', {})
            if not trends_data:
                print("No trend data available for this timeframe")
                return

            for component, trend_data in trends_data.items():
                if trend_data:
                    current = trend_data[-1] if trend_data else 0
                    previous = trend_data[0] if len(trend_data) > 1 else current
                    change = current - previous
                    change_pct = (change / previous * 100) if previous > 0 else 0

                    trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    print(f"{trend_icon} {component}:")
                    print(f"    Current: {current:.2%}")
                    print(f"    Change: {change:+.2%} ({change_pct:+.1f}%)")
                    print(f"    Data Points: {len(trend_data)}")
                    print()

        finally:
            await self.integration.shutdown_integration()

    async def show_analytics(self, timeframe: str):
        """Show analytics report"""
        print(f"📊 Analytics Report - {timeframe.upper()}")
        print("=" * 50)

        # Initialize temporarily
        await self.integration.initialize_integration()

        try:
            report = await self.integration.get_analytics_report(timeframe)

            if 'error' in report:
                print(f"❌ Error: {report['error']}")
                return

            print(f"Generated: {report.get('generated_at', 'Unknown')}")
            print(f"Timeframe: {report.get('timeframe', timeframe)}")
            print()

            # Health Score Trend
            health_trend = report.get('health_score_trend', [])
            if health_trend:
                current = health_trend[-1] if health_trend else 0
                previous = health_trend[0] if len(health_trend) > 1 else current
                change = current - previous

                print(f"📈 Health Score Trend:")
                print(f"    Current: {current:.2%}")
                print(f"    Change: {change:+.2%}")
                print(f"    Data Points: {len(health_trend)}")
                print()

            # Component Performance
            component_perf = report.get('component_performance', {})
            if component_perf:
                print(f"⚙️  Component Performance:")
                for component, score in sorted(component_perf.items(), key=lambda x: x[1]):
                    status = "✅" if score > 0.8 else "⚠️" if score > 0.6 else "❌"
                    print(f"    {status} {component}: {score:.2%}")
                print()

            # Recommendations
            recommendations = report.get('recommendations', [])
            if recommendations:
                print(f"💡 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"    {i}. {rec}")
                print()

            # Key Insights
            insights = report.get('key_insights', [])
            if insights:
                print(f"🔍 Key Insights:")
                for insight in insights:
                    print(f"    • {insight}")

        finally:
            await self.integration.shutdown_integration()

    async def run(self):
        """Main entry point"""
        self.parse_arguments()

        try:
            if self.args.standalone:
                await self.run_standalone_mode()
            elif self.args.check:
                await self.run_health_check()
            elif self.args.dashboard:
                await self.show_dashboard()
            elif self.args.maintenance:
                await self.show_maintenance_recommendations()
            elif self.args.predictions:
                await self.show_predictions()
            elif self.args.trends:
                await self.show_trends(self.args.trends)
            elif self.args.analytics:
                await self.show_analytics(self.args.analytics)
            else:
                print("🤖 DuckBot Health Maintenance System")
                print("=" * 50)
                print("Use --help for available options")
                print("\nQuick commands:")
                print("  --check         Run immediate health check")
                print("  --dashboard     Show health dashboard")
                print("  --maintenance   Show maintenance recommendations")
                print("  --predictions   Show prediction insights")
                print("  --trends day   Show health trends")
                print("  --standalone    Run continuous monitoring")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"Launcher error: {e}")
            print(f"❌ Error: {e}")

async def main():
    """Main function"""
    launcher = HealthMaintenanceLauncher()
    await launcher.run()

if __name__ == "__main__":
    asyncio.run(main())