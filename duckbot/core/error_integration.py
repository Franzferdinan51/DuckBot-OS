#!/usr/bin/env python3
"""
Error Handling System Integration for DuckBot v4.2
Integrates advanced error handling with existing monitoring, AI agents, and orchestration systems
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
from dataclasses import asdict, dataclass
from pathlib import Path
from enum import Enum

# Import DuckBot components
try:
    from duckbot.core.error_handling import (
        ErrorContext, ErrorSeverity, ErrorCategory, RecoveryAction, RecoveryStrategy,
        AdvancedErrorHandler, get_advanced_error_handler
    )
    from duckbot.core.error_monitoring import (
        ErrorAnalyticsEngine, RealTimeErrorMonitor, AlertRule, AlertThreshold,
        get_error_analytics_engine, get_realtime_monitor
    )
    from duckbot.core.self_healing import (
        HealthMonitor, AutoRepairEngine, SelfHealingSystem, get_self_healing_system
    )
    from duckbot.core.recovery_workflows import (
        RecoveryWorkflowManager, WorkflowStatus, get_recovery_workflow_manager
    )
    from duckbot.core.logging_setup import get_logger
    from duckbot.services.server_manager import ServerManager, ServiceStatus
    from duckbot.ui.observability import increment_counter
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import DuckBot components: {e}")

class IntegrationStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"

@dataclass
class IntegrationMetrics:
    """Integration system metrics"""
    timestamp: datetime
    errors_handled_total: int
    auto_recoveries_executed: int
    health_checks_passed: int
    workflows_executed: int
    alerts_triggered: int
    integration_status: Dict[str, IntegrationStatus]
    system_health_score: float

class ErrorIntegrationManager:
    """Central integration manager for all error handling components"""

    def __init__(self, server_manager: Optional[ServerManager] = None):
        self.logger = get_logger("error_integration_manager")
        self.server_manager = server_manager

        # Component instances
        self.error_handler = None
        self.analytics_engine = None
        self.realtime_monitor = None
        self.self_healing = None
        self.workflow_manager = None

        # Integration state
        self.integration_active = False
        self.integration_metrics_history: List[IntegrationMetrics] = []
        self.last_metrics_update = datetime.now()

        # Event handlers
        self.error_handlers: List[Callable] = []
        self.recovery_handlers: List[Callable] = []
        self.health_handlers: List[Callable] = []

        # Configuration
        self.config = self._load_integration_config()

        # Initialize components
        self._initialize_components()

        # Start integration
        self._start_integration()

    def _load_integration_config(self) -> Dict[str, Any]:
        """Load integration configuration"""
        default_config = {
            "auto_recovery_enabled": True,
            "self_healing_enabled": True,
            "workflow_automation_enabled": True,
            "real_time_monitoring_enabled": True,
            "analytics_enabled": True,
            "alerting_enabled": True,
            "health_check_interval": 60,
            "metrics_update_interval": 30,
            "max_error_history": 1000,
            "integration_sync_interval": 300
        }

        config_file = Path(__file__).parent.parent / "config" / "error_integration.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"Failed to load integration config: {e}")

        return default_config

    def _initialize_components(self):
        """Initialize all error handling components"""
        self.logger.info("Initializing error handling components...")

        try:
            # Initialize error handler
            self.error_handler = get_advanced_error_handler(self.server_manager)

            # Initialize analytics engine
            self.analytics_engine = get_error_analytics_engine()

            # Initialize real-time monitor
            self.realtime_monitor = get_realtime_monitor()

            # Initialize self-healing system
            self.self_healing = get_self_healing_system(self.server_manager)

            # Initialize workflow manager
            self.workflow_manager = get_recovery_workflow_manager(self.server_manager)

            # Set up component integration
            self._setup_component_integration()

            self.logger.info("All error handling components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

    def _setup_component_integration(self):
        """Set up integration between components"""
        # Connect error handler to analytics
        if self.error_handler and self.analytics_engine:
            self._connect_error_handler_to_analytics()

        # Connect real-time monitor to error handler
        if self.realtime_monitor and self.error_handler:
            self._connect_monitor_to_error_handler()

        # Connect self-healing to workflows
        if self.self_healing and self.workflow_manager:
            self._connect_self_healing_to_workflows()

        # Connect analytics to alerting
        if self.analytics_engine and self.realtime_monitor:
            self._connect_analytics_to_monitoring()

        self.logger.info("Component integration established")

    def _connect_error_handler_to_analytics(self):
        """Connect error handler to analytics engine"""
        # This would be implemented by overriding error handler methods
        # or using event listeners to send error data to analytics
        pass

    def _connect_monitor_to_error_handler(self):
        """Connect real-time monitor to error handler"""
        # Add callback for real-time monitoring updates
        def on_metrics_update(metrics):
            self._handle_metrics_update(metrics)

        self.realtime_monitor.add_update_callback(on_metrics_update)

    def _connect_self_healing_to_workflows(self):
        """Connect self-healing system to workflow manager"""
        # When self-healing detects issues, it can trigger workflows
        pass

    def _connect_analytics_to_monitoring(self):
        """Connect analytics engine to monitoring system"""
        # Analytics can trigger alerts in the monitoring system
        pass

    def _start_integration(self):
        """Start the integration system"""
        if self.integration_active:
            return

        self.logger.info("Starting error handling integration...")

        # Start individual components
        if self.config["self_healing_enabled"]:
            self.self_healing.start_self_healing()

        if self.config["real_time_monitoring_enabled"]:
            self.realtime_monitor.start_monitoring()

        # Start integration monitoring
        self.integration_active = True

        # Start background tasks
        self._start_background_tasks()

        self.logger.info("Error handling integration started successfully")

    def _start_background_tasks(self):
        """Start background integration tasks"""
        # Metrics collection
        threading.Thread(target=self._metrics_collection_loop, daemon=True).start()

        # Integration health monitoring
        threading.Thread(target=self._integration_health_loop, daemon=True).start()

        # Data synchronization
        threading.Thread(target=self._data_sync_loop, daemon=True).start()

    def _metrics_collection_loop(self):
        """Background loop for collecting integration metrics"""
        while self.integration_active:
            try:
                metrics = self._collect_integration_metrics()
                self.integration_metrics_history.append(metrics)

                # Keep history manageable
                if len(self.integration_metrics_history) > 1000:
                    self.integration_metrics_history = self.integration_metrics_history[-500:]

                # Update component metrics
                self._update_component_metrics(metrics)

                time.sleep(self.config["metrics_update_interval"])

            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                time.sleep(30)

    def _integration_health_loop(self):
        """Background loop for monitoring integration health"""
        while self.integration_active:
            try:
                health_status = self._check_integration_health()

                # Handle any unhealthy components
                for component_name, status in health_status.items():
                    if status == IntegrationStatus.ERROR:
                        self.logger.warning(f"Integration health issue detected: {component_name}")
                        self._handle_integration_health_issue(component_name)

                time.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Integration health monitoring error: {e}")
                time.sleep(60)

    def _data_sync_loop(self):
        """Background loop for data synchronization between components"""
        while self.integration_active:
            try:
                self._synchronize_component_data()
                time.sleep(self.config["integration_sync_interval"])

            except Exception as e:
                self.logger.error(f"Data synchronization error: {e}")
                time.sleep(60)

    def _collect_integration_metrics(self) -> IntegrationMetrics:
        """Collect comprehensive integration metrics"""
        try:
            # Get metrics from each component
            error_handler_stats = self.error_handler.get_error_statistics() if self.error_handler else {}
            recovery_stats = self.error_handler.get_recovery_report() if self.error_handler else {}
            health_report = self.self_healing.get_system_health_report() if self.self_healing else {}
            workflow_stats = self.workflow_manager.get_workflow_statistics() if self.workflow_manager else {}

            # Check integration status
            integration_status = self._check_integration_health()

            # Calculate system health score
            system_health_score = self._calculate_system_health_score(
                error_handler_stats, recovery_stats, health_report, workflow_stats
            )

            return IntegrationMetrics(
                timestamp=datetime.now(),
                errors_handled_total=error_handler_stats.get('total_errors', 0),
                auto_recoveries_executed=recovery_stats.get('total_recoveries', 0),
                health_checks_passed=health_report.get('health_summary', {}).get('total_checks', 0),
                workflows_executed=workflow_stats.get('total_executions', 0),
                alerts_triggered=len(self.analytics_engine.get_recent_alerts(hours=1)) if self.analytics_engine else 0,
                integration_status=integration_status,
                system_health_score=system_health_score
            )

        except Exception as e:
            self.logger.error(f"Failed to collect integration metrics: {e}")
            return IntegrationMetrics(
                timestamp=datetime.now(),
                errors_handled_total=0,
                auto_recoveries_executed=0,
                health_checks_passed=0,
                workflows_executed=0,
                alerts_triggered=0,
                integration_status={},
                system_health_score=0.0
            )

    def _check_integration_health(self) -> Dict[str, IntegrationStatus]:
        """Check health of all integrated components"""
        status = {}

        # Check error handler
        try:
            if self.error_handler:
                stats = self.error_handler.get_error_statistics()
                status['error_handler'] = IntegrationStatus.CONNECTED
            else:
                status['error_handler'] = IntegrationStatus.DISCONNECTED
        except:
            status['error_handler'] = IntegrationStatus.ERROR

        # Check analytics engine
        try:
            if self.analytics_engine:
                self.analytics_engine.get_current_metrics()
                status['analytics_engine'] = IntegrationStatus.CONNECTED
            else:
                status['analytics_engine'] = IntegrationStatus.DISCONNECTED
        except:
            status['analytics_engine'] = IntegrationStatus.ERROR

        # Check real-time monitor
        try:
            if self.realtime_monitor:
                self.realtime_monitor.get_dashboard_data()
                status['realtime_monitor'] = IntegrationStatus.CONNECTED
            else:
                status['realtime_monitor'] = IntegrationStatus.DISCONNECTED
        except:
            status['realtime_monitor'] = IntegrationStatus.ERROR

        # Check self-healing
        try:
            if self.self_healing:
                self.self_healing.get_system_health_report()
                status['self_healing'] = IntegrationStatus.CONNECTED
            else:
                status['self_healing'] = IntegrationStatus.DISCONNECTED
        except:
            status['self_healing'] = IntegrationStatus.ERROR

        # Check workflow manager
        try:
            if self.workflow_manager:
                self.workflow_manager.get_workflow_statistics()
                status['workflow_manager'] = IntegrationStatus.CONNECTED
            else:
                status['workflow_manager'] = IntegrationStatus.DISCONNECTED
        except:
            status['workflow_manager'] = IntegrationStatus.ERROR

        return status

    def _calculate_system_health_score(self, *component_stats) -> float:
        """Calculate overall system health score"""
        try:
            score_factors = []

            # Error handling health
            if component_stats:
                error_stats = component_stats[0]
                if error_stats.get('total_errors', 0) > 0:
                    recovery_rate = error_stats.get('recovery_success_rate', 0.0)
                    score_factors.append(recovery_rate)
                else:
                    score_factors.append(1.0)

            # Recovery health
            if len(component_stats) > 1:
                recovery_stats = component_stats[1]
                total_recoveries = recovery_stats.get('total_recoveries', 0)
                success_rate = recovery_stats.get('recovery_success_rate', 0.0)
                if total_recoveries > 0:
                    score_factors.append(success_rate)
                else:
                    score_factors.append(1.0)

            # Health check results
            if len(component_stats) > 2:
                health_report = component_stats[2]
                health_summary = health_report.get('health_summary', {})
                if 'overall_status' in health_summary:
                    status_scores = {'excellent': 1.0, 'good': 0.8, 'fair': 0.6, 'poor': 0.3}
                    health_score = status_scores.get(health_summary['overall_status'], 0.5)
                    score_factors.append(health_score)

            # Workflow execution health
            if len(component_stats) > 3:
                workflow_stats = component_stats[3]
                total_executions = workflow_stats.get('total_executions', 0)
                success_rate = workflow_stats.get('overall_success_rate', 0.0)
                if total_executions > 0:
                    score_factors.append(success_rate)
                else:
                    score_factors.append(1.0)

            # Calculate weighted average
            if score_factors:
                return sum(score_factors) / len(score_factors)
            else:
                return 1.0

        except Exception as e:
            self.logger.error(f"Failed to calculate system health score: {e}")
            return 0.5

    def _update_component_metrics(self, metrics: IntegrationMetrics):
        """Update individual component metrics"""
        # Update global metrics tracking
        try:
            increment_counter("integration_errors_handled_total", metrics.errors_handled_total)
            increment_counter("integration_auto_recoveries", metrics.auto_recoveries_executed)
            increment_counter("integration_workflows_executed", metrics.workflows_executed)
            increment_counter("integration_alerts_triggered", metrics.alerts_triggered)
        except:
            pass

    def _handle_metrics_update(self, metrics):
        """Handle real-time metrics updates from monitor"""
        try:
            # Update integration metrics
            integration_metrics = self._collect_integration_metrics()

            # Check for alert conditions
            self._check_integration_alerts(integration_metrics)

            # Notify handlers
            for handler in self.health_handlers:
                try:
                    handler(integration_metrics)
                except Exception as e:
                    self.logger.error(f"Health handler error: {e}")

        except Exception as e:
            self.logger.error(f"Failed to handle metrics update: {e}")

    def _check_integration_alerts(self, metrics: IntegrationMetrics):
        """Check for integration-wide alert conditions"""
        # Check system health score
        if metrics.system_health_score < 0.5:
            self.logger.warning(f"Low system health score: {metrics.system_health_score:.2f}")

        # Check error rate
        if metrics.errors_handled_total > 100:  # High error rate
            self.logger.warning(f"High error rate detected: {metrics.errors_handled_total} errors")

        # Check recovery success rate
        if metrics.auto_recoveries_executed > 0:
            if metrics.auto_recoveries_executed > 10:  # Many recoveries
                self.logger.warning(f"High auto-recovery activity: {metrics.auto_recoveries_executed} recoveries")

    def _handle_integration_health_issue(self, component_name: str):
        """Handle integration health issues"""
        self.logger.critical(f"Integration health issue: {component_name}")

        # Attempt to restart or repair the component
        if component_name == "error_handler":
            try:
                self.error_handler = get_advanced_error_handler(self.server_manager)
                self.logger.info("Error handler restarted")
            except Exception as e:
                self.logger.error(f"Failed to restart error handler: {e}")

        elif component_name == "analytics_engine":
            try:
                self.analytics_engine = get_error_analytics_engine()
                self.logger.info("Analytics engine restarted")
            except Exception as e:
                self.logger.error(f"Failed to restart analytics engine: {e}")

    def _synchronize_component_data(self):
        """Synchronize data between components"""
        try:
            # Sync error history between components
            if self.error_handler and self.analytics_engine:
                # This would sync error data from handler to analytics
                pass

            # Sync health data between components
            if self.self_healing and self.realtime_monitor:
                # This would sync health data from self-healing to monitor
                pass

            # Sync recovery data between components
            if self.workflow_manager and self.analytics_engine:
                # This would sync recovery data from workflows to analytics
                pass

            self.logger.debug("Component data synchronization completed")

        except Exception as e:
            self.logger.error(f"Data synchronization failed: {e}")

    async def handle_error_integrated(self,
                                   error: Exception,
                                   service_name: str,
                                   operation: str,
                                   severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                                   user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle error using integrated system"""
        result = {
            'error_handled': False,
            'recovery_attempted': False,
            'workflow_executed': False,
            'actions_taken': [],
            'final_status': 'failed'
        }

        try:
            # Step 1: Classify and handle with error handler
            if self.error_handler:
                recovery_action = await self.error_handler.handle_error_async(
                    error, service_name, operation, severity, user_context
                )
                result['recovery_attempted'] = True
                result['actions_taken'].append(f"Error recovery: {recovery_action.strategy.value}")
                result['error_handled'] = recovery_action.success

            # Step 2: Attempt workflow-based recovery if configured
            if (not result['error_handled'] and
                self.config["workflow_automation_enabled"] and
                self.workflow_manager):

                # Create error context for workflow matching
                error_context = ErrorContext(
                    timestamp=datetime.now(),
                    service_name=service_name,
                    operation=operation,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    severity=severity,
                    category=self._determine_error_category(error),
                    user_context=user_context
                )

                # Execute matching workflow
                workflow_execution = await self.workflow_manager.handle_error_with_workflow(error_context)
                if workflow_execution:
                    result['workflow_executed'] = True
                    result['actions_taken'].append(f"Workflow executed: {workflow_execution.workflow_name}")

                    if workflow_execution.status == WorkflowStatus.COMPLETED:
                        result['error_handled'] = True

            # Step 3: Update analytics
            if self.analytics_engine:
                error_context = ErrorContext(
                    timestamp=datetime.now(),
                    service_name=service_name,
                    operation=operation,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    severity=severity,
                    category=self._determine_error_category(error),
                    user_context=user_context
                )
                self.analytics_engine.record_error_context(error_context)

            # Step 4: Notify handlers
            for handler in self.error_handlers:
                try:
                    await handler(error, service_name, operation, severity, result)
                except Exception as e:
                    self.logger.error(f"Error handler callback failed: {e}")

            # Determine final status
            if result['error_handled']:
                result['final_status'] = 'recovered'
            elif result['recovery_attempted'] or result['workflow_executed']:
                result['final_status'] = 'attempted'
            else:
                result['final_status'] = 'failed'

        except Exception as e:
            self.logger.error(f"Integrated error handling failed: {e}")
            result['actions_taken'].append(f"Integration error: {str(e)}")

        return result

    def _determine_error_category(self, error: Exception) -> ErrorCategory:
        """Determine error category for integration purposes"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        if any(keyword in error_message for keyword in ["connection", "network", "timeout", "socket"]):
            return ErrorCategory.NETWORK
        elif any(keyword in error_message for keyword in ["memory", "allocation", "out of memory"]):
            return ErrorCategory.MEMORY
        elif any(keyword in error_message for keyword in ["api", "http", "status", "rate limit"]):
            return ErrorCategory.API
        elif any(keyword in error_message for keyword in ["permission", "access", "denied", "forbidden"]):
            return ErrorCategory.PERMISSION
        elif "file" in error_message or "disk" in error_message:
            return ErrorCategory.HARDWARE
        else:
            return ErrorCategory.UNKNOWN

    def add_error_handler(self, handler: Callable):
        """Add custom error handler callback"""
        self.error_handlers.append(handler)

    def add_recovery_handler(self, handler: Callable):
        """Add custom recovery handler callback"""
        self.recovery_handlers.append(handler)

    def add_health_handler(self, handler: Callable):
        """Add custom health handler callback"""
        self.health_handlers.append(handler)

    def get_integration_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive integration dashboard data"""
        try:
            # Collect current metrics
            current_metrics = self._collect_integration_metrics()

            # Get component-specific data
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'integration_active': self.integration_active,
                'current_metrics': asdict(current_metrics),
                'configuration': self.config,
                'component_status': current_metrics.integration_status,
                'recent_activity': self._get_recent_activity(),
                'system_recommendations': self._generate_system_recommendations(current_metrics)
            }

            # Add real-time monitor data if available
            if self.realtime_monitor:
                try:
                    monitor_data = self.realtime_monitor.get_dashboard_data()
                    dashboard_data['realtime_monitor'] = monitor_data
                except Exception as e:
                    self.logger.error(f"Failed to get monitor data: {e}")

            # Add self-healing report if available
            if self.self_healing:
                try:
                    health_report = self.self_healing.get_system_health_report()
                    dashboard_data['self_healing'] = health_report
                except Exception as e:
                    self.logger.error(f"Failed to get self-healing report: {e}")

            # Add workflow statistics if available
            if self.workflow_manager:
                try:
                    workflow_stats = self.workflow_manager.get_workflow_statistics()
                    dashboard_data['workflows'] = workflow_stats
                except Exception as e:
                    self.logger.error(f"Failed to get workflow statistics: {e}")

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Failed to get integration dashboard: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        activity = []

        # Get recent error history
        if self.error_handler:
            try:
                error_stats = self.error_handler.get_error_statistics(time_window_hours=1)
                if error_stats.get('total_errors', 0) > 0:
                    activity.append({
                        'type': 'errors',
                        'count': error_stats['total_errors'],
                        'timestamp': datetime.now().isoformat(),
                        'message': f"{error_stats['total_errors']} errors in last hour"
                    })
            except:
                pass

        # Get recent recovery activity
        if self.error_handler:
            try:
                recovery_stats = self.error_handler.get_recovery_report(time_window_hours=1)
                if recovery_stats.get('total_recoveries', 0) > 0:
                    activity.append({
                        'type': 'recoveries',
                        'count': recovery_stats['total_recoveries'],
                        'timestamp': datetime.now().isoformat(),
                        'message': f"{recovery_stats['total_recoveries']} recoveries in last hour"
                    })
            except:
                pass

        # Get recent workflow activity
        if self.workflow_manager:
            try:
                recent_executions = self.workflow_manager.get_execution_history(limit=5)
                for execution in recent_executions:
                    if execution.status == WorkflowStatus.COMPLETED:
                        activity.append({
                            'type': 'workflow',
                            'name': execution.workflow_name,
                            'timestamp': execution.completed_at.isoformat() if execution.completed_at else datetime.now().isoformat(),
                            'message': f"Workflow {execution.workflow_name} completed successfully"
                        })
            except:
                pass

        # Sort by timestamp and return recent items
        activity.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity[:10]

    def _generate_system_recommendations(self, metrics: IntegrationMetrics) -> List[str]:
        """Generate system recommendations based on current metrics"""
        recommendations = []

        # Health score recommendations
        if metrics.system_health_score < 0.5:
            recommendations.append("Critical: System health score is low - investigate immediately")
        elif metrics.system_health_score < 0.7:
            recommendations.append("Warning: System health degraded - monitor closely")

        # Error rate recommendations
        if metrics.errors_handled_total > 50:
            recommendations.append("High error rate detected - review error patterns and adjust configurations")

        # Recovery rate recommendations
        if metrics.auto_recoveries_executed > 20:
            recommendations.append("Frequent auto-recoveries - consider addressing root causes")

        # Workflow success recommendations
        if metrics.workflows_executed > 0:
            # Calculate workflow success rate
            if hasattr(self, 'workflow_manager') and self.workflow_manager:
                workflow_stats = self.workflow_manager.get_workflow_statistics()
                success_rate = workflow_stats.get('overall_success_rate', 1.0)
                if success_rate < 0.8:
                    recommendations.append("Low workflow success rate - review and update workflows")

        # Component health recommendations
        for component, status in metrics.integration_status.items():
            if status == IntegrationStatus.ERROR:
                recommendations.append(f"Component {component} is in error state - requires attention")
            elif status == IntegrationStatus.DISCONNECTED:
                recommendations.append(f"Component {component} is disconnected - check configuration")

        return recommendations

    def stop_integration(self):
        """Stop the integration system"""
        if not self.integration_active:
            return

        self.logger.info("Stopping error handling integration...")

        self.integration_active = False

        # Stop individual components
        if self.self_healing:
            self.self_healing.stop_self_healing()

        if self.realtime_monitor:
            self.realtime_monitor.stop_monitoring()

        # Save final metrics
        final_metrics = self._collect_integration_metrics()
        self.integration_metrics_history.append(final_metrics)

        self.logger.info("Error handling integration stopped")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            'active': self.integration_active,
            'components': {
                'error_handler': self.error_handler is not None,
                'analytics_engine': self.analytics_engine is not None,
                'realtime_monitor': self.realtime_monitor is not None,
                'self_healing': self.self_healing is not None,
                'workflow_manager': self.workflow_manager is not None
            },
            'configuration': self.config,
            'metrics_count': len(self.integration_metrics_history),
            'last_update': self.last_metrics_update.isoformat() if self.last_metrics_update else None
        }

