#!/usr/bin/env python3
"""
Intelligent Alerting System with Pattern Recognition
Advanced alerting with machine learning-based anomaly detection and predictive analytics
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(Enum):
    THRESHOLD = "threshold"
    TREND = "trend"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    PREDICTIVE = "predictive"
    CORRELATION = "correlation"

@dataclass
class Alert:
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    service_name: Optional[str] = None
    metrics: Dict[str, Any] = None
    context: Dict[str, Any] = None
    timestamp: datetime = None
    acknowledged: bool = False
    resolved: bool = False
    confidence: float = 1.0
    prediction: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metrics is None:
            self.metrics = {}
        if self.context is None:
            self.context = {}

@dataclass
class AlertRule:
    name: str
    type: AlertType
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message_template: str
    cooldown: int = 300  # seconds
    enabled: bool = True
    context_filters: Optional[Dict[str, Any]] = None

class IntelligentAlertingSystem:
    """Advanced alerting system with ML-based pattern recognition"""

    def __init__(self, db_path: str = "alerts.db"):
        self.db_path = db_path
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.correlations: Dict[str, List[str]] = {}

        # Alert subscriptions
        self.alert_subscribers: List[Callable] = []

        # Machine learning models (simplified)
        self.models: Dict[str, Any] = {}

        # Initialize system
        self._initialize_database()
        self._load_default_rules()
        self._initialize_patterns()

    def _initialize_database(self):
        """Initialize alert database"""
        import sqlite3

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        service_name TEXT,
                        metrics TEXT,
                        context TEXT,
                        timestamp DATETIME NOT NULL,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        confidence REAL DEFAULT 1.0,
                        prediction TEXT
                    )
                ''')

                # Metrics history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp DATETIME NOT NULL,
                        context TEXT
                    )
                ''')

                # Patterns table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        service_name TEXT,
                        pattern_data TEXT NOT NULL,
                        confidence REAL,
                        timestamp DATETIME NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')

                # Correlations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS correlations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service1 TEXT NOT NULL,
                        service2 TEXT NOT NULL,
                        correlation_coefficient REAL,
                        lag_seconds INTEGER,
                        confidence REAL,
                        timestamp DATETIME NOT NULL
                    )
                ''')

                conn.commit()
                logger.info("Alerting system database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize alerting database: {e}")

    def _load_default_rules(self):
        """Load default alerting rules"""
        self.alert_rules = {
            'high_cpu_usage': AlertRule(
                name='high_cpu_usage',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('cpu_percent', 0) > 80,
                severity=AlertSeverity.WARNING,
                message_template='High CPU usage: {cpu_percent}%',
                cooldown=300
            ),
            'critical_cpu_usage': AlertRule(
                name='critical_cpu_usage',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('cpu_percent', 0) > 95,
                severity=AlertSeverity.CRITICAL,
                message_template='Critical CPU usage: {cpu_percent}%',
                cooldown=60
            ),
            'high_memory_usage': AlertRule(
                name='high_memory_usage',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('memory_percent', 0) > 85,
                severity=AlertSeverity.WARNING,
                message_template='High memory usage: {memory_percent}%',
                cooldown=300
            ),
            'critical_memory_usage': AlertRule(
                name='critical_memory_usage',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('memory_percent', 0) > 95,
                severity=AlertSeverity.CRITICAL,
                message_template='Critical memory usage: {memory_percent}%',
                cooldown=60
            ),
            'service_down': AlertRule(
                name='service_down',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('status') == 'unhealthy',
                severity=AlertSeverity.CRITICAL,
                message_template='Service {service_name} is down',
                cooldown=60
            ),
            'slow_response': AlertRule(
                name='slow_response',
                type=AlertType.THRESHOLD,
                condition=lambda data: data.get('response_time', 0) > 5,
                severity=AlertSeverity.WARNING,
                message_template='Slow response from {service_name}: {response_time}s',
                cooldown=300
            ),
            'frequent_restarts': AlertRule(
                name='frequent_restarts',
                type=AlertType.PATTERN,
                condition=lambda data: data.get('restart_count', 0) > 3,
                severity=AlertSeverity.WARNING,
                message_template='Service {service_name} restarting frequently: {restart_count} times',
                cooldown=600
            ),
            'memory_leak_detected': AlertRule(
                name='memory_leak_detected',
                type=AlertType.TREND,
                condition=lambda data: self._detect_memory_leak(data),
                severity=AlertSeverity.WARNING,
                message_template='Potential memory leak detected in {service_name}',
                cooldown=3600
            ),
            'performance_degradation': AlertRule(
                name='performance_degradation',
                type=AlertType.TREND,
                condition=lambda data: self._detect_performance_degradation(data),
                severity=AlertSeverity.WARNING,
                message_template='Performance degradation detected for {service_name}',
                cooldown=1800
            ),
            'anomalous_behavior': AlertRule(
                name='anomalous_behavior',
                type=AlertType.ANOMALY,
                condition=lambda data: self._detect_anomaly(data),
                severity=AlertSeverity.INFO,
                message_template='Anomalous behavior detected for {service_name}',
                cooldown=1800
            ),
            'predictive_failure': AlertRule(
                name='predictive_failure',
                type=AlertType.PREDICTIVE,
                condition=lambda data: self._predict_failure(data),
                severity=AlertSeverity.WARNING,
                message_template='Predicted potential failure for {service_name} in {time_to_failure}',
                cooldown=3600
            )
        }

    def _initialize_patterns(self):
        """Initialize pattern detection"""
        self.patterns = {
            'diurnal': {
                'description': 'Daily usage patterns',
                'period': 86400,  # 24 hours in seconds
                'enabled': True
            },
            'weekly': {
                'description': 'Weekly usage patterns',
                'period': 604800,  # 7 days in seconds
                'enabled': True
            },
            'spike': {
                'description': 'Sudden usage spikes',
                'threshold_multiplier': 3.0,
                'enabled': True
            },
            'dip': {
                'description': 'Sudden usage drops',
                'threshold_multiplier': 0.3,
                'enabled': True
            }
        }

    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def subscribe_to_alerts(self, callback: Callable):
        """Subscribe to alert notifications"""
        self.alert_subscribers.append(callback)

    def unsubscribe_from_alerts(self, callback: Callable):
        """Unsubscribe from alert notifications"""
        if callback in self.alert_subscribers:
            self.alert_subscribers.remove(callback)

    async def process_metrics(self, service_name: str, metrics: Dict[str, Any]):
        """Process incoming metrics and trigger alerts"""
        try:
            timestamp = datetime.now()

            # Store metrics in history
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    self.metrics_history[f"{service_name}.{metric_name}"].append({
                        'timestamp': timestamp,
                        'value': value,
                        'service': service_name
                    })

                    # Store in database
                    await self._store_metric(service_name, metric_name, value, timestamp)

            # Update baselines
            self._update_baselines(service_name, metrics)

            # Detect correlations
            self._detect_correlations(service_name, metrics)

            # Check alert rules
            await self._check_alert_rules(service_name, metrics)

            # Detect patterns
            await self._detect_patterns(service_name, metrics)

            # Predictive analysis
            await self._predictive_analysis(service_name, metrics)

        except Exception as e:
            logger.error(f"Error processing metrics for {service_name}: {e}")

    async def _check_alert_rules(self, service_name: str, metrics: Dict[str, Any]):
        """Check all alert rules against current metrics"""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            try:
                # Prepare data for condition check
                check_data = {
                    'service_name': service_name,
                    'timestamp': datetime.now(),
                    **metrics
                }

                # Apply context filters
                if rule.context_filters:
                    if not all(check_data.get(k) == v for k, v in rule.context_filters.items()):
                        continue

                # Check condition
                if rule.condition(check_data):
                    # Check cooldown
                    alert_key = f"{rule_name}_{service_name}"
                    if self._is_in_cooldown(alert_key, rule.cooldown):
                        continue

                    # Generate alert
                    alert = Alert(
                        id=f"{rule_name}_{service_name}_{int(time.time())}",
                        type=rule.type,
                        severity=rule.severity,
                        title=f"{rule.name.replace('_', ' ').title()}",
                        message=rule.message_template.format(**check_data),
                        service_name=service_name,
                        metrics=metrics,
                        context={
                            'rule_name': rule_name,
                            'rule_type': rule.type.value,
                            'check_data': check_data
                        }
                    )

                    await self._trigger_alert(alert)

            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")

    def _is_in_cooldown(self, alert_key: str, cooldown_seconds: int) -> bool:
        """Check if alert is in cooldown period"""
        # Check active alerts
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            time_since_alert = (datetime.now() - alert.timestamp).total_seconds()
            return time_since_alert < cooldown_seconds

        # Check alert history
        for alert in reversed(self.alert_history):
            if alert.id.startswith(alert_key):
                time_since_alert = (datetime.now() - alert.timestamp).total_seconds()
                return time_since_alert < cooldown_seconds

        return False

    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        try:
            # Store active alert
            self.active_alerts[alert.id] = alert

            # Add to history
            self.alert_history.append(alert)

            # Store in database
            await self._store_alert(alert)

            # Notify subscribers
            for subscriber in self.alert_subscribers:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(alert)
                    else:
                        subscriber(alert)
                except Exception as e:
                    logger.error(f"Error in alert subscriber: {e}")

            logger.warning(f"Alert triggered: {alert.severity.value} - {alert.message}")

        except Exception as e:
            logger.error(f"Error triggering alert: {e}")

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO alerts
                    (id, type, severity, title, message, service_name, metrics, context, timestamp, acknowledged, resolved, confidence, prediction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.id,
                    alert.type.value,
                    alert.severity.value,
                    alert.title,
                    alert.message,
                    alert.service_name,
                    json.dumps(alert.metrics),
                    json.dumps(alert.context),
                    alert.timestamp,
                    alert.acknowledged,
                    alert.resolved,
                    alert.confidence,
                    json.dumps(alert.prediction) if alert.prediction else None
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing alert: {e}")

    async def _store_metric(self, service_name: str, metric_name: str, value: float, timestamp: datetime):
        """Store metric in database"""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO metrics_history (service_name, metric_name, value, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (service_name, metric_name, value, timestamp))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing metric: {e}")

    def _update_baselines(self, service_name: str, metrics: Dict[str, Any]):
        """Update baseline metrics for anomaly detection"""
        if service_name not in self.baselines:
            self.baselines[service_name] = {}

        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                key = f"{service_name}.{metric_name}"
                history = self.metrics_history[key]

                if len(history) >= 10:  # Need sufficient history
                    values = [h['value'] for h in history]
                    self.baselines[service_name][metric_name] = {
                        'mean': statistics.mean(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0,
                        'median': statistics.median(values),
                        'percentile_95': np.percentile(values, 95) if len(values) > 0 else 0,
                        'updated': datetime.now()
                    }

    def _detect_correlations(self, service_name: str, metrics: Dict[str, Any]):
        """Detect correlations between services and metrics"""
        current_time = time.time()

        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                key = f"{service_name}.{metric_name}"
                current_history = self.metrics_history[key]

                if len(current_history) < 20:  # Need sufficient history
                    continue

                # Check correlations with other metrics
                for other_key, other_history in self.metrics_history.items():
                    if other_key == key:
                        continue

                    if len(other_history) >= 20:
                        correlation = self._calculate_correlation(current_history, other_history)
                        if abs(correlation) > 0.7:  # Strong correlation
                            correlation_key = f"{key}__{other_key}"
                            self.correlations[correlation_key] = {
                                'services': [service_name, other_key.split('.')[0]],
                                'metrics': [metric_name, other_key.split('.')[1]],
                                'coefficient': correlation,
                                'timestamp': current_time
                            }

    def _calculate_correlation(self, history1: deque, history2: deque) -> float:
        """Calculate Pearson correlation coefficient between two metric histories"""
        try:
            # Align timestamps and extract values
            values1 = []
            values2 = []

            for entry in history1:
                # Find closest entry in history2
                closest = min(history2, key=lambda x: abs(x['timestamp'] - entry['timestamp']))
                if abs((entry['timestamp'] - closest['timestamp']).total_seconds()) < 60:  # Within 1 minute
                    values1.append(entry['value'])
                    values2.append(closest['value'])

            if len(values1) < 10:
                return 0.0

            return statistics.correlation(values1, values2) if len(values1) > 1 else 0.0

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0

    async def _detect_patterns(self, service_name: str, metrics: Dict[str, Any]):
        """Detect patterns in metrics"""
        try:
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    key = f"{service_name}.{metric_name}"
                    history = self.metrics_history[key]

                    if len(history) < 50:  # Need sufficient history
                        continue

                    # Detect various patterns
                    await self._detect_spike_pattern(key, history)
                    await self._detect_dip_pattern(key, history)
                    await self._detect_seasonal_pattern(key, history)
                    await self._detect_trend_pattern(key, history)

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")

    async def _detect_spike_pattern(self, key: str, history: deque):
        """Detect sudden spikes in metrics"""
        if len(history) < 10:
            return

        recent_values = [h['value'] for h in list(history)[-10:]]
        older_values = [h['value'] for h in list(history)[-50:-10]]

        if not older_values:
            return

        recent_avg = statistics.mean(recent_values)
        older_avg = statistics.mean(older_values)

        if older_avg > 0 and recent_avg > older_avg * 3:  # 3x increase
            alert = Alert(
                id=f"spike_{key}_{int(time.time())}",
                type=AlertType.PATTERN,
                severity=AlertSeverity.WARNING,
                title="Usage Spike Detected",
                message=f"Sudden spike detected in {key}: {recent_avg:.2f} vs baseline {older_avg:.2f}",
                metrics={'current_avg': recent_avg, 'baseline_avg': older_avg, 'multiplier': recent_avg / older_avg}
            )

            await self._trigger_alert(alert)

    async def _detect_dip_pattern(self, key: str, history: deque):
        """Detect sudden dips in metrics"""
        if len(history) < 10:
            return

        recent_values = [h['value'] for h in list(history)[-10:]]
        older_values = [h['value'] for h in list(history)[-50:-10]]

        if not older_values:
            return

        recent_avg = statistics.mean(recent_values)
        older_avg = statistics.mean(older_values)

        if older_avg > 0 and recent_avg < older_avg * 0.3:  # 70% decrease
            alert = Alert(
                id=f"dip_{key}_{int(time.time())}",
                type=AlertType.PATTERN,
                severity=AlertSeverity.INFO,
                title="Usage Dip Detected",
                message=f"Sudden dip detected in {key}: {recent_avg:.2f} vs baseline {older_avg:.2f}",
                metrics={'current_avg': recent_avg, 'baseline_avg': older_avg, 'multiplier': recent_avg / older_avg}
            )

            await self._trigger_alert(alert)

    async def _detect_seasonal_pattern(self, key: str, history: deque):
        """Detect seasonal patterns (simplified)"""
        # This would use more sophisticated time series analysis in a production system
        pass

    async def _detect_trend_pattern(self, key: str, history: deque):
        """Detect trend patterns"""
        if len(history) < 20:
            return

        values = [h['value'] for h in list(history)[-20:]]
        first_half = values[:10]
        second_half = values[10:]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if first_avg > 0:
            trend_percent = ((second_avg - first_avg) / first_avg) * 100

            if abs(trend_percent) > 50:  # 50% change
                trend_direction = "increasing" if trend_percent > 0 else "decreasing"

                alert = Alert(
                    id=f"trend_{key}_{int(time.time())}",
                    type=AlertType.TREND,
                    severity=AlertSeverity.INFO,
                    title=f"Trend Pattern Detected",
                    message=f"{trend_direction.title()} trend detected in {key}: {trend_percent:.1f}% change",
                    metrics={'trend_percent': trend_percent, 'trend_direction': trend_direction}
                )

                await self._trigger_alert(alert)

    async def _predictive_analysis(self, service_name: str, metrics: Dict[str, Any]):
        """Perform predictive analysis for early warning"""
        try:
            # Simple linear regression for trend prediction
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    key = f"{service_name}.{metric_name}"
                    history = self.metrics_history[key]

                    if len(history) < 20:
                        continue

                    # Predict future values
                    prediction = self._predict_future_values(history)

                    if prediction and prediction.get('anomaly_risk', 0) > 0.7:
                        alert = Alert(
                            id=f"predictive_{key}_{int(time.time())}",
                            type=AlertType.PREDICTIVE,
                            severity=AlertSeverity.WARNING,
                            title="Predictive Alert",
                            message=f"High risk of anomaly predicted for {key} in {prediction.get('time_to_failure', 'unknown')}",
                            prediction=prediction,
                            confidence=prediction.get('confidence', 0.5)
                        )

                        await self._trigger_alert(alert)

        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")

    def _predict_future_values(self, history: deque, steps_ahead: int = 10) -> Optional[Dict[str, Any]]:
        """Simple linear regression prediction"""
        try:
            if len(history) < 20:
                return None

            values = [h['value'] for h in list(history)[-20:]]
            times = list(range(len(values)))

            # Simple linear regression
            n = len(values)
            sum_x = sum(times)
            sum_y = sum(values)
            sum_xy = sum(t * v for t, v in zip(times, values))
            sum_x2 = sum(t * t for t in times)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Predict future values
            future_values = [slope * (n + i) + intercept for i in range(1, steps_ahead + 1)]

            # Calculate confidence and anomaly risk
            current_value = values[-1]
            predicted_avg = statistics.mean(future_values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0

            anomaly_risk = 0
            if std_dev > 0:
                z_score = abs(predicted_avg - current_value) / std_dev
                anomaly_risk = min(z_score / 3.0, 1.0)  # Normalize to 0-1

            return {
                'future_values': future_values,
                'predicted_avg': predicted_avg,
                'anomaly_risk': anomaly_risk,
                'confidence': max(0, 1 - anomaly_risk),
                'time_to_failure': f"{steps_ahead * 5} minutes"  # Assuming 5-minute intervals
            }

        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return None

    # Rule condition helper methods
    def _detect_memory_leak(self, data: Dict[str, Any]) -> bool:
        """Detect potential memory leaks"""
        service_name = data.get('service_name')
        if not service_name:
            return False

        key = f"{service_name}.memory_percent"
        history = self.metrics_history[key]

        if len(history) < 60:  # Need at least 1 hour of data
            return False

        # Check for steady upward trend
        values = [h['value'] for h in list(history)[-60:]]
        first_quarter = values[:15]
        last_quarter = values[-15:]

        first_avg = statistics.mean(first_quarter)
        last_avg = statistics.mean(last_quarter)

        # 25% increase over time period
        return last_avg > first_avg * 1.25

    def _detect_performance_degradation(self, data: Dict[str, Any]) -> bool:
        """Detect performance degradation"""
        service_name = data.get('service_name')
        if not service_name:
            return False

        key = f"{service_name}.response_time"
        history = self.metrics_history[key]

        if len(history) < 30:
            return False

        # Check for increasing response times
        values = [h['value'] for h in list(history)[-30:] if h['value'] > 0]
        if len(values) < 20:
            return False

        recent_values = values[-10:]
        older_values = values[-30:-10]

        recent_avg = statistics.mean(recent_values)
        older_avg = statistics.mean(older_values)

        # 50% increase in response time
        return recent_avg > older_avg * 1.5

    def _detect_anomaly(self, data: Dict[str, Any]) -> bool:
        """Detect anomalous behavior using statistical methods"""
        service_name = data.get('service_name')
        if not service_name:
            return False

        # Check multiple metrics for anomalies
        anomaly_count = 0
        total_checks = 0

        for metric_name, value in data.items():
            if isinstance(value, (int, float)):
                key = f"{service_name}.{metric_name}"
                baseline = self.baselines.get(service_name, {}).get(metric_name)

                if baseline and baseline.get('std', 0) > 0:
                    z_score = abs(value - baseline['mean']) / baseline['std']
                    if z_score > 3:  # 3 standard deviations
                        anomaly_count += 1
                    total_checks += 1

        return total_checks > 0 and (anomaly_count / total_checks) > 0.3  # 30% of metrics anomalous

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            await self._update_alert_in_db(alert_id, {'acknowledged': True})
            return True
        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            await self._update_alert_in_db(alert_id, {'resolved': True})
            del self.active_alerts[alert_id]
            return True
        return False

    async def _update_alert_in_db(self, alert_id: str, updates: Dict[str, Any]):
        """Update alert in database"""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [alert_id]

                cursor.execute(f'UPDATE alerts SET {set_clause} WHERE id = ?', values)
                conn.commit()

        except Exception as e:
            logger.error(f"Error updating alert in DB: {e}")

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return alerts

    def get_alert_history(self, hours: int = 24, service_name: Optional[str] = None) -> List[Alert]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = [alert for alert in self.alert_history if alert.timestamp > cutoff_time]
        if service_name:
            history = [alert for alert in history if alert.service_name == service_name]

        return history

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        active_alerts = self.get_active_alerts()

        return {
            'total_active_alerts': len(active_alerts),
            'alerts_by_severity': {
                'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                'warning': len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                'info': len([a for a in active_alerts if a.severity == AlertSeverity.INFO])
            },
            'services_monitored': len(self.baselines),
            'correlations_detected': len(self.correlations),
            'timestamp': datetime.now().isoformat()
        }

# Global instance
_intelligent_alerting_system: Optional[IntelligentAlertingSystem] = None

def get_intelligent_alerting_system() -> IntelligentAlertingSystem:
    """Get the global intelligent alerting system instance"""
    global _intelligent_alerting_system
    if _intelligent_alerting_system is None:
        _intelligent_alerting_system = IntelligentAlertingSystem()
    return _intelligent_alerting_system