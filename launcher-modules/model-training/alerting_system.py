#!/usr/bin/env python3
"""
Alerting and Notification System for DuckBot Training
Provides comprehensive alerting and notification capabilities for training events and system status.
"""

import os
import sys
import json
import time
import email
import smtplib
import logging
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from pathlib import Path
import sqlite3
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import webbrowser

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertCategory(Enum):
    """Alert categories"""
    TRAINING = "training"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    MODEL = "model"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"

class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    DESKTOP = "desktop"
    CONSOLE = "console"
    FILE = "file"

@dataclass
class AlertConfig:
    """Configuration for alerting system"""
    enable_email: bool = False
    enable_slack: bool = False
    enable_discord: bool = False
    enable_telegram: bool = False
    enable_webhook: bool = False
    enable_desktop: bool = True
    enable_console: bool = True
    enable_file: bool = True

    # Email configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_from: str = ""
    email_password: str = ""
    email_to: List[str] = field(default_factory=list)

    # Slack configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"

    # Discord configuration
    discord_webhook_url: str = ""

    # Telegram configuration
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Webhook configuration
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    # File configuration
    log_file_path: str = "alerts.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Alert filtering
    min_severity: AlertSeverity = AlertSeverity.WARNING
    allowed_categories: List[AlertCategory] = field(default_factory=lambda: list(AlertCategory))
    rate_limit_seconds: int = 60  # Minimum seconds between similar alerts
    max_alerts_per_hour: int = 100

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = "training_system"
    tags: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationRule:
    """Notification routing rule"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]  # Conditions for matching alerts
    channels: List[NotificationChannel]  # Where to send notifications
    template: Optional[str] = None  # Custom message template
    enabled: bool = True
    priority: int = 0  # Higher priority rules are evaluated first

class AlertDatabase:
    """Database for storing alerts and notifications"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    severity TEXT,
                    category TEXT,
                    title TEXT,
                    message TEXT,
                    details TEXT,
                    source TEXT,
                    tags TEXT,
                    resolved BOOLEAN,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    metadata TEXT
                )
            """)

            # Notifications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    channel TEXT,
                    timestamp TEXT,
                    status TEXT,
                    message TEXT,
                    response_data TEXT,
                    FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
                )
            """)

            # Notification rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT,
                    conditions TEXT,
                    channels TEXT,
                    template TEXT,
                    enabled BOOLEAN,
                    priority INTEGER
                )
            """)

            # Alert history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    user_id TEXT,
                    details TEXT,
                    FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_timestamp ON alert_history(timestamp)")

    def store_alert(self, alert: Alert):
        """Store alert in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alerts (
                    alert_id, timestamp, severity, category, title, message,
                    details, source, tags, resolved, resolved_at, resolved_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.timestamp.isoformat(),
                alert.severity.value,
                alert.category.value,
                alert.title,
                alert.message,
                json.dumps(alert.details),
                alert.source,
                json.dumps(alert.tags),
                alert.resolved,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                alert.resolved_by,
                json.dumps(alert.metadata)
            ))

    def store_notification(self, alert_id: str, channel: str, status: str, message: str, response_data: str = None):
        """Store notification attempt"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO notifications (
                    alert_id, channel, timestamp, status, message, response_data
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                channel,
                datetime.now().isoformat(),
                status,
                message,
                response_data
            ))

    def get_alerts(self, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   severity: Optional[AlertSeverity] = None,
                   category: Optional[AlertCategory] = None,
                   resolved: Optional[bool] = None) -> List[Alert]:
        """Get alerts from database"""
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        if category:
            query += " AND category = ?"
            params.append(category.value)
        if resolved is not None:
            query += " AND resolved = ?"
            params.append(resolved)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            alerts = []
            for row in cursor.fetchall():
                alert_dict = {
                    'alert_id': row[0],
                    'timestamp': datetime.fromisoformat(row[1]),
                    'severity': AlertSeverity(row[2]),
                    'category': AlertCategory(row[3]),
                    'title': row[4],
                    'message': row[5],
                    'details': json.loads(row[6]) if row[6] else {},
                    'source': row[7],
                    'tags': json.loads(row[8]) if row[8] else [],
                    'resolved': bool(row[9]),
                    'resolved_at': datetime.fromisoformat(row[10]) if row[10] else None,
                    'resolved_by': row[11],
                    'metadata': json.loads(row[12]) if row[12] else {}
                }
                alerts.append(Alert(**alert_dict))
            return alerts

    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Mark alert as resolved"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE alerts SET resolved = TRUE, resolved_at = ?, resolved_by = ?
                WHERE alert_id = ?
            """, (datetime.now().isoformat(), resolved_by, alert_id))

            # Add to history
            conn.execute("""
                INSERT INTO alert_history (alert_id, action, timestamp, user_id)
                VALUES (?, 'resolved', ?, ?)
            """, (alert_id, datetime.now().isoformat(), resolved_by))

