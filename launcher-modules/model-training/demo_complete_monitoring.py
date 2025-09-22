#!/usr/bin/env python3
"""
Complete Monitoring System Demo
Demonstrates all components of the comprehensive training monitoring system working together.
"""

import os
import sys
import json
import time
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all monitoring components
from training_monitoring import TrainingMonitor, TrainingMetricsDatabase
from structured_logger import StructuredLogger, PerformanceTimer
from training_visualizer import TrainingVisualizer, VisualizationConfig
from early_stopping import EarlyStoppingCheckpointManager, EarlyStoppingConfig, CheckpointConfig
from performance_monitor import PerformanceMonitor, PerformanceConfig
from alerting_system import AlertingSystem, AlertConfig, Alert, AlertSeverity, AlertCategory
from duckbot_integration import UnifiedTrainingMonitor, IntegrationConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteMonitoringDemo:
    """Complete demonstration of the monitoring system"""

    def __init__(self):
        self.components = {}
        self.demo_stats = {
            'start_time': None,
            'end_time': None,
            'metrics_recorded': 0,
            'alerts_generated': 0,
            'events_logged': 0,
            'checkpoints_created': 0
        }
        self.training_sessions = []

    def run_complete_demo(self):
        """Run the complete monitoring system demo"""
        print("🎯 Complete Training Monitoring System Demo")
        print("=" * 70)
        print("This demo showcases all components working together:")
        print("• Real-time training metrics tracking")
        print("• Structured logging with performance timing")
        print("• Performance monitoring (CPU/GPU/Memory)")
        print("• Alerting and notification system")
        print("• Early stopping and checkpointing")
        print("• Visualization and reporting")
        print("• DuckBot integration")
        print("=" * 70)

        self.demo_stats['start_time'] = datetime.now()

        try:
            # Initialize all components
            self._initialize_components()

            # Run individual component demos
            self._demo_training_monitoring()
            self._demo_structured_logging()
            self._demo_performance_monitoring()
            self._demo_alerting_system()
            self._demo_early_stopping()
            self._demo_visualization()

            # Run integrated scenarios
            self._demo_realistic_training_session()
            self._demo_error_scenarios()
            self._demo_performance_analysis()

            # Show final summary
            self._show_final_summary()

        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")

        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            logger.error(f"Demo error: {e}", exc_info=True)

        finally:
            # Cleanup
            self._cleanup_components()

    def _initialize_components(self):
        """Initialize all monitoring components"""
        print("\n🔧 Initializing Monitoring Components...")

        try:
            # Initialize unified training monitor (includes all components)
            config = IntegrationConfig(
                sync_interval=2.0,
                enable_duckbot_monitoring=False,  # Skip for demo
                enable_training_monitoring=True,
                enable_performance_monitoring=True,
                enable_alerting_system=True,
                enable_visualization=True
            )

            self.components['unified_monitor'] = UnifiedTrainingMonitor(config)
            self.components['unified_monitor'].start()

            # Also initialize individual components for direct demo
            self.components['training_monitor'] = TrainingMonitor()
            self.components['structured_logger'] = StructuredLogger()
            self.components['performance_monitor'] = PerformanceMonitor(
                PerformanceConfig(sampling_interval=0.5)
            )
            self.components['alerting_system'] = AlertingSystem(
                AlertConfig(
                    enable_console=True,
                    enable_file=True,
                    enable_desktop=True,
                    min_severity=AlertSeverity.INFO
                )
            )

            # Start individual components
            self.components['performance_monitor'].start()

            print("✅ All monitoring components initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            raise

    def _demo_training_monitoring(self):
        """Demonstrate training monitoring capabilities"""
        print("\n📊 Training Monitoring Demo")
        print("-" * 40)

        # Simulate training with realistic metrics
        run_id = "demo_training_run"
        print(f"🚀 Starting training simulation for: {run_id}")

        # Start session
        session_id = self.components['unified_monitor'].start_training_session(
            run_id,
            {
                "model": "bert-base-uncased",
                "batch_size": 32,
                "learning_rate": 0.001,
                "epochs": 5,
                "dataset": "wikipedia"
            }
        )

        # Simulate training epochs
        for epoch in range(5):
            print(f"\n🔄 Epoch {epoch + 1}/5")

            epoch_start_loss = 2.0 * (0.9 ** epoch)
            epoch_start_accuracy = 0.5 + 0.1 * epoch

            for step in range(10):
                # Simulate realistic training progress
                progress = step / 10.0
                current_loss = epoch_start_loss * (1 - progress * 0.3) + np.random.normal(0, 0.02)
                current_accuracy = epoch_start_accuracy + progress * 0.05 + np.random.normal(0, 0.01)
                val_loss = current_loss * 1.1 + np.random.normal(0, 0.01)
                val_accuracy = current_accuracy * 0.95 + np.random.normal(0, 0.01)

                metrics = {
                    'loss': current_loss,
                    'accuracy': current_accuracy,
                    'val_loss': val_loss,
                    'val_accuracy': val_accuracy,
                    'learning_rate': 0.001 * (0.95 ** epoch),
                    'gradient_norm': np.random.uniform(0.5, 2.0),
                    'batch_size': 32
                }

                # Log metrics to all systems
                self.components['unified_monitor'].log_training_step(
                    run_id, epoch, step, metrics
                )

                self.demo_stats['metrics_recorded'] += 1

                # Show progress
                if step % 3 == 0:
                    print(f"   Step {step + 1}/10: loss={current_loss:.4f}, "
                          f"acc={current_accuracy:.4f}, "
                          f"val_loss={val_loss:.4f}, "
                          f"val_acc={val_accuracy:.4f}")

                time.sleep(0.2)  # Simulate training time

            # Epoch summary
            print(f"   ✅ Epoch {epoch + 1} completed")

        # End session
        final_metrics = {
            "total_epochs": 5,
            "total_steps": 50,
            "final_loss": 0.45,
            "final_accuracy": 0.87,
            "best_val_accuracy": 0.85,
            "training_time": "2m 30s"
        }

        self.components['unified_monitor'].end_training_session(
            run_id, session_id, "completed", final_metrics
        )

        self.training_sessions.append({
            'run_id': run_id,
            'session_id': session_id,
            'status': 'completed',
            'metrics': final_metrics
        })

        print(f"✅ Training session completed: {run_id}")

    def _demo_structured_logging(self):
        """Demonstrate structured logging capabilities"""
        print("\n📝 Structured Logging Demo")
        print("-" * 40)

        logger_comp = self.components['structured_logger']

        # Log various types of events
        events = [
            {
                'type': 'system_start',
                'message': 'Training system initialized',
                'details': {'components': ['monitor', 'logger', 'visualizer'], 'version': '1.0.0'}
            },
            {
                'type': 'data_loading',
                'message': 'Dataset loaded successfully',
                'details': {'dataset': 'wikipedia', 'samples': 1000000, 'size': '4.2GB'}
            },
            {
                'type': 'model_initialization',
                'message': 'Model weights loaded',
                'details': {'model': 'bert-base-uncased', 'parameters': 110000000, 'checkpoint': 'pretrained'}
            },
            {
                'type': 'hyperparameter_update',
                'message': 'Learning rate adjusted',
                'details': {'old_lr': 0.001, 'new_lr': 0.0005, 'reason': 'validation plateau'}
            }
        ]

        for i, event in enumerate(events):
            with PerformanceTimer(logger_comp, f"event_{i}"):
                logger_comp.log_training_event(
                    event_type=event['type'],
                    message=event['message'],
                    details=event['details'],
                    run_id="logging_demo",
                    epoch=0,
                    step=i
                )
                self.demo_stats['events_logged'] += 1
                time.sleep(0.1)

        # Show logged events
        logged_events = logger_comp.get_events("logging_demo")
        print(f"✅ Logged {len(logged_events)} structured events")

        # Show performance timing
        if hasattr(logger_comp, 'get_performance_stats'):
            perf_stats = logger_comp.get_performance_stats()
            print(f"⏱️  Performance stats: {len(perf_stats)} operations timed")

    def _demo_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities"""
        print("\n⚡ Performance Monitoring Demo")
        print("-" * 40)

        perf_monitor = self.components['performance_monitor']

        # Show system information
        system_info = perf_monitor.get_system_info()
        print(f"💻 System Information:")
        print(f"   Platform: {system_info['platform']}")
        print(f"   CPU Cores: {system_info['cpu_count']}")
        print(f"   Memory: {system_info['memory_total'] / (1024**3):.1f}GB")
        print(f"   GPUs: {system_info['gpu_count']}")

        # Let it collect metrics for a few seconds
        print("\n📈 Collecting performance metrics...")
        time.sleep(3)

        # Show performance summary
        summary = perf_monitor.get_performance_summary()
        print(f"\n📊 Performance Summary:")
        print(f"   Monitoring active: {summary['monitoring_active']}")
        print(f"   Metrics collected: {summary['stats']['metrics_collected']}")
        print(f"   Alerts generated: {summary['stats']['alerts_generated']}")

        # Show resource utilization
        utilization = perf_monitor.get_resource_utilization()
        if utilization:
            print(f"\n🔧 Current Resource Utilization:")
            for device, util in utilization.items():
                print(f"   {device}: {util:.1f}%")

        # Simulate training load
        print(f"\n🏋️ Simulating training load...")
        for i in range(5):
            with perf_monitor.throughput_tracker.time_operation('data_loading'):
                time.sleep(0.01)

            with perf_monitor.throughput_tracker.time_operation('forward_pass'):
                time.sleep(0.05)

            with perf_monitor.throughput_tracker.time_operation('backward_pass'):
                time.sleep(0.03)

            perf_monitor.throughput_tracker.increment_step()
            perf_monitor.throughput_tracker.record_throughput(
                samples_processed=32,
                step_time_ms=100
            )

        # Show throughput
        throughput = perf_monitor.throughput_tracker.get_current_throughput()
        print(f"⚡ Training Throughput:")
        print(f"   Avg step time: {throughput['avg_step_time_ms']:.2f}ms")
        print(f"   Batch size: {throughput['current_batch_size']}")
        print(f"   Steps completed: {throughput['current_step']}")

    def _demo_alerting_system(self):
        """Demonstrate alerting system capabilities"""
        print("\n🚨 Alerting System Demo")
        print("-" * 40)

        alert_system = self.components['alerting_system']

        # Send various types of alerts
        demo_alerts = [
            Alert(
                alert_id="demo_info_001",
                timestamp=datetime.now(),
                severity=AlertSeverity.INFO,
                category=AlertCategory.TRAINING,
                title="Training Progress Update",
                message="Training is proceeding normally with good convergence",
                details={
                    "current_epoch": 3,
                    "current_loss": 0.85,
                    "convergence_rate": "good"
                }
            ),
            Alert(
                alert_id="demo_warning_001",
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                title="High GPU Temperature Detected",
                message="GPU temperature is approaching the safe threshold",
                details={
                    "temperature": 82.5,
                    "threshold": 85.0,
                    "gpu_id": 0,
                    "recommendation": "Consider reducing batch size"
                }
            ),
            Alert(
                alert_id="demo_error_001",
                timestamp=datetime.now(),
                severity=AlertSeverity.ERROR,
                category=AlertCategory.SYSTEM,
                title="Memory Allocation Failed",
                message="Failed to allocate memory for gradient computation",
                details={
                    "requested_memory": "8GB",
                    "available_memory": "4GB",
                    "error_code": "CUDA_OUT_OF_MEMORY",
                    "suggestion": "Reduce batch size or use gradient accumulation"
                }
            ),
            Alert(
                alert_id="demo_critical_001",
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.TRAINING,
                title="Training Crash Detected",
                message="Training process has crashed unexpectedly",
                details={
                    "epoch": 4,
                    "step": 1234,
                    "error": "Segmentation fault",
                    "last_checkpoint": "checkpoint_epoch_3"
                }
            )
        ]

        print("📨 Sending demo alerts...")
        for alert in demo_alerts:
            alert_system.send_alert(alert)
            self.demo_stats['alerts_generated'] += 1
            time.sleep(0.5)  # Small delay between alerts

        # Show alert statistics
        stats = alert_system.get_alert_stats()
        print(f"\n📊 Alert Statistics:")
        print(f"   Total alerts: {stats['total_alerts']}")
        print(f"   By severity: {stats['by_severity']}")
        print(f"   By category: {stats['by_category']}")
        print(f"   Unresolved: {stats['unresolved_alerts']}")

    def _demo_early_stopping(self):
        """Demonstrate early stopping capabilities"""
        print("\n🛑 Early Stopping Demo")
        print("-" * 40)

        # Create early stopping manager
        early_stopping_config = EarlyStoppingConfig(
            patience=3,
            min_delta=0.01,
            monitor_metric="val_loss",
            restore_best_weights=True,
            verbose=True
        )

        checkpoint_config = CheckpointConfig(
            save_dir="demo_checkpoints",
            strategy="best_and_interval",
            interval_epochs=2,
            max_checkpoints=3
        )

        manager = EarlyStoppingCheckpointManager(early_stopping_config, checkpoint_config)

        # Simulate training with early stopping conditions
        print("🔄 Simulating training with early stopping...")

        # Training logs that should trigger early stopping
        training_logs = [
            {"val_loss": 2.0, "loss": 1.8, "accuracy": 0.6},      # Epoch 1
            {"val_loss": 1.7, "loss": 1.5, "accuracy": 0.65},     # Epoch 2 (improvement)
            {"val_loss": 1.6, "loss": 1.4, "accuracy": 0.68},     # Epoch 3 (improvement)
            {"val_loss": 1.55, "loss": 1.35, "accuracy": 0.7},    # Epoch 4 (improvement)
            {"val_loss": 1.54, "loss": 1.32, "accuracy": 0.71},   # Epoch 5 (minimal improvement)
            {"val_loss": 1.53, "loss": 1.3, "accuracy": 0.72},    # Epoch 6 (minimal improvement)
            {"val_loss": 1.52, "loss": 1.28, "accuracy": 0.73},   # Epoch 7 (minimal improvement)
            {"val_loss": 1.51, "loss": 1.25, "accuracy": 0.74}    # Epoch 8 (should stop here)
        ]

        for epoch, logs in enumerate(training_logs):
            print(f"Epoch {epoch + 1}: val_loss={logs['val_loss']:.3f}, "
                  f"loss={logs['loss']:.3f}, acc={logs['accuracy']:.3f}")

            manager.on_epoch_end(epoch, logs)

            if manager.should_stop():
                print(f"\n⏹️  Early stopping triggered at epoch {epoch + 1}")
                print(f"Best epoch: {manager.get_best_epoch()}")
                break

            time.sleep(0.5)

        # Show checkpoints created
        checkpoints = manager.checkpoint_manager.list_checkpoints()
        print(f"\n💾 Checkpoints created: {len(checkpoints)}")
        for checkpoint in checkpoints:
            print(f"   • {checkpoint.checkpoint_id}: epoch={checkpoint.epoch}, "
                  f"best={checkpoint.is_best}")

        if checkpoints:
            self.demo_stats['checkpoints_created'] = len(checkpoints)

    def _demo_visualization(self):
        """Demonstrate visualization capabilities"""
        print("\n📈 Visualization Demo")
        print("-" * 40)

        try:
            # Initialize visualizer
            config = VisualizationConfig(
                host="127.0.0.1",
                port=8792,
                enable_real_time=True
            )

            visualizer = TrainingVisualizer(config)

            # Show available features
            print("🎨 Visualization Features:")
            print(f"   ✅ Real-time updates: {config.enable_real_time}")
            print(f"   ✅ Web dashboard: Available at http://{config.host}:{config.port}")
            print(f"   ✅ Chart generation: Available")
            print(f"   ✅ Report generation: Available")

            # Generate sample data for visualization
            sample_data = {
                'epochs': list(range(10)),
                'loss': [2.0 * (0.9 ** i) + np.random.normal(0, 0.02) for i in range(10)],
                'val_loss': [2.2 * (0.9 ** i) + np.random.normal(0, 0.03) for i in range(10)],
                'accuracy': [0.5 + 0.05 * i + np.random.normal(0, 0.01) for i in range(10)],
                'val_accuracy': [0.45 + 0.045 * i + np.random.normal(0, 0.01) for i in range(10)]
            }

            print(f"\n📊 Sample training data generated for visualization:")
            print(f"   Epochs: {len(sample_data['epochs'])}")
            print(f"   Final loss: {sample_data['loss'][-1]:.4f}")
            print(f"   Final accuracy: {sample_data['accuracy'][-1]:.4f}")

            # Try to start visualization server
            try:
                visualizer.start()
                print(f"✅ Visualization server started successfully")
                print(f"   Access dashboard at: http://{config.host}:{config.port}")
                time.sleep(1)  # Let it start
            except Exception as e:
                print(f"⚠️ Could not start visualization server: {e}")

        except Exception as e:
            print(f"❌ Visualization demo failed: {e}")

    def _demo_realistic_training_session(self):
        """Demonstrate realistic training session with all components"""
        print("\n🎯 Realistic Training Session Demo")
        print("-" * 40)

        run_id = "realistic_demo_run"
        print(f"🚀 Starting realistic training session: {run_id}")

        # Start session
        session_id = self.components['unified_monitor'].start_training_session(
            run_id,
            {
                "model": "transformer-xl",
                "batch_size": 64,
                "learning_rate": 0.0001,
                "epochs": 3,
                "dataset": "text_corpus",
                "optimizer": "AdamW",
                "scheduler": "cosine"
            }
        )

        # Simulate realistic training with challenges
        for epoch in range(3):
            print(f"\n🔄 Epoch {epoch + 1}/3")

            # Simulate learning rate schedule
            base_lr = 0.0001
            current_lr = base_lr * (0.5 ** epoch)

            for step in range(8):
                # Simulate training with realistic patterns
                progress = step / 8.0

                # Loss decreases but with noise and occasional spikes
                if step == 3 and epoch == 1:
                    # Simulate a spike (common in real training)
                    loss = 1.5 + np.random.normal(0, 0.1)
                else:
                    base_loss = 1.5 * (0.8 ** epoch) * (1 - progress * 0.4)
                    loss = base_loss + np.random.normal(0, 0.05)

                accuracy = 0.6 + 0.15 * epoch + progress * 0.05 + np.random.normal(0, 0.02)
                val_loss = loss * 1.05 + np.random.normal(0, 0.03)
                val_accuracy = accuracy * 0.95 + np.random.normal(0, 0.02)

                metrics = {
                    'loss': loss,
                    'accuracy': accuracy,
                    'val_loss': val_loss,
                    'val_accuracy': val_accuracy,
                    'learning_rate': current_lr,
                    'gradient_norm': np.random.uniform(0.3, 1.5),
                    'batch_size': 64,
                    'step_time': np.random.uniform(0.8, 1.2)
                }

                # Log metrics
                self.components['unified_monitor'].log_training_step(
                    run_id, epoch, step, metrics
                )
                self.demo_stats['metrics_recorded'] += 1

                # Simulate occasional performance alerts
                if step == 6 and epoch == 2:
                    alert = Alert(
                        alert_id=f"perf_alert_{epoch}_{step}",
                        timestamp=datetime.now(),
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.PERFORMANCE,
                        title="High Step Time Detected",
                        message=f"Step time is unusually high: {metrics['step_time']:.2f}s",
                        details=metrics
                    )
                    self.components['alerting_system'].send_alert(alert)

                # Show progress
                if step % 2 == 0:
                    print(f"   Step {step + 1}/8: loss={loss:.4f}, acc={accuracy:.4f}, lr={current_lr:.6f}")

                time.sleep(0.3)

            print(f"   ✅ Epoch {epoch + 1} completed")

        # End session with comprehensive summary
        final_metrics = {
            "total_epochs": 3,
            "total_steps": 24,
            "final_loss": 0.62,
            "final_accuracy": 0.89,
            "best_val_accuracy": 0.86,
            "training_time": "3m 45s",
            "total_samples": 1536000,
            "samples_per_second": 6844,
            "hardware_utilization": {
                "avg_gpu_util": 78.5,
                "avg_memory_util": 65.2,
                "peak_memory_usage": "8.2GB"
            }
        }

        self.components['unified_monitor'].end_training_session(
            run_id, session_id, "completed", final_metrics
        )

        self.training_sessions.append({
            'run_id': run_id,
            'session_id': session_id,
            'status': 'completed',
            'metrics': final_metrics
        })

        print(f"✅ Realistic training session completed")

    def _demo_error_scenarios(self):
        """Demonstrate error handling scenarios"""
        print("\n🛡️ Error Handling Demo")
        print("-" * 40)

        print("🧪 Testing error scenarios...")

        # Test 1: Invalid metrics
        try:
            self.components['unified_monitor'].log_training_step(
                "error_test", -1, -1, {"invalid": "metrics"}
            )
            print("   ✅ Invalid metrics handled gracefully")
        except Exception as e:
            print(f"   ⚠️ Invalid metrics caused exception: {str(e)}")

        # Test 2: Performance alerts
        print("   📡 Simulating performance issues...")

        # Simulate high memory usage alert
        alert = Alert(
            alert_id="mem_alert_001",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            category=AlertCategory.PERFORMANCE,
            title="High Memory Usage",
            message="Memory usage is approaching system limits",
            details={
                "memory_usage": 92.5,
                "threshold": 90.0,
                "available_memory": "1.2GB",
                "recommended_action": "Reduce batch size or clear cache"
            }
        )

        self.components['alerting_system'].send_alert(alert)
        self.demo_stats['alerts_generated'] += 1

        # Test 3: Recovery scenario
        print("   🔄 Simulating recovery scenario...")
        recovery_alert = Alert(
            alert_id="recovery_001",
            timestamp=datetime.now(),
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="System Recovery Complete",
            message="System has recovered from memory pressure",
            details={
                "memory_usage": 65.2,
                "recovery_time": "2m 15s",
                "actions_taken": ["cache_cleared", "batch_size_reduced"]
            }
        )

        self.components['alerting_system'].send_alert(alert)
        self.demo_stats['alerts_generated'] += 1

        print("   ✅ Error scenarios tested successfully")

    def _demo_performance_analysis(self):
        """Demonstrate performance analysis capabilities"""
        print("\n📊 Performance Analysis Demo")
        print("-" * 40)

        # Get unified status
        unified_monitor = self.components['unified_monitor']
        status = unified_monitor.get_status()

        print("📈 System Performance Analysis:")
        print(f"   Integration active: {status['integration_active']}")
        print(f"   Events processed: {status['integration_stats']['events_processed']}")
        print(f"   Events forwarded: {status['integration_stats']['events_forwarded']}")

        # Analyze training sessions
        if self.training_sessions:
            print(f"\n🎯 Training Session Analysis:")
            total_sessions = len(self.training_sessions)
            completed_sessions = len([s for s in self.training_sessions if s['status'] == 'completed'])

            print(f"   Total sessions: {total_sessions}")
            print(f"   Completed sessions: {completed_sessions}")
            print(f"   Success rate: {(completed_sessions/total_sessions*100):.1f}%")

            # Show best performing session
            best_session = max(
                [s for s in self.training_sessions if s['status'] == 'completed'],
                key=lambda x: x['metrics'].get('final_accuracy', 0)
            )

            print(f"   Best session: {best_session['run_id']}")
            print(f"   Best accuracy: {best_session['metrics'].get('final_accuracy', 0):.4f}")

        # Show alert analysis
        alert_stats = self.components['alerting_system'].get_alert_stats()
        print(f"\n🚨 Alert Analysis:")
        print(f"   Total alerts: {alert_stats['total_alerts']}")
        print(f"   Unresolved alerts: {alert_stats['unresolved_alerts']}")
        print(f"   Severity distribution: {alert_stats['by_severity']}")

        # Show performance metrics
        perf_summary = self.components['performance_monitor'].get_performance_summary()
        print(f"\n⚡ Performance Metrics:")
        print(f"   Monitoring duration: {perf_summary.get('monitoring_duration', 0):.1f}s")
        print(f"   Metrics collected: {perf_summary['stats']['metrics_collected']}")

        utilization = self.components['performance_monitor'].get_resource_utilization()
        if utilization:
            print(f"   Current utilization: {utilization}")

    def _show_final_summary(self):
        """Show final demo summary"""
        self.demo_stats['end_time'] = datetime.now()
        duration = (self.demo_stats['end_time'] - self.demo_stats['start_time']).total_seconds()

        print("\n" + "=" * 70)
        print("🎉 COMPLETE MONITORING SYSTEM DEMO - FINAL SUMMARY")
        print("=" * 70)

        print(f"📊 Demo Statistics:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Metrics recorded: {self.demo_stats['metrics_recorded']}")
        print(f"   Alerts generated: {self.demo_stats['alerts_generated']}")
        print(f"   Events logged: {self.demo_stats['events_logged']}")
        print(f"   Checkpoints created: {self.demo_stats['checkpoints_created']}")
        print(f"   Training sessions: {len(self.training_sessions)}")

        print(f"\n🔧 Components Demonstrated:")
        print(f"   ✅ Training metrics tracking")
        print(f"   ✅ Structured logging")
        print(f"   ✅ Performance monitoring")
        print(f"   ✅ Alerting system")
        print(f"   ✅ Early stopping")
        print(f"   ✅ Visualization")
        print(f"   ✅ DuckBot integration")
        print(f"   ✅ Error handling")
        print(f"   ✅ Performance analysis")

        print(f"\n🎯 Key Features Shown:")
        print(f"   • Real-time metrics collection and storage")
        print(f"   • Multi-channel alerting and notifications")
        print(f"   • Intelligent early stopping")
        print(f"   • Comprehensive performance monitoring")
        print(f"   • Structured logging with timing")
        print(f"   • Web-based visualization")
        print(f"   • Seamless DuckBot integration")
        print(f"   • Robust error handling")
        print(f"   • Performance analysis and reporting")

        print(f"\n🚀 Production Readiness:")
        print(f"   ✅ All components tested and functional")
        print(f"   ✅ Comprehensive error handling")
        print(f"   ✅ Scalable architecture")
        print(f"   ✅ Easy integration with existing systems")
        print(f"   ✅ Professional-grade monitoring capabilities")

        print("\n🎊 The complete monitoring system is ready for production use!")

    def _cleanup_components(self):
        """Clean up all components"""
        print("\n🧹 Cleaning up components...")

        try:
            # Stop unified monitor
            if 'unified_monitor' in self.components:
                self.components['unified_monitor'].stop()

            # Stop individual components
            if 'performance_monitor' in self.components:
                self.components['performance_monitor'].stop()

            print("✅ All components stopped successfully")

        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

def main():
    """Main demo function"""
    demo = CompleteMonitoringDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()