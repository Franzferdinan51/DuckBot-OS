"""
DuckBot Network Security System

Advanced network security providing:
- Rate limiting and throttling
- IP whitelisting/blacklisting
- SSL/TLS configuration management
- Firewall rules integration
- Network threat detection
- DDoS protection

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import ipaddress
import re
import socket
import ssl
import asyncio
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, validator
import logging
from collections import defaultdict, deque
import time
import threading
from pathlib import Path

network_security_logger = logging.getLogger('duckbot.network_security')

class ThreatLevel(Enum):
    """Network threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    """Network security actions"""
    ALLOW = "allow"
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    CHALLENGE = "challenge"
    MONITOR = "monitor"
    LOG_ONLY = "log_only"

class FirewallRuleType(Enum):
    """Firewall rule types"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    FORWARD = "forward"

class SSLProtocol(Enum):
    """SSL/TLS protocols"""
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"

class NetworkEventType(Enum):
    """Network event types"""
    CONNECTION_ATTEMPT = "connection_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    MALFORMED_REQUEST = "malformed_request"
    DDOS_ATTEMPT = "ddos_attempt"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    MALICIOUS_USER_AGENT = "malicious_user_agent"
    GEOIP_BLOCK = "geoip_block"
    CERTIFICATE_ERROR = "certificate_error"

@dataclass
class NetworkEvent:
    """Network security event"""
    id: str
    timestamp: datetime
    event_type: NetworkEventType
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    protocol: str
    threat_level: ThreatLevel
    action_taken: ActionType
    details: Dict[str, Any] = field(default_factory=dict)
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

class IPReputation(BaseModel):
    """IP address reputation data"""
    ip_address: str
    country: Optional[str] = None
    city: Optional[str] = None
    organization: Optional[str] = None
    threat_score: float = 0.0  # 0.0 to 1.0
    is_proxy: bool = False
    is_vpn: bool = False
    is_tor: bool = False
    is_known_malicious: bool = False
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    total_connections: int = 0
    blocked_connections: int = 0
    suspicious_activities: List[str] = Field(default_factory=list)
    custom_tags: List[str] = Field(default_factory=list)

class RateLimitRule(BaseModel):
    """Rate limiting rule configuration"""
    name: str
    window_size_seconds: int = 60
    max_requests: int = 100
    burst_limit: int = 10
    key_extractor: str  # "ip", "user", "session", "endpoint"
    action: ActionType = ActionType.BLOCK
    cooldown_period_seconds: int = 300
    enabled: bool = True

class FirewallRule(BaseModel):
    """Firewall rule configuration"""
    name: str
    rule_type: FirewallRuleType
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None  # "tcp", "udp", "icmp"
    action: ActionType
    priority: int = 0
    enabled: bool = True
    description: str = ""
    expires_at: Optional[datetime] = None

class SSLConfig(BaseModel):
    """SSL/TLS configuration"""
    enabled: bool = True
    protocols: List[SSLProtocol] = [SSLProtocol.TLS_1_2, SSLProtocol.TLS_1_3]
    cipher_suites: List[str] = Field(default_factory=list)
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    certificate_chain_path: Optional[str] = None
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    ocsp_stapling: bool = True
    session_resumption: bool = True
    client_auth_required: bool = False

class GeoIPRule(BaseModel):
    """Geographic IP blocking rule"""
    name: str
    countries: List[str]  # ISO country codes
    action: ActionType
    exceptions: List[str] = Field(default_factory=list)  # IP exceptions
    enabled: bool = True
    description: str = ""

class NetworkSecurityManager:
    """Advanced Network Security Manager"""

    def __init__(self, config_path: str = "network_security_config.json"):
        self.config_path = Path(config_path)
        self.ip_reputations: Dict[str, IPReputation] = {}
        self.rate_limit_rules: Dict[str, RateLimitRule] = {}
        self.firewall_rules: List[FirewallRule] = []
        self.ssl_config = SSLConfig()
        self.geoip_rules: Dict[str, GeoIPRule] = {}

        # Rate limiting state
        self.request_counters: Dict[str, deque] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.rate_limit_violations: Dict[str, List[datetime]] = {}

        # Threat detection
        self.connection_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.suspicious_patterns: Dict[str, re.Pattern] = {}
        self.known_malicious_ips: Set[str] = set()

        # SSL context cache
        self.ssl_contexts: Dict[str, ssl.SSLContext] = {}

        # Statistics
        self.stats = {
            "total_connections": 0,
            "blocked_connections": 0,
            "rate_limited_connections": 0,
            "suspicious_activities": 0,
            "ssl_handshakes": 0,
            "ssl_errors": 0
        }

        # Threading
        self.running = False
        self.cleanup_thread = None
        self.stats_thread = None

        # Load configuration
        self._load_configuration()
        self._initialize_default_rules()
        self._initialize_suspicious_patterns()

        # Start background threads
        self._start_background_threads()

        network_security_logger.info("NetworkSecurityManager initialized")

    def _load_configuration(self):
        """Load network security configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                # Load SSL configuration
                if "ssl_config" in config:
                    self.ssl_config = SSLConfig(**config["ssl_config"])

                # Load rate limit rules
                for rule_data in config.get("rate_limit_rules", []):
                    rule = RateLimitRule(**rule_data)
                    self.rate_limit_rules[rule.name] = rule

                # Load firewall rules
                for rule_data in config.get("firewall_rules", []):
                    rule = FirewallRule(**rule_data)
                    self.firewall_rules.append(rule)

                # Load GeoIP rules
                for rule_data in config.get("geoip_rules", []):
                    rule = GeoIPRule(**rule_data)
                    self.geoip_rules[rule.name] = rule

                # Load known malicious IPs
                self.known_malicious_ips.update(config.get("known_malicious_ips", []))

                network_security_logger.info("Network security configuration loaded")
            except Exception as e:
                network_security_logger.error(f"Failed to load configuration: {e}")

    def _save_configuration(self):
        """Save network security configuration"""
        try:
            config = {
                "ssl_config": self.ssl_config.dict(),
                "rate_limit_rules": [rule.dict() for rule in self.rate_limit_rules.values()],
                "firewall_rules": [rule.dict() for rule in self.firewall_rules],
                "geoip_rules": [rule.dict() for rule in self.geoip_rules.values()],
                "known_malicious_ips": list(self.known_malicious_ips),
                "last_updated": datetime.utcnow().isoformat()
            }

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)

            network_security_logger.info("Network security configuration saved")
        except Exception as e:
            network_security_logger.error(f"Failed to save configuration: {e}")

    def _initialize_default_rules(self):
        """Initialize default security rules"""
        # Default rate limiting rules
        default_rate_limits = [
            RateLimitRule(
                name="general_ip_limit",
                window_size_seconds=60,
                max_requests=100,
                key_extractor="ip",
                action=ActionType.RATE_LIMIT
            ),
            RateLimitRule(
                name="auth_limit",
                window_size_seconds=300,
                max_requests=5,
                key_extractor="ip",
                action=ActionType.BLOCK,
                cooldown_period_seconds=1800
            ),
            RateLimitRule(
                name="api_limit",
                window_size_seconds=60,
                max_requests=1000,
                key_extractor="ip",
                action=ActionType.RATE_LIMIT
            ),
            RateLimitRule(
                name="user_session_limit",
                window_size_seconds=60,
                max_requests=50,
                key_extractor="session",
                action=ActionType.RATE_LIMIT
            )
        ]

        for rule in default_rate_limits:
            self.rate_limit_rules[rule.name] = rule

        # Default firewall rules
        default_firewall_rules = [
            FirewallRule(
                name="block_suspicious_ports",
                rule_type=FirewallRuleType.INBOUND,
                destination_port=22,  # SSH
                action=ActionType.BLOCK,
                priority=100,
                description="Block SSH access"
            ),
            FirewallRule(
                name="allow_web_traffic",
                rule_type=FirewallRuleType.INBOUND,
                destination_port=[80, 443],
                protocol="tcp",
                action=ActionType.ALLOW,
                priority=10,
                description="Allow web traffic"
            )
        ]

        self.firewall_rules.extend(default_firewall_rules)

        # Sort firewall rules by priority
        self.firewall_rules.sort(key=lambda x: x.priority, reverse=True)

    def _initialize_suspicious_patterns(self):
        """Initialize suspicious request patterns"""
        suspicious_patterns = {
            "sql_injection": re.compile(r'(?i)(union|select|insert|update|delete|drop|create|alter|exec)\s+\w+'),
            "xss_attack": re.compile(r'(?i)<script|javascript:|on\w+\s*='),
            "path_traversal": re.compile(r'\.\./|\.\.\\'),
            "command_injection": re.compile(r'(?i)(;|\||&|\$\(|`|nc|netcat|wget|curl)'),
            "buffer_overflow": re.compile(r'A{1000,}'),  # Long string of 'A's
            "user_agent_injection": re.compile(r'(?i)(nikto|nmap|sqlmap|metasploit|burp|zap)'),
            "directory_traversal": re.compile(r'(?i)(etc/passwd|winnt/system32|cmd\.exe)'),
            "file_inclusion": re.compile(r'(?i)(php://|data://|ftp://|http://)'),
            "ldap_injection": re.compile(r'(?i)\*\)(\)|\(|&)(|\)'),
            "xml_injection": re.compile(r'(?i)(<!ENTITY|SYSTEM|PUBLIC)')
        }

        self.suspicious_patterns = suspicious_patterns

    def _start_background_threads(self):
        """Start background maintenance threads"""
        self.running = True

        # Cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # Statistics thread
        self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        self.stats_thread.start()

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                self._cleanup_expired_blocks()
                self._cleanup_rate_limit_counters()
                self._cleanup_connection_history()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                network_security_logger.error(f"Cleanup loop error: {e}")

    def _stats_loop(self):
        """Background statistics collection"""
        while self.running:
            try:
                self._collect_network_statistics()
                time.sleep(60)  # Run every minute
            except Exception as e:
                network_security_logger.error(f"Stats loop error: {e}")

    def check_connection(self, source_ip: str, source_port: int, destination_ip: str,
                      destination_port: int, protocol: str, user_agent: str = None,
                      session_id: str = None, request_id: str = None) -> Tuple[bool, ActionType, str]:
        """Check if connection should be allowed"""
        self.stats["total_connections"] += 1

        # Create network event
        event = NetworkEvent(
            id=f"net_{int(time.time() * 1000000)}_{secrets.token_hex(4)}",
            timestamp=datetime.utcnow(),
            event_type=NetworkEventType.CONNECTION_ATTEMPT,
            source_ip=source_ip,
            source_port=source_port,
            destination_ip=destination_ip,
            destination_port=destination_port,
            protocol=protocol,
            threat_level=ThreatLevel.LOW,
            action_taken=ActionType.ALLOW,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )

        # Check if IP is currently blocked
        if source_ip in self.blocked_ips:
            if self.blocked_ips[source_ip] > datetime.utcnow():
                event.action_taken = ActionType.BLOCK
                event.threat_level = ThreatLevel.HIGH
                event.details["reason"] = "IP temporarily blocked"
                self._log_network_event(event)
                return False, ActionType.BLOCK, "IP address is blocked"
            else:
                # Block expired
                del self.blocked_ips[source_ip]

        # Check against known malicious IPs
        if source_ip in self.known_malicious_ips:
            event.action_taken = ActionType.BLOCK
            event.threat_level = ThreatLevel.CRITICAL
            event.details["reason"] = "Known malicious IP"
            self._log_network_event(event)
            self.stats["blocked_connections"] += 1
            return False, ActionType.BLOCK, "Known malicious IP address"

        # Check GeoIP blocking
        geoip_action = self._check_geoip_rules(source_ip)
        if geoip_action != ActionType.ALLOW:
            event.action_taken = geoip_action
            event.threat_level = ThreatLevel.MEDIUM
            event.details["reason"] = "GeoIP restriction"
            self._log_network_event(event)
            self.stats["blocked_connections"] += 1
            return False, geoip_action, "GeoIP restriction applied"

        # Check firewall rules
        firewall_action = self._check_firewall_rules(source_ip, source_port, destination_ip, destination_port, protocol)
        if firewall_action != ActionType.ALLOW:
            event.action_taken = firewall_action
            event.threat_level = ThreatLevel.MEDIUM
            event.details["reason"] = "Firewall rule"
            self._log_network_event(event)
            if firewall_action == ActionType.BLOCK:
                self.stats["blocked_connections"] += 1
            return False, firewall_action, "Firewall rule restriction"

        # Check rate limiting
        rate_limit_action = self._check_rate_limits(source_ip, session_id, destination_port)
        if rate_limit_action != ActionType.ALLOW:
            event.action_taken = rate_limit_action
            event.threat_level = ThreatLevel.MEDIUM
            event.details["reason"] = "Rate limit exceeded"
            self._log_network_event(event)
            self.stats["rate_limited_connections"] += 1
            return False, rate_limit_action, "Rate limit exceeded"

        # Check for suspicious patterns
        threat_info = self._detect_threats(source_ip, user_agent, destination_port)
        if threat_info["detected"]:
            event.action_taken = threat_info["action"]
            event.threat_level = threat_info["threat_level"]
            event.details = threat_info["details"]
            self._log_network_event(event)
            self.stats["suspicious_activities"] += 1

            if threat_info["action"] == ActionType.BLOCK:
                self.stats["blocked_connections"] += 1
                return False, threat_info["action"], threat_info["reason"]

        # Update IP reputation
        self._update_ip_reputation(source_ip, "connection_allowed")

        # Log successful connection
        self._log_network_event(event)

        return True, ActionType.ALLOW, "Connection allowed"

    def _check_geoip_rules(self, ip_address: str) -> ActionType:
        """Check GeoIP blocking rules"""
        try:
            # Get IP geolocation (simplified - in real implementation, use GeoIP database)
            geo_data = self._get_geoip_data(ip_address)
            country = geo_data.get("country", "")

            for rule in self.geoip_rules.values():
                if not rule.enabled:
                    continue

                if country in rule.countries:
                    # Check exceptions
                    if ip_address not in rule.exceptions:
                        return rule.action

            return ActionType.ALLOW

        except Exception as e:
            network_security_logger.error(f"GeoIP check failed: {e}")
            return ActionType.ALLOW  # Fail open

    def _get_geoip_data(self, ip_address: str) -> Dict[str, str]:
        """Get geolocation data for IP (simplified implementation)"""
        # In real implementation, use GeoIP database or API
        # This is a placeholder implementation
        try:
            ip_obj = ipaddress.ip_address(ip_address)

            # Simple local network detection
            if ip_obj.is_private:
                return {"country": "LOCAL", "city": "Local Network"}

            # Default response
            return {"country": "UNKNOWN", "city": "Unknown"}

        except ValueError:
            return {"country": "INVALID", "city": "Invalid IP"}

    def _check_firewall_rules(self, source_ip: str, source_port: int, destination_ip: str,
                            destination_port: int, protocol: str) -> ActionType:
        """Check against firewall rules"""
        for rule in self.firewall_rules:
            if not rule.enabled:
                continue

            # Check if rule has expired
            if rule.expires_at and rule.expires_at <= datetime.utcnow():
                continue

            # Check rule conditions
            if rule.source_ip and not self._matches_ip_pattern(source_ip, rule.source_ip):
                continue

            if rule.source_port and source_port != rule.source_port:
                continue

            if rule.destination_ip and not self._matches_ip_pattern(destination_ip, rule.destination_ip):
                continue

            if rule.destination_port:
                if isinstance(rule.destination_port, list):
                    if destination_port not in rule.destination_port:
                        continue
                else:
                    if destination_port != rule.destination_port:
                        continue

            if rule.protocol and protocol.lower() != rule.protocol.lower():
                continue

            # Rule matches, return specified action
            return rule.action

        return ActionType.ALLOW

    def _matches_ip_pattern(self, ip: str, pattern: str) -> bool:
        """Check if IP matches pattern (supports CIDR)"""
        try:
            if '/' in pattern:
                # CIDR notation
                network = ipaddress.ip_network(pattern, strict=False)
                return ipaddress.ip_address(ip) in network
            else:
                # Exact match
                return ip == pattern
        except ValueError:
            return False

    def _check_rate_limits(self, source_ip: str, session_id: str = None, endpoint: str = None) -> ActionType:
        """Check rate limiting rules"""
        current_time = time.time()

        for rule in self.rate_limit_rules.values():
            if not rule.enabled:
                continue

            # Extract key based on rule configuration
            if rule.key_extractor == "ip":
                key = f"ip_{source_ip}"
            elif rule.key_extractor == "session" and session_id:
                key = f"session_{session_id}"
            elif rule.key_extractor == "endpoint" and endpoint:
                key = f"endpoint_{endpoint}"
            else:
                key = f"ip_{source_ip}"  # Default to IP

            # Initialize counter if not exists
            if key not in self.request_counters:
                self.request_counters[key] = deque()

            # Clean old requests
            window_start = current_time - rule.window_size_seconds
            while self.request_counters[key] and self.request_counters[key][0] < window_start:
                self.request_counters[key].popleft()

            # Check burst limit
            current_window_count = len(self.request_counters[key])
            if current_window_count >= rule.burst_limit:
                # Record violation
                if key not in self.rate_limit_violations:
                    self.rate_limit_violations[key] = []
                self.rate_limit_violations[key].append(datetime.utcnow())

                # Block IP if too many violations
                violations = self.rate_limit_violations[key]
                recent_violations = [v for v in violations if (datetime.utcnow() - v).total_seconds() < rule.cooldown_period_seconds]
                self.rate_limit_violations[key] = recent_violations

                if len(recent_violations) >= 3:
                    self.block_ip(source_ip, duration=rule.cooldown_period_seconds)
                    return ActionType.BLOCK

                return rule.action

            # Add current request to counter
            self.request_counters[key].append(current_time)

        return ActionType.ALLOW

    def _detect_threats(self, source_ip: str, user_agent: str = None, destination_port: int = None) -> Dict[str, Any]:
        """Detect network threats and suspicious activities"""
        threat_info = {
            "detected": False,
            "action": ActionType.LOG_ONLY,
            "threat_level": ThreatLevel.LOW,
            "reason": "",
            "details": {}
        }

        # Check user agent for suspicious patterns
        if user_agent:
            for pattern_name, pattern in self.suspicious_patterns.items():
                if pattern.search(user_agent):
                    threat_info["detected"] = True
                    threat_info["action"] = ActionType.BLOCK
                    threat_info["threat_level"] = ThreatLevel.HIGH
                    threat_info["reason"] = f"Suspicious user agent pattern: {pattern_name}"
                    threat_info["details"]["pattern"] = pattern_name
                    threat_info["details"]["user_agent"] = user_agent

                    # Update IP reputation
                    self._update_ip_reputation(source_ip, "suspicious_user_agent")
                    break

        # Check for port scanning behavior
        if self._detect_port_scan(source_ip):
            threat_info["detected"] = True
            threat_info["action"] = ActionType.BLOCK
            threat_info["threat_level"] = ThreatLevel.HIGH
            threat_info["reason"] = "Port scanning detected"
            threat_info["details"]["scan_type"] = "port_scan"

            # Update IP reputation
            self._update_ip_reputation(source_ip, "port_scan")

        # Check for DDoS patterns
        if self._detect_ddos_attempt(source_ip):
            threat_info["detected"] = True
            threat_info["action"] = ActionType.BLOCK
            threat_info["threat_level"] = ThreatLevel.CRITICAL
            threat_info["reason"] = "DDoS attempt detected"
            threat_info["details"]["attack_type"] = "ddos"

            # Update IP reputation
            self._update_ip_reputation(source_ip, "ddos_attempt")

        # Check connection frequency
        if self._check_connection_frequency(source_ip):
            threat_info["detected"] = True
            threat_info["action"] = ActionType.RATE_LIMIT
            threat_info["threat_level"] = ThreatLevel.MEDIUM
            threat_info["reason"] = "High connection frequency"
            threat_info["details"]["issue"] = "connection_frequency"

        return threat_info

    def _detect_port_scan(self, source_ip: str) -> bool:
        """Detect port scanning behavior"""
        current_time = time.time()

        if source_ip not in self.connection_history:
            return False

        # Get recent connections (last 60 seconds)
        recent_connections = [
            conn for conn in self.connection_history[source_ip]
            if current_time - conn["timestamp"] < 60
        ]

        if len(recent_connections) < 10:
            return False

        # Check if connecting to many different ports
        unique_ports = set(conn["port"] for conn in recent_connections)

        # If more than 10 unique ports in 60 seconds, consider it a port scan
        return len(unique_ports) > 10

    def _detect_ddos_attempt(self, source_ip: str) -> bool:
        """Detect DDoS attack patterns"""
        current_time = time.time()

        if source_ip not in self.connection_history:
            return False

        # Get recent connections (last 10 seconds)
        recent_connections = [
            conn for conn in self.connection_history[source_ip]
            if current_time - conn["timestamp"] < 10
        ]

        # If more than 50 connections in 10 seconds, consider it DDoS
        return len(recent_connections) > 50

    def _check_connection_frequency(self, source_ip: str) -> bool:
        """Check for unusually high connection frequency"""
        current_time = time.time()

        if source_ip not in self.connection_history:
            return False

        # Get recent connections (last 30 seconds)
        recent_connections = [
            conn for conn in self.connection_history[source_ip]
            if current_time - conn["timestamp"] < 30
        ]

        # If more than 100 connections in 30 seconds, flag as suspicious
        return len(recent_connections) > 100

    def _update_ip_reputation(self, ip_address: str, activity: str):
        """Update IP address reputation"""
        current_time = datetime.utcnow()

        if ip_address not in self.ip_reputations:
            self.ip_reputations[ip_address] = IPReputation(
                ip_address=ip_address,
                first_seen=current_time
            )

        reputation = self.ip_reputations[ip_address]
        reputation.last_seen = current_time
        reputation.total_connections += 1

        # Update reputation based on activity
        if activity in ["suspicious_user_agent", "port_scan", "ddos_attempt"]:
            reputation.threat_score = min(1.0, reputation.threat_score + 0.2)
            reputation.suspicious_activities.append(activity)
        elif activity == "connection_blocked":
            reputation.blocked_connections += 1
            reputation.threat_score = min(1.0, reputation.threat_score + 0.1)
        elif activity == "connection_allowed":
            reputation.threat_score = max(0.0, reputation.threat_score - 0.01)

        # Add to connection history
        self.connection_history[ip_address].append({
            "timestamp": time.time(),
            "activity": activity
        })

    def block_ip(self, ip_address: str, duration: int = 3600, reason: str = "Security violation"):
        """Block an IP address for specified duration"""
        block_until = datetime.utcnow() + timedelta(seconds=duration)
        self.blocked_ips[ip_address] = block_until

        # Update IP reputation
        if ip_address in self.ip_reputations:
            self.ip_reputations[ip_address].threat_score = min(1.0, self.ip_reputations[ip_address].threat_score + 0.3)

        network_security_logger.warning(f"Blocked IP {ip_address} for {duration} seconds: {reason}")

    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP address"""
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            network_security_logger.info(f"Unblocked IP: {ip_address}")
            return True
        return False

    def add_firewall_rule(self, rule: FirewallRule) -> bool:
        """Add a new firewall rule"""
        self.firewall_rules.append(rule)
        # Sort by priority
        self.firewall_rules.sort(key=lambda x: x.priority, reverse=True)
        self._save_configuration()
        network_security_logger.info(f"Added firewall rule: {rule.name}")
        return True

    def remove_firewall_rule(self, rule_name: str) -> bool:
        """Remove a firewall rule"""
        for i, rule in enumerate(self.firewall_rules):
            if rule.name == rule_name:
                del self.firewall_rules[i]
                self._save_configuration()
                network_security_logger.info(f"Removed firewall rule: {rule_name}")
                return True
        return False

    def create_ssl_context(self, purpose: str = "server") -> ssl.SSLContext:
        """Create SSL context with secure configuration"""
        cache_key = f"{purpose}_{hash(str(self.ssl_config.dict()))}"

        if cache_key in self.ssl_contexts:
            return self.ssl_contexts[cache_key]

        if purpose == "server":
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        else:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        # Set minimum protocol version
        min_version = ssl.TLSVersion.TLSv1_2
        context.minimum_version = min_version

        # Set cipher suites
        if self.ssl_config.cipher_suites:
            context.set_ciphers(':'.join(self.ssl_config.cipher_suites))
        else:
            # Use secure default cipher suites
            context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')

        # Enable certificate verification
        context.verify_mode = ssl.CERT_REQUIRED

        # Load certificate and private key
        if (self.ssl_config.certificate_path and self.ssl_config.private_key_path and
            Path(self.ssl_config.certificate_path).exists() and
            Path(self.ssl_config.private_key_path).exists()):

            context.load_cert_chain(
                certfile=self.ssl_config.certificate_path,
                keyfile=self.ssl_config.private_key_path
            )

            if self.ssl_config.certificate_chain_path:
                context.load_verify_locations(cafile=self.ssl_config.certificate_chain_path)

        # Enable OCSP stapling
        if self.ssl_config.ocsp_stapling:
            # Note: OCSP stapling configuration is server-specific
            pass

        # Cache the context
        self.ssl_contexts[cache_key] = context
        self.stats["ssl_handshakes"] += 1

        return context

    def _log_network_event(self, event: NetworkEvent):
        """Log network security event"""
        # In real implementation, this would integrate with the audit logger
        log_message = (
            f"[{event.event_type.value}] {event.source_ip}:{event.source_port} -> "
            f"{event.destination_ip}:{event.destination_port} - "
            f"Action: {event.action_taken.value} - "
            f"Threat: {event.threat_level.value}"
        )

        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            network_security_logger.error(log_message)
        elif event.threat_level == ThreatLevel.MEDIUM:
            network_security_logger.warning(log_message)
        else:
            network_security_logger.info(log_message)

    def _cleanup_expired_blocks(self):
        """Clean up expired IP blocks"""
        current_time = datetime.utcnow()
        expired_ips = [ip for ip, expiry in self.blocked_ips.items() if expiry <= current_time]

        for ip in expired_ips:
            del self.blocked_ips[ip]
            network_security_logger.info(f"Expired block removed for IP: {ip}")

    def _cleanup_rate_limit_counters(self):
        """Clean up old rate limit counters"""
        current_time = time.time()

        # Clean old request counters
        expired_keys = []
        for key, timestamps in self.request_counters.items():
            if timestamps and (current_time - timestamps[-1]) > 3600:  # 1 hour
                expired_keys.append(key)

        for key in expired_keys:
            del self.request_counters[key]

        # Clean old rate limit violations
        for key, violations in self.rate_limit_violations.items():
            recent_violations = [
                v for v in violations if (datetime.utcnow() - v).total_seconds() < 3600
            ]
            self.rate_limit_violations[key] = recent_violations

    def _cleanup_connection_history(self):
        """Clean up old connection history"""
        # Keep only last 1000 connections per IP
        for ip in self.connection_history:
            if len(self.connection_history[ip]) > 1000:
                # Keep most recent 1000
                recent_connections = list(self.connection_history[ip])[-1000:]
                self.connection_history[ip] = deque(recent_connections, maxlen=1000)

    def _collect_network_statistics(self):
        """Collect network security statistics"""
        # This could be extended to send metrics to monitoring systems
        stats = self.get_network_security_stats()

        # Log if there are concerning metrics
        if stats["blocked_rate"] > 0.1:  # More than 10% blocked
            network_security_logger.warning(f"High block rate: {stats['blocked_rate']:.2%}")

        if stats["suspicious_activity_rate"] > 0.05:  # More than 5% suspicious
            network_security_logger.warning(f"High suspicious activity rate: {stats['suspicious_activity_rate']:.2%}")

    def get_network_security_stats(self) -> Dict[str, Any]:
        """Get network security statistics"""
        total_connections = self.stats["total_connections"]

        if total_connections == 0:
            return {
                "total_connections": 0,
                "blocked_connections": 0,
                "rate_limited_connections": 0,
                "suspicious_activities": 0,
                "blocked_rate": 0.0,
                "suspicious_activity_rate": 0.0
            }

        return {
            "total_connections": total_connections,
            "blocked_connections": self.stats["blocked_connections"],
            "rate_limited_connections": self.stats["rate_limited_connections"],
            "suspicious_activities": self.stats["suspicious_activities"],
            "ssl_handshakes": self.stats["ssl_handshakes"],
            "ssl_errors": self.stats["ssl_errors"],
            "currently_blocked_ips": len(self.blocked_ips),
            "active_rate_limits": len(self.request_counters),
            "ip_reputations_tracked": len(self.ip_reputations),
            "blocked_rate": self.stats["blocked_connections"] / total_connections,
            "suspicious_activity_rate": self.stats["suspicious_activities"] / total_connections,
            "high_risk_ips": len([r for r in self.ip_reputations.values() if r.threat_score > 0.7]),
            "known_malicious_ips": len(self.known_malicious_ips)
        }

    def get_ip_reputation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get IP reputation information"""
        if ip_address in self.ip_reputations:
            reputation = self.ip_reputations[ip_address]
            return {
                "ip_address": reputation.ip_address,
                "threat_score": reputation.threat_score,
                "country": reputation.country,
                "organization": reputation.organization,
                "is_proxy": reputation.is_proxy,
                "is_vpn": reputation.is_vpn,
                "is_tor": reputation.is_tor,
                "is_known_malicious": reputation.is_known_malicious,
                "total_connections": reputation.total_connections,
                "blocked_connections": reputation.blocked_connections,
                "suspicious_activities": reputation.suspicious_activities,
                "first_seen": reputation.first_seen.isoformat(),
                "last_seen": reputation.last_seen.isoformat()
            }
        return None

    def add_known_malicious_ip(self, ip_address: str, source: str = "manual"):
        """Add IP to known malicious IPs list"""
        self.known_malicious_ips.add(ip_address)

        # Update reputation if exists
        if ip_address in self.ip_reputations:
            self.ip_reputations[ip_address].is_known_malicious = True
            self.ip_reputations[ip_address].threat_score = 1.0

        self._save_configuration()
        network_security_logger.info(f"Added malicious IP: {ip_address} (source: {source})")

    def remove_known_malicious_ip(self, ip_address: str) -> bool:
        """Remove IP from known malicious IPs list"""
        if ip_address in self.known_malicious_ips:
            self.known_malicious_ips.remove(ip_address)

            # Update reputation if exists
            if ip_address in self.ip_reputations:
                self.ip_reputations[ip_address].is_known_malicious = False
                self.ip_reputations[ip_address].threat_score = max(0.0, self.ip_reputations[ip_address].threat_score - 0.5)

            self._save_configuration()
            network_security_logger.info(f"Removed malicious IP: {ip_address}")
            return True
        return False

    def shutdown(self):
        """Shutdown the network security manager"""
        self.running = False

        # Wait for threads to finish
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        if self.stats_thread:
            self.stats_thread.join(timeout=5)

        # Save configuration
        self._save_configuration()

        network_security_logger.info("NetworkSecurityManager shutdown complete")