class NotificationChannel:
    """Base class for notification channels"""

    def __init__(self, config: AlertConfig):
        self.config = config

    def send_notification(self, alert: Alert) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError

    def format_message(self, alert: Alert, template: Optional[str] = None) -> str:
        """Format alert message"""
        if template:
            return self._apply_template(template, alert)

        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }

        return (
            f"{severity_emoji.get(alert.severity, '📢')} **{alert.title}**\n\n"
            f"**Severity:** {alert.severity.value.upper()}\n"
            f"**Category:** {alert.category.value}\n"
            f"**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{alert.message}\n\n"
            f"**Details:**\n{json.dumps(alert.details, indent=2)}"
        )

    def _apply_template(self, template: str, alert: Alert) -> str:
        """Apply template to alert"""
        # Simple template substitution
        replacements = {
            '{{alert_id}}': alert.alert_id,
            '{{severity}}': alert.severity.value,
            '{{category}}': alert.category.value,
            '{{title}}': alert.title,
            '{{message}}': alert.message,
            '{{timestamp}}': alert.timestamp.isoformat(),
            '{{source}}': alert.source
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, str(value))

        return result

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def send_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        if not self.config.enable_email or not self.config.email_to:
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Add body
            body = self.format_message(alert)
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_from, self.config.email_password)
                text = msg.as_string()
                server.sendmail(self.config.email_from, self.config.email_to, text)

            return True

        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
            return False

class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""

    def send_notification(self, alert: Alert) -> bool:
        """Send Slack notification"""
        if not self.config.enable_slack or not self.config.slack_webhook_url:
            return False

        try:
            # Prepare message
            color = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "danger"
            }.get(alert.severity, "#808080")

            payload = {
                "channel": self.config.slack_channel,
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Category",
                                "value": alert.category.value,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            }
                        ],
                        "footer": alert.source
                    }
                ]
            }

            # Send to Slack
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            return True

        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")
            return False

class DiscordNotificationChannel(NotificationChannel):
    """Discord notification channel"""

    def send_notification(self, alert: Alert) -> bool:
        """Send Discord notification"""
        if not self.config.enable_discord or not self.config.discord_webhook_url:
            return False

        try:
            # Prepare message
            color = {
                AlertSeverity.INFO: 0x2ECC71,  # Green
                AlertSeverity.WARNING: 0xF39C12,  # Yellow
                AlertSeverity.ERROR: 0xE74C3C,  # Red
                AlertSeverity.CRITICAL: 0x8B0000  # Dark Red
            }.get(alert.severity, 0x808080)

            payload = {
                "embeds": [
                    {
                        "title": alert.title,
                        "description": alert.message,
                        "color": color,
                        "fields": [
                            {
                                "name": "Severity",
                                "value": alert.severity.value.upper(),
                                "inline": True
                            },
                            {
                                "name": "Category",
                                "value": alert.category.value,
                                "inline": True
                            },
                            {
                                "name": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                "inline": True
                            }
                        ],
                        "footer": {
                            "text": alert.source
                        },
                        "timestamp": alert.timestamp.isoformat()
                    }
                ]
            }

            # Send to Discord
            response = requests.post(
                self.config.discord_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            return True

        except Exception as e:
            logging.error(f"Failed to send Discord notification: {e}")
            return False

class DesktopNotificationChannel(NotificationChannel):
    """Desktop notification channel"""

    def send_notification(self, alert: Alert) -> bool:
        """Send desktop notification"""
        if not self.config.enable_desktop:
            return False

        try:
            import tkinter as tk
            from tkinter import messagebox

            def show_notification():
                root = tk.Tk()
                root.withdraw()  # Hide main window

                title = f"[{alert.severity.value.upper()}] {alert.title}"
                messagebox.showwarning(title, alert.message)
                root.destroy()

            # Show notification in separate thread to avoid blocking
            thread = threading.Thread(target=show_notification, daemon=True)
            thread.start()

            return True

        except Exception as e:
            logging.error(f"Failed to send desktop notification: {e}")
            return False

class ConsoleNotificationChannel(NotificationChannel):
    """Console notification channel"""

    def send_notification(self, alert: Alert) -> bool:
        """Send console notification"""
        if not self.config.enable_console:
            return False

        try:
            # Color codes for different severity levels
            colors = {
                AlertSeverity.INFO: "\033[36m",      # Cyan
                AlertSeverity.WARNING: "\033[33m",   # Yellow
                AlertSeverity.ERROR: "\033[31m",     # Red
                AlertSeverity.CRITICAL: "\033[91m"   # Bright Red
            }
            reset_color = "\033[0m"

            color = colors.get(alert.severity, "")
            message = self.format_message(alert)

            print(f"\n{color}{'='*60}{reset_color}")
            print(f"{color}{message}{reset_color}")
            print(f"{color}{'='*60}{reset_color}\n")

            return True

        except Exception as e:
            logging.error(f"Failed to send console notification: {e}")
            return False

class FileNotificationChannel(NotificationChannel):
    """File notification channel"""

    def __init__(self, config: AlertConfig):
        super().__init__(config)
        self._setup_log_file()

    def _setup_log_file(self):
        """Setup log file with rotation"""
        from logging.handlers import RotatingFileHandler

        self.file_handler = RotatingFileHandler(
            self.config.log_file_path,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        self.file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))

    def send_notification(self, alert: Alert) -> bool:
        """Send file notification"""
        if not self.config.enable_file:
            return False

        try:
            log_record = logging.LogRecord(
                name="AlertingSystem",
                level=getattr(logging, alert.severity.value.upper()),
                pathname="",
                lineno=0,
                msg=self.format_message(alert),
                args=(),
                exc_info=None
            )

            self.file_handler.handle(log_record)
            return True

        except Exception as e:
            logging.error(f"Failed to send file notification: {e}")
            return False

class AlertingSystem:
    """Main alerting and notification system"""

    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self.database = AlertDatabase("alerts.db")

        # Initialize notification channels
        self.channels = {
            NotificationChannel.EMAIL: EmailNotificationChannel(self.config),
            NotificationChannel.SLACK: SlackNotificationChannel(self.config),
            NotificationChannel.DISCORD: DiscordNotificationChannel(self.config),
            NotificationChannel.DESKTOP: DesktopNotificationChannel(self.config),
            NotificationChannel.CONSOLE: ConsoleNotificationChannel(self.config),
            NotificationChannel.FILE: FileNotificationChannel(self.config)
        }

        # Initialize notification rules
        self.rules = self._load_default_rules()

        # Rate limiting
        self.rate_limiter = {}
        self.alerts_this_hour = 0
        self.hour_start_time = datetime.now()

        # Event callbacks
        self.alert_callbacks = []

    def _load_default_rules(self) -> List[NotificationRule]:
        """Load default notification rules"""
        rules = [
            NotificationRule(
                rule_id="critical_all",
                name="Critical alerts to all channels",
                conditions={"severity": "critical"},
                channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.DISCORD,
                    NotificationChannel.DESKTOP,
                    NotificationChannel.CONSOLE,
                    NotificationChannel.FILE
                ],
                priority=10
            ),
            NotificationRule(
                rule_id="error_system",
                name="System errors to console and file",
                conditions={
                    "severity": "error",
                    "category": "system"
                },
                channels=[
                    NotificationChannel.CONSOLE,
                    NotificationChannel.FILE
                ],
                priority=5
            ),
            NotificationRule(
                rule_id="warning_training",
                name="Training warnings to console",
                conditions={
                    "severity": "warning",
                    "category": "training"
                },
                channels=[NotificationChannel.CONSOLE],
                priority=3
            ),
            NotificationRule(
                rule_id="info_performance",
                name="Performance info to file",
                conditions={
                    "severity": "info",
                    "category": "performance"
                },
                channels=[NotificationChannel.FILE],
                priority=1
            )
        ]
        return rules

    def send_alert(self, alert: Alert):
        """Send alert through appropriate channels"""
        # Check if alert should be processed
        if not self._should_process_alert(alert):
            return

        # Store alert in database
        self.database.store_alert(alert)

        # Apply notification rules
        applicable_rules = self._get_applicable_rules(alert)

        for rule in applicable_rules:
            if not rule.enabled:
                continue

            for channel in rule.channels:
                if channel in self.channels:
                    success = self.channels[channel].send_notification(alert)

                    # Store notification result
                    self.database.store_notification(
                        alert.alert_id,
                        channel.value,
                        "sent" if success else "failed",
                        self.channels[channel].format_message(alert, rule.template)
                    )

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logging.error(f"Error in alert callback: {e}")

        # Update rate limiting
        self._update_rate_limiting(alert)

    def _should_process_alert(self, alert: Alert) -> bool:
        """Check if alert should be processed based on filters"""
        # Check severity
        if alert.severity.value not in [s.value for s in AlertSeverity if s.value >= self.config.min_severity.value]:
            return False

        # Check category
        if alert.category not in self.config.allowed_categories:
            return False

        # Check rate limiting
        alert_key = f"{alert.severity.value}:{alert.category.value}:{alert.title}"
        if alert_key in self.rate_limiter:
            time_since_last = (datetime.now() - self.rate_limiter[alert_key]).total_seconds()
            if time_since_last < self.config.rate_limit_seconds:
                return False

        # Check hourly limit
        if self.alerts_this_hour >= self.config.max_alerts_per_hour:
            time_since_hour_start = (datetime.now() - self.hour_start_time).total_seconds()
            if time_since_hour_start < 3600:  # Less than an hour
                return False
            else:
                # Reset hourly counter
                self.alerts_this_hour = 0
                self.hour_start_time = datetime.now()

        return True

    def _get_applicable_rules(self, alert: Alert) -> List[NotificationRule]:
        """Get applicable notification rules for alert"""
        applicable_rules = []

        for rule in self.rules:
            if self._matches_rule(alert, rule):
                applicable_rules.append(rule)

        # Sort by priority (descending)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)

        return applicable_rules

    def _matches_rule(self, alert: Alert, rule: NotificationRule) -> bool:
        """Check if alert matches rule conditions"""
        for key, value in rule.conditions.items():
            if key == "severity":
                if alert.severity.value != value:
                    return False
            elif key == "category":
                if alert.category.value != value:
                    return False
            elif key in alert.details:
                if alert.details[key] != value:
                    return False
            else:
                # Unknown condition key
                return False

        return True

    def _update_rate_limiting(self, alert: Alert):
        """Update rate limiting information"""
        alert_key = f"{alert.severity.value}:{alert.category.value}:{alert.title}"
        self.rate_limiter[alert_key] = datetime.now()
        self.alerts_this_hour += 1

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)

    def add_rule(self, rule: NotificationRule):
        """Add notification rule"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str):
        """Remove notification rule"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

    def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Resolve an alert"""
        self.database.resolve_alert(alert_id, resolved_by)

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)

        stats = {
            'total_alerts': len(self.database.get_alerts()),
            'alerts_last_hour': len(self.database.get_alerts(start_time=last_hour)),
            'alerts_last_day': len(self.database.get_alerts(start_time=last_day)),
            'alerts_last_week': len(self.database.get_alerts(start_time=last_week)),
            'unresolved_alerts': len(self.database.get_alerts(resolved=False)),
            'by_severity': {},
            'by_category': {}
        }

        # Count by severity
        for severity in AlertSeverity:
            stats['by_severity'][severity.value] = len(
                self.database.get_alerts(severity=severity)
            )

        # Count by category
        for category in AlertCategory:
            stats['by_category'][category.value] = len(
                self.database.get_alerts(category=category)
            )

        return stats

# Example usage and demo
def demo_alerting_system():
    """Demonstrate alerting system functionality"""
    print("🚨 Alerting System Demo")
    print("=" * 40)

    # Create alerting system with demo configuration
    config = AlertConfig(
        enable_desktop=True,
        enable_console=True,
        enable_file=True,
        min_severity=AlertSeverity.INFO
    )

    alerting_system = AlertingSystem(config)

    # Add callback for alerts
    def handle_alert(alert: Alert):
        print(f"📢 Alert received: {alert.title} ({alert.severity.value})")

    alerting_system.add_alert_callback(handle_alert)

    # Send sample alerts
    print("\n📨 Sending sample alerts...")

    alerts = [
        Alert(
            alert_id="alert_001",
            timestamp=datetime.now(),
            severity=AlertSeverity.INFO,
            category=AlertCategory.TRAINING,
            title="Training Started",
            message="Model training has started successfully",
            details={"model": "bert-base-uncased", "batch_size": 32, "epochs": 10}
        ),
        Alert(
            alert_id="alert_002",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            category=AlertCategory.PERFORMANCE,
            title="High GPU Temperature",
            message="GPU temperature exceeded safe threshold",
            details={"temperature": 87.5, "threshold": 85.0, "gpu_id": 0}
        ),
        Alert(
            alert_id="alert_003",
            timestamp=datetime.now(),
            severity=AlertSeverity.ERROR,
            category=AlertCategory.SYSTEM,
            title="Memory Allocation Failed",
            message="Failed to allocate memory for batch processing",
            details={"requested_memory": "8GB", "available_memory": "4GB", "error_code": "CUDA_OUT_OF_MEMORY"}
        ),
        Alert(
            alert_id="alert_004",
            timestamp=datetime.now(),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.TRAINING,
            title="Training Crash Detected",
            message="Training process crashed unexpectedly",
            details={"epoch": 5, "step": 1234, "error": "Segmentation fault"}
        )
    ]

    for alert in alerts:
        alerting_system.send_alert(alert)
        time.sleep(1)  # Small delay between alerts

    # Show statistics
    print("\n📊 Alert Statistics:")
    stats = alerting_system.get_alert_stats()
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Unresolved alerts: {stats['unresolved_alerts']}")
    print(f"  By severity: {stats['by_severity']}")
    print(f"  By category: {stats['by_category']}")

    # Simulate resolving an alert
    print("\n✅ Resolving training crash alert...")
    alerting_system.resolve_alert("alert_004", "demo_user")

    # Show updated statistics
    updated_stats = alerting_system.get_alert_stats()
    print(f"  Unresolved alerts after resolution: {updated_stats['unresolved_alerts']}")

    return alerting_system

if __name__ == "__main__":
    demo_alerting_system()