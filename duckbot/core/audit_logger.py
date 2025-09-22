"""
DuckBot Audit Logging System

Comprehensive audit logging for security events, user activities,
and compliance reporting. Supports multiple storage backends and
real-time monitoring capabilities.

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import sqlite3
import asyncio
import aiofiles
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import gzip
import csv
from .security_framework import SecurityEvent, SecurityEventType, ResourceType

audit_logger = logging.getLogger('duckbot.audit')

class LogLevel(Enum):
    """Log levels for audit entries"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class StorageBackend(Enum):
    """Storage backends for audit logs"""
    SQLITE = "sqlite"
    FILE = "file"
    ELASTICSEARCH = "elasticsearch"
    REMOTE = "remote"

class ComplianceStandard(Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOX = "sox"
    ISO27001 = "iso27001"
    NIST = "nist"

@dataclass
class AuditFilter:
    """Filter criteria for audit log queries"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    event_type: Optional[SecurityEventType] = None
    resource_type: Optional[ResourceType] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[str] = None
    result: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

@dataclass
class ComplianceReport:
    """Compliance report data"""
    standard: ComplianceStandard
    period_start: datetime
    period_end: datetime
    total_events: int
    security_events: int
    data_access_events: int
    admin_actions: int
    failed_authentications: int
    unique_users: int
    compliance_score: float
    findings: List[Dict[str, Any]]

class AuditLogger:
    """Main audit logging system"""

    def __init__(self, storage_backend: StorageBackend = StorageBackend.SQLITE,
                 database_path: str = "audit_log.db",
                 log_directory: str = "audit_logs",
                 max_file_size_mb: int = 100,
                 retention_days: int = 365):
        self.storage_backend = storage_backend
        self.database_path = Path(database_path)
        self.log_directory = Path(log_directory)
        self.max_file_size = max_file_size * 1024 * 1024  # Convert to bytes
        self.retention_days = retention_days

        # Create directories
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Initialize storage backend
        if storage_backend == StorageBackend.SQLITE:
            self._init_sqlite_database()
        elif storage_backend == StorageBackend.FILE:
            self._init_file_logging()

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Real-time monitoring subscribers
        self.monitoring_subscribers: List[callable] = []

        audit_logger.info(f"AuditLogger initialized with {storage_backend.value} backend")

    def _init_sqlite_database(self):
        """Initialize SQLite database for audit logging"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Create audit_log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    details TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_log(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON audit_log(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_address ON audit_log(ip_address)')

            conn.commit()
            conn.close()

            audit_logger.info("SQLite database initialized for audit logging")
        except Exception as e:
            audit_logger.error(f"Failed to initialize SQLite database: {e}")
            raise

    def _init_file_logging(self):
        """Initialize file-based audit logging"""
        try:
            # Create log file for current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            self.current_log_file = self.log_directory / f"audit_{current_date}.log"

            audit_logger.info("File-based audit logging initialized")
        except Exception as e:
            audit_logger.error(f"Failed to initialize file logging: {e}")
            raise

    async def log_event(self, event: SecurityEvent):
        """Log a security event asynchronously"""
        try:
            if self.storage_backend == StorageBackend.SQLITE:
                await self._log_to_sqlite(event)
            elif self.storage_backend == StorageBackend.FILE:
                await self._log_to_file(event)

            # Notify monitoring subscribers
            await self._notify_subscribers(event)

        except Exception as e:
            audit_logger.error(f"Failed to log audit event: {e}")
            # Fallback to local file logging
            await self._log_to_fallback_file(event)

    async def _log_to_sqlite(self, event: SecurityEvent):
        """Log event to SQLite database"""
        def _sync_log():
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO audit_log (
                        id, event_type, user_id, username, session_id, ip_address,
                        user_agent, resource_type, resource_id, action, result,
                        severity, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.id,
                    event.event_type.value,
                    event.user_id,
                    event.username,
                    event.session_id,
                    event.ip_address,
                    event.user_agent,
                    event.resource_type.value if event.resource_type else None,
                    event.resource_id,
                    event.action,
                    event.result,
                    event.severity,
                    json.dumps(event.details),
                    event.timestamp.isoformat()
                ))

                conn.commit()
                conn.close()

            except Exception as e:
                audit_logger.error(f"SQLite logging failed: {e}")
                raise

        await asyncio.get_event_loop().run_in_executor(self.executor, _sync_log)

    async def _log_to_file(self, event: SecurityEvent):
        """Log event to file"""
        try:
            # Check if we need to rotate log file
            await self._rotate_log_file()

            # Format log entry
            log_entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "username": event.username,
                "session_id": event.session_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "resource_type": event.resource_type.value if event.resource_type else None,
                "resource_id": event.resource_id,
                "action": event.action,
                "result": event.result,
                "severity": event.severity,
                "details": event.details
            }

            # Write to file
            async with aiofiles.open(self.current_log_file, mode='a', encoding='utf-8') as f:
                await f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            audit_logger.error(f"File logging failed: {e}")
            raise

    async def _rotate_log_file(self):
        """Rotate log file if it exceeds size limit"""
        try:
            if self.current_log_file.exists():
                file_size = self.current_log_file.stat().st_size

                if file_size >= self.max_file_size:
                    # Compress current log file
                    compressed_file = self.current_log_file.with_suffix('.log.gz')
                    await self._compress_file(self.current_log_file, compressed_file)

                    # Create new log file
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    timestamp = datetime.now().strftime("%H%M%S")
                    self.current_log_file = self.log_directory / f"audit_{current_date}_{timestamp}.log"

        except Exception as e:
            audit_logger.error(f"Log rotation failed: {e}")

    async def _compress_file(self, source: Path, target: Path):
        """Compress file using gzip"""
        def _sync_compress():
            with open(source, 'rb') as f_in:
                with gzip.open(target, 'wb') as f_out:
                    f_out.writelines(f_in)
            source.unlink()  # Remove original file

        await asyncio.get_event_loop().run_in_executor(self.executor, _sync_compress)

    async def _log_to_fallback_file(self, event: SecurityEvent):
        """Fallback logging when primary backend fails"""
        try:
            fallback_file = self.log_directory / "audit_fallback.log"
            async with aiofiles.open(fallback_file, mode='a', encoding='utf-8') as f:
                await f.write(f"[FALLBACK] {datetime.now().isoformat()} - {event.event_type.value} - {event.action}\n")

        except Exception as e:
            audit_logger.critical(f"Fallback logging failed: {e}")

    async def _notify_subscribers(self, event: SecurityEvent):
        """Notify real-time monitoring subscribers"""
        for subscriber in self.monitoring_subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                audit_logger.error(f"Failed to notify monitoring subscriber: {e}")

    def add_monitoring_subscriber(self, callback: callable):
        """Add a callback for real-time monitoring"""
        self.monitoring_subscribers.append(callback)

    def remove_monitoring_subscriber(self, callback: callable):
        """Remove monitoring subscriber"""
        if callback in self.monitoring_subscribers:
            self.monitoring_subscribers.remove(callback)

    async def query_events(self, filter_criteria: AuditFilter) -> List[SecurityEvent]:
        """Query audit events with filtering"""
        try:
            if self.storage_backend == StorageBackend.SQLITE:
                return await self._query_sqlite(filter_criteria)
            elif self.storage_backend == StorageBackend.FILE:
                return await self._query_files(filter_criteria)

            return []

        except Exception as e:
            audit_logger.error(f"Failed to query audit events: {e}")
            return []

    async def _query_sqlite(self, filter_criteria: AuditFilter) -> List[SecurityEvent]:
        """Query events from SQLite database"""
        def _sync_query():
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()

                # Build query
                query = "SELECT * FROM audit_log WHERE 1=1"
                params = []

                if filter_criteria.user_id:
                    query += " AND user_id = ?"
                    params.append(filter_criteria.user_id)

                if filter_criteria.username:
                    query += " AND username = ?"
                    params.append(filter_criteria.username)

                if filter_criteria.event_type:
                    query += " AND event_type = ?"
                    params.append(filter_criteria.event_type.value)

                if filter_criteria.resource_type:
                    query += " AND resource_type = ?"
                    params.append(filter_criteria.resource_type.value)

                if filter_criteria.ip_address:
                    query += " AND ip_address = ?"
                    params.append(filter_criteria.ip_address)

                if filter_criteria.session_id:
                    query += " AND session_id = ?"
                    params.append(filter_criteria.session_id)

                if filter_criteria.start_date:
                    query += " AND timestamp >= ?"
                    params.append(filter_criteria.start_date.isoformat())

                if filter_criteria.end_date:
                    query += " AND timestamp <= ?"
                    params.append(filter_criteria.end_date.isoformat())

                if filter_criteria.severity:
                    query += " AND severity = ?"
                    params.append(filter_criteria.severity)

                if filter_criteria.result:
                    query += " AND result = ?"
                    params.append(filter_criteria.result)

                query += " ORDER BY timestamp DESC"

                if filter_criteria.limit:
                    query += " LIMIT ?"
                    params.append(filter_criteria.limit)

                if filter_criteria.offset:
                    query += " OFFSET ?"
                    params.append(filter_criteria.offset)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to SecurityEvent objects
                events = []
                for row in rows:
                    event = SecurityEvent(
                        id=row[0],
                        event_type=SecurityEventType(row[1]),
                        user_id=row[2],
                        username=row[3],
                        session_id=row[4],
                        ip_address=row[5],
                        user_agent=row[6],
                        resource_type=ResourceType(row[7]) if row[7] else None,
                        resource_id=row[8],
                        action=row[9],
                        result=row[10],
                        severity=row[11],
                        details=json.loads(row[12]) if row[12] else {},
                        timestamp=datetime.fromisoformat(row[13])
                    )
                    events.append(event)

                conn.close()
                return events

            except Exception as e:
                audit_logger.error(f"SQLite query failed: {e}")
                return []

        return await asyncio.get_event_loop().run_in_executor(self.executor, _sync_query)

    async def _query_files(self, filter_criteria: AuditFilter) -> List[SecurityEvent]:
        """Query events from log files"""
        events = []

        try:
            # Get all log files
            log_files = list(self.log_directory.glob("audit_*.log"))
            log_files.extend(self.log_directory.glob("audit_*.log.gz"))

            for log_file in sorted(log_files, reverse=True):
                if filter_criteria.limit and len(events) >= filter_criteria.limit:
                    break

                file_events = await self._read_log_file(log_file, filter_criteria)
                events.extend(file_events)

        except Exception as e:
            audit_logger.error(f"File query failed: {e}")

        return events[:filter_criteria.limit] if filter_criteria.limit else events

    async def _read_log_file(self, log_file: Path, filter_criteria: AuditFilter) -> List[SecurityEvent]:
        """Read events from a single log file"""
        events = []

        try:
            if log_file.suffix == '.gz':
                # Read compressed file
                def _read_gzip():
                    with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                        return f.readlines()

                lines = await asyncio.get_event_loop().run_in_executor(self.executor, _read_gzip)
            else:
                # Read uncompressed file
                async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                    lines = await f.readlines()

            for line in lines:
                try:
                    data = json.loads(line.strip())
                    event = SecurityEvent(
                        id=data.get('id', ''),
                        event_type=SecurityEventType(data['event_type']),
                        user_id=data.get('user_id'),
                        username=data.get('username'),
                        session_id=data.get('session_id'),
                        ip_address=data.get('ip_address'),
                        user_agent=data.get('user_agent'),
                        resource_type=ResourceType(data['resource_type']) if data.get('resource_type') else None,
                        resource_id=data.get('resource_id'),
                        action=data['action'],
                        result=data['result'],
                        severity=data.get('severity', 'info'),
                        details=data.get('details', {}),
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )

                    # Apply filters
                    if self._matches_filter(event, filter_criteria):
                        events.append(event)

                except Exception as e:
                    audit_logger.warning(f"Failed to parse log entry: {e}")
                    continue

        except Exception as e:
            audit_logger.error(f"Failed to read log file {log_file}: {e}")

        return events

    def _matches_filter(self, event: SecurityEvent, filter_criteria: AuditFilter) -> bool:
        """Check if event matches filter criteria"""
        if filter_criteria.user_id and event.user_id != filter_criteria.user_id:
            return False

        if filter_criteria.username and event.username != filter_criteria.username:
            return False

        if filter_criteria.event_type and event.event_type != filter_criteria.event_type:
            return False

        if filter_criteria.resource_type and event.resource_type != filter_criteria.resource_type:
            return False

        if filter_criteria.ip_address and event.ip_address != filter_criteria.ip_address:
            return False

        if filter_criteria.session_id and event.session_id != filter_criteria.session_id:
            return False

        if filter_criteria.start_date and event.timestamp < filter_criteria.start_date:
            return False

        if filter_criteria.end_date and event.timestamp > filter_criteria.end_date:
            return False

        if filter_criteria.severity and event.severity != filter_criteria.severity:
            return False

        if filter_criteria.result and event.result != filter_criteria.result:
            return False

        return True

    async def generate_compliance_report(self, standard: ComplianceStandard,
                                      period_start: datetime,
                                      period_end: datetime) -> ComplianceReport:
        """Generate compliance report for specified period"""
        try:
            # Query events for the period
            filter_criteria = AuditFilter(
                start_date=period_start,
                end_date=period_end
            )
            events = await self.query_events(filter_criteria)

            # Calculate metrics
            total_events = len(events)
            security_events = len([e for e in events if e.severity in ['high', 'critical']])
            data_access_events = len([e for e in events if e.event_type in [
                SecurityEventType.DATA_ACCESS, SecurityEventType.DATA_MODIFICATION
            ]])
            admin_actions = len([e for e in events if e.username and 'admin' in e.username.lower()])
            failed_authentications = len([e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE])
            unique_users = len(set(e.user_id for e in events if e.user_id))

            # Calculate compliance score based on standard
            compliance_score = self._calculate_compliance_score(events, standard)

            # Generate findings
            findings = self._generate_compliance_findings(events, standard)

            return ComplianceReport(
                standard=standard,
                period_start=period_start,
                period_end=period_end,
                total_events=total_events,
                security_events=security_events,
                data_access_events=data_access_events,
                admin_actions=admin_actions,
                failed_authentications=failed_authentications,
                unique_users=unique_users,
                compliance_score=compliance_score,
                findings=findings
            )

        except Exception as e:
            audit_logger.error(f"Failed to generate compliance report: {e}")
            raise

    def _calculate_compliance_score(self, events: List[SecurityEvent], standard: ComplianceStandard) -> float:
        """Calculate compliance score based on standard requirements"""
        score = 100.0

        # Deduct points for security events
        security_events = [e for e in events if e.severity in ['high', 'critical']]
        score -= len(security_events) * 5

        # Deduct points for failed authentications
        failed_logins = [e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]
        score -= len(failed_logins) * 2

        # Standard-specific deductions
        if standard == ComplianceStandard.GDPR:
            # Check for data access logging
            data_access = [e for e in events if e.event_type in [SecurityEventType.DATA_ACCESS, SecurityEventType.DATA_MODIFICATION]]
            if not data_access:
                score -= 20

        elif standard == ComplianceStandard.HIPAA:
            # Check for patient data access logging
            phi_access = [e for e in events if 'phi' in str(e.details).lower()]
            if not phi_access:
                score -= 15

        elif standard == ComplianceStandard.PCI_DSS:
            # Check for payment card data access
            card_data = [e for e in events if 'card' in str(e.details).lower()]
            if not card_data:
                score -= 25

        return max(0, min(100, score))

    def _generate_compliance_findings(self, events: List[SecurityEvent], standard: ComplianceStandard) -> List[Dict[str, Any]]:
        """Generate compliance findings"""
        findings = []

        # Check for missing audit trails
        critical_actions = [
            SecurityEventType.USER_CREATE, SecurityEventType.USER_DELETE,
            SecurityEventType.ROLE_CREATE, SecurityEventType.ROLE_DELETE,
            SecurityEventType.SECURITY_CONFIG_CHANGE
        ]

        missing_critical_logs = False
        for action in critical_actions:
            action_events = [e for e in events if e.event_type == action]
            if not action_events:
                missing_critical_logs = True
                break

        if missing_critical_logs:
            findings.append({
                "severity": "high",
                "category": "Audit Trail",
                "description": "Missing audit logs for critical security actions",
                "recommendation": "Enable comprehensive logging for all administrative actions"
            })

        # Check for excessive failed logins
        failed_logins = [e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]
        if len(failed_logins) > 100:
            findings.append({
                "severity": "medium",
                "category": "Authentication",
                "description": f"High number of failed login attempts ({len(failed_logins)})",
                "recommendation": "Implement account lockout policies and monitor for brute force attacks"
            })

        # Check for privilege escalation
        privilege_events = [e for e in events if 'admin' in str(e.action).lower()]
        if len(privilege_events) > 50:
            findings.append({
                "severity": "medium",
                "category": "Access Control",
                "description": "High number of administrative privilege usage",
                "recommendation": "Review administrative access and implement principle of least privilege"
            })

        return findings

    async def export_audit_log(self, output_format: str = "json", output_file: str = None) -> str:
        """Export audit log to specified format"""
        try:
            filter_criteria = AuditFilter()
            events = await self.query_events(filter_criteria)

            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"audit_export_{timestamp}.{output_format}"

            output_path = Path(output_file)

            if output_format.lower() == "json":
                await self._export_json(events, output_path)
            elif output_format.lower() == "csv":
                await self._export_csv(events, output_path)
            else:
                raise ValueError(f"Unsupported export format: {output_format}")

            audit_logger.info(f"Audit log exported to {output_file}")
            return str(output_path)

        except Exception as e:
            audit_logger.error(f"Failed to export audit log: {e}")
            raise

    async def _export_json(self, events: List[SecurityEvent], output_path: Path):
        """Export events to JSON format"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_events": len(events),
            "events": [event.to_dict() for event in events]
        }

        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(export_data, indent=2, default=str))

    async def _export_csv(self, events: List[SecurityEvent], output_path: Path):
        """Export events to CSV format"""
        import csv

        async with aiofiles.open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'timestamp', 'event_type', 'user_id', 'username', 'session_id',
                'ip_address', 'user_agent', 'resource_type', 'resource_id',
                'action', 'result', 'severity', 'details'
            ])

            # Write events
            for event in events:
                writer.writerow([
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.user_id,
                    event.username,
                    event.session_id,
                    event.ip_address,
                    event.user_agent,
                    event.resource_type.value if event.resource_type else '',
                    event.resource_id,
                    event.action,
                    event.result,
                    event.severity,
                    json.dumps(event.details)
                ])

    async def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            if self.storage_backend == StorageBackend.SQLITE:
                await self._cleanup_sqlite(cutoff_date)
            elif self.storage_backend == StorageBackend.FILE:
                await self._cleanup_files(cutoff_date)

            audit_logger.info(f"Cleaned up audit logs older than {cutoff_date}")

        except Exception as e:
            audit_logger.error(f"Failed to cleanup old logs: {e}")

    async def _cleanup_sqlite(self, cutoff_date: datetime):
        """Clean up old SQLite entries"""
        def _sync_cleanup():
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff_date.isoformat(),))
                conn.commit()
                conn.close()

            except Exception as e:
                audit_logger.error(f"SQLite cleanup failed: {e}")

        await asyncio.get_event_loop().run_in_executor(self.executor, _sync_cleanup)

    async def _cleanup_files(self, cutoff_date: datetime):
        """Clean up old log files"""
        try:
            log_files = list(self.log_directory.glob("audit_*.log"))
            log_files.extend(self.log_directory.glob("audit_*.log.gz"))

            for log_file in log_files:
                try:
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        log_file.unlink()
                        audit_logger.info(f"Deleted old log file: {log_file}")
                except Exception as e:
                    audit_logger.error(f"Failed to delete log file {log_file}: {e}")

        except Exception as e:
            audit_logger.error(f"File cleanup failed: {e}")

    async def get_audit_statistics(self, period_start: datetime = None, period_end: datetime = None) -> Dict[str, Any]:
        """Get audit log statistics"""
        try:
            if not period_start:
                period_start = datetime.now() - timedelta(days=7)
            if not period_end:
                period_end = datetime.now()

            filter_criteria = AuditFilter(start_date=period_start, end_date=period_end)
            events = await self.query_events(filter_criteria)

            # Calculate statistics
            stats = {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "total_events": len(events),
                "events_by_type": {},
                "events_by_severity": {},
                "events_by_user": {},
                "events_by_hour": {},
                "top_ip_addresses": {},
                "failed_authentications": 0,
                "security_events": 0
            }

            # Group events by various criteria
            for event in events:
                # By event type
                event_type = event.event_type.value
                stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1

                # By severity
                severity = event.severity
                stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1

                # By user
                if event.username:
                    user = event.username
                    stats["events_by_user"][user] = stats["events_by_user"].get(user, 0) + 1

                # By hour
                hour = event.timestamp.hour
                stats["events_by_hour"][hour] = stats["events_by_hour"].get(hour, 0) + 1

                # By IP address
                if event.ip_address:
                    ip = event.ip_address
                    stats["top_ip_addresses"][ip] = stats["top_ip_addresses"].get(ip, 0) + 1

                # Count specific event types
                if event.event_type == SecurityEventType.LOGIN_FAILURE:
                    stats["failed_authentications"] += 1

                if event.severity in ['high', 'critical']:
                    stats["security_events"] += 1

            # Sort and limit top results
            stats["top_ip_addresses"] = dict(sorted(stats["top_ip_addresses"].items(), key=lambda x: x[1], reverse=True)[:10])
            stats["events_by_user"] = dict(sorted(stats["events_by_user"].items(), key=lambda x: x[1], reverse=True)[:10])

            return stats

        except Exception as e:
            audit_logger.error(f"Failed to get audit statistics: {e}")
            return {}

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        asyncio.create_task(self._periodic_cleanup())
        asyncio.create_task(self._periodic_statistics_update())

    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(24 * 60 * 60)  # Run daily
                await self.cleanup_old_logs()
            except Exception as e:
                audit_logger.error(f"Periodic cleanup failed: {e}")

    async def _periodic_statistics_update(self):
        """Periodic statistics update task"""
        while True:
            try:
                await asyncio.sleep(60 * 60)  # Run hourly
                # Update statistics cache or send to monitoring system
                stats = await self.get_audit_statistics()
                # Could send to monitoring dashboard here
            except Exception as e:
                audit_logger.error(f"Periodic statistics update failed: {e}")