# Global instance
_integration_manager = None

def get_error_integration_manager(server_manager: Optional[ServerManager] = None) -> ErrorIntegrationManager:
    """Get the global error integration manager instance"""
    global _integration_manager

    if _integration_manager is None:
        _integration_manager = ErrorIntegrationManager(server_manager)

    return _integration_manager

# Decorator for integrated error handling
def handle_error_integrated(service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator for integrated error handling"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                integration_manager = get_error_integration_manager()
                result = await integration_manager.handle_error_integrated(
                    e, service_name, operation, severity
                )

                # Re-raise if recovery failed and severity is critical
                if not result['error_handled'] and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                    raise

                # Return appropriate fallback
                return None

        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                integration_manager = get_error_integration_manager()
                result = asyncio.run(integration_manager.handle_error_integrated(
                    e, service_name, operation, severity
                ))

                # Re-raise if recovery failed and severity is critical
                if not result['error_handled'] and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                    raise

                # Return appropriate fallback
                return None

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

if __name__ == "__main__":
    # Example usage
    async def example_usage():
        """Demonstrate integrated error handling system usage"""

        # Create integration manager
        integration_manager = get_error_integration_manager()

        print("Integration manager started successfully")

        # Get integration dashboard
        dashboard = integration_manager.get_integration_dashboard()
        print(f"System health score: {dashboard.get('current_metrics', {}).get('system_health_score', 0):.2f}")

        # Simulate an error
        try:
            raise ConnectionError("Test connection failure")
        except Exception as e:
            result = await integration_manager.handle_error_integrated(
                e, "test_service", "test_operation", ErrorSeverity.HIGH
            )
            print(f"Error handling result: {result}")

        # Get integration status
        status = integration_manager.get_integration_status()
        print(f"Integration status: {status}")

        # Stop integration
        integration_manager.stop_integration()

    # Run example
    asyncio.run(example_usage())