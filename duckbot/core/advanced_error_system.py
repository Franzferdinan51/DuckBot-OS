#!/usr/bin/env python3
"""
Advanced Error Handling System Integration for DuckBot v4.2
Main integration file that brings together all error handling components
"""

import os
import sys
import time
import json
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path

# Import all error handling components
try:
    from duckbot.core.error_handling import (
        ErrorContext, ErrorSeverity, ErrorCategory, RecoveryAction, RecoveryStrategy,
        AdvancedErrorHandler, get_advanced_error_handler, handle_errors, ErrorHandlerContext
    )
    from duckbot.core.error_monitoring import (
        ErrorAnalyticsEngine, RealTimeErrorMonitor, AlertRule, AlertThreshold,
        get_error_analytics_engine, get_realtime_monitor
    )
    from duckbot.core.self_healing import (
        HealthMonitor, AutoRepairEngine, SelfHealingSystem, get_self_healing_system
    )
    from duckbot.core.recovery_workflows import (
        RecoveryWorkflowManager, RecoveryWorkflow, WorkflowStep, get_recovery_workflow_manager
    )
    from duckbot.core.error_integration import (
        ErrorIntegrationManager, IntegrationMetrics, get_error_integration_manager,
        handle_error_integrated
    )
    from duckbot.core.recovery_dashboard import (
        RecoveryDashboard, DashboardConfig, get_recovery_dashboard
    )
    from duckbot.core.logging_setup import get_logger
    from duckbot.services.server_manager import ServerManager, ServiceStatus
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import DuckBot components: {e}")

