"""
DuckBot Security Monitoring and Threat Detection System

Real-time security monitoring and threat detection including:
- Intrusion detection and prevention
- Anomaly detection and behavioral analysis
- Real-time threat alerts
- Security incident response
- Vulnerability scanning
- Compliance monitoring
- Security metrics and reporting

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import threading
import time
import ipaddress
import re
import hashlib
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import statistics
from collections import defaultdict, deque
import aiohttp
import aiofiles

security_monitor_logger = logging.getLogger('duckbot.security.monitoring')

class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"

class ThreatType(Enum):
    """Threat types"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    DDOS_ATTACK = "ddos_attack"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    MALWARE_DETECTED = "malware_detected"
    PHISHING_ATTEMPT = "phishing_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    SUSPICIOUS_NETWORK = "suspicious_network"
    ZERO_DAY_EXPLOIT = "zero_day_exploit"
    ACCOUNT_TAKEOVER = "account_takeover"
    CREDENTIAL_STUFFING = "credential_stuffing"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"

class EventType(Enum):
    """Event types for monitoring"""
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    API_REQUEST = "api_request"
    WEB_REQUEST = "web_request"
    FILE_UPLOAD = "file_upload"
    CONFIG_CHANGE = "config_change"
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    NETWORK_EVENT = "network_event"

@dataclass
class SecurityEvent:
    """Security event for monitoring"""
    id: str
    event_type: EventType
    timestamp: datetime
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    details: Dict[str, Any] = None
    severity: ThreatLevel = ThreatLevel.LOW
    source: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class SecurityAlert:
    """Security alert"""
    id: str
    threat_type: ThreatType
    severity: ThreatLevel
    title: str
    description: str
    timestamp: datetime
    source_events: List[str]
    affected_resources: List[str]
    status: AlertStatus = AlertStatus.OPEN
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class SecurityMetrics:
    """Security metrics"""
    total_events: int
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    unique_ips: int
    unique_users: int
    blocked_requests: int
    failed_authentications: int
    suspicious_activities: int
    uptime_percentage: float
    response_time_avg: float
    threat_detection_rate: float

@dataclass
class AnomalyDetection:
    """Anomaly detection configuration"""
    enabled: bool = True
    sensitivity: float = 0.7  # 0.0 to 1.0
    window_size: int = 100  # Number of events to analyze
    baseline_period: int = 7  # Days for baseline
    check_interval: int = 60  # Seconds between checks

