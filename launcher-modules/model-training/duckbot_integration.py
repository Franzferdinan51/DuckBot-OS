#!/usr/bin/env python3
"""
DuckBot Integration for Training Monitoring System
Integrates the training monitoring system with existing DuckBot monitoring infrastructure.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import DuckBot monitoring components
try:
    from duckbot.core.monitoring_system import DuckBotMonitoring, MonitoringDatabase, MetricsCollector
    from duckbot.core.logging_setup import setup_logging
    from duckbot.analytics.analytics_engine import AnalyticsEngine
    DUCKBOT_MONITORING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"DuckBot monitoring components not available: {e}")
    DUCKBOT_MONITORING_AVAILABLE = False

# Import training monitoring components
from training_monitoring import TrainingMonitor, TrainingMetricsDatabase, RealTimeMetricsCollector
from structured_logger import StructuredLogger, LogDatabase, PerformanceTimer
from training_visualizer import TrainingVisualizer, VisualizationConfig
from early_stopping import EarlyStoppingCheckpointManager, EarlyStoppingConfig, CheckpointConfig
from performance_monitor import PerformanceMonitor, PerformanceConfig
from alerting_system import AlertingSystem, AlertConfig, Alert, AlertSeverity, AlertCategory

@dataclass
class IntegrationConfig:
    """Configuration for DuckBot integration"""
    enable_duckbot_monitoring: bool = True
    enable_training_monitoring: bool = True
    enable_performance_monitoring: bool = True
    enable_alerting_system: bool = True
    enable_visualization: bool = True

    # Data synchronization settings
    sync_interval: float = 30.0  # seconds
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 5.0

    # Event forwarding settings
    forward_to_duckbot: bool = True
    forward_training_events: bool = True
    forward_performance_events: bool = True
    forward_alerts: bool = True

    # Unified dashboard settings
    unified_dashboard_port: int = 8790
    enable_real_time_updates: bool = True
    websocket_path: str = "/ws/training"

class DuckBotIntegrationManager:
    """Main integration manager for DuckBot training monitoring"""

    def __init__(self, config: IntegrationConfig = None):
        self.config = config or IntegrationConfig()
        self.is_running = False
        self.integration_stats = {
            'events_processed': 0,
            'events_forwarded': 0,
            'alerts_generated': 0,
            'sync_cycles': 0,
            'start_time': None,
            'last_sync_time': None
        }

        # Initialize DuckBot components
        self.duckbot_monitoring = None
        self.duckbot_analytics = None
        self._init_duckbot_components()

        # Initialize training monitoring components
        self.training_monitor = None
        self.structured_logger = None
        self.training_visualizer = None
        self.early_stopping_manager = None
        self.performance_monitor = None
        self.alerting_system = None
        self._init_training_components()

        # Synchronization thread
        self.sync_thread = None

        # Event callbacks
        self.event_callbacks = []

    def _init_duckbot_components(self):
        """Initialize DuckBot monitoring components"""
        if not self.config.enable_duckbot_monitoring or not DUCKBOT_MONITORING_AVAILABLE:
            return

        try:
            # Initialize DuckBot monitoring
            self.duckbot_monitoring = DuckBotMonitoring()

            # Initialize DuckBot analytics
            self.duckbot_analytics = AnalyticsEngine()

            logging.info("DuckBot monitoring components initialized")

        except Exception as e:
            logging.error(f"Failed to initialize DuckBot components: {e}")

    def _init_training_components(self):
        """Initialize training monitoring components"""
        try:
            # Initialize structured logger
            if self.config.enable_training_monitoring:
                self.structured_logger = StructuredLogger()

            # Initialize training monitor
            if self.config.enable_training_monitoring:
                self.training_monitor = TrainingMonitor()

            # Initialize training visualizer
            if self.config.enable_visualization:
                self.training_visualizer = TrainingVisualizer()

            # Initialize early stopping manager
            if self.config.enable_training_monitoring:
                early_stopping_config = EarlyStoppingConfig(
                    patience=10,
                    min_delta=0.001,
                    monitor_metric="val_loss",
                    restore_best_weights=True
                )
                checkpoint_config = CheckpointConfig(
                    save_dir="training_checkpoints",
                    strategy="best_and_interval",
                    interval_epochs=5,
                    max_checkpoints=5
                )
                self.early_stopping_manager = EarlyStoppingCheckpointManager(
                    early_stopping_config, checkpoint_config
                )

            # Initialize performance monitor
            if self.config.enable_performance_monitoring:
                performance_config = PerformanceConfig(
                    sampling_interval=1.0,
                    enable_gpu_monitoring=True,
                    detailed_metrics=True
                )
                self.performance_monitor = PerformanceMonitor(performance_config)

            # Initialize alerting system
            if self.config.enable_alerting_system:
                alert_config = AlertConfig(
                    enable_console=True,
                    enable_file=True,
                    enable_desktop=True,
                    min_severity=AlertSeverity.WARNING
                )
                self.alerting_system = AlertingSystem(alert_config)

            logging.info("Training monitoring components initialized")

        except Exception as e:
            logging.error(f"Failed to initialize training components: {e}")

    def start(self):
        """Start the integration system"""
        if self.is_running:
            return

        self.is_running = True
        self.integration_stats['start_time'] = datetime.now()

        # Set up event callbacks
        self._setup_event_callbacks()

        # Start all monitoring components
        self._start_monitoring_components()

        # Start synchronization thread
        self._start_synchronization()

        logging.info("DuckBot integration started")

    def stop(self):
        """Stop the integration system"""
        if not self.is_running:
            return

        self.is_running = False

        # Stop monitoring components
        self._stop_monitoring_components()

        # Stop synchronization thread
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)

        logging.info("DuckBot integration stopped")

    def _setup_event_callbacks(self):
        """Set up event callbacks for cross-component communication"""
        if self.training_monitor:
            self.training_monitor.add_callback(self._handle_training_event)

        if self.performance_monitor:
            self.performance_monitor.add_alert_callback(self._handle_performance_alert)

        if self.alerting_system:
            self.alerting_system.add_alert_callback(self._handle_alert)

    def _start_monitoring_components(self):
        """Start all monitoring components"""
        # Start training monitoring
        if self.training_monitor:
            self.training_monitor.start()

        # Start performance monitoring
        if self.performance_monitor:
            self.performance_monitor.start()

        # Start visualization
        if self.training_visualizer:
            self.training_visualizer.start()

    def _stop_monitoring_components(self):
        """Stop all monitoring components"""
        # Stop training monitoring
        if self.training_monitor:
            self.training_monitor.stop()

        # Stop performance monitoring
        if self.performance_monitor:
            self.performance_monitor.stop()

        # Stop visualization
        if self.training_visualizer:
            self.training_visualizer.stop()

    def _start_synchronization(self):
        """Start data synchronization thread"""
        def sync_loop():
            while self.is_running:
                try:
                    self._synchronize_data()
                    self.integration_stats['sync_cycles'] += 1
                    self.integration_stats['last_sync_time'] = datetime.now()
                    time.sleep(self.config.sync_interval)
                except Exception as e:
                    logging.error(f"Error in synchronization: {e}")
                    time.sleep(self.config.retry_delay)

        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()

    def _synchronize_data(self):
        """Synchronize data between DuckBot and training monitoring systems"""
        if not self.duckbot_monitoring:
            return

        try:
            # Synchronize training metrics
            if self.training_monitor:
                self._sync_training_metrics()

            # Synchronize performance metrics
            if self.performance_monitor:
                self._sync_performance_metrics()

            # Synchronize alerts
            if self.alerting_system:
                self._sync_alerts()

        except Exception as e:
            logging.error(f"Error synchronizing data: {e}")

    def _sync_training_metrics(self):
        """Synchronize training metrics with DuckBot"""
        if not self.config.forward_training_events:
            return

        try:
            # Get recent training metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=self.config.sync_interval)

            # Query training database for recent metrics
            recent_metrics = self.training_monitor.database.get_recent_metrics(
                start_time, end_time
            )

            # Forward to DuckBot monitoring
            for metric in recent_metrics:
                if self.config.forward_to_duckbot and self.duckbot_monitoring:
                    self.duckbot_monitoring.record_metric(
                        metric_name=f"training_{metric['metric_type']}",
                        metric_value=metric['value'],
                        tags={
                            'source': 'training_monitoring',
                            'run_id': metric['run_id'],
                            'epoch': metric['epoch'],
                            'step': metric['step']
                        }
                    )
                    self.integration_stats['events_forwarded'] += 1

                self.integration_stats['events_processed'] += 1

        except Exception as e:
            logging.error(f"Error synchronizing training metrics: {e}")

    def _sync_performance_metrics(self):
        """Synchronize performance metrics with DuckBot"""
        if not self.config.forward_performance_events:
            return

        try:
            # Get current performance metrics
            performance_summary = self.performance_monitor.get_performance_summary()

            # Forward resource utilization to DuckBot
            if self.config.forward_to_duckbot and self.duckbot_monitoring:
                resource_util = self.performance_monitor.get_resource_utilization()

                for device, utilization in resource_util.items():
                    self.duckbot_monitoring.record_metric(
                        metric_name=f"resource_utilization_{device}",
                        metric_value=utilization,
                        tags={
                            'source': 'performance_monitoring',
                            'device': device
                        }
                    )
                    self.integration_stats['events_forwarded'] += 1

            self.integration_stats['events_processed'] += 1

        except Exception as e:
            logging.error(f"Error synchronizing performance metrics: {e}")

    def _sync_alerts(self):
        """Synchronize alerts with DuckBot"""
        if not self.config.forward_alerts:
            return

        try:
            # Get recent alerts
            recent_alerts = self.alerting_system.database.get_alerts(
                start_time=datetime.now() - timedelta(seconds=self.config.sync_interval)
            )

            # Forward to DuckBot monitoring
            for alert in recent_alerts:
                if self.config.forward_to_duckbot and self.duckbot_monitoring:
                    self.duckbot_monitoring.record_event(
                        event_type=f"alert_{alert.severity.value}",
                        event_data={
                            'title': alert.title,
                            'message': alert.message,
                            'category': alert.category.value,
                            'source': alert.source,
                            'details': alert.details
                        }
                    )
                    self.integration_stats['events_forwarded'] += 1

                self.integration_stats['events_processed'] += 1

        except Exception as e:
            logging.error(f"Error synchronizing alerts: {e}")

    def _handle_training_event(self, event_data: Dict[str, Any]):
        """Handle training events"""
        self.integration_stats['events_processed'] += 1

        # Forward to DuckBot if configured
        if self.config.forward_to_duckbot and self.duckbot_monitoring:
            self.duckbot_monitoring.record_event(
                event_type="training_event",
                event_data=event_data
            )
            self.integration_stats['events_forwarded'] += 1

        # Log to structured logger
        if self.structured_logger:
            self.structured_logger.log_training_event(
                event_type=event_data.get('event_type', 'unknown'),
                message=event_data.get('message', ''),
                details=event_data.get('details', {}),
                run_id=event_data.get('run_id'),
                epoch=event_data.get('epoch'),
                step=event_data.get('step')
            )

        # Call event callbacks
        for callback in self.event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logging.error(f"Error in event callback: {e}")

    def _handle_performance_alert(self, alert_data: Dict[str, Any]):
        """Handle performance alerts"""
        self.integration_stats['events_processed'] += 1

        # Convert to training alert if alerting system is available
        if self.alerting_system:
            alert = Alert(
                alert_id=f"perf_{int(time.time())}",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                title=alert_data.get('message', 'Performance Alert'),
                message=alert_data.get('message', ''),
                details=alert_data
            )
            self.alerting_system.send_alert(alert)
            self.integration_stats['alerts_generated'] += 1

        # Forward to DuckBot if configured
        if self.config.forward_to_duckbot and self.duckbot_monitoring:
            self.duckbot_monitoring.record_event(
                event_type="performance_alert",
                event_data=alert_data
            )
            self.integration_stats['events_forwarded'] += 1

    def _handle_alert(self, alert: Alert):
        """Handle alerts from alerting system"""
        self.integration_stats['alerts_generated'] += 1

        # Forward to DuckBot if configured
        if self.config.forward_to_duckbot and self.duckbot_monitoring:
            self.duckbot_monitoring.record_event(
                event_type=f"alert_{alert.severity.value}",
                event_data={
                    'title': alert.title,
                    'message': alert.message,
                    'category': alert.category.value,
                    'source': alert.source,
                    'details': alert.details
                }
            )
            self.integration_stats['events_forwarded'] += 1

    def add_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add event callback"""
        self.event_callbacks.append(callback)

    def get_unified_status(self) -> Dict[str, Any]:
        """Get unified status of all monitoring systems"""
        status = {
            'integration_active': self.is_running,
            'integration_stats': self.integration_stats.copy(),
            'components': {
                'duckbot_monitoring': self.duckbot_monitoring is not None,
                'training_monitor': self.training_monitor is not None,
                'performance_monitor': self.performance_monitor is not None,
                'alerting_system': self.alerting_system is not None,
                'visualization': self.training_visualizer is not None,
                'early_stopping': self.early_stopping_manager is not None
            }
        }

        # Add component-specific status
        if self.training_monitor:
            status['training_status'] = self.training_monitor.get_status()

        if self.performance_monitor:
            status['performance_status'] = self.performance_monitor.get_performance_summary()

        if self.alerting_system:
            status['alerting_status'] = self.alerting_system.get_alert_stats()

        if self.duckbot_monitoring:
            try:
                status['duckbot_status'] = self.duckbot_monitoring.get_system_status()
            except:
                pass

        return status

    def get_unified_dashboard_data(self) -> Dict[str, Any]:
        """Get unified dashboard data"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'training_metrics': {},
            'performance_metrics': {},
            'alerts': [],
            'system_status': {}
        }

        # Get training metrics
        if self.training_monitor:
            try:
                dashboard_data['training_metrics'] = self.training_monitor.get_recent_summary()
            except:
                pass

        # Get performance metrics
        if self.performance_monitor:
            try:
                dashboard_data['performance_metrics'] = self.performance_monitor.get_performance_summary()
            except:
                pass

        # Get recent alerts
        if self.alerting_system:
            try:
                recent_alerts = self.alerting_system.database.get_alerts(
                    start_time=datetime.now() - timedelta(hours=1),
                    resolved=False
                )
                dashboard_data['alerts'] = [
                    {
                        'id': alert.alert_id,
                        'severity': alert.severity.value,
                        'category': alert.category.value,
                        'title': alert.title,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in recent_alerts
                ]
            except:
                pass

        # Get system status
        dashboard_data['system_status'] = self.get_unified_status()

        return dashboard_data

class UnifiedTrainingMonitor:
    """Unified interface for training monitoring"""

    def __init__(self, config: IntegrationConfig = None):
        self.config = config or IntegrationConfig()
        self.integration_manager = DuckBotIntegrationManager(config)

    def start_training_session(self, run_id: str, config: Dict[str, Any]) -> str:
        """Start a new training session"""
        session_id = f"session_{run_id}_{int(time.time())}"

        # Log session start
        if self.integration_manager.structured_logger:
            self.integration_manager.structured_logger.log_training_event(
                event_type="session_start",
                message=f"Training session started: {run_id}",
                details={
                    'session_id': session_id,
                    'run_id': run_id,
                    'config': config
                },
                run_id=run_id
            )

        # Send alert
        if self.integration_manager.alerting_system:
            alert = Alert(
                alert_id=f"session_start_{session_id}",
                timestamp=datetime.now(),
                severity=AlertSeverity.INFO,
                category=AlertCategory.TRAINING,
                title="Training Session Started",
                message=f"Training session {run_id} has started",
                details={
                    'session_id': session_id,
                    'run_id': run_id,
                    'config': config
                }
            )
            self.integration_manager.alerting_system.send_alert(alert)

        return session_id

    def log_training_step(self, run_id: str, epoch: int, step: int, metrics: Dict[str, float]):
        """Log a training step"""
        # Log to structured logger
        if self.integration_manager.structured_logger:
            self.integration_manager.structured_logger.log_training_event(
                event_type="training_step",
                message=f"Training step completed",
                details=metrics,
                run_id=run_id,
                epoch=epoch,
                step=step
            )

        # Update training monitor
        if self.integration_manager.training_monitor:
            self.integration_manager.training_monitor.record_metrics(
                run_id=run_id,
                epoch=epoch,
                step=step,
                metrics=metrics
            )

        # Check for early stopping
        if self.integration_manager.early_stopping_manager:
            self.integration_manager.early_stopping_manager.on_epoch_end(epoch, metrics)

    def end_training_session(self, run_id: str, session_id: str, status: str, details: Dict[str, Any]):
        """End a training session"""
        # Log session end
        if self.integration_manager.structured_logger:
            self.integration_manager.structured_logger.log_training_event(
                event_type="session_end",
                message=f"Training session ended: {status}",
                details={
                    'session_id': session_id,
                    'run_id': run_id,
                    'status': status,
                    'final_details': details
                },
                run_id=run_id
            )

        # Send alert
        if self.integration_manager.alerting_system:
            severity = AlertSeverity.INFO if status == "completed" else AlertSeverity.ERROR
            alert = Alert(
                alert_id=f"session_end_{session_id}",
                timestamp=datetime.now(),
                severity=severity,
                category=AlertCategory.TRAINING,
                title=f"Training Session {status.title()}",
                message=f"Training session {run_id} has {status}",
                details={
                    'session_id': session_id,
                    'run_id': run_id,
                    'status': status,
                    'final_details': details
                }
            )
            self.integration_manager.alerting_system.send_alert(alert)

    def start(self):
        """Start the unified monitoring system"""
        self.integration_manager.start()

    def stop(self):
        """Stop the unified monitoring system"""
        self.integration_manager.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return self.integration_manager.get_unified_status()

# Example usage and demo
def demo_duckbot_integration():
    """Demonstrate DuckBot integration functionality"""
    print("🔗 DuckBot Integration Demo")
    print("=" * 40)

    # Create integration manager
    config = IntegrationConfig(
        enable_duckbot_monitoring=True,
        enable_training_monitoring=True,
        enable_performance_monitoring=True,
        enable_alerting_system=True,
        enable_visualization=True,
        sync_interval=5.0,  # Faster sync for demo
        forward_to_duckbot=True
    )

    integration_manager = DuckBotIntegrationManager(config)

    # Add event callback
    def handle_event(event_data: Dict[str, Any]):
        print(f"📡 Event: {event_data.get('event_type', 'unknown')}")

    integration_manager.add_event_callback(handle_event)

    # Start integration
    print("\n🚀 Starting DuckBot integration...")
    integration_manager.start()

    try:
        # Simulate training activity
        print("📊 Simulating training activity...")

        # Start training session
        run_id = "demo_training_run"
        config = {
            "model": "bert-base-uncased",
            "batch_size": 32,
            "learning_rate": 0.001,
            "epochs": 5
        }

        session_id = integration_manager.start_training_session(run_id, config)
        print(f"🎯 Training session started: {session_id}")

        # Simulate training steps
        for epoch in range(3):
            for step in range(5):
                # Simulate metrics
                metrics = {
                    "loss": 2.0 * (0.9 ** epoch) + np.random.normal(0, 0.1),
                    "accuracy": 0.5 + 0.1 * epoch + np.random.normal(0, 0.05),
                    "val_loss": 2.2 * (0.9 ** epoch) + np.random.normal(0, 0.1),
                    "val_accuracy": 0.45 + 0.1 * epoch + np.random.normal(0, 0.05)
                }

                integration_manager.log_training_step(run_id, epoch, step, metrics)

                time.sleep(0.5)  # Simulate training time

            # Show status after each epoch
            status = integration_manager.get_unified_status()
            print(f"\n📈 Status after epoch {epoch + 1}:")
            print(f"  Events processed: {status['integration_stats']['events_processed']}")
            print(f"  Events forwarded: {status['integration_stats']['events_forwarded']}")
            print(f"  Alerts generated: {status['integration_stats']['alerts_generated']}")
            print(f"  Sync cycles: {status['integration_stats']['sync_cycles']}")

            # Show component status
            print(f"  Components active:")
            for component, active in status['components'].items():
                print(f"    {component}: {'✓' if active else '✗'}")

        # End training session
        integration_manager.end_training_session(
            run_id, session_id, "completed",
            {"total_epochs": 3, "total_steps": 15, "final_accuracy": 0.75}
        )

        # Wait for final sync
        time.sleep(2)

        # Show final status
        final_status = integration_manager.get_unified_status()
        print(f"\n📊 Final Integration Status:")
        print(f"  Total events processed: {final_status['integration_stats']['events_processed']}")
        print(f"  Total events forwarded: {final_status['integration_stats']['events_forwarded']}")
        print(f"  Total alerts generated: {final_status['integration_stats']['alerts_generated']}")
        print(f"  Total sync cycles: {final_status['integration_stats']['sync_cycles']}")

        # Show dashboard data
        dashboard_data = integration_manager.get_unified_dashboard_data()
        print(f"\n🎛️  Dashboard Summary:")
        print(f"  Recent alerts: {len(dashboard_data['alerts'])}")
        print(f"  Training metrics available: {len(dashboard_data['training_metrics']) > 0}")
        print(f"  Performance metrics available: {len(dashboard_data['performance_metrics']) > 0}")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")

    finally:
        # Stop integration
        integration_manager.stop()

    return integration_manager

if __name__ == "__main__":
    import threading
    demo_duckbot_integration()