class AdvancedErrorSystem:
    """Main coordinator for the advanced error handling system"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("advanced_error_system")
        self.server_manager = server_manager

        # System components
        self.error_handler = None
        self.analytics_engine = None
        self.realtime_monitor = None
        self.self_healing = None
        self.workflow_manager = None
        self.integration_manager = None
        self.dashboard = None

        # System state
        self.system_initialized = False
        self.system_running = False
        self.start_time = None

        # Configuration
        self.config = self._load_system_config()

        # Performance metrics
        self.metrics = {
            'errors_handled': 0,
            'recoveries_executed': 0,
            'workflows_executed': 0,
            'health_checks_performed': 0,
            'alerts_triggered': 0,
            'dashboard_requests': 0
        }

        self.logger.info("🚀 Advanced Error Handling System v4.2 initializing...")

    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration"""
        default_config = {
            "error_handling": {
                "enabled": True,
                "auto_recovery": True,
                "max_error_history": 1000,
                "classification_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "real_time": True,
                "analytics": True,
                "prediction": True,
                "alerting": True
            },
            "self_healing": {
                "enabled": True,
                "auto_repair": True,
                "health_checks": True,
                "diagnostics": True
            },
            "workflows": {
                "enabled": True,
                "auto_execute": True,
                "rollback": True
            },
            "dashboard": {
                "enabled": True,
                "port": 8790,
                "host": "127.0.0.1",
                "theme": "dark",
                "auto_refresh": 30
            },
            "integration": {
                "enabled": True,
                "data_sync": True,
                "health_monitoring": True
            }
        }

        config_file = Path(__file__).parent.parent / "config" / "advanced_error_system.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with default config
                    self._merge_configs(default_config, loaded_config)
            except Exception as e:
                self.logger.error(f"Failed to load system config: {e}")

        return default_config

    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value

    def initialize_system(self) -> bool:
        """Initialize all system components"""
        if self.system_initialized:
            self.logger.warning("System already initialized")
            return True

        self.logger.info("🔧 Initializing Advanced Error Handling System components...")

        try:
            # Step 1: Initialize error handling
            if self.config["error_handling"]["enabled"]:
                self.logger.info("  - Error Handler...")
                self.error_handler = get_advanced_error_handler(self.server_manager)
                self.logger.info("    ✅ Error Handler initialized")

            # Step 2: Initialize monitoring and analytics
            if self.config["monitoring"]["enabled"]:
                self.logger.info("  - Analytics Engine...")
                self.analytics_engine = get_error_analytics_engine()

                if self.config["monitoring"]["real_time"]:
                    self.logger.info("  - Real-time Monitor...")
                    self.realtime_monitor = get_realtime_monitor()

                self.logger.info("    ✅ Monitoring system initialized")

            # Step 3: Initialize self-healing
            if self.config["self_healing"]["enabled"]:
                self.logger.info("  - Self-Healing System...")
                self.self_healing = get_self_healing_system(self.server_manager)
                self.logger.info("    ✅ Self-Healing system initialized")

            # Step 4: Initialize workflow management
            if self.config["workflows"]["enabled"]:
                self.logger.info("  - Workflow Manager...")
                self.workflow_manager = get_recovery_workflow_manager(self.server_manager)
                self.logger.info("    ✅ Workflow Manager initialized")

            # Step 5: Initialize integration manager
            if self.config["integration"]["enabled"]:
                self.logger.info("  - Integration Manager...")
                self.integration_manager = get_error_integration_manager(self.server_manager)
                self.logger.info("    ✅ Integration Manager initialized")

            # Step 6: Initialize dashboard
            if self.config["dashboard"]["enabled"]:
                self.logger.info("  - Recovery Dashboard...")
                self.dashboard = get_recovery_dashboard(self.integration_manager)
                self.logger.info("    ✅ Recovery Dashboard initialized")

            # Step 7: Setup component integration
            self.logger.info("  - Component Integration...")
            self._setup_component_integration()
            self.logger.info("    ✅ Component integration complete")

            self.system_initialized = True
            self.logger.info("🎉 Advanced Error Handling System v4.2 initialized successfully!")

            # Print system summary
            self._print_system_summary()

            return True

        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            return False

    def _setup_component_integration(self):
        """Setup integration between all components"""
        if not self.integration_manager:
            return

        # The integration manager already handles component integration
        # We just need to ensure it's properly connected

        # Add custom error handlers if needed
        def on_error_handled(error, service_name, operation, severity, result):
            self.metrics['errors_handled'] += 1
            self.logger.debug(f"Error handled: {service_name}.{operation} -> {result['final_status']}")

        def on_health_update(metrics):
            self.metrics['health_checks_performed'] += 1
            # Update system metrics
            self._update_system_metrics(metrics)

        # Register handlers with integration manager
        self.integration_manager.add_error_handler(on_error_handled)
        self.integration_manager.add_health_handler(on_health_update)

    def _update_system_metrics(self, metrics: IntegrationMetrics):
        """Update system metrics from integration metrics"""
        self.metrics['auto_recoveries_executed'] = metrics.auto_recoveries_executed
        self.metrics['alerts_triggered'] = metrics.alerts_triggered

        # Additional metrics can be extracted from individual components

    def start_system(self) -> bool:
        """Start the advanced error handling system"""
        if not self.system_initialized:
            self.logger.error("System must be initialized before starting")
            return False

        if self.system_running:
            self.logger.warning("System is already running")
            return True

        self.logger.info("🚀 Starting Advanced Error Handling System v4.2...")
        self.start_time = time.time()

        try:
            # Start individual components
            if self.error_handler:
                self.logger.info("  - Starting Error Handler monitoring...")
                # Error handler monitoring is started automatically

            if self.realtime_monitor and self.config["monitoring"]["real_time"]:
                self.logger.info("  - Starting Real-time Monitoring...")
                self.realtime_monitor.start_monitoring()

            if self.self_healing and self.config["self_healing"]["enabled"]:
                self.logger.info("  - Starting Self-Healing...")
                self.self_healing.start_self_healing()

            if self.dashboard and self.config["dashboard"]["enabled"]:
                self.logger.info("  - Starting Recovery Dashboard...")
                dashboard_config = self.config["dashboard"]
                self.dashboard.start_dashboard(
                    host=dashboard_config["host"],
                    port=dashboard_config["port"]
                )

            self.system_running = True

            # Start background tasks
            self._start_background_tasks()

            self.logger.info("✅ Advanced Error Handling System v4.2 started successfully!")
            self.logger.info(f"📊 Dashboard available at: http://{self.config['dashboard']['host']}:{self.config['dashboard']['port']}")
            self.logger.info("🔍 System is now monitoring and ready to handle errors")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start system: {e}")
            return False

    def _start_background_tasks(self):
        """Start background system tasks"""
        # Metrics collection
        threading.Thread(target=self._metrics_collection_loop, daemon=True).start()

        # System health monitoring
        threading.Thread(target=self._system_health_loop, daemon=True).start()

        # Performance reporting
        threading.Thread(target=self._performance_reporting_loop, daemon=True).start()

        self.logger.debug("Background tasks started")

    def _metrics_collection_loop(self):
        """Background loop for collecting system metrics"""
        while self.system_running:
            try:
                time.sleep(60)  # Collect metrics every minute

                if self.integration_manager:
                    # Get integration metrics
                    integration_metrics = self.integration_manager._collect_integration_metrics()

                    # Update system metrics
                    self._update_system_metrics(integration_metrics)

            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                time.sleep(30)

    def _system_health_loop(self):
        """Background loop for monitoring system health"""
        while self.system_running:
            try:
                time.sleep(300)  # Check health every 5 minutes

                health_status = self._check_system_health()

                if not health_status['healthy']:
                    self.logger.warning(f"System health issues detected: {health_status['issues']}")

                    # Attempt to heal the system
                    self._attempt_system_healing(health_status)

            except Exception as e:
                self.logger.error(f"System health monitoring error: {e}")
                time.sleep(60)

    def _performance_reporting_loop(self):
        """Background loop for performance reporting"""
        while self.system_running:
            try:
                time.sleep(3600)  # Report every hour

                self._generate_performance_report()

            except Exception as e:
                self.logger.error(f"Performance reporting error: {e}")
                time.sleep(300)

    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health_status = {
            'healthy': True,
            'issues': [],
            'component_status': {}
        }

        # Check each component
        components = {
            'error_handler': self.error_handler,
            'analytics_engine': self.analytics_engine,
            'realtime_monitor': self.realtime_monitor,
            'self_healing': self.self_healing,
            'workflow_manager': self.workflow_manager,
            'dashboard': self.dashboard
        }

        for component_name, component in components.items():
            try:
                if component:
                    # Basic health check - can we access the component?
                    if hasattr(component, 'get_system_health_report'):
                        report = component.get_system_health_report()
                        health_status['component_status'][component_name] = 'healthy'
                    elif hasattr(component, 'get_error_statistics'):
                        stats = component.get_error_statistics()
                        health_status['component_status'][component_name] = 'healthy'
                    else:
                        health_status['component_status'][component_name] = 'unknown'
                else:
                    health_status['component_status'][component_name] = 'disabled'

            except Exception as e:
                health_status['component_status'][component_name] = 'error'
                health_status['issues'].append(f"{component_name}: {str(e)}")
                health_status['healthy'] = False

        return health_status

    def _attempt_system_healing(self, health_status: Dict[str, Any]):
        """Attempt to heal system issues"""
        self.logger.info("🔧 Attempting system self-healing...")

        for component_name, status in health_status['component_status'].items():
            if status == 'error':
                self.logger.warning(f"Attempting to heal {component_name}...")

                try:
                    if component_name == 'error_handler' and self.error_handler:
                        # Restart error handler
                        self.error_handler = get_advanced_error_handler(self.server_manager)
                        self.logger.info("✅ Error handler restarted")

                    elif component_name == 'analytics_engine' and self.analytics_engine:
                        # Restart analytics engine
                        self.analytics_engine = get_error_analytics_engine()
                        self.logger.info("✅ Analytics engine restarted")

                    # Add more component healing as needed

                except Exception as e:
                    self.logger.error(f"Failed to heal {component_name}: {e}")

    def _generate_performance_report(self):
        """Generate and log performance report"""
        try:
            uptime_seconds = time.time() - self.start_time if self.start_time else 0
            uptime_hours = uptime_seconds / 3600

            report = {
                'timestamp': datetime.now().isoformat(),
                'uptime_hours': uptime_hours,
                'metrics': self.metrics.copy(),
                'component_status': self._check_system_health()
            }

            # Log report
            self.logger.info(f"📊 Performance Report - Uptime: {uptime_hours:.1f}h")
            self.logger.info(f"   Errors handled: {report['metrics']['errors_handled']}")
            self.logger.info(f"   Recoveries executed: {report['metrics']['recoveries_executed']}")
            self.logger.info(f"   Workflows executed: {report['metrics']['workflows_executed']}")
            self.logger.info(f"   Health checks: {report['metrics']['health_checks_performed']}")

            # Save report to file
            report_file = Path(__file__).parent.parent / "logs" / f"error_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(exist_ok=True)

            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.debug(f"Performance report saved to: {report_file}")

        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")

    async def handle_error(self,
                          error: Exception,
                          service_name: str,
                          operation: str,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          user_context: Optional[Dict[str, Any]] = None,
                          use_integration: bool = True) -> Dict[str, Any]:
        """Handle an error using the advanced error handling system"""
        if not self.system_running:
            self.logger.warning("System is not running - error will be logged but not processed")
            return {'handled': False, 'reason': 'system_not_running'}

        self.metrics['errors_handled'] += 1

        try:
            if use_integration and self.integration_manager:
                # Use integrated error handling
                result = await self.integration_manager.handle_error_integrated(
                    error, service_name, operation, severity, user_context
                )
                return result
            elif self.error_handler:
                # Use basic error handler
                recovery_action = await self.error_handler.handle_error_async(
                    error, service_name, operation, severity, user_context
                )
                return {
                    'error_handled': recovery_action.success,
                    'recovery_attempted': True,
                    'recovery_strategy': recovery_action.strategy.value,
                    'final_status': 'recovered' if recovery_action.success else 'failed'
                }
            else:
                return {'handled': False, 'reason': 'no_error_handler'}

        except Exception as e:
            self.logger.error(f"Error handling failed: {e}")
            return {'handled': False, 'reason': 'handling_exception', 'exception': str(e)}

    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        if not self.system_running:
            return {'error': 'System not running'}

        self.logger.info("🔍 Running comprehensive system diagnostics...")

        diagnostic_report = {
            'timestamp': datetime.now().isoformat(),
            'system_initialized': self.system_initialized,
            'system_running': self.system_running,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'components': {},
            'metrics': self.metrics.copy(),
            'recommendations': []
        }

        # Check each component
        components = {
            'error_handler': self.error_handler,
            'analytics_engine': self.analytics_engine,
            'realtime_monitor': self.realtime_monitor,
            'self_healing': self.self_healing,
            'workflow_manager': self.workflow_manager,
            'dashboard': self.dashboard
        }

        for component_name, component in components.items():
            try:
                if component:
                    if hasattr(component, 'get_system_health_report'):
                        report = component.get_system_health_report()
                        diagnostic_report['components'][component_name] = {
                            'status': 'healthy',
                            'report': report
                        }
                    elif hasattr(component, 'get_error_statistics'):
                        stats = component.get_error_statistics()
                        diagnostic_report['components'][component_name] = {
                            'status': 'healthy',
                            'statistics': stats
                        }
                    else:
                        diagnostic_report['components'][component_name] = {
                            'status': 'active',
                            'type': type(component).__name__
                        }
                else:
                    diagnostic_report['components'][component_name] = {
                        'status': 'disabled'
                    }

            except Exception as e:
                diagnostic_report['components'][component_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                diagnostic_report['recommendations'].append(f"Fix {component_name}: {str(e)}")

        # Add system-level recommendations
        if diagnostic_report['metrics']['errors_handled'] > 100:
            diagnostic_report['recommendations'].append("High error rate detected - review error patterns")

        if diagnostic_report['metrics']['recoveries_executed'] > 50:
            diagnostic_report['recommendations'].append("Frequent recoveries - investigate root causes")

        self.logger.info("✅ System diagnostics completed")
        return diagnostic_report

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_initialized': self.system_initialized,
            'system_running': self.system_running,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0,
            'metrics': self.metrics.copy(),
            'configuration': self.config,
            'components': {}
        }

        # Add component statuses
        if self.integration_manager:
            try:
                integration_status = self.integration_manager.get_integration_status()
                status['integration'] = integration_status
            except:
                status['integration'] = {'error': 'Failed to get integration status'}

        # Add dashboard status
        if self.dashboard:
            try:
                dashboard_status = self.dashboard.get_dashboard_status()
                status['dashboard'] = dashboard_status
            except:
                status['dashboard'] = {'error': 'Failed to get dashboard status'}

        return status

    def execute_workflow(self, workflow_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a recovery workflow"""
        if not self.system_running or not self.workflow_manager:
            return {'success': False, 'error': 'Workflow manager not available'}

        try:
            execution = asyncio.run(self.workflow_manager.execute_workflow(
                workflow_id,
                trigger_error="manual",
                parameters=parameters or {}
            ))

            self.metrics['workflows_executed'] += 1

            return {
                'success': execution.status == WorkflowStatus.COMPLETED,
                'execution_id': execution.execution_id,
                'workflow_name': execution.workflow_name,
                'status': execution.status.value,
                'execution_time_ms': execution.execution_time_ms
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop_system(self) -> bool:
        """Stop the advanced error handling system"""
        if not self.system_running:
            self.logger.warning("System is not running")
            return True

        self.logger.info("🛑 Stopping Advanced Error Handling System v4.2...")

        try:
            # Stop dashboard
            if self.dashboard:
                self.logger.info("  - Stopping Recovery Dashboard...")
                self.dashboard.stop_dashboard()

            # Stop self-healing
            if self.self_healing:
                self.logger.info("  - Stopping Self-Healing...")
                self.self_healing.stop_self_healing()

            # Stop real-time monitoring
            if self.realtime_monitor:
                self.logger.info("  - Stopping Real-time Monitoring...")
                self.realtime_monitor.stop_monitoring()

            # Stop integration
            if self.integration_manager:
                self.logger.info("  - Stopping Integration Manager...")
                self.integration_manager.stop_integration()

            self.system_running = False

            # Generate final report
            self._generate_performance_report()

            self.logger.info("✅ Advanced Error Handling System v4.2 stopped successfully!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to stop system: {e}")
            return False

    def _print_system_summary(self):
        """Print system initialization summary"""
        self.logger.info("=" * 60)
        self.logger.info("🎉 ADVANCED ERROR HANDLING SYSTEM v4.2 - INITIALIZATION COMPLETE")
        self.logger.info("=" * 60)

        # Component status
        components = [
            ("Error Handler", self.error_handler is not None),
            ("Analytics Engine", self.analytics_engine is not None),
            ("Real-time Monitor", self.realtime_monitor is not None),
            ("Self-Healing", self.self_healing is not None),
            ("Workflow Manager", self.workflow_manager is not None),
            ("Integration Manager", self.integration_manager is not None),
            ("Recovery Dashboard", self.dashboard is not None)
        ]

        for name, status in components:
            status_icon = "✅" if status else "❌"
            self.logger.info(f"  {status_icon} {name}")

        # Feature summary
        self.logger.info("")
        self.logger.info("🚀 FEATURES ENABLED:")
        features = [
            ("Error Classification & Recovery", self.config["error_handling"]["enabled"]),
            ("Real-time Monitoring & Analytics", self.config["monitoring"]["enabled"]),
            ("Predictive Error Analysis", self.config["monitoring"]["prediction"]),
            ("Self-Healing & Auto-Repair", self.config["self_healing"]["enabled"]),
            ("Configurable Recovery Workflows", self.config["workflows"]["enabled"]),
            ("Integration with DuckBot Systems", self.config["integration"]["enabled"]),
            ("Web Dashboard & Reporting", self.config["dashboard"]["enabled"])
        ]

        for name, enabled in features:
            status_icon = "✅" if enabled else "❌"
            self.logger.info(f"  {status_icon} {name}")

        # Configuration summary
        dashboard_config = self.config["dashboard"]
        self.logger.info("")
        self.logger.info(f"📊 DASHBOARD: http://{dashboard_config['host']}:{dashboard_config['port']}")
        self.logger.info(f"🎨 THEME: {dashboard_config['theme'].upper()}")
        self.logger.info(f"🔄 AUTO-REFRESH: {dashboard_config['auto_refresh']}s")

        self.logger.info("=" * 60)
        self.logger.info("System is ready to handle errors with advanced recovery capabilities!")
        self.logger.info("=" * 60)

# Global instance
_advanced_error_system = None

def get_advanced_error_system(server_manager: Optional[ServerManager] = None) -> AdvancedErrorSystem:
    """Get the global advanced error system instance"""
    global _advanced_error_system

    if _advanced_error_system is None:
        _advanced_error_system = AdvancedErrorSystem(server_manager)

    return _advanced_error_system

# Convenience functions
def initialize_advanced_error_handling(server_manager: Optional[ServerManager] = None) -> bool:
    """Initialize the advanced error handling system"""
    system = get_advanced_error_system(server_manager)
    return system.initialize_system()

def start_advanced_error_handling() -> bool:
    """Start the advanced error handling system"""
    system = get_advanced_error_system()
    return system.start_system()

def stop_advanced_error_handling() -> bool:
    """Stop the advanced error handling system"""
    system = get_advanced_error_system()
    return system.stop_system()

# Decorators for easy use
def advanced_error_handler(service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator for advanced error handling"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                system = get_advanced_error_system()
                result = await system.handle_error(e, service_name, operation, severity)
                if not result['error_handled'] and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                    raise
                return None

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                system = get_advanced_error_system()
                result = asyncio.run(system.handle_error(e, service_name, operation, severity))
                if not result['error_handled'] and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                    raise
                return None

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Context manager for advanced error handling
class AdvancedErrorContext:
    """Context manager for advanced error handling"""
    def __init__(self, service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.service_name = service_name
        self.operation = operation
        self.severity = severity
        self.system = get_advanced_error_system()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            result = await self.system.handle_error(
                exc_val, self.service_name, self.operation, self.severity
            )
            # Return True to suppress exception if recovery was successful
            # and severity is not critical or high
            return (result['error_handled'] and
                    self.severity not in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH])
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            result = asyncio.run(self.system.handle_error(
                exc_val, self.service_name, self.operation, self.severity
            ))
            # Return True to suppress exception if recovery was successful
            # and severity is not critical or high
            return (result['error_handled'] and
                    self.severity not in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH])
        return False

if __name__ == "__main__":
    # Command line interface
    import argparse

    parser = argparse.ArgumentParser(description="DuckBot Advanced Error Handling System v4.2")
    parser.add_argument('--action', choices=['init', 'start', 'stop', 'status', 'diagnostics'], default='start',
                       help='Action to perform')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get system instance
    system = get_advanced_error_system()

    if args.action == 'init':
        success = system.initialize_system()
        if success:
            print("✅ System initialized successfully")
        else:
            print("❌ System initialization failed")

    elif args.action == 'start':
        if not system.system_initialized:
            success = system.initialize_system()
            if not success:
                print("❌ System initialization failed")
                sys.exit(1)

        success = system.start_system()
        if success:
            print("✅ System started successfully")
            print("📊 Dashboard: http://127.0.0.1:8790")
            print("Press Ctrl+C to stop the system")

            try:
                while system.system_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping system...")
                system.stop_system()
                print("✅ System stopped")
        else:
            print("❌ System start failed")

    elif args.action == 'stop':
        success = system.stop_system()
        if success:
            print("✅ System stopped successfully")
        else:
            print("❌ System stop failed")

    elif args.action == 'status':
        status = system.get_system_status()
        print(f"System Status: {'Running' if status['system_running'] else 'Stopped'}")
        print(f"Initialized: {'Yes' if status['system_initialized'] else 'No'}")
        print(f"Uptime: {status['uptime_seconds']:.1f} seconds")
        print(f"Errors handled: {status['metrics']['errors_handled']}")
        print(f"Recoveries: {status['metrics']['recoveries_executed']}")

    elif args.action == 'diagnostics':
        diagnostics = system.run_diagnostics()
        print("🔍 System Diagnostics:")
        print(f"Timestamp: {diagnostics['timestamp']}")
        print(f"System Running: {diagnostics['system_running']}")
        print(f"Components: {len(diagnostics['components'])}")

        for component_name, component_info in diagnostics['components'].items():
            status = component_info['status']
            icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
            print(f"  {icon} {component_name}: {status}")

        if diagnostics['recommendations']:
            print("\n💡 Recommendations:")
            for rec in diagnostics['recommendations']:
                print(f"  • {rec}")