class SecurityMonitor:
    """Main security monitoring system"""

    def __init__(self, anomaly_config: AnomalyDetection = None):
        self.anomaly_config = anomaly_config or AnomalyDetection()

        # Event storage
        self.events: deque = deque(maxlen=10000)
        self.alerts: Dict[str, SecurityAlert] = {}
        self.event_history: List[SecurityEvent] = []

        # Threat detection patterns
        self.threat_patterns = self._load_threat_patterns()
        self.ip_reputation = {}
        self.user_behavior_profiles = defaultdict(dict)
        self.baseline_metrics = {}

        # Rate limiting and tracking
        self.ip_request_counts = defaultdict(int)
        self.user_request_counts = defaultdict(int)
        self.failed_login_attempts = defaultdict(list)

        # Alert handlers
        self.alert_handlers: List[Callable] = []

        # Background tasks
        self.monitoring_active = False
        self.background_tasks = []

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Statistics
        self.metrics = SecurityMetrics(
            total_events=0,
            total_alerts=0,
            critical_alerts=0,
            high_alerts=0,
            medium_alerts=0,
            low_alerts=0,
            unique_ips=0,
            unique_users=0,
            blocked_requests=0,
            failed_authentications=0,
            suspicious_activities=0,
            uptime_percentage=100.0,
            response_time_avg=0.0,
            threat_detection_rate=0.0
        )

        security_monitor_logger.info("SecurityMonitor initialized")

    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns"""
        return {
            "sql_injection": [
                r"(union\s+select)",
                r"(drop\s+table)",
                r"(insert\s+into)",
                r"(update\s+\w+\s+set)",
                r"(delete\s+from)",
                r"(exec\s*\()",
                r"(xp_cmdshell)",
                r"(''|'')",
                r"(--)",
                r"(/\*.*\*/)"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"eval\s*\(",
                r"document\.cookie",
                r"document\.write"
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"~/",
                r"/etc/passwd",
                r"c:\\windows\\system32",
                r"\.\.\.%2f"
            ],
            "command_injection": [
                r"[;&|`$(){}\\]",
                r"/dev/tcp",
                r"nc\s+-l",
                r"curl\s+",
                r"wget\s+",
                r"exec\s+",
                r"system\s*\("
            ],
            "brute_force": [
                r"rapid.*login.*attempts",
                r"multiple.*failed.*authentications"
            ]
        }

    async def start_monitoring(self):
        """Start security monitoring"""
        self.monitoring_active = True
        security_monitor_logger.info("Security monitoring started")

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._anomaly_detection_loop()),
            asyncio.create_task(self._threat_detection_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]

    async def stop_monitoring(self):
        """Stop security monitoring"""
        self.monitoring_active = False
        security_monitor_logger.info("Security monitoring stopped")

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def add_security_event(self, event: SecurityEvent):
        """Add security event for monitoring"""
        try:
            # Add to event queue
            self.events.append(event)
            self.event_history.append(event)

            # Update metrics
            self._update_metrics(event)

            # Update tracking data
            self._update_tracking_data(event)

            # Real-time threat detection
            asyncio.create_task(self._detect_threats_in_realtime(event))

        except Exception as e:
            security_monitor_logger.error(f"Failed to add security event: {e}")

    async def _detect_threats_in_realtime(self, event: SecurityEvent):
        """Detect threats in real-time"""
        try:
            # Check for immediate threats
            if event.event_type == EventType.FAILED_LOGIN:
                await self._check_brute_force_attack(event)

            # Check for suspicious patterns
            if event.details:
                await self._check_suspicious_patterns(event)

            # Check for anomalous behavior
            if self.anomaly_config.enabled:
                await self._check_anomalous_behavior(event)

        except Exception as e:
            security_monitor_logger.error(f"Real-time threat detection failed: {e}")

    async def _check_brute_force_attack(self, event: SecurityEvent):
        """Check for brute force attacks"""
        if not event.ip_address or not event.username:
            return

        ip_key = f"brute_force_ip:{event.ip_address}"
        user_key = f"brute_force_user:{event.username}"

        # Track failed attempts
        now = datetime.utcnow()
        self.failed_login_attempts[ip_key].append(now)
        self.failed_login_attempts[user_key].append(now)

        # Clean old attempts (last hour)
        cutoff = now - timedelta(hours=1)
        self.failed_login_attempts[ip_key] = [t for t in self.failed_login_attempts[ip_key] if t > cutoff]
        self.failed_login_attempts[user_key] = [t for t in self.failed_login_attempts[user_key] if t > cutoff]

        # Check thresholds
        ip_attempts = len(self.failed_login_attempts[ip_key])
        user_attempts = len(self.failed_login_attempts[user_key])

        if ip_attempts > 10 or user_attempts > 5:
            await self._create_security_alert(
                threat_type=ThreatType.BRUTE_FORCE,
                severity=ThreatLevel.HIGH if ip_attempts > 20 else ThreatLevel.MEDIUM,
                title="Potential Brute Force Attack",
                description=f"Detected {ip_attempts} failed login attempts from IP {event.ip_address} and {user_attempts} for user {event.username}",
                source_events=[event.id],
                affected_resources=[event.ip_address, event.username],
                metadata={
                    "ip_attempts": ip_attempts,
                    "user_attempts": user_attempts,
                    "time_window": "1 hour"
                }
            )

    async def _check_suspicious_patterns(self, event: SecurityEvent):
        """Check for suspicious patterns in event details"""
        details_str = json.dumps(event.details).lower()

        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, details_str, re.IGNORECASE):
                    await self._create_security_alert(
                        threat_type=ThreatType(threat_type),
                        severity=ThreatLevel.HIGH,
                        title=f"Potential {threat_type.replace('_', ' ').title()} Attack",
                        description=f"Detected suspicious pattern in {event.event_type.value} event",
                        source_events=[event.id],
                        affected_resources=[event.resource or "unknown"],
                        metadata={
                            "pattern": pattern,
                            "event_type": event.event_type.value,
                            "user_id": event.user_id
                        }
                    )

    async def _check_anomalous_behavior(self, event: SecurityEvent):
        """Check for anomalous behavior patterns"""
        if not event.user_id:
            return

        # Get user behavior profile
        user_profile = self.user_behavior_profiles[event.user_id]

        # Update activity patterns
        if event.event_type not in user_profile:
            user_profile[event.event_type] = {
                "count": 0,
                "avg_per_hour": 0.0,
                "last_seen": None
            }

        user_profile[event.event_type]["count"] += 1
        user_profile[event.event_type]["last_seen"] = event.timestamp

        # Calculate hourly rate
        recent_events = [e for e in self.event_history if e.user_id == event.user_id and
                        e.timestamp > event.timestamp - timedelta(hours=1)]
        hourly_rate = len(recent_events)

        # Check for anomalies
        if len(self.event_history) > self.anomaly_config.window_size:
            baseline = self._get_baseline_metric(event.event_type)
            if baseline and hourly_rate > baseline * 2:  # 2x baseline
                await self._create_security_alert(
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    severity=ThreatLevel.MEDIUM,
                    title="Anomalous User Activity",
                    description=f"User {event.username or event.user_id} showing unusual activity patterns",
                    source_events=[event.id],
                    affected_resources=[event.user_id],
                    metadata={
                        "user_id": event.user_id,
                        "hourly_rate": hourly_rate,
                        "baseline_rate": baseline,
                        "event_type": event.event_type.value
                    }
                )

    def _get_baseline_metric(self, event_type: EventType) -> Optional[float]:
        """Get baseline metric for event type"""
        key = f"baseline_{event_type.value}"
        return self.baseline_metrics.get(key)

    def _update_tracking_data(self, event: SecurityEvent):
        """Update tracking data for metrics"""
        # Track IP addresses
        if event.ip_address:
            self.ip_request_counts[event.ip_address] += 1

        # Track users
        if event.user_id:
            self.user_request_counts[event.user_id] += 1

        # Track failed authentications
        if event.event_type == EventType.FAILED_LOGIN:
            self.metrics.failed_authentications += 1

    def _update_metrics(self, event: SecurityEvent):
        """Update security metrics"""
        self.metrics.total_events += 1

        if event.severity == ThreatLevel.CRITICAL:
            self.metrics.suspicious_activities += 1

    async def _anomaly_detection_loop(self):
        """Background anomaly detection loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.anomaly_config.check_interval)
                await self._run_anomaly_detection()
            except Exception as e:
                security_monitor_logger.error(f"Anomaly detection loop error: {e}")

    async def _run_anomaly_detection(self):
        """Run comprehensive anomaly detection"""
        try:
            # Check for unusual traffic patterns
            await self._detect_traffic_anomalies()

            # Check for unusual authentication patterns
            await self._detect_auth_anomalies()

            # Check for unusual system behavior
            await self._detect_system_anomalies()

        except Exception as e:
            security_monitor_logger.error(f"Anomaly detection error: {e}")

    async def _detect_traffic_anomalies(self):
        """Detect traffic anomalies"""
        # Get recent events
        now = datetime.utcnow()
        recent_events = [e for e in self.event_history if e.timestamp > now - timedelta(minutes=5)]

        if not recent_events:
            return

        # Check for traffic spikes
        current_rate = len(recent_events) / 5  # events per minute
        baseline = self._get_baseline_metric("traffic_rate")

        if baseline and current_rate > baseline * 5:  # 5x baseline
            # Find contributing IPs
            ip_counts = defaultdict(int)
            for event in recent_events:
                if event.ip_address:
                    ip_counts[event.ip_address] += 1

            top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            await self._create_security_alert(
                threat_type=ThreatType.DDOS_ATTACK,
                severity=ThreatLevel.HIGH,
                title="Traffic Spike Detected",
                description=f"Unusual traffic spike detected: {current_rate:.1f} events/minute (baseline: {baseline:.1f})",
                source_events=[e.id for e in recent_events[:10]],
                affected_resources=[ip for ip, count in top_ips],
                metadata={
                    "current_rate": current_rate,
                    "baseline_rate": baseline,
                    "top_ips": top_ips,
                    "time_window": "5 minutes"
                }
            )

    async def _detect_auth_anomalies(self):
        """Detect authentication anomalies"""
        # Check for concurrent sessions from different locations
        user_sessions = defaultdict(list)
        now = datetime.utcnow()

        for event in self.event_history:
            if event.event_type in [EventType.LOGIN, EventType.FAILED_LOGIN] and event.user_id:
                if event.timestamp > now - timedelta(hours=1):
                    user_sessions[event.user_id].append(event)

        for user_id, events in user_sessions.items():
            unique_ips = set(e.ip_address for e in events if e.ip_address)
            if len(unique_ips) > 3:  # More than 3 unique IPs in 1 hour
                await self._create_security_alert(
                    threat_type=ThreatType.ACCOUNT_TAKEOVER,
                    severity=ThreatLevel.HIGH,
                    title="Suspicious Account Activity",
                    description=f"User {user_id} has sessions from {len(unique_ips)} different IP addresses",
                    source_events=[e.id for e in events],
                    affected_resources=[user_id],
                    metadata={
                        "user_id": user_id,
                        "unique_ips": len(unique_ips),
                        "ip_addresses": list(unique_ips),
                        "time_window": "1 hour"
                    }
                )

    async def _detect_system_anomalies(self):
        """Detect system anomalies"""
        # Check for unusual configuration changes
        config_events = [e for e in self.event_history if e.event_type == EventType.CONFIG_CHANGE]
        now = datetime.utcnow()

        recent_config_changes = [e for e in config_events if e.timestamp > now - timedelta(hours=1)]

        if len(recent_config_changes) > 10:  # More than 10 config changes in 1 hour
            await self._create_security_alert(
                threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                severity=ThreatLevel.HIGH,
                title="Excessive Configuration Changes",
                description=f"Detected {len(recent_config_changes)} configuration changes in the last hour",
                source_events=[e.id for e in recent_config_changes],
                affected_resources=["system_config"],
                metadata={
                    "change_count": len(recent_config_changes),
                    "time_window": "1 hour",
                    "users_affected": list(set(e.username for e in recent_config_changes if e.username))
                }
            )

    async def _threat_detection_loop(self):
        """Background threat detection loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                await self._run_threat_detection()
            except Exception as e:
                security_monitor_logger.error(f"Threat detection loop error: {e}")

    async def _run_threat_detection(self):
        """Run comprehensive threat detection"""
        try:
            # Check for IP reputation issues
            await self._check_ip_reputation()

            # Check for credential stuffing
            await self._check_credential_stuffing()

            # Check for privilege escalation attempts
            await self._check_privilege_escalation()

        except Exception as e:
            security_monitor_logger.error(f"Threat detection error: {e}")

    async def _check_ip_reputation(self):
        """Check IP reputation"""
        # Get recent IPs with high activity
        recent_ips = defaultdict(int)
        now = datetime.utcnow()

        for event in self.event_history:
            if event.timestamp > now - timedelta(minutes=10) and event.ip_address:
                recent_ips[event.ip_address] += 1

        for ip, count in recent_ips.items():
            if count > 50:  # More than 50 requests in 10 minutes
                # Check if IP is known malicious
                if await self._is_malicious_ip(ip):
                    await self._create_security_alert(
                        threat_type=ThreatType.SUSPICIOUS_NETWORK,
                        severity=ThreatLevel.HIGH,
                        title="Malicious IP Activity",
                        description=f"IP {ip} with high activity ({count} requests) is known to be malicious",
                        source_events=[],
                        affected_resources=[ip],
                        metadata={
                            "ip_address": ip,
                            "request_count": count,
                            "time_window": "10 minutes",
                            "reputation": "malicious"
                        }
                    )

    async def _is_malicious_ip(self, ip_address: str) -> bool:
        """Check if IP is malicious (simplified implementation)"""
        # In a real implementation, this would query threat intelligence services
        malicious_ranges = [
            "192.168.1.100",  # Example malicious IP
            "10.0.0.50"       # Example malicious IP
        ]
        return ip_address in malicious_ranges

    async def _check_credential_stuffing(self):
        """Check for credential stuffing attacks"""
        # Look for patterns of failed logins across multiple accounts
        ip_failed_logins = defaultdict(list)
        now = datetime.utcnow()

        for event in self.event_history:
            if (event.event_type == EventType.FAILED_LOGIN and
                event.timestamp > now - timedelta(minutes=5) and
                event.ip_address):
                ip_failed_logins[event.ip_address].append(event)

        for ip, events in ip_failed_logins.items():
            unique_users = len(set(e.username for e in events if e.username))
            if unique_users > 5:  # Failed logins for more than 5 users
                await self._create_security_alert(
                    threat_type=ThreatType.CREDENTIAL_STUFFING,
                    severity=ThreatLevel.HIGH,
                    title="Credential Stuffing Attack",
                    description=f"IP {ip} attempting to access {unique_users} different accounts",
                    source_events=[e.id for e in events],
                    affected_resources=[ip],
                    metadata={
                        "ip_address": ip,
                        "unique_users": unique_users,
                        "total_attempts": len(events),
                        "time_window": "5 minutes"
                    }
                )

    async def _check_privilege_escalation(self):
        """Check for privilege escalation attempts"""
        # Look for suspicious admin actions
        admin_events = [e for e in self.event_history if e.event_type == EventType.ADMIN_ACTION]
        now = datetime.utcnow()

        recent_admin_events = [e for e in admin_events if e.timestamp > now - timedelta(hours=1)]

        if len(recent_admin_events) > 5:  # More than 5 admin actions in 1 hour
            await self._create_security_alert(
                threat_type=ThreatType.PRIVILEGE_ESCALATION,
                severity=ThreatLevel.HIGH,
                title="Excessive Administrative Activity",
                description=f"Detected {len(recent_admin_events)} administrative actions in the last hour",
                source_events=[e.id for e in recent_admin_events],
                affected_resources=["system"],
                metadata={
                    "action_count": len(recent_admin_events),
                    "time_window": "1 hour",
                    "admins_involved": list(set(e.username for e in recent_admin_events if e.username))
                }
            )

    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                self._collect_metrics()
            except Exception as e:
                security_monitor_logger.error(f"Metrics collection loop error: {e}")

    def _collect_metrics(self):
        """Collect security metrics"""
        try:
            # Count unique IPs
            self.metrics.unique_ips = len(self.ip_request_counts)

            # Count unique users
            self.metrics.unique_users = len(self.user_request_counts)

            # Count alerts by severity
            self.metrics.critical_alerts = len([a for a in self.alerts.values() if a.severity == ThreatLevel.CRITICAL])
            self.metrics.high_alerts = len([a for a in self.alerts.values() if a.severity == ThreatLevel.HIGH])
            self.metrics.medium_alerts = len([a for a in self.alerts.values() if a.severity == ThreatLevel.MEDIUM])
            self.metrics.low_alerts = len([a for a in self.alerts.values() if a.severity == ThreatLevel.LOW])
            self.metrics.total_alerts = len(self.alerts)

            # Calculate threat detection rate
            if self.metrics.total_events > 0:
                self.metrics.threat_detection_rate = (self.metrics.suspicious_activities / self.metrics.total_events) * 100

        except Exception as e:
            security_monitor_logger.error(f"Metrics collection error: {e}")

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_data()
            except Exception as e:
                security_monitor_logger.error(f"Cleanup loop error: {e}")

    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            # Keep only last 30 days of history
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            self.event_history = [e for e in self.event_history if e.timestamp > cutoff_date]

            # Clean up old IP request counts
            for ip in list(self.ip_request_counts.keys()):
                if self.ip_request_counts[ip] < 10:  # Remove low-count IPs
                    del self.ip_request_counts[ip]

            # Clean up old user request counts
            for user_id in list(self.user_request_counts.keys()):
                if self.user_request_counts[user_id] < 5:  # Remove low-count users
                    del self.user_request_counts[user_id]

            # Clean up old failed login attempts
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for key in list(self.failed_login_attempts.keys()):
                self.failed_login_attempts[key] = [t for t in self.failed_login_attempts[key] if t > cutoff_time]
                if not self.failed_login_attempts[key]:
                    del self.failed_login_attempts[key]

        except Exception as e:
            security_monitor_logger.error(f"Cleanup error: {e}")

    async def _create_security_alert(self, threat_type: ThreatType, severity: ThreatLevel,
                                   title: str, description: str, source_events: List[str],
                                   affected_resources: List[str], metadata: Dict[str, Any] = None):
        """Create security alert"""
        try:
            alert_id = hashlib.sha256(f"{threat_type.value}_{datetime.utcnow().isoformat()}".encode()).hexdigest()

            alert = SecurityAlert(
                id=alert_id,
                threat_type=threat_type,
                severity=severity,
                title=title,
                description=description,
                timestamp=datetime.utcnow(),
                source_events=source_events,
                affected_resources=affected_resources,
                metadata=metadata or {}
            )

            self.alerts[alert_id] = alert

            # Update metrics
            self.metrics.total_alerts += 1
            if severity == ThreatLevel.CRITICAL:
                self.metrics.critical_alerts += 1
            elif severity == ThreatLevel.HIGH:
                self.metrics.high_alerts += 1
            elif severity == ThreatLevel.MEDIUM:
                self.metrics.medium_alerts += 1
            else:
                self.metrics.low_alerts += 1

            # Log alert
            security_monitor_logger.warning(f"Security Alert: {title} - {description}")

            # Notify alert handlers
            await self._notify_alert_handlers(alert)

        except Exception as e:
            security_monitor_logger.error(f"Failed to create security alert: {e}")

    async def _notify_alert_handlers(self, alert: SecurityAlert):
        """Notify alert handlers"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                security_monitor_logger.error(f"Alert handler error: {e}")

    def add_alert_handler(self, handler: Callable):
        """Add alert handler"""
        self.alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable):
        """Remove alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)

    def get_alerts(self, status: AlertStatus = None, severity: ThreatLevel = None,
                   threat_type: ThreatType = None, limit: int = None) -> List[SecurityAlert]:
        """Get alerts with filtering"""
        alerts = list(self.alerts.values())

        if status:
            alerts = [a for a in alerts if a.status == status]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if threat_type:
            alerts = [a for a in alerts if a.threat_type == threat_type]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            alerts = alerts[:limit]

        return alerts

    def get_alert(self, alert_id: str) -> Optional[SecurityAlert]:
        """Get specific alert by ID"""
        return self.alerts.get(alert_id)

    def update_alert_status(self, alert_id: str, status: AlertStatus,
                          assigned_to: str = None, resolution_notes: str = None) -> bool:
        """Update alert status"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = status
            if assigned_to:
                alert.assigned_to = assigned_to
            if resolution_notes:
                alert.resolution_notes = resolution_notes
            return True
        return False

    def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics"""
        return self.metrics

    def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [e for e in self.event_history if e.timestamp > cutoff_time]

        # Sort by timestamp (newest first)
        recent_events.sort(key=lambda x: x.timestamp, reverse=True)

        return recent_events[:limit]

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat summary"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        events_24h = [e for e in self.event_history if e.timestamp > last_24h]
        events_7d = [e for e in self.event_history if e.timestamp > last_7d]

        alerts_24h = [a for a in self.alerts.values() if a.timestamp > last_24h]
        alerts_7d = [a for a in self.alerts.values() if a.timestamp > last_7d]

        return {
            "period": {
                "last_24h": {
                    "events": len(events_24h),
                    "alerts": len(alerts_24h),
                    "critical_alerts": len([a for a in alerts_24h if a.severity == ThreatLevel.CRITICAL]),
                    "high_alerts": len([a for a in alerts_24h if a.severity == ThreatLevel.HIGH])
                },
                "last_7d": {
                    "events": len(events_7d),
                    "alerts": len(alerts_7d),
                    "critical_alerts": len([a for a in alerts_7d if a.severity == ThreatLevel.CRITICAL]),
                    "high_alerts": len([a for a in alerts_7d if a.severity == ThreatLevel.HIGH])
                }
            },
            "active_threats": len([a for a in self.alerts.values() if a.status in [AlertStatus.OPEN, AlertStatus.INVESTIGATING]]),
            "resolved_threats": len([a for a in self.alerts.values() if a.status == AlertStatus.RESOLVED]),
            "threat_types": {
                threat_type.value: len([a for a in self.alerts.values() if a.threat_type == threat_type])
                for threat_type in ThreatType
            },
            "top_attacker_ips": self._get_top_attacker_ips(),
            "most_targeted_users": self._get_most_targeted_users()
        }

    def _get_top_attacker_ips(self) -> List[Tuple[str, int]]:
        """Get top attacker IPs"""
        ip_scores = defaultdict(int)

        for alert in self.alerts.values():
            for resource in alert.affected_resources:
                if self._is_ip_address(resource):
                    ip_scores[resource] += self._get_threat_score(alert.severity)

        return sorted(ip_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    def _get_most_targeted_users(self) -> List[Tuple[str, int]]:
        """Get most targeted users"""
        user_scores = defaultdict(int)

        for alert in self.alerts.values():
            for resource in alert.affected_resources:
                if not self._is_ip_address(resource):
                    user_scores[resource] += self._get_threat_score(alert.severity)

        return sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    def _is_ip_address(self, resource: str) -> bool:
        """Check if resource is an IP address"""
        try:
            ipaddress.ip_address(resource)
            return True
        except ValueError:
            return False

    def _get_threat_score(self, severity: ThreatLevel) -> int:
        """Get threat score based on severity"""
        scores = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.HIGH: 5,
            ThreatLevel.CRITICAL: 10
        }
        return scores.get(severity, 1)

    async def export_security_report(self, format: str = "json", hours: int = 24) -> str:
        """Export security report"""
        try:
            report_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "period_hours": hours,
                "metrics": self.metrics.to_dict(),
                "threat_summary": self.get_threat_summary(),
                "recent_events": [e.to_dict() for e in self.get_recent_events(hours, 50)],
                "active_alerts": [a.to_dict() for a in self.get_alerts(status=AlertStatus.OPEN)]
            }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_report_{timestamp}.{format}"

            if format.lower() == "json":
                async with aiofiles.open(filename, 'w') as f:
                    await f.write(json.dumps(report_data, indent=2, default=str))
            elif format.lower() == "csv":
                await self._export_csv_report(report_data, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")

            security_monitor_logger.info(f"Security report exported to {filename}")
            return filename

        except Exception as e:
            security_monitor_logger.error(f"Failed to export security report: {e}")
            raise

    async def _export_csv_report(self, report_data: Dict[str, Any], filename: str):
        """Export report as CSV"""
        import csv

        async with aiofiles.open(filename, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write metrics summary
            writer.writerow(["Metric", "Value"])
            for key, value in report_data["metrics"].items():
                writer.writerow([key, value])

            # Write alerts
            writer.writerow([])
            writer.writerow(["Alert ID", "Threat Type", "Severity", "Title", "Timestamp", "Status"])
            for alert in report_data["active_alerts"]:
                writer.writerow([
                    alert["id"],
                    alert["threat_type"],
                    alert["severity"],
                    alert["title"],
                    alert["timestamp"],
                    alert["status"]
                ])

            # Write events
            writer.writerow([])
            writer.writerow(["Event ID", "Type", "User", "IP", "Timestamp", "Severity"])
            for event in report_data["recent_events"]:
                writer.writerow([
                    event["id"],
                    event["event_type"],
                    event["username"],
                    event["ip_address"],
                    event["timestamp"],
                    event["severity"]
                ])