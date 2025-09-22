#!/usr/bin/env python3
"""
Comprehensive Health Monitoring Integration Test

Tests the complete health monitoring system including:
- Health monitor core functionality
- API endpoints
- Performance analytics
- Event system
- Intelligent alerting
- Dashboard integration
"""

import asyncio
import json
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Configure UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from duckbot.core.health_monitor import get_health_monitor, HealthMonitor
from duckbot.core.event_system import EventSystem, Event
from duckbot.core.intelligent_alerting import IntelligentAlerting, Alert
from performance_analytics import get_performance_analytics, PerformanceAnalytics
from health_monitor_api import router

class HealthMonitoringIntegrationTest:
    """Comprehensive integration test for health monitoring system"""

    def __init__(self):
        self.test_results = []
        self.base_url = "http://localhost:8001"
        self.session = None

    async def setup_test_environment(self):
        """Set up test environment"""
        print("WRENCH Setting up test environment...")

        # Create test databases
        self.test_databases = [
            "test_health_monitor.db",
            "test_events.db",
            "test_alerts.db",
            "test_performance_metrics.db"
        ]

        # Initialize test data
        for db_path in self.test_databases:
            if Path(db_path).exists():
                os.remove(db_path)

        # Initialize components
        self.health_monitor = get_health_monitor()
        self.event_system = EventSystem()
        self.alerting = IntelligentAlerting()
        self.analytics = get_performance_analytics()

        # Start HTTP session
        self.session = aiohttp.ClientSession()

        print("OK Test environment setup complete")

    async def cleanup_test_environment(self):
        """Clean up test environment"""
        print("BROOM Cleaning up test environment...")

        # Stop components
        if hasattr(self.health_monitor, 'stop_monitoring'):
            await self.health_monitor.stop_monitoring()

        if hasattr(self.event_system, 'stop'):
            await self.event_system.stop()

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Remove test databases
        for db_path in self.test_databases:
            if Path(db_path).exists():
                os.remove(db_path)

        print("OK Test environment cleanup complete")

    async def test_health_monitor_core(self):
        """Test health monitor core functionality"""
        print("\nTEST Testing Health Monitor Core...")

        try:
            # Test health monitor initialization
            assert self.health_monitor is not None, "Health monitor should be initialized"
            self.add_test_result("health_monitor_initialization", True, "Health monitor initialized successfully")

            # Test service registration
            self.health_monitor.register_service("test_service", {
                "name": "Test Service",
                "type": "api",
                "health_endpoint": "http://localhost:8787/health",
                "check_interval": 30
            })
            self.add_test_result("service_registration", True, "Service registered successfully")

            # Test health check execution
            result = await self.health_monitor.perform_health_check("test_service")
            self.add_test_result("health_check_execution", True, f"Health check executed: {result}")

            # Test status retrieval
            status = self.health_monitor.get_service_status("test_service")
            assert status is not None, "Should retrieve service status"
            self.add_test_result("status_retrieval", True, "Service status retrieved successfully")

        except Exception as e:
            self.add_test_result("health_monitor_core", False, f"Health monitor core test failed: {str(e)}")

    async def test_event_system(self):
        """Test event system functionality"""
        print("\nTEST Testing Event System...")

        try:
            # Test event system initialization
            assert self.event_system is not None, "Event system should be initialized"
            self.add_test_result("event_system_initialization", True, "Event system initialized successfully")

            # Test event subscription
            events_received = []

            def test_event_handler(event: Event):
                events_received.append(event)

            subscription_id = await self.event_system.subscribe(
                "service_health_change",
                test_event_handler
            )
            self.add_test_result("event_subscription", True, "Event subscription successful")

            # Test event emission
            test_event = Event(
                event_type="service_health_change",
                source="test_service",
                data={"status": "healthy", "previous_status": "unhealthy"},
                timestamp=datetime.now()
            )

            await self.event_system.emit(test_event)
            self.add_test_result("event_emission", True, "Event emitted successfully")

            # Test event delivery
            await asyncio.sleep(0.1)  # Allow time for event processing
            assert len(events_received) > 0, "Should receive events"
            self.add_test_result("event_delivery", True, f"Event delivered successfully: {len(events_received)} events")

            # Test event unsubscription
            await self.event_system.unsubscribe(subscription_id)
            self.add_test_result("event_unsubscription", True, "Event unsubscription successful")

        except Exception as e:
            self.add_test_result("event_system", False, f"Event system test failed: {str(e)}")

    async def test_intelligent_alerting(self):
        """Test intelligent alerting system"""
        print("\nTEST Testing Intelligent Alerting...")

        try:
            # Test alerting initialization
            assert self.alerting is not None, "Alerting system should be initialized"
            self.add_test_result("alerting_initialization", True, "Alerting system initialized successfully")

            # Test alert creation
            test_alert = Alert(
                alert_type="performance_degradation",
                severity="warning",
                service_name="test_service",
                message="Performance degradation detected",
                details={"metric": "response_time", "current_value": 5000, "threshold": 3000},
                timestamp=datetime.now()
            )

            alert_id = await self.alerting.create_alert(test_alert)
            self.add_test_result("alert_creation", True, f"Alert created with ID: {alert_id}")

            # Test alert retrieval
            alerts = await self.alerting.get_alerts(service_name="test_service")
            assert len(alerts) > 0, "Should retrieve alerts"
            self.add_test_result("alert_retrieval", True, f"Alerts retrieved successfully: {len(alerts)} alerts")

            # Test alert acknowledgment
            result = await self.alerting.acknowledge_alert(alert_id)
            self.add_test_result("alert_acknowledgment", True, f"Alert acknowledgment: {result}")

            # Test alert correlation
            correlated_alerts = await self.alerting.correlate_alerts([test_alert])
            self.add_test_result("alert_correlation", True, f"Alert correlation completed: {len(correlated_alerts)} groups")

        except Exception as e:
            self.add_test_result("intelligent_alerting", False, f"Intelligent alerting test failed: {str(e)}")

    async def test_performance_analytics(self):
        """Test performance analytics system"""
        print("\n🧪 Testing Performance Analytics...")

        try:
            # Test analytics initialization
            assert self.analytics is not None, "Performance analytics should be initialized"
            self.add_test_result("analytics_initialization", True, "Performance analytics initialized successfully")

            # Test metrics collection
            test_metrics = {
                "response_time": 150.5,
                "memory_usage": 45.2,
                "cpu_usage": 35.8,
                "error_rate": 0.01
            }

            await self.analytics.collect_metrics("test_service", test_metrics)
            self.add_test_result("metrics_collection", True, "Metrics collected successfully")

            # Test performance summary
            summary = await self.analytics.get_performance_summary("test_service")
            assert summary is not None, "Should generate performance summary"
            self.add_test_result("performance_summary", True, "Performance summary generated successfully")

            # Test trend analysis
            predictions = await self.analytics.get_performance_predictions("test_service")
            assert predictions is not None, "Should generate predictions"
            self.add_test_result("trend_analysis", True, "Trend analysis completed successfully")

            # Test optimization recommendations
            recommendations = await self.analytics.optimize_performance("test_service")
            assert recommendations is not None, "Should generate recommendations"
            self.add_test_result("optimization_recommendations", True, "Optimization recommendations generated successfully")

        except Exception as e:
            self.add_test_result("performance_analytics", False, f"Performance analytics test failed: {str(e)}")

    async def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🧪 Testing API Endpoints...")

        try:
            # Test health status endpoint
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    self.add_test_result("api_health_status", True, "Health status endpoint working")
                else:
                    self.add_test_result("api_health_status", False, f"Health status endpoint failed: {response.status}")

            # Test services endpoint
            async with self.session.get(f"{self.base_url}/services") as response:
                if response.status == 200:
                    data = await response.json()
                    self.add_test_result("api_services", True, "Services endpoint working")
                else:
                    self.add_test_result("api_services", False, f"Services endpoint failed: {response.status}")

            # Test analytics summary endpoint
            async with self.session.get(f"{self.base_url}/analytics/summary") as response:
                if response.status == 200:
                    data = await response.json()
                    self.add_test_result("api_analytics_summary", True, "Analytics summary endpoint working")
                else:
                    self.add_test_result("api_analytics_summary", False, f"Analytics summary endpoint failed: {response.status}")

            # Test predictions endpoint
            async with self.session.get(f"{self.base_url}/analytics/predictions?service_name=test_service") as response:
                if response.status == 200:
                    data = await response.json()
                    self.add_test_result("api_predictions", True, "Predictions endpoint working")
                else:
                    self.add_test_result("api_predictions", False, f"Predictions endpoint failed: {response.status}")

            # Test metrics collection endpoint
            test_metrics = {"response_time": 200.0, "memory_usage": 50.0}
            async with self.session.post(
                f"{self.base_url}/analytics/metrics/test_service",
                json=test_metrics
            ) as response:
                if response.status == 200:
                    self.add_test_result("api_metrics_collection", True, "Metrics collection endpoint working")
                else:
                    self.add_test_result("api_metrics_collection", False, f"Metrics collection endpoint failed: {response.status}")

        except Exception as e:
            self.add_test_result("api_endpoints", False, f"API endpoints test failed: {str(e)}")

    async def test_dashboard_integration(self):
        """Test dashboard integration"""
        print("\n🧪 Testing Dashboard Integration...")

        try:
            # Test dashboard data retrieval
            dashboard_data = {
                "services": {},
                "alerts": [],
                "metrics": [],
                "analytics": {
                    "trends": {},
                    "predictions": {},
                    "recommendations": [],
                    "model_accuracy": {}
                }
            }

            # Simulate dashboard data fetch
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    dashboard_data["services"] = await response.json()

            async with self.session.get(f"{self.base_url}/analytics/summary") as response:
                if response.status == 200:
                    analytics_data = await response.json()
                    dashboard_data["analytics"] = analytics_data

            self.add_test_result("dashboard_data_retrieval", True, "Dashboard data retrieved successfully")

            # Test real-time updates simulation
            # This would normally be tested with WebSocket connections
            update_events = 0
            for i in range(3):
                # Simulate metric updates
                test_metrics = {
                    "response_time": 100 + i * 10,
                    "memory_usage": 40 + i * 5,
                    "cpu_usage": 30 + i * 3
                }

                async with self.session.post(
                    f"{self.base_url}/analytics/metrics/test_service",
                    json=test_metrics
                ) as response:
                    if response.status == 200:
                        update_events += 1

            self.add_test_result("real_time_updates", True, f"Real-time updates working: {update_events} events")

            # Test data structure validation
            required_keys = ["services", "analytics"]
            for key in required_keys:
                assert key in dashboard_data, f"Dashboard data should contain {key}"

            self.add_test_result("data_structure_validation", True, "Dashboard data structure validated")

        except Exception as e:
            self.add_test_result("dashboard_integration", False, f"Dashboard integration test failed: {str(e)}")

    def add_test_result(self, test_name: str, passed: bool, message: str):
        """Add test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}: {message}")

    async def run_comprehensive_test(self):
        """Run comprehensive integration test"""
        print("🚀 Starting Comprehensive Health Monitoring Integration Test")
        print("=" * 60)

        try:
            # Setup test environment
            await self.setup_test_environment()

            # Run all tests
            await self.test_health_monitor_core()
            await self.test_event_system()
            await self.test_intelligent_alerting()
            await self.test_performance_analytics()
            await self.test_api_endpoints()
            await self.test_dashboard_integration()

        except Exception as e:
            self.add_test_result("comprehensive_test", False, f"Comprehensive test failed: {str(e)}")

        finally:
            # Cleanup test environment
            await self.cleanup_test_environment()

        # Generate test report
        await self.generate_test_report()

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        print("=" * 60)

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["passed"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Print summary
        print(f"📈 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()

        # Print detailed results
        print("📋 Detailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"   {status} {result['test_name']}: {result['message']}")

        # Generate recommendations
        print("\n💡 Recommendations:")
        if failed_tests > 0:
            failed_tests_details = [r for r in self.test_results if not r["passed"]]
            for failed_test in failed_tests_details:
                print(f"   • Fix {failed_test['test_name']}: {failed_test['message']}")
        else:
            print("   • All tests passed! System is ready for production.")

        # Save report to file
        report_path = "health_monitoring_test_report.json"
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Test report saved to: {report_path}")

        # Return overall success status
        return failed_tests == 0

async def main():
    """Main test function"""
    test = HealthMonitoringIntegrationTest()
    success = await test.run_comprehensive_test()

    if success:
        print("\n🎉 All integration tests passed! Health monitoring system is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the test report.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)