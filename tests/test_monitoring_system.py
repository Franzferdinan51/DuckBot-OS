#!/usr/bin/env python3
"""
Comprehensive test suite for DuckBot Monitoring System
"""

import unittest
import asyncio
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import monitoring components
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from duckbot.core.monitoring_system import (
    DuckBotMonitoring, MonitoringDatabase, MetricsCollector, AgentMonitor,
    ServiceHealthMonitor, AlertManager, UserActivityTracker, SystemMetric,
    AgentMetric, ServiceHealth, Alert, AlertLevel, HealthStatus, MetricType
)
from duckbot.services.enhanced_monitoring_dashboard import EnhancedMonitoringDashboard
from duckbot.analytics.monitoring_analytics import (
    MonitoringAnalytics, PerformanceAnalyzer, DataExporter, ReportGenerator,
    AnalyticsPeriod, ReportFormat
)
from duckbot.integrations.monitoring_integration import (
    get_monitoring_integration, monitor_agent, monitor_user_activity,
    monitor_service, MonitoredServerManager
)

class TestMonitoringDatabase(unittest.TestCase):
    """Test monitoring database functionality"""

    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)

    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database initialization"""
        self.assertIsNotNone(self.db)
        self.assertTrue(os.path.exists(self.temp_db.name))

    def test_store_system_metric(self):
        """Test storing system metrics"""
        metric = SystemMetric(
            name="test_cpu",
            value=75.5,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags={"host": "test"}
        )

        self.db.store_system_metric(metric)

        # Retrieve and verify
        metrics = self.db.get_system_metrics(name="test_cpu", limit=1)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]["name"], "test_cpu")
        self.assertEqual(metrics[0]["value"], 75.5)

    def test_store_agent_metric(self):
        """Test storing agent metrics"""
        metric = AgentMetric(
            agent_id="test_agent",
            agent_type="test",
            response_time_ms=150.5,
            success=True,
            model_used="test-model",
            tokens_used=100,
            timestamp=datetime.now()
        )

        self.db.store_agent_metric(metric)

        # Verify through database query
        with self.db.db_path as db_path:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_metrics WHERE agent_id = ?", ("test_agent",))
            result = cursor.fetchone()
            conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test_agent")  # agent_id
        self.assertEqual(result[3], 150.5)  # response_time_ms

    def test_store_service_health(self):
        """Test storing service health"""
        health = ServiceHealth(
            service_name="test_service",
            status=HealthStatus.HEALTHY,
            response_time_ms=25.5,
            last_check=datetime.now(),
            metrics={"cpu": 10.5}
        )

        self.db.store_service_health(health)

        # Verify through database query
        with self.db.db_path as db_path:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM service_health WHERE service_name = ?", ("test_service",))
            result = cursor.fetchone()
            conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test_service")  # service_name
        self.assertEqual(result[2], "healthy")  # status

    def test_store_alert(self):
        """Test storing alerts"""
        alert = Alert(
            id="test_alert_1",
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="This is a test alert",
            source="test",
            timestamp=datetime.now(),
            tags={"test": True}
        )

        self.db.store_alert(alert)

        # Retrieve and verify
        alerts = self.db.get_active_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["id"], "test_alert_1")
        self.assertEqual(alerts[0]["level"], "warning")

class TestMetricsCollector(unittest.TestCase):
    """Test metrics collection functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.collector = MetricsCollector(self.db)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 75.5
        mock_memory.return_value = Mock(percent=65.2, available=8 * 1024**3)
        mock_disk.return_value = Mock(total=500 * 1024**3, used=250 * 1024**3)

        # Collect metrics
        self.collector._collect_all_metrics()

        # Verify metrics were stored
        metrics = self.db.get_system_metrics(limit=10)
        self.assertGreater(len(metrics), 0)

        # Check for specific metrics
        cpu_metrics = [m for m in metrics if m["name"] == "cpu_percent"]
        self.assertEqual(len(cpu_metrics), 1)
        self.assertEqual(cpu_metrics[0]["value"], 75.5)

        memory_metrics = [m for m in metrics if m["name"] == "memory_percent"]
        self.assertEqual(len(memory_metrics), 1)
        self.assertEqual(memory_metrics[0]["value"], 65.2)

class TestAgentMonitor(unittest.TestCase):
    """Test agent monitoring functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.agent_monitor = AgentMonitor(self.db)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def test_record_agent_interaction(self):
        """Test recording agent interactions"""
        self.agent_monitor.record_agent_interaction(
            agent_id="test_agent",
            agent_type="chat",
            response_time_ms=150.5,
            success=True,
            model_used="gpt-4",
            tokens_used=100
        )

        # Check in-memory metrics
        summary = self.agent_monitor.get_agent_performance_summary("test_agent")
        self.assertEqual(summary["total_requests"], 1)
        self.assertEqual(summary["successful_requests"], 1)
        self.assertEqual(summary["avg_response_time"], 150.5)
        self.assertEqual(summary["total_tokens"], 100)

        # Check database storage
        with self.db.db_path as db_path:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_metrics WHERE agent_id = ?", ("test_agent",))
            result = cursor.fetchone()
            conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test_agent")

    def test_multiple_interactions(self):
        """Test recording multiple agent interactions"""
        # Record multiple interactions
        interactions = [
            (100.0, True, "gpt-4", 50),
            (200.0, True, "gpt-4", 75),
            (150.0, False, "gpt-4", 0, "Test error"),
        ]

        for i, (response_time, success, model, tokens, *error) in enumerate(interactions):
            self.agent_monitor.record_agent_interaction(
                agent_id=f"test_agent_{i}",
                agent_type="chat",
                response_time_ms=response_time,
                success=success,
                model_used=model,
                tokens_used=tokens,
                error_message=error[0] if error else ""
            )

        # Check summaries
        for i in range(len(interactions)):
            summary = self.agent_monitor.get_agent_performance_summary(f"test_agent_{i}")
            self.assertEqual(summary["total_requests"], 1)
            if i == 2:  # The failed interaction
                self.assertEqual(summary["failed_requests"], 1)
            else:
                self.assertEqual(summary["successful_requests"], 1)

class TestAlertManager(unittest.TestCase):
    """Test alert management functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.alert_manager = AlertManager(self.db)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def test_alert_rules(self):
        """Test default alert rules"""
        # Test high CPU usage alert
        metrics = {"cpu_percent": 95.0}
        self.alert_manager.check_alerts(metrics)

        # Check if alert was created
        alerts = self.db.get_active_alerts()
        cpu_alerts = [a for a in alerts if "high_cpu_usage" in a["title"].lower()]
        self.assertGreater(len(cpu_alerts), 0)

    def test_alert_resolution(self):
        """Test alert resolution"""
        # Create an alert first
        alert = Alert(
            id="test_alert",
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="Test message",
            source="test",
            timestamp=datetime.now()
        )
        self.db.store_alert(alert)

        # Verify it's active
        alerts = self.db.get_active_alerts()
        self.assertEqual(len(alerts), 1)

        # Resolve the alert
        self.alert_manager.resolve_alert("test_alert")

        # Verify it's resolved
        alerts = self.db.get_active_alerts()
        self.assertEqual(len(alerts), 0)

class TestUserActivityTracker(unittest.TestCase):
    """Test user activity tracking functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.tracker = UserActivityTracker(self.db)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def test_session_management(self):
        """Test session management"""
        # Start a session
        session_id = self.tracker.start_session("test_user")
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.tracker.active_sessions)

        # Record activity
        self.tracker.record_activity(
            session_id=session_id,
            activity_type="chat",
            feature_used="ai_response",
            response_time_ms=150.0,
            satisfaction_score=5
        )

        # Check activity summary
        summary = self.tracker.get_activity_summary(hours=24)
        self.assertEqual(summary["total_activities"], 1)
        self.assertEqual(summary["avg_response_time"], 150.0)
        self.assertEqual(summary["avg_satisfaction"], 5.0)

        # End session
        self.tracker.end_session(session_id)
        self.assertNotIn(session_id, self.tracker.active_sessions)

class TestMonitoringIntegration(unittest.TestCase):
    """Test monitoring integration functionality"""

    def setUp(self):
        """Set up test environment"""
        self.integration = get_monitoring_integration()
        self.integration.disable_integration()  # Start disabled

    def test_integration_enable_disable(self):
        """Test integration enable/disable"""
        self.assertFalse(self.integration._integration_enabled)
        self.integration.enable_integration()
        self.assertTrue(self.integration._integration_enabled)
        self.integration.disable_integration()
        self.assertFalse(self.integration._integration_enabled)

    def test_user_context(self):
        """Test user context setting"""
        user_id = "test_user"
        self.integration.set_user_context(user_id=user_id)

        self.assertEqual(self.integration.current_user, user_id)
        self.assertIsNotNone(self.integration.session_id)

    @patch('duckbot.integrations.monitoring_integration.get_monitoring')
    def test_record_agent_interaction(self, mock_get_monitoring):
        """Test recording agent interactions"""
        # Mock monitoring system
        mock_monitoring = Mock()
        mock_get_monitoring.return_value = mock_monitoring

        self.integration.enable_integration()
        self.integration.set_user_context(user_id="test_user")

        # Record interaction
        self.integration.record_agent_interaction(
            agent_id="test_agent",
            agent_type="chat",
            response_time_ms=150.5,
            success=True,
            model_used="gpt-4",
            tokens_used=100
        )

        # Verify calls were made
        mock_monitoring.record_agent_interaction.assert_called_once()
        mock_monitoring.record_user_activity.assert_called_once()

class TestDecorators(unittest.TestCase):
    """Test monitoring decorators"""

    def setUp(self):
        """Set up test environment"""
        self.integration = get_monitoring_integration()
        self.integration.enable_integration()

    def tearDown(self):
        """Clean up test environment"""
        self.integration.disable_integration()

    def test_monitor_agent_decorator(self):
        """Test agent monitoring decorator"""
        @monitor_agent(agent_id="test_decorator_agent", agent_type="decorated_test")
        def test_function():
            time.sleep(0.1)  # Simulate work
            return "success"

        # Mock the integration
        with patch.object(self.integration, 'record_agent_interaction') as mock_record:
            result = test_function()
            self.assertEqual(result, "success")

            # Verify recording was called
            mock_record.assert_called_once()
            call_args = mock_record.call_args
            self.assertEqual(call_args[1]['agent_id'], "test_decorator_agent")
            self.assertEqual(call_args[1]['agent_type'], "decorated_test")
            self.assertTrue(call_args[1]['success'])
            self.assertGreater(call_args[1]['response_time_ms'], 0)

    def test_monitor_user_activity_decorator(self):
        """Test user activity monitoring decorator"""
        @monitor_user_activity(activity_type="test_activity", feature_used="test_feature")
        def test_function():
            time.sleep(0.05)  # Simulate work
            return "success"

        # Mock the integration
        with patch.object(self.integration, 'record_user_activity') as mock_record:
            result = test_function()
            self.assertEqual(result, "success")

            # Verify recording was called
            mock_record.assert_called_once()
            call_args = mock_record.call_args
            self.assertEqual(call_args[1]['activity_type'], "test_activity")
            self.assertEqual(call_args[1]['feature_used'], "test_feature")
            self.assertEqual(call_args[1]['satisfaction_score'], 5)

class TestPerformanceAnalyzer(unittest.TestCase):
    """Test performance analysis functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.analyzer = PerformanceAnalyzer(self.db)

        # Insert test data
        self._insert_test_data()

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def _insert_test_data(self):
        """Insert test data for analysis"""
        # Insert system metrics
        for i in range(100):
            metric = SystemMetric(
                name="cpu_percent",
                value=50 + (i % 40),  # Range from 50 to 90
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now() - timedelta(minutes=i),
                tags={"host": "test"}
            )
            self.db.store_system_metric(metric)

        # Insert agent metrics
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            for i in range(50):
                cursor.execute('''
                    INSERT INTO agent_metrics (
                        agent_id, agent_type, response_time_ms, success,
                        model_used, tokens_used, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"agent_{i % 5}",
                    "chat",
                    100 + (i * 5),  # Response times from 100ms to 345ms
                    i % 10 != 0,  # 90% success rate
                    "gpt-4",
                    50 + i,
                    (datetime.now() - timedelta(minutes=i)).isoformat()
                ))
            conn.commit()

    def test_system_performance_analysis(self):
        """Test system performance analysis"""
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()

        analysis = self.analyzer.analyze_system_performance(start_time, end_time)

        self.assertIn("period", analysis)
        self.assertIn("metrics_analysis", analysis)
        self.assertIn("summary", analysis)

        # Check CPU analysis
        if "cpu_percent" in analysis["metrics_analysis"]:
            cpu_analysis = analysis["metrics_analysis"]["cpu_percent"]
            self.assertIn("avg", cpu_analysis)
            self.assertIn("min", cpu_analysis)
            self.assertIn("max", cpu_analysis)
            self.assertIn("trend", cpu_analysis)

    def test_agent_performance_analysis(self):
        """Test agent performance analysis"""
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()

        analysis = self.analyzer.analyze_agent_performance(start_time, end_time)

        self.assertIn("period", analysis)
        self.assertIn("agents_analysis", analysis)
        self.assertIn("summary", analysis)

        # Check agent summary
        summary = analysis["summary"]
        self.assertIn("total_agents", summary)
        self.assertIn("total_requests", summary)
        self.assertIn("overall_success_rate", summary)

class TestDataExporter(unittest.TestCase):
    """Test data export functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.exporter = DataExporter(self.db)

        # Insert test data
        self._insert_test_data()

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def _insert_test_data(self):
        """Insert test data for export"""
        # Insert system metrics
        for i in range(10):
            metric = SystemMetric(
                name="cpu_percent",
                value=50 + i,
                metric_type=MetricType.GAUGE,
                timestamp=datetime.now() - timedelta(minutes=i),
                tags={"host": "test"}
            )
            self.db.store_system_metric(metric)

    def test_export_csv(self):
        """Test CSV export"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        export_path = self.exporter.export_system_metrics(
            start_time, end_time, ReportFormat.CSV
        )

        self.assertTrue(os.path.exists(export_path))
        self.assertTrue(export_path.endswith('.csv'))

        # Verify file contents
        with open(export_path, 'r') as f:
            content = f.read()
            self.assertIn("cpu_percent", content)

        # Clean up
        os.unlink(export_path)

    def test_export_json(self):
        """Test JSON export"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        export_path = self.exporter.export_system_metrics(
            start_time, end_time, ReportFormat.JSON
        )

        self.assertTrue(os.path.exists(export_path))
        self.assertTrue(export_path.endswith('.json'))

        # Verify file contents
        with open(export_path, 'r') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

        # Clean up
        os.unlink(export_path)

class TestReportGenerator(unittest.TestCase):
    """Test report generation functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MonitoringDatabase(self.temp_db.name)
        self.report_generator = ReportGenerator(self.db)

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)

    def test_generate_comprehensive_report(self):
        """Test comprehensive report generation"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        report_path = self.report_generator.generate_comprehensive_report(start_time, end_time)

        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(report_path.endswith('.json'))

        # Verify report contents
        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertIn("metadata", report)
        self.assertIn("executive_summary", report)
        self.assertIn("system_performance", report)
        self.assertIn("agent_performance", report)
        self.assertIn("service_health", report)
        self.assertIn("alerts_summary", report)
        self.assertIn("recommendations", report)

        # Clean up
        os.unlink(report_path)

        # Check if HTML version was also generated
        html_path = report_path.replace('.json', '.html')
        if os.path.exists(html_path):
            os.unlink(html_path)

class TestMonitoringSystemIntegration(unittest.TestCase):
    """Test integration of all monitoring components"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_monitoring.db")
        self.monitoring = DuckBotMonitoring(self.db_path)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # Start monitoring
        self.monitoring.start(metrics_interval=0.1, health_check_interval=0.2)

        # Record some activities
        self.monitoring.record_agent_interaction(
            agent_id="integration_test_agent",
            agent_type="test",
            response_time_ms=150.5,
            success=True,
            model_used="test-model",
            tokens_used=100
        )

        # Start user session
        session_id = self.monitoring.user_activity_tracker.start_session("test_user")
        self.monitoring.record_user_activity(
            session_id=session_id,
            activity_type="integration_test",
            feature_used="monitoring",
            response_time_ms=75.0,
            satisfaction_score=5
        )

        # Let it collect some metrics
        time.sleep(0.5)

        # Get system status
        status = self.monitoring.get_system_status()

        self.assertIn("timestamp", status)
        self.assertIn("system_metrics", status)
        self.assertIn("agents", status)
        self.assertIn("services", status)

        # Stop monitoring
        self.monitoring.stop()

    def test_error_handling(self):
        """Test error handling in monitoring system"""
        # Test with invalid database path
        invalid_db_path = "/invalid/path/monitoring.db"
        monitoring = DuckBotMonitoring(invalid_db_path)

        # Should handle errors gracefully
        status = monitoring.get_system_status()
        self.assertIn("error", status)

        monitoring.stop()

def run_comprehensive_tests():
    """Run all monitoring system tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestMonitoringDatabase,
        TestMetricsCollector,
        TestAgentMonitor,
        TestAlertManager,
        TestUserActivityTracker,
        TestMonitoringIntegration,
        TestDecorators,
        TestPerformanceAnalyzer,
        TestDataExporter,
        TestReportGenerator,
        TestMonitoringSystemIntegration
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()

if __name__ == "__main__":
    print("=== DuckBot Monitoring System Test Suite ===")
    success = run_comprehensive_tests()

    if success:
        print("\n✅ All tests passed! Monitoring system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")

    exit(0 if success else 1)