#!/usr/bin/env python3
"""
Advanced Error Monitoring and Analytics System for DuckBot v4.2
Provides real-time error tracking, analytics, and predictive monitoring
"""

import os
import sys
import time
import json
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import statistics
from collections import defaultdict, deque
import numpy as np
from enum import Enum

# Import existing components
try:
    from duckbot.core.error_handling import ErrorContext, ErrorSeverity, ErrorCategory, RecoveryAction
    from duckbot.core.logging_setup import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class AlertThreshold(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorMetrics:
    """Real-time error metrics"""
    timestamp: datetime
    total_errors: int
    errors_by_category: Dict[str, int]
    errors_by_severity: Dict[str, int]
    errors_by_service: Dict[str, int]
    recovery_success_rate: float
    average_recovery_time_ms: float
    active_circuit_breakers: int
    system_health_score: float

@dataclass
class ErrorTrend:
    """Error trend analysis"""
    metric_name: str
    current_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0.0 to 1.0
    prediction_1h: float  # Predicted value in 1 hour
    confidence: float    # Prediction confidence 0.0 to 1.0
    alert_triggered: bool

@dataclass
class AlertRule:
    """Alert configuration rule"""
    rule_id: str
    name: str
    metric: str
    operator: str  # ">", "<", "==", ">=", "<="
    threshold: float
    severity: AlertThreshold
    cooldown_minutes: int
    enabled: bool
    notification_channels: List[str]
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class ErrorAnalyticsEngine:
    """Advanced error analytics and prediction engine"""

    def __init__(self, db_path: Optional[str] = None):
        self.logger = get_logger("error_analytics")
        self.db_path = db_path or Path(__file__).parent.parent / "data" / "error_monitoring.db"
        self.metrics_history: deque = deque(maxlen=1000)  # Last 1000 metrics
        self.alert_rules: Dict[str, AlertRule] = {}
        self.prediction_models: Dict[str, Any] = {}

        # Initialize database
        self._initialize_database()

        # Load default alert rules
        self._load_default_alert_rules()

        # Start background processing
        self._start_background_tasks()

    def _initialize_database(self):
        """Initialize the monitoring database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    total_errors INTEGER,
                    errors_by_category TEXT,
                    errors_by_severity TEXT,
                    errors_by_service TEXT,
                    recovery_success_rate REAL,
                    average_recovery_time_ms REAL,
                    active_circuit_breakers INTEGER,
                    system_health_score REAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    metric_name TEXT,
                    current_value REAL,
                    prediction_1h REAL,
                    prediction_6h REAL,
                    confidence REAL,
                    trend_direction TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    rule_id TEXT,
                    rule_name TEXT,
                    metric_value REAL,
                    threshold_value REAL,
                    severity TEXT,
                    message TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    pattern_id TEXT,
                    pattern_name TEXT,
                    severity TEXT,
                    services_affected TEXT,
                    error_count INTEGER,
                    confidence_score REAL
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON error_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON error_predictions(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alert_history(timestamp)")

    def _load_default_alert_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_error_rate",
                name="High Error Rate Alert",
                metric="total_errors_per_minute",
                operator=">",
                threshold=10.0,
                severity=AlertThreshold.HIGH,
                cooldown_minutes=5,
                enabled=True,
                notification_channels=["log", "system"]
            ),
            AlertRule(
                rule_id="low_recovery_success",
                name="Low Recovery Success Rate",
                metric="recovery_success_rate",
                operator="<",
                threshold=0.7,
                severity=AlertThreshold.MEDIUM,
                cooldown_minutes=10,
                enabled=True,
                notification_channels=["log"]
            ),
            AlertRule(
                rule_id="critical_errors_spike",
                name="Critical Errors Spike",
                metric="critical_errors_per_minute",
                operator=">",
                threshold=2.0,
                severity=AlertThreshold.CRITICAL,
                cooldown_minutes=2,
                enabled=True,
                notification_channels=["log", "system", "admin"]
            ),
            AlertRule(
                rule_id="system_health_degraded",
                name="System Health Degraded",
                metric="system_health_score",
                operator="<",
                threshold=0.6,
                severity=AlertThreshold.MEDIUM,
                cooldown_minutes=15,
                enabled=True,
                notification_channels=["log"]
            ),
            AlertRule(
                rule_id="memory_pressure_high",
                name="High Memory Pressure",
                metric="memory_usage_percent",
                operator=">",
                threshold=90.0,
                severity=AlertThreshold.HIGH,
                cooldown_minutes=5,
                enabled=True,
                notification_channels=["log"]
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    def _start_background_tasks(self):
        """Start background analytics tasks"""
        # Start metrics aggregation
        threading.Thread(target=self._metrics_aggregation_loop, daemon=True).start()

        # Start prediction engine
        threading.Thread(target=self._prediction_loop, daemon=True).start()

        # Start pattern detection
        threading.Thread(target=self._pattern_detection_loop, daemon=True).start()

        self.logger.info("Background analytics tasks started")

    def _metrics_aggregation_loop(self):
        """Background loop for metrics aggregation"""
        while True:
            try:
                time.sleep(60)  # Aggregate every minute
                self._aggregate_current_metrics()
            except Exception as e:
                self.logger.error(f"Metrics aggregation error: {e}")

    def _prediction_loop(self):
        """Background loop for predictive analytics"""
        while True:
            try:
                time.sleep(300)  # Run predictions every 5 minutes
                self._generate_predictions()
            except Exception as e:
                self.logger.error(f"Prediction loop error: {e}")

    def _pattern_detection_loop(self):
        """Background loop for pattern detection"""
        while True:
            try:
                time.sleep(600)  # Check patterns every 10 minutes
                self._detect_error_patterns()
            except Exception as e:
                self.logger.error(f"Pattern detection error: {e}")

    def record_error_context(self, error_context: ErrorContext):
        """Record an error context for analytics"""
        # This would be called by the error handling system
        # For now, we'll just log it
        self.logger.debug(f"Recording error context: {error_context.service_name}.{error_context.operation}")

    def record_recovery_action(self, recovery_action: RecoveryAction):
        """Record a recovery action for analytics"""
        # This would be called by the recovery engine
        self.logger.debug(f"Recording recovery action: {recovery_action.strategy.value}")

    def _aggregate_current_metrics(self):
        """Aggregate current error metrics"""
        try:
            # Get current timestamp
            timestamp = datetime.now()

            # Calculate metrics (this would integrate with the error classifier)
            metrics = self._calculate_current_metrics()

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO error_metrics (
                        timestamp, total_errors, errors_by_category, errors_by_severity,
                        errors_by_service, recovery_success_rate, average_recovery_time_ms,
                        active_circuit_breakers, system_health_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    metrics['total_errors'],
                    json.dumps(metrics['errors_by_category']),
                    json.dumps(metrics['errors_by_severity']),
                    json.dumps(metrics['errors_by_service']),
                    metrics['recovery_success_rate'],
                    metrics['average_recovery_time_ms'],
                    metrics['active_circuit_breakers'],
                    metrics['system_health_score']
                ))

            # Add to in-memory history
            self.metrics_history.append(metrics)

            # Check alert rules
            self._check_alert_rules(metrics)

            self.logger.debug(f"Metrics aggregated: {metrics['total_errors']} total errors")

        except Exception as e:
            self.logger.error(f"Metrics aggregation failed: {e}")

    def _calculate_current_metrics(self) -> Dict[str, Any]:
        """Calculate current error metrics"""
        # This would integrate with the error classifier to get real data
        # For now, returning mock data structure
        return {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'errors_by_service': {},
            'recovery_success_rate': 0.0,
            'average_recovery_time_ms': 0.0,
            'active_circuit_breakers': 0,
            'system_health_score': 1.0
        }

    def _check_alert_rules(self, metrics: Dict[str, Any]):
        """Check alert rules against current metrics"""
        current_time = datetime.now()

        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered:
                cooldown_expired = (current_time - rule.last_triggered).total_seconds() >= (rule.cooldown_minutes * 60)
                if not cooldown_expired:
                    continue

            # Get metric value
            metric_value = self._get_metric_value(metrics, rule.metric)
            if metric_value is None:
                continue

            # Check if rule is triggered
            triggered = self._evaluate_rule(rule.operator, metric_value, rule.threshold)

            if triggered:
                self._trigger_alert(rule, metric_value)

    def _get_metric_value(self, metrics: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Get metric value by name"""
        # Map metric names to actual values
        metric_mapping = {
            'total_errors_per_minute': metrics.get('total_errors', 0),
            'recovery_success_rate': metrics.get('recovery_success_rate', 0.0),
            'critical_errors_per_minute': metrics.get('errors_by_severity', {}).get('critical', 0),
            'system_health_score': metrics.get('system_health_score', 1.0),
            'memory_usage_percent': self._get_memory_usage()
        }

        return metric_mapping.get(metric_name)

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0

    def _evaluate_rule(self, operator: str, value: float, threshold: float) -> bool:
        """Evaluate if a rule condition is met"""
        try:
            if operator == ">":
                return value > threshold
            elif operator == "<":
                return value < threshold
            elif operator == "==":
                return abs(value - threshold) < 0.001
            elif operator == ">=":
                return value >= threshold
            elif operator == "<=":
                return value <= threshold
            else:
                return False
        except:
            return False

    def _trigger_alert(self, rule: AlertRule, metric_value: float):
        """Trigger an alert"""
        current_time = datetime.now()

        # Update rule
        rule.last_triggered = current_time
        rule.trigger_count += 1

        # Create alert message
        message = f"Alert triggered: {rule.name} - {rule.metric} {rule.operator} {rule.threshold} (current: {metric_value:.2f})"

        # Log alert
        if rule.severity == AlertThreshold.CRITICAL:
            self.logger.critical(message)
        elif rule.severity == AlertThreshold.HIGH:
            self.logger.error(message)
        elif rule.severity == AlertThreshold.MEDIUM:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alert_history (
                    timestamp, rule_id, rule_name, metric_value, threshold_value, severity, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                current_time, rule.rule_id, rule.name, metric_value, rule.threshold,
                rule.severity.value, message
            ))

        # Send notifications
        for channel in rule.notification_channels:
            self._send_notification(channel, message, rule.severity)

    def _send_notification(self, channel: str, message: str, severity: AlertThreshold):
        """Send notification through specified channel"""
        if channel == "log":
            # Already logged above
            pass
        elif channel == "system":
            # Could integrate with system notification
            print(f"SYSTEM ALERT: {message}")
        elif channel == "admin":
            # Could send email, Slack, etc.
            self.logger.info(f"Admin notification would be sent: {message}")

    def _generate_predictions(self):
        """Generate predictive analytics"""
        try:
            current_time = datetime.now()

            # Generate predictions for various metrics
            metrics_to_predict = [
                'total_errors', 'recovery_success_rate', 'system_health_score'
            ]

            for metric in metrics_to_predict:
                prediction = self._predict_metric_trend(metric)

                if prediction:
                    # Store prediction
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            INSERT INTO error_predictions (
                                timestamp, metric_name, current_value, prediction_1h,
                                prediction_6h, confidence, trend_direction
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            current_time,
                            metric,
                            prediction['current_value'],
                            prediction['prediction_1h'],
                            prediction['prediction_6h'],
                            prediction['confidence'],
                            prediction['trend_direction']
                        ))

                    # Check if prediction triggers alerts
                    if prediction['alert_triggered']:
                        self.logger.warning(f"Predictive alert for {metric}: {prediction['trend_direction']} trend detected")

        except Exception as e:
            self.logger.error(f"Prediction generation failed: {e}")

    def _predict_metric_trend(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Predict trend for a specific metric"""
        try:
            # Get historical data
            historical_data = self._get_historical_data(metric_name, hours=24)

            if len(historical_data) < 10:
                return None  # Not enough data for prediction

            # Simple trend analysis using linear regression
            x = list(range(len(historical_data)))
            y = historical_data

            # Calculate trend
            if len(x) > 1 and len(y) > 1:
                correlation = np.corrcoef(x, y)[0, 1]

                # Determine trend direction
                if correlation > 0.3:
                    trend_direction = "increasing"
                elif correlation < -0.3:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"

                # Simple linear prediction
                if abs(correlation) > 0.1:
                    slope = np.polyfit(x, y, 1)[0]
                    current_value = y[-1]
                    prediction_1h = current_value + (slope * 60)  # 60 minutes worth of trend
                    prediction_6h = current_value + (slope * 360)  # 6 hours worth of trend
                    confidence = min(abs(correlation), 1.0)
                else:
                    prediction_1h = current_value
                    prediction_6h = current_value
                    confidence = 0.1

                # Check if trend is concerning
                alert_triggered = False
                if metric_name == 'total_errors' and trend_direction == "increasing" and confidence > 0.7:
                    alert_triggered = True
                elif metric_name == 'recovery_success_rate' and trend_direction == "decreasing" and confidence > 0.7:
                    alert_triggered = True
                elif metric_name == 'system_health_score' and trend_direction == "decreasing" and confidence > 0.7:
                    alert_triggered = True

                return {
                    'metric_name': metric_name,
                    'current_value': current_value,
                    'trend_direction': trend_direction,
                    'trend_strength': abs(correlation),
                    'prediction_1h': prediction_1h,
                    'prediction_6h': prediction_6h,
                    'confidence': confidence,
                    'alert_triggered': alert_triggered
                }

        except Exception as e:
            self.logger.error(f"Trend prediction failed for {metric_name}: {e}")

        return None

    def _get_historical_data(self, metric_name: str, hours: int = 24) -> List[float]:
        """Get historical data for a metric"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT total_errors FROM error_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """, (cutoff_time,))

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {metric_name}: {e}")
            return []

    def _detect_error_patterns(self):
        """Detect recurring error patterns"""
        try:
            current_time = datetime.now()

            # Look for patterns in recent errors
            patterns = self._analyze_error_patterns()

            for pattern in patterns:
                # Store detected pattern
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO error_patterns (
                            timestamp, pattern_id, pattern_name, severity,
                            services_affected, error_count, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_time,
                        pattern['pattern_id'],
                        pattern['pattern_name'],
                        pattern['severity'],
                        json.dumps(pattern['services_affected']),
                        pattern['error_count'],
                        pattern['confidence_score']
                    ))

                # Log significant patterns
                if pattern['confidence_score'] > 0.7:
                    self.logger.warning(f"Error pattern detected: {pattern['pattern_name']} (confidence: {pattern['confidence_score']:.2f})")

        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")

    def _analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """Analyze error patterns in recent data"""
        # This is a simplified pattern detection
        # In a real implementation, this would use more sophisticated algorithms

        patterns = []

        # Look for service-specific error clusters
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get recent error distribution by service
                cursor = conn.execute("""
                    SELECT errors_by_service FROM error_metrics
                    WHERE timestamp >= datetime('now', '-1 hour')
                """)

                service_errors = defaultdict(int)
                for row in cursor.fetchall():
                    if row[0]:
                        service_data = json.loads(row[0])
                        for service, count in service_data.items():
                            service_errors[service] += count

                # Find services with high error rates
                for service, count in service_errors.items():
                    if count > 5:  # More than 5 errors in the last hour
                        patterns.append({
                            'pattern_id': f"service_error_spike_{service}",
                            'pattern_name': f"Service Error Spike: {service}",
                            'severity': 'high',
                            'services_affected': [service],
                            'error_count': count,
                            'confidence_score': min(count / 10.0, 1.0)
                        })

        except Exception as e:
            self.logger.error(f"Service pattern analysis failed: {e}")

        return patterns

    def get_current_metrics(self) -> ErrorMetrics:
        """Get current error metrics"""
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            return ErrorMetrics(
                timestamp=datetime.now(),
                total_errors=latest_metrics['total_errors'],
                errors_by_category=latest_metrics['errors_by_category'],
                errors_by_severity=latest_metrics['errors_by_severity'],
                errors_by_service=latest_metrics['errors_by_service'],
                recovery_success_rate=latest_metrics['recovery_success_rate'],
                average_recovery_time_ms=latest_metrics['average_recovery_time_ms'],
                active_circuit_breakers=latest_metrics['active_circuit_breakers'],
                system_health_score=latest_metrics['system_health_score']
            )
        else:
            return ErrorMetrics(
                timestamp=datetime.now(),
                total_errors=0,
                errors_by_category={},
                errors_by_severity={},
                errors_by_service={},
                recovery_success_rate=0.0,
                average_recovery_time_ms=0.0,
                active_circuit_breakers=0,
                system_health_score=1.0
            )

    def get_error_trends(self, hours: int = 24) -> List[ErrorTrend]:
        """Get error trends for various metrics"""
        trends = []

        metrics_to_analyze = [
            'total_errors', 'recovery_success_rate', 'system_health_score'
        ]

        for metric in metrics_to_analyze:
            prediction = self._predict_metric_trend(metric)
            if prediction:
                trends.append(ErrorTrend(
                    metric_name=metric,
                    current_value=prediction['current_value'],
                    trend_direction=prediction['trend_direction'],
                    trend_strength=prediction['trend_strength'],
                    prediction_1h=prediction['prediction_1h'],
                    confidence=prediction['confidence'],
                    alert_triggered=prediction['alert_triggered']
                ))

        return trends

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, rule_name, metric_value, threshold_value, severity, message
                    FROM alert_history
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))

                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'timestamp': row[0],
                        'rule_name': row[1],
                        'metric_value': row[2],
                        'threshold_value': row[3],
                        'severity': row[4],
                        'message': row[5]
                    })

                return alerts

        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                # Get basic statistics
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_metrics,
                        AVG(total_errors) as avg_errors,
                        MAX(total_errors) as max_errors,
                        AVG(recovery_success_rate) as avg_recovery_rate,
                        AVG(system_health_score) as avg_health_score
                    FROM error_metrics
                    WHERE timestamp >= ?
                """, (cutoff_time,))

                stats_row = cursor.fetchone()

                # Get category distribution
                cursor = conn.execute("""
                    SELECT errors_by_category FROM error_metrics
                    WHERE timestamp >= ?
                """, (cutoff_time,))

                category_totals = defaultdict(int)
                for row in cursor.fetchall():
                    if row[0]:
                        categories = json.loads(row[0])
                        for category, count in categories.items():
                            category_totals[category] += count

                return {
                    'total_metrics_records': stats_row[0],
                    'average_errors_per_minute': stats_row[1],
                    'peak_errors_per_minute': stats_row[2],
                    'average_recovery_rate': stats_row[3],
                    'average_system_health': stats_row[4],
                    'error_distribution_by_category': dict(category_totals),
                    'analysis_period_hours': hours
                }

        except Exception as e:
            self.logger.error(f"Failed to get error statistics: {e}")
            return {}

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule_id}")

    def get_alert_rules(self) -> Dict[str, AlertRule]:
        """Get all alert rules"""
        return self.alert_rules.copy()

class RealTimeErrorMonitor:
    """Real-time error monitoring dashboard interface"""

    def __init__(self, analytics_engine: ErrorAnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.logger = get_logger("realtime_monitor")
        self.update_callbacks: List[Callable] = []
        self.monitoring_active = False

    def add_update_callback(self, callback: Callable):
        """Add a callback to be called when metrics are updated"""
        self.update_callbacks.append(callback)

    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.logger.info("Real-time monitoring started")

        # Start monitoring loop
        threading.Thread(target=self._monitoring_loop, daemon=True).start()

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        self.logger.info("Real-time monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Get current metrics
                metrics = self.analytics_engine.get_current_metrics()

                # Notify callbacks
                for callback in self.update_callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Update callback failed: {e}")

                # Wait for next update
                time.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(30)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get current metrics
            current_metrics = self.analytics_engine.get_current_metrics()

            # Get error trends
            trends = self.analytics_engine.get_error_trends()

            # Get recent alerts
            recent_alerts = self.analytics_engine.get_recent_alerts(hours=1)

            # Get error statistics
            stats = self.analytics_engine.get_error_statistics(hours=24)

            # Calculate health summary
            health_summary = self._calculate_health_summary(current_metrics, trends)

            return {
                'timestamp': datetime.now().isoformat(),
                'current_metrics': asdict(current_metrics),
                'trends': [asdict(trend) for trend in trends],
                'recent_alerts': recent_alerts[:10],  # Last 10 alerts
                'statistics': stats,
                'health_summary': health_summary,
                'system_status': self._determine_system_status(health_summary)
            }

        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}

    def _calculate_health_summary(self, metrics: ErrorMetrics, trends: List[ErrorTrend]) -> Dict[str, Any]:
        """Calculate overall health summary"""
        health_score = metrics.system_health_score
        recovery_rate = metrics.recovery_success_rate

        # Assess trends
        concerning_trends = [t for t in trends if t.alert_triggered]
        positive_trends = [t for t in trends if t.trend_direction == "increasing" and
                          t.metric_name in ['recovery_success_rate', 'system_health_score']]

        # Determine overall health status
        if health_score >= 0.9 and recovery_rate >= 0.8 and not concerning_trends:
            status = "excellent"
        elif health_score >= 0.7 and recovery_rate >= 0.6 and len(concerning_trends) <= 1:
            status = "good"
        elif health_score >= 0.5 and recovery_rate >= 0.4:
            status = "fair"
        else:
            status = "poor"

        return {
            'overall_health_score': health_score,
            'recovery_success_rate': recovery_rate,
            'status': status,
            'concerning_trends': len(concerning_trends),
            'positive_trends': len(positive_trends),
            'recommendations': self._generate_health_recommendations(metrics, trends, status)
        }

    def _determine_system_status(self, health_summary: Dict[str, Any]) -> str:
        """Determine overall system status"""
        status = health_summary['status']

        if status == "excellent":
            return "🟢 All Systems Operational"
        elif status == "good":
            return "🟡 Minor Issues Detected"
        elif status == "fair":
            return "🟠 Performance Degraded"
        else:
            return "🔴 Critical Issues Present"

    def _generate_health_recommendations(self, metrics: ErrorMetrics, trends: List[ErrorTrend], status: str) -> List[str]:
        """Generate health recommendations"""
        recommendations = []

        # Based on metrics
        if metrics.recovery_success_rate < 0.7:
            recommendations.append("Review and improve recovery strategies")

        if metrics.system_health_score < 0.6:
            recommendations.append("Investigate system health issues")

        if metrics.active_circuit_breakers > 2:
            recommendations.append("Multiple circuit breakers active - investigate root causes")

        # Based on trends
        for trend in trends:
            if trend.alert_triggered:
                if trend.metric_name == "total_errors":
                    recommendations.append(f"Error rate is {trend.trend_direction} - investigate cause")
                elif trend.metric_name == "recovery_success_rate":
                    recommendations.append(f"Recovery success rate is {trend.trend_direction} - review recovery procedures")
                elif trend.metric_name == "system_health_score":
                    recommendations.append(f"System health is {trend.trend_direction} - perform system maintenance")

        # Add general recommendations based on status
        if status == "poor":
            recommendations.append("Immediate attention required - consider escalating to operations team")
        elif status == "fair":
            recommendations.append("Schedule maintenance window to address issues")

        return recommendations

# Global instances
_analytics_engine = None
_realtime_monitor = None

def get_error_analytics_engine() -> ErrorAnalyticsEngine:
    """Get the global error analytics engine instance"""
    global _analytics_engine

    if _analytics_engine is None:
        _analytics_engine = ErrorAnalyticsEngine()

    return _analytics_engine

def get_realtime_monitor() -> RealTimeErrorMonitor:
    """Get the global real-time monitor instance"""
    global _realtime_monitor

    if _realtime_monitor is None:
        _realtime_monitor = RealTimeErrorMonitor(get_error_analytics_engine())

    return _realtime_monitor

if __name__ == "__main__":
    # Example usage
    def example_usage():
        """Demonstrate error monitoring system usage"""

        # Create analytics engine
        analytics_engine = ErrorAnalyticsEngine()

        # Create real-time monitor
        monitor = RealTimeErrorMonitor(analytics_engine)

        # Add update callback
        def on_metrics_update(metrics):
            print(f"Metrics updated: {metrics.total_errors} errors, health score: {metrics.system_health_score:.2f}")

        monitor.add_update_callback(on_metrics_update)

        # Start monitoring
        monitor.start_monitoring()

        # Simulate some activity
        print("Monitoring started... Running for 2 minutes")
        time.sleep(120)

        # Get dashboard data
        dashboard_data = monitor.get_dashboard_data()
        print(f"Dashboard data: {dashboard_data}")

        # Stop monitoring
        monitor.stop_monitoring()

    example_usage()