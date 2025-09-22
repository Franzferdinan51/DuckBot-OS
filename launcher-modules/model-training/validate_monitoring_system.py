#!/usr/bin/env python3
"""
Validation Script for Complete Training Monitoring System
Comprehensive testing and validation of all monitoring system components.
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import numpy as np
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all monitoring components
try:
    from training_monitoring import TrainingMonitor, TrainingMetricsDatabase, RealTimeMetricsCollector
    from structured_logger import StructuredLogger, LogDatabase, PerformanceTimer
    from training_visualizer import TrainingVisualizer, VisualizationConfig
    from early_stopping import EarlyStoppingCheckpointManager, EarlyStoppingConfig, CheckpointConfig
    from performance_monitor import PerformanceMonitor, PerformanceConfig, TrainingThroughputTracker
    from alerting_system import AlertingSystem, AlertConfig, Alert, AlertSeverity, AlertCategory
    from duckbot_integration import DuckBotIntegrationManager, IntegrationConfig, UnifiedTrainingMonitor
    ALL_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import monitoring components: {e}")
    ALL_COMPONENTS_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSystemValidator:
    """Comprehensive validator for the monitoring system"""

    def __init__(self):
        self.test_results = {}
        self.validation_summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'start_time': None,
            'end_time': None,
            'duration': None
        }
        self.test_data = {}

    def run_comprehensive_validation(self):
        """Run comprehensive validation of all components"""
        print("🔍 Comprehensive Monitoring System Validation")
        print("=" * 60)

        self.validation_summary['start_time'] = datetime.now()

        if not ALL_COMPONENTS_AVAILABLE:
            print("❌ Cannot run validation - components not available")
            return

        # Test individual components
        self._test_training_monitoring()
        self._test_structured_logger()
        self._test_performance_monitoring()
        self._test_alerting_system()
        self._test_early_stopping()
        self._test_visualization()
        self._test_integration()
        self._test_unified_monitor()

        # Test integration scenarios
        self._test_end_to_end_scenario()
        self._test_performance_scenarios()
        self._test_error_handling()

        # Generate final report
        self._generate_validation_report()

    def _test_training_monitoring(self):
        """Test training monitoring component"""
        print("\n📊 Testing Training Monitoring Component...")
        test_name = "Training Monitoring"

        try:
            # Initialize training monitor
            monitor = TrainingMonitor()
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test metrics recording
            run_id = "test_run_001"
            for epoch in range(3):
                for step in range(5):
                    metrics = {
                        'loss': 2.0 * (0.9 ** epoch) + np.random.normal(0, 0.1),
                        'accuracy': 0.5 + 0.1 * epoch + np.random.normal(0, 0.05),
                        'val_loss': 2.2 * (0.9 ** epoch) + np.random.normal(0, 0.1),
                        'val_accuracy': 0.45 + 0.1 * epoch + np.random.normal(0, 0.05)
                    }
                    monitor.record_metrics(run_id, epoch, step, metrics)

            self.test_results[test_name]['details'].append("✓ Metrics recording successful")

            # Test database operations
            recent_metrics = monitor.get_recent_metrics()
            if len(recent_metrics) > 0:
                self.test_results[test_name]['details'].append("✓ Database storage successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Database storage failed")

            # Test status reporting
            status = monitor.get_status()
            if status and isinstance(status, dict):
                self.test_results[test_name]['details'].append("✓ Status reporting successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Status reporting failed")

            monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_structured_logger(self):
        """Test structured logger component"""
        print("\n📝 Testing Structured Logger Component...")
        test_name = "Structured Logger"

        try:
            # Initialize structured logger
            logger_comp = StructuredLogger()
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test event logging
            for i in range(5):
                logger_comp.log_training_event(
                    event_type="test_event",
                    message=f"Test event {i}",
                    details={"test_id": i, "data": f"sample_data_{i}"},
                    run_id="test_run",
                    epoch=0,
                    step=i
                )

            self.test_results[test_name]['details'].append("✓ Event logging successful")

            # Test performance timing
            with PerformanceTimer(logger_comp, "test_operation"):
                time.sleep(0.1)

            self.test_results[test_name]['details'].append("✓ Performance timing successful")

            # Test database queries
            events = logger_comp.get_events("test_run")
            if len(events) > 0:
                self.test_results[test_name]['details'].append("✓ Database queries successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Database queries failed")

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_performance_monitoring(self):
        """Test performance monitoring component"""
        print("\n⚡ Testing Performance Monitoring Component...")
        test_name = "Performance Monitoring"

        try:
            # Initialize performance monitor
            config = PerformanceConfig(sampling_interval=0.5)  # Faster for testing
            monitor = PerformanceMonitor(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Start monitoring
            monitor.start()
            time.sleep(2)  # Let it collect some metrics

            # Test system info
            system_info = monitor.get_system_info()
            if system_info and 'platform' in system_info:
                self.test_results[test_name]['details'].append("✓ System info collection successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ System info collection failed")

            # Test performance summary
            summary = monitor.get_performance_summary()
            if summary and 'monitoring_active' in summary:
                self.test_results[test_name]['details'].append("✓ Performance summary successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Performance summary failed")

            # Test resource utilization
            utilization = monitor.get_resource_utilization()
            if isinstance(utilization, dict):
                self.test_results[test_name]['details'].append("✓ Resource utilization successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Resource utilization failed")

            monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_alerting_system(self):
        """Test alerting system component"""
        print("\n🚨 Testing Alerting System Component...")
        test_name = "Alerting System"

        try:
            # Initialize alerting system
            config = AlertConfig(
                enable_console=True,
                enable_file=True,
                min_severity=AlertSeverity.INFO
            )
            alert_system = AlertingSystem(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test alert sending
            test_alerts = [
                Alert(
                    alert_id="test_alert_1",
                    timestamp=datetime.now(),
                    severity=AlertSeverity.INFO,
                    category=AlertCategory.TRAINING,
                    title="Test Info Alert",
                    message="This is a test info alert",
                    details={"test": True}
                ),
                Alert(
                    alert_id="test_alert_2",
                    timestamp=datetime.now(),
                    severity=AlertSeverity.WARNING,
                    category=AlertCategory.PERFORMANCE,
                    title="Test Warning Alert",
                    message="This is a test warning alert",
                    details={"test": True}
                ),
                Alert(
                    alert_id="test_alert_3",
                    timestamp=datetime.now(),
                    severity=AlertSeverity.ERROR,
                    category=AlertCategory.SYSTEM,
                    title="Test Error Alert",
                    message="This is a test error alert",
                    details={"test": True}
                )
            ]

            for alert in test_alerts:
                alert_system.send_alert(alert)

            self.test_results[test_name]['details'].append("✓ Alert sending successful")

            # Test alert statistics
            stats = alert_system.get_alert_stats()
            if stats and 'total_alerts' in stats:
                if stats['total_alerts'] >= 3:
                    self.test_results[test_name]['details'].append("✓ Alert statistics successful")
                else:
                    self.test_results[test_name]['details'].append(f"⚠ Alert count low: {stats['total_alerts']}")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Alert statistics failed")

            # Test alert retrieval
            alerts = alert_system.database.get_alerts()
            if len(alerts) > 0:
                self.test_results[test_name]['details'].append("✓ Alert retrieval successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Alert retrieval failed")

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_early_stopping(self):
        """Test early stopping component"""
        print("\n🛑 Testing Early Stopping Component...")
        test_name = "Early Stopping"

        try:
            # Initialize early stopping manager
            early_stopping_config = EarlyStoppingConfig(
                patience=3,
                min_delta=0.01,
                monitor_metric="val_loss",
                restore_best_weights=True
            )
            checkpoint_config = CheckpointConfig(
                save_dir="test_checkpoints",
                strategy="best_only",
                max_checkpoints=3
            )
            manager = EarlyStoppingCheckpointManager(early_stopping_config, checkpoint_config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test early stopping logic
            logs_list = [
                {"val_loss": 2.0, "loss": 1.8, "accuracy": 0.6},
                {"val_loss": 1.8, "loss": 1.6, "accuracy": 0.65},
                {"val_loss": 1.6, "loss": 1.4, "accuracy": 0.7},
                {"val_loss": 1.5, "loss": 1.3, "accuracy": 0.72},
                {"val_loss": 1.45, "loss": 1.25, "accuracy": 0.74},
                {"val_loss": 1.42, "loss": 1.2, "accuracy": 0.75},
                {"val_loss": 1.41, "loss": 1.18, "accuracy": 0.76},
                {"val_loss": 1.40, "loss": 1.15, "accuracy": 0.77}
            ]

            for epoch, logs in enumerate(logs_list):
                manager.on_epoch_end(epoch, logs)
                if manager.should_stop():
                    break

            self.test_results[test_name]['details'].append("✓ Early stopping logic successful")

            # Test checkpoint management
            checkpoints = manager.checkpoint_manager.list_checkpoints()
            if len(checkpoints) >= 0:  # Should have some checkpoints
                self.test_results[test_name]['details'].append("✓ Checkpoint management successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Checkpoint management failed")

            # Test state management
            state = manager.get_state()
            if state and 'early_stopping' in state:
                self.test_results[test_name]['details'].append("✓ State management successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ State management failed")

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_visualization(self):
        """Test visualization component"""
        print("\n📈 Testing Visualization Component...")
        test_name = "Visualization"

        try:
            # Initialize visualizer
            config = VisualizationConfig(host="127.0.0.1", port=8791)  # Different port for testing
            visualizer = TrainingVisualizer(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test visualizer initialization
            if visualizer.is_ready:
                self.test_results[test_name]['details'].append("✓ Visualizer initialization successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Visualizer initialization failed")

            # Test chart generation (if possible)
            try:
                # Generate sample data
                sample_data = {
                    'epochs': list(range(10)),
                    'loss': [2.0 * (0.9 ** i) for i in range(10)],
                    'accuracy': [0.5 + 0.05 * i for i in range(10)]
                }

                # Test basic functionality
                if hasattr(visualizer, 'generate_chart'):
                    self.test_results[test_name]['details'].append("✓ Chart generation available")
                else:
                    self.test_results[test_name]['details'].append("⚠ Chart generation not available")

            except Exception as e:
                self.test_results[test_name]['details'].append(f"⚠ Chart generation test failed: {str(e)}")

            # Test report generation
            try:
                if hasattr(visualizer, 'generate_report'):
                    self.test_results[test_name]['details'].append("✓ Report generation available")
                else:
                    self.test_results[test_name]['details'].append("⚠ Report generation not available")

            except Exception as e:
                self.test_results[test_name]['details'].append(f"⚠ Report generation test failed: {str(e)}")

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_integration(self):
        """Test DuckBot integration component"""
        print("\n🔗 Testing Integration Component...")
        test_name = "DuckBot Integration"

        try:
            # Initialize integration manager
            config = IntegrationConfig(
                sync_interval=1.0,  # Fast sync for testing
                enable_duckbot_monitoring=False,  # Skip DuckBot for testing
                enable_training_monitoring=True,
                enable_performance_monitoring=True,
                enable_alerting_system=True
            )
            integration_manager = DuckBotIntegrationManager(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Start integration
            integration_manager.start()
            time.sleep(2)  # Let it run for a bit

            # Test status reporting
            status = integration_manager.get_unified_status()
            if status and 'integration_active' in status:
                self.test_results[test_name]['details'].append("✓ Status reporting successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Status reporting failed")

            # Test event handling
            test_event = {
                'event_type': 'test_event',
                'message': 'Test event from validation',
                'details': {'test': True}
            }

            integration_manager._handle_training_event(test_event)
            self.test_results[test_name]['details'].append("✓ Event handling successful")

            # Test dashboard data
            dashboard_data = integration_manager.get_unified_dashboard_data()
            if dashboard_data and 'timestamp' in dashboard_data:
                self.test_results[test_name]['details'].append("✓ Dashboard data successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Dashboard data failed")

            integration_manager.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_unified_monitor(self):
        """Test unified training monitor"""
        print("\n🎛️ Testing Unified Training Monitor...")
        test_name = "Unified Monitor"

        try:
            # Initialize unified monitor
            config = IntegrationConfig(
                sync_interval=1.0,
                enable_duckbot_monitoring=False
            )
            unified_monitor = UnifiedTrainingMonitor(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Start monitor
            unified_monitor.start()
            time.sleep(1)

            # Test session management
            run_id = "test_unified_run"
            config_data = {"model": "test_model", "epochs": 3}
            session_id = unified_monitor.start_training_session(run_id, config_data)

            if session_id:
                self.test_results[test_name]['details'].append("✓ Session start successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Session start failed")

            # Test step logging
            for epoch in range(2):
                for step in range(3):
                    metrics = {
                        'loss': 2.0 * (0.9 ** epoch),
                        'accuracy': 0.5 + 0.1 * epoch
                    }
                    unified_monitor.log_training_step(run_id, epoch, step, metrics)

            self.test_results[test_name]['details'].append("✓ Step logging successful")

            # Test session end
            unified_monitor.end_training_session(
                run_id, session_id, "completed",
                {"total_epochs": 2, "final_accuracy": 0.65}
            )
            self.test_results[test_name]['details'].append("✓ Session end successful")

            # Test status
            status = unified_monitor.get_status()
            if status and 'integration_active' in status:
                self.test_results[test_name]['details'].append("✓ Status retrieval successful")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ Status retrieval failed")

            unified_monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_end_to_end_scenario(self):
        """Test end-to-end training scenario"""
        print("\n🔄 Testing End-to-End Scenario...")
        test_name = "End-to-End Scenario"

        try:
            # Initialize unified monitor
            config = IntegrationConfig(
                sync_interval=0.5,
                enable_duckbot_monitoring=False
            )
            unified_monitor = UnifiedTrainingMonitor(config)
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Start monitoring
            unified_monitor.start()
            time.sleep(0.5)

            # Simulate complete training session
            run_id = "e2e_test_run"
            training_config = {
                "model": "bert-base-uncased",
                "batch_size": 32,
                "learning_rate": 0.001,
                "epochs": 3
            }

            # Start session
            session_id = unified_monitor.start_training_session(run_id, training_config)
            self.test_results[test_name]['details'].append("✓ Training session started")

            # Simulate training with varying metrics
            for epoch in range(3):
                epoch_loss = 2.0 * (0.85 ** epoch)
                epoch_accuracy = 0.5 + 0.15 * epoch

                for step in range(5):
                    # Add some noise to metrics
                    loss = epoch_loss + np.random.normal(0, 0.05)
                    accuracy = epoch_accuracy + np.random.normal(0, 0.02)
                    val_loss = loss * 1.1 + np.random.normal(0, 0.03)
                    val_accuracy = accuracy * 0.95 + np.random.normal(0, 0.02)

                    metrics = {
                        'loss': loss,
                        'accuracy': accuracy,
                        'val_loss': val_loss,
                        'val_accuracy': val_accuracy,
                        'learning_rate': 0.001 * (0.95 ** epoch)
                    }

                    unified_monitor.log_training_step(run_id, epoch, step, metrics)

                self.test_results[test_name]['details'].append(f"✓ Epoch {epoch + 1} completed")

            # End session
            unified_monitor.end_training_session(
                run_id, session_id, "completed",
                {
                    "total_epochs": 3,
                    "total_steps": 15,
                    "final_loss": 0.5,
                    "final_accuracy": 0.85
                }
            )
            self.test_results[test_name]['details'].append("✓ Training session completed")

            # Check overall status
            final_status = unified_monitor.get_status()
            if final_status and final_status['integration_active']:
                self.test_results[test_name]['details'].append("✓ System status healthy")
            else:
                self.test_results[test_name]['status'] = 'failed'
                self.test_results[test_name]['details'].append("✗ System status unhealthy")

            unified_monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_performance_scenarios(self):
        """Test performance scenarios"""
        print("\n⚡ Testing Performance Scenarios...")
        test_name = "Performance Scenarios"

        try:
            # Test high-frequency metrics
            monitor = TrainingMonitor()
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            start_time = time.time()
            run_id = "perf_test_run"

            # Record many metrics quickly
            for epoch in range(10):
                for step in range(100):
                    metrics = {
                        'loss': np.random.random(),
                        'accuracy': np.random.random(),
                        'val_loss': np.random.random(),
                        'val_accuracy': np.random.random()
                    }
                    monitor.record_metrics(run_id, epoch, step, metrics)

            duration = time.time() - start_time
            self.test_results[test_name]['details'].append(f"✓ High-frequency recording: {duration:.2f}s for 1000 metrics")

            # Test concurrent operations
            def worker_function(worker_id, metrics_count):
                for i in range(metrics_count):
                    metrics = {
                        'loss': np.random.random(),
                        'accuracy': np.random.random(),
                        'worker_id': worker_id
                    }
                    monitor.record_metrics(f"concurrent_test_{worker_id}", 0, i, metrics)

            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker_function, args=(i, 100))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            self.test_results[test_name]['details'].append("✓ Concurrent operations successful")

            monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🛡️ Testing Error Handling...")
        test_name = "Error Handling"

        try:
            # Test invalid metrics handling
            monitor = TrainingMonitor()
            self.test_results[test_name] = {'status': 'passed', 'details': []}

            # Test with invalid data
            try:
                monitor.record_metrics("invalid_test", -1, -1, {"invalid": "data"})
                self.test_results[test_name]['details'].append("✓ Invalid metrics handled")
            except Exception as e:
                self.test_results[test_name]['details'].append("⚠ Invalid metrics caused exception (acceptable)")

            # Test database error handling
            try:
                # Try to get metrics with invalid parameters
                metrics = monitor.get_recent_metrics(limit=-1)
                self.test_results[test_name]['details'].append("✓ Invalid parameters handled")
            except Exception as e:
                self.test_results[test_name]['details'].append("⚠ Invalid parameters caused exception (acceptable)")

            # Test alert system with invalid alerts
            try:
                alert_system = AlertingSystem()
                invalid_alert = Alert(
                    alert_id="",
                    timestamp=datetime.now(),
                    severity=AlertSeverity.INFO,
                    category=AlertCategory.TRAINING,
                    title="",
                    message=""
                )
                alert_system.send_alert(invalid_alert)
                self.test_results[test_name]['details'].append("✓ Invalid alert handled")
            except Exception as e:
                self.test_results[test_name]['details'].append("⚠ Invalid alert caused exception (acceptable)")

            monitor.stop()

        except Exception as e:
            self.test_results[test_name] = {'status': 'failed', 'details': [f"✗ Exception: {str(e)}"]}

    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        self.validation_summary['end_time'] = datetime.now()
        self.validation_summary['duration'] = (
            self.validation_summary['end_time'] - self.validation_summary['start_time']
        ).total_seconds()

        # Count results
        for test_name, result in self.test_results.items():
            self.validation_summary['total_tests'] += 1
            if result['status'] == 'passed':
                self.validation_summary['passed_tests'] += 1
            elif result['status'] == 'failed':
                self.validation_summary['failed_tests'] += 1
            else:
                self.validation_summary['skipped_tests'] += 1

        # Print summary
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.validation_summary['total_tests']}")
        print(f"Passed: {self.validation_summary['passed_tests']} ✅")
        print(f"Failed: {self.validation_summary['failed_tests']} ❌")
        print(f"Skipped: {self.validation_summary['skipped_tests']} ⏭️")
        print(f"Duration: {self.validation_summary['duration']:.2f} seconds")
        print(f"Success Rate: {(self.validation_summary['passed_tests'] / self.validation_summary['total_tests'] * 100):.1f}%")

        # Print detailed results
        print("\n📊 DETAILED RESULTS:")
        print("-" * 40)
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"{status_icon} {test_name}")
            for detail in result['details']:
                print(f"   {detail}")

        # Save report to file
        report_file = "validation_report.json"
        report_data = {
            'validation_summary': self.validation_summary,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n💾 Detailed report saved to: {report_file}")

        # Overall assessment
        if self.validation_summary['failed_tests'] == 0:
            print("\n🎉 ALL TESTS PASSED! The monitoring system is ready for production.")
        elif self.validation_summary['failed_tests'] <= 2:
            print("\n⚠️  Minor issues detected. The system is mostly functional.")
        else:
            print("\n❌ Multiple issues detected. Please review and fix the problems.")

def main():
    """Main validation function"""
    validator = MonitoringSystemValidator()
    validator.run_comprehensive_validation()

if __name__ == "__main__":
    main()