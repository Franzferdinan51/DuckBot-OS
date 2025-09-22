"""
DuckBot Security Hardening Module

Comprehensive security hardening measures including:
- Input validation and sanitization
- XSS and CSRF protection
- SQL injection prevention
- Rate limiting and DDoS protection
- Secure communication encryption
- Security headers implementation
- File upload security
- Session security

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import re
import hashlib
import secrets
import base64
import ipaddress
import json
import html
import urllib.parse
from pathlib import Path
import logging
from dataclasses import dataclass
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

security_logger = logging.getLogger('duckbot.security.hardening')

class SecurityThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InputType(Enum):
    """Input types for validation"""
    USERNAME = "username"
    EMAIL = "email"
    PASSWORD = "password"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    SQL = "sql"
    COMMAND = "command"
    URL = "url"
    FILENAME = "filename"
    PHONE = "phone"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"

class FileUploadType(Enum):
    """File upload types"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    CODE = "code"
    ANY = "any"

@dataclass
class ValidationResult:
    """Validation result for input"""
    is_valid: bool
    sanitized_value: Optional[str] = None
    error_message: Optional[str] = None
    threat_level: SecurityThreatLevel = SecurityThreatLevel.LOW
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

@dataclass
class SecurityHeaders:
    """Security headers configuration"""
    content_security_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=(), payment=()"
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    cache_control: str = "no-store, no-cache, must-revalidate, proxy-revalidate"
    pragma: str = "no-cache"
    expires: str = "0"

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    requests_per_day: int = 86400
    burst_limit: int = 10
    window_size_seconds: int = 60

@dataclass
class FileUploadConfig:
    """File upload security configuration"""
    max_file_size_mb: int = 10
    allowed_extensions: Set[str] = None
    allowed_mime_types: Set[str] = None
    scan_for_malware: bool = True
    sanitize_filenames: bool = True
    generate_unique_names: bool = True
    store_separately: bool = True

    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'}
        if self.allowed_mime_types is None:
            self.allowed_mime_types = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain', 'application/msword'}

class SecurityHardening:
    """Main security hardening class"""

    def __init__(self, security_headers: SecurityHeaders = None,
                 rate_limit_config: RateLimitConfig = None,
                 file_upload_config: FileUploadConfig = None):
        self.security_headers = security_headers or SecurityHeaders()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.file_upload_config = file_upload_config or FileUploadConfig()

        # Rate limiting storage
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}

        # CSRF token storage
        self.csrf_tokens: Dict[str, Tuple[datetime, str]] = {}

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Security patterns
        self.sql_injection_patterns = self._load_sql_injection_patterns()
        self.xss_patterns = self._load_xss_patterns()
        self.command_injection_patterns = self._load_command_injection_patterns()
        self.path_traversal_patterns = self._load_path_traversal_patterns()

        security_logger.info("SecurityHardening initialized")

    def _load_sql_injection_patterns(self) -> List[str]:
        """Load SQL injection detection patterns"""
        return [
            r"(''|'')",
            r"('OR|'or)",
            r"(--)",
            r"(/\*.*\*/)",
            r"(;\s*$)",
            r"(0x[0-9a-fA-F]+)",
            r"(union\s+select)",
            r"(insert\s+into)",
            r"(update\s+\w+\s+set)",
            r"(delete\s+from)",
            r"(drop\s+table)",
            r"(exec\s*\()",
            r"(xp_cmdshell)",
            r"(sp_oacreate)",
            r"(waitfor\s+delay)",
            r"(benchmark\s*\()",
            r"(load_file\s*\()",
            r"(into\s+outfile)",
            r"(into\s+dumpfile)",
            r"(substring\s*\()",
            r"(mid\s*\()",
            r"(char\s*\()",
            r"(ascii\s*\()",
            r"(length\s*\()",
            r"(count\s*\()"
        ]

    def _load_xss_patterns(self) -> List[str]:
        """Load XSS detection patterns"""
        return [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"eval\s*\(",
            r"setTimeout\s*\(",
            r"setInterval\s*\(",
            r"document\.cookie",
            r"document\.write",
            r"window\.location",
            r"alert\s*\(",
            r"confirm\s*\(",
            r"prompt\s*\(",
            r"<\?php",
            r"<%.*%>",
            r"&lt;script&gt;",
            r"&lt;iframe&gt;",
            r"data:text/html",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*="
        ]

    def _load_command_injection_patterns(self) -> List[str]:
        """Load command injection detection patterns"""
        return [
            r"[;&|`$(){}\\]",
            r"/dev/tcp",
            r"/dev/udp",
            r"nc\s+-l",
            r"netcat\s+-l",
            r"telnet\s+",
            r"curl\s+",
            r"wget\s+",
            r"fetch\s+",
            r"exec\s+",
            r"eval\s+",
            r"system\s*\(",
            r"shell_exec\s*\(",
            r"passthru\s*\(",
            r"popen\s*\(",
            r"proc_open\s*\("",
            r"`.*`",
            r"\$\(",
            r"<.*>",
            r">.*>",
            r"\|\|",
            r"&&",
            r";",
            r"&",
            r"`"
        ]

    def _load_path_traversal_patterns(self) -> List[str]:
        """Load path traversal detection patterns"""
        return [
            r"\.\./",
            r"\.\.\\",
            r"~/",
            r"~\\",
            r"/etc/passwd",
            r"/etc/shadow",
            r"c:\\windows\\system32",
            r"../../../../",
            r"..\\..\\..\\",
            r"/proc/self/environ",
            r"/windows/system32",
            r"\.\.\.%2f",
            r"%2e%2e%2f",
            r"%2e%2e\\"
        ]

    def validate_input(self, input_value: str, input_type: InputType,
                      allow_empty: bool = False) -> ValidationResult:
        """Validate and sanitize input based on type"""
        try:
            if not input_value and not allow_empty:
                return ValidationResult(
                    is_valid=False,
                    error_message="Input cannot be empty",
                    threat_level=SecurityThreatLevel.MEDIUM
                )

            if not input_value and allow_empty:
                return ValidationResult(is_valid=True, sanitized_value="")

            # Type-specific validation
            if input_type == InputType.USERNAME:
                return self._validate_username(input_value)
            elif input_type == InputType.EMAIL:
                return self._validate_email(input_value)
            elif input_type == InputType.PASSWORD:
                return self._validate_password(input_value)
            elif input_type == InputType.HTML:
                return self._validate_html(input_value)
            elif input_type == InputType.MARKDOWN:
                return self._validate_markdown(input_value)
            elif input_type == InputType.JSON:
                return self._validate_json(input_value)
            elif input_type == InputType.SQL:
                return self._validate_sql(input_value)
            elif input_type == InputType.COMMAND:
                return self._validate_command(input_value)
            elif input_type == InputType.URL:
                return self._validate_url(input_value)
            elif input_type == InputType.FILENAME:
                return self._validate_filename(input_value)
            elif input_type == InputType.PHONE:
                return self._validate_phone(input_value)
            elif input_type == InputType.INTEGER:
                return self._validate_integer(input_value)
            elif input_type == InputType.FLOAT:
                return self._validate_float(input_value)
            elif input_type == InputType.BOOLEAN:
                return self._validate_boolean(input_value)
            elif input_type == InputType.DATE:
                return self._validate_date(input_value)
            elif input_type == InputType.TIME:
                return self._validate_time(input_value)
            elif input_type == InputType.DATETIME:
                return self._validate_datetime(input_value)
            else:
                return self._validate_text(input_value)

        except Exception as e:
            security_logger.error(f"Input validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="Input validation error",
                threat_level=SecurityThreatLevel.HIGH
            )

    def _validate_username(self, username: str) -> ValidationResult:
        """Validate username"""
        errors = []
        warnings = []

        # Length check
        if len(username) < 3 or len(username) > 50:
            errors.append("Username must be between 3 and 50 characters")

        # Character check
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            errors.append("Username can only contain letters, numbers, hyphens, and underscores")

        # Reserved names
        reserved_names = {'admin', 'administrator', 'root', 'system', 'support', 'security'}
        if username.lower() in reserved_names:
            warnings.append("This username is commonly targeted by attackers")

        # Threat detection
        if self._detect_threat_patterns(username, self.sql_injection_patterns + self.xss_patterns):
            errors.append("Username contains suspicious patterns")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=username.strip().lower() if len(errors) == 0 else None,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_email(self, email: str) -> ValidationResult:
        """Validate email address"""
        errors = []
        warnings = []

        # Basic format check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")

        # Length check
        if len(email) > 254:
            errors.append("Email address too long")

        # Check for disposable email domains
        disposable_domains = {'tempmail.org', '10minutemail.com', 'guerrillamail.com'}
        domain = email.split('@')[-1].lower()
        if domain in disposable_domains:
            warnings.append("Disposable email addresses are not recommended")

        # Threat detection
        if self._detect_threat_patterns(email, self.sql_injection_patterns + self.xss_patterns):
            errors.append("Email contains suspicious patterns")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=email.strip().lower() if len(errors) == 0 else None,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_password(self, password: str) -> ValidationResult:
        """Validate password"""
        errors = []
        warnings = []

        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        # Character variety
        if not re.search(r'[A-Z]', password):
            warnings.append("Password should contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            warnings.append("Password should contain at least one lowercase letter")

        if not re.search(r'\d', password):
            warnings.append("Password should contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            warnings.append("Password should contain at least one special character")

        # Common passwords
        common_passwords = {'password', '123456', '12345678', 'qwerty', 'abc123'}
        if password.lower() in common_passwords:
            errors.append("Password is too common")

        # Threat detection
        if self._detect_threat_patterns(password, self.sql_injection_patterns + self.xss_patterns):
            errors.append("Password contains suspicious patterns")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=None,  # Never return sanitized password
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_html(self, html_content: str) -> ValidationResult:
        """Validate and sanitize HTML content"""
        errors = []
        warnings = []

        # Detect XSS patterns
        if self._detect_threat_patterns(html_content, self.xss_patterns):
            errors.append("HTML contains potentially malicious content")

        # Sanitize HTML
        sanitized = self._sanitize_html(html_content)

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.MEDIUM,
            warnings=warnings
        )

    def _validate_markdown(self, markdown_content: str) -> ValidationResult:
        """Validate and sanitize Markdown content"""
        errors = []
        warnings = []

        # Check for HTML injection
        if re.search(r'<script[^>]*>.*?</script>', markdown_content, re.IGNORECASE):
            warnings.append("Markdown contains script tags")

        # Check for dangerous links
        if re.search(r'javascript:', markdown_content, re.IGNORECASE):
            errors.append("Markdown contains dangerous links")

        # Basic sanitization
        sanitized = self._sanitize_markdown(markdown_content)

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_json(self, json_content: str) -> ValidationResult:
        """Validate JSON content"""
        errors = []

        try:
            # Parse JSON
            parsed = json.loads(json_content)

            # Sanitize JSON
            sanitized = self._sanitize_json(parsed)

            return ValidationResult(
                is_valid=True,
                sanitized_value=json.dumps(sanitized),
                error_message=None,
                threat_level=SecurityThreatLevel.LOW
            )

        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid JSON: {str(e)}",
                threat_level=SecurityThreatLevel.MEDIUM
            )

    def _validate_sql(self, sql_content: str) -> ValidationResult:
        """Validate SQL content"""
        errors = []
        warnings = []

        # Detect SQL injection patterns
        if self._detect_threat_patterns(sql_content, self.sql_injection_patterns):
            errors.append("SQL contains potentially dangerous patterns")

        # Sanitize SQL
        sanitized = self._sanitize_sql(sql_content)

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.MEDIUM,
            warnings=warnings
        )

    def _validate_command(self, command: str) -> ValidationResult:
        """Validate command input"""
        errors = []
        warnings = []

        # Detect command injection patterns
        if self._detect_threat_patterns(command, self.command_injection_patterns):
            errors.append("Command contains potentially dangerous patterns")

        # Detect path traversal
        if self._detect_threat_patterns(command, self.path_traversal_patterns):
            errors.append("Command contains path traversal patterns")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=self._sanitize_command(command),
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.MEDIUM,
            warnings=warnings
        )

    def _validate_url(self, url: str) -> ValidationResult:
        """Validate URL"""
        errors = []
        warnings = []

        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            errors.append("Invalid URL format")

        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
        for protocol in dangerous_protocols:
            if protocol in url.lower():
                errors.append(f"URL contains dangerous protocol: {protocol}")

        # Check for internal IP addresses
        if self._contains_internal_ip(url):
            warnings.append("URL may contain internal network references")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=url.strip(),
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_filename(self, filename: str) -> ValidationResult:
        """Validate filename"""
        errors = []
        warnings = []

        # Length check
        if len(filename) > 255:
            errors.append("Filename too long")

        # Character check
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, filename):
            errors.append("Filename contains invalid characters")

        # Reserved filenames
        reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'lpt1', 'lpt2'}
        if filename.lower() in reserved_names:
            errors.append("Filename is reserved by the system")

        # Path traversal detection
        if self._detect_threat_patterns(filename, self.path_traversal_patterns):
            errors.append("Filename contains path traversal patterns")

        # Extension check
        if hasattr(self.file_upload_config, 'allowed_extensions'):
            ext = Path(filename).suffix.lower()
            if ext not in self.file_upload_config.allowed_extensions:
                errors.append(f"File extension '{ext}' is not allowed")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=self._sanitize_filename(filename),
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _validate_text(self, text: str) -> ValidationResult:
        """Validate general text input"""
        errors = []
        warnings = []

        # Basic threat detection
        if self._detect_threat_patterns(text, self.xss_patterns + self.sql_injection_patterns):
            warnings.append("Text contains potentially suspicious patterns")

        # Length check
        if len(text) > 10000:
            warnings.append("Text input is very long")

        # Sanitize text
        sanitized = self._sanitize_text(text)

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.MEDIUM if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _detect_threat_patterns(self, input_string: str, patterns: List[str]) -> bool:
        """Detect threat patterns in input"""
        for pattern in patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                security_logger.warning(f"Threat pattern detected: {pattern}")
                return True
        return False

    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content"""
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE)

        # Remove dangerous attributes
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)

        # Remove dangerous tags
        dangerous_tags = ['iframe', 'object', 'embed', 'applet']
        for tag in dangerous_tags:
            sanitized = re.sub(fr'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def _sanitize_markdown(self, markdown_content: str) -> str:
        """Sanitize Markdown content"""
        # Remove dangerous HTML
        sanitized = self._sanitize_html(markdown_content)

        # Sanitize links
        sanitized = re.sub(r'\[([^\]]+)\]\(javascript:[^\)]+\)', r'\1', sanitized, flags=re.IGNORECASE)

        return sanitized

    def _sanitize_json(self, json_data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(json_data, str):
            return html.escape(json_data)
        elif isinstance(json_data, dict):
            return {k: self._sanitize_json(v) for k, v in json_data.items()}
        elif isinstance(json_data, list):
            return [self._sanitize_json(item) for item in json_data]
        else:
            return json_data

    def _sanitize_sql(self, sql_content: str) -> str:
        """Sanitize SQL content"""
        # Escape single quotes
        sanitized = sql_content.replace("'", "''")

        # Remove dangerous comments
        sanitized = re.sub(r'--.*$', '', sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)

        return sanitized

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command input"""
        # Remove dangerous characters
        dangerous_chars = ['|', '&', ';', '$', '`', '\\', '>', '<', '!']
        sanitized = command
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename"""
        # Remove invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')

        # Truncate if too long
        if len(sanitized) > 255:
            name, ext = Path(sanitized).stem, Path(sanitized).suffix
            sanitized = name[:255-len(ext)] + ext

        return sanitized

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        # Escape HTML entities
        sanitized = html.escape(text)

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        return sanitized

    def _contains_internal_ip(self, url: str) -> bool:
        """Check if URL contains internal IP addresses"""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname

            if hostname:
                try:
                    ip = ipaddress.ip_address(hostname)
                    return ip.is_private or ip.is_loopback
                except ValueError:
                    # Check for common internal hostnames
                    internal_hosts = ['localhost', '127.0.0.1', '::1']
                    return hostname.lower() in internal_hosts

            return False
        except Exception:
            return False

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[token] = (datetime.utcnow(), session_id)
        return token

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        if token not in self.csrf_tokens:
            return False

        token_time, token_session_id = self.csrf_tokens[token]

        # Check if token is expired (1 hour)
        if datetime.utcnow() - token_time > timedelta(hours=1):
            del self.csrf_tokens[token]
            return False

        # Check if session matches
        return token_session_id == session_id

    def check_rate_limit(self, identifier: str, window_size: int = 60) -> bool:
        """Check if identifier has exceeded rate limit"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_size)

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Clean old requests
        self.rate_limits[identifier] = [req_time for req_time in self.rate_limits[identifier] if req_time > cutoff]

        # Check limit
        return len(self.rate_limits[identifier]) < self.rate_limit_config.requests_per_minute

    def record_request(self, identifier: str):
        """Record a request for rate limiting"""
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        self.rate_limits[identifier].append(datetime.utcnow())

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return {
            'Content-Security-Policy': self.security_headers.content_security_policy,
            'X-Frame-Options': self.security_headers.x_frame_options,
            'X-Content-Type-Options': self.security_headers.x_content_type_options,
            'X-XSS-Protection': self.security_headers.x_xss_protection,
            'Referrer-Policy': self.security_headers.referrer_policy,
            'Permissions-Policy': self.security_headers.permissions_policy,
            'Strict-Transport-Security': self.security_headers.strict_transport_security,
            'Cache-Control': self.security_headers.cache_control,
            'Pragma': self.security_headers.pragma,
            'Expires': self.security_headers.expires
        }

    def validate_file_upload(self, file_data: bytes, filename: str,
                           content_type: str, upload_type: FileUploadType = FileUploadType.ANY) -> ValidationResult:
        """Validate file upload"""
        errors = []
        warnings = []

        # Check file size
        if len(file_data) > self.file_upload_config.max_file_size_mb * 1024 * 1024:
            errors.append(f"File size exceeds limit of {self.file_upload_config.max_file_size_mb}MB")

        # Check file extension
        if self.file_upload_config.sanitize_filenames:
            sanitized_filename = self._sanitize_filename(filename)
        else:
            sanitized_filename = filename

        # Check allowed extensions
        if upload_type != FileUploadType.ANY and self.file_upload_config.allowed_extensions:
            ext = Path(sanitized_filename).suffix.lower()
            if ext not in self.file_upload_config.allowed_extensions:
                errors.append(f"File extension '{ext}' is not allowed")

        # Check MIME type
        if self.file_upload_config.allowed_mime_types:
            if content_type not in self.file_upload_config.allowed_mime_types:
                errors.append(f"MIME type '{content_type}' is not allowed")

        # Basic malware scan (check for common signatures)
        if self.file_upload_config.scan_for_malware:
            if self._scan_for_malware(file_data):
                errors.append("File appears to contain malicious content")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_value=sanitized_filename,
            error_message="; ".join(errors) if errors else None,
            threat_level=SecurityThreatLevel.HIGH if errors else SecurityThreatLevel.LOW,
            warnings=warnings
        )

    def _scan_for_malware(self, file_data: bytes) -> bool:
        """Basic malware scanning"""
        # Check for common malware signatures
        malware_signatures = [
            b'<script',
            b'eval(',
            b'document.write',
            b'window.location',
            b'function()',
            b'<?php',
            b'<%='
        ]

        for signature in malware_signatures:
            if signature.lower() in file_data.lower():
                security_logger.warning(f"Malware signature detected: {signature}")
                return True

        # Check for executable content
        executable_signatures = [
            b'MZ',  # PE header
            b'\x7fELF',  # ELF header
            b'#!/',  # Shebang
        ]

        for signature in executable_signatures:
            if file_data.startswith(signature):
                security_logger.warning(f"Executable content detected: {signature}")
                return True

        return False

    def cleanup_expired_tokens(self):
        """Clean up expired CSRF tokens"""
        now = datetime.utcnow()
        expired_tokens = [
            token for token, (token_time, _) in self.csrf_tokens.items()
            if now - token_time > timedelta(hours=1)
        ]

        for token in expired_tokens:
            del self.csrf_tokens[token]

    def cleanup_rate_limits(self):
        """Clean up old rate limit entries"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)

        expired_identifiers = [
            identifier for identifier, requests in self.rate_limits.items()
            if not requests or requests[-1] < cutoff
        ]

        for identifier in expired_identifiers:
            del self.rate_limits[identifier]

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "active_csrf_tokens": len(self.csrf_tokens),
            "rate_limited_identifiers": len(self.rate_limits),
            "security_headers_enabled": True,
            "file_upload_validation_enabled": True,
            "input_validation_enabled": True,
            "csrf_protection_enabled": True,
            "rate_limiting_enabled": True
        }

# Decorator for requiring CSRF protection
def require_csrf_token():
    """Decorator to require CSRF token for endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract CSRF token from request (implementation depends on framework)
            csrf_token = kwargs.get('csrf_token') or args[0].get('csrf_token')
            session_id = kwargs.get('session_id') or args[0].get('session_id')

            if not csrf_token or not session_id:
                return {"error": "CSRF token and session ID required"}

            # Validate CSRF token (implementation depends on security hardening instance)
            if not hasattr(wrapper, 'security_hardening'):
                return {"error": "Security hardening not configured"}

            if not wrapper.security_hardening.validate_csrf_token(csrf_token, session_id):
                return {"error": "Invalid CSRF token"}

            return await func(*args, **kwargs)

        return wrapper
    return decorator

# Decorator for rate limiting
def rate_limit(requests_per_minute: int = 60, identifier_key: str = 'ip_address'):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract identifier from request
            identifier = kwargs.get(identifier_key) or getattr(args[0], identifier_key, 'unknown')

            # Check rate limit (implementation depends on security hardening instance)
            if not hasattr(wrapper, 'security_hardening'):
                return {"error": "Security hardening not configured"}

            if not wrapper.security_hardening.check_rate_limit(identifier):
                return {"error": "Rate limit exceeded"}

            wrapper.security_hardening.record_request(identifier)
            return await func(*args, **kwargs)

        return wrapper
    return decorator

# Decorator for input validation
def validate_input(input_field: str, input_type: InputType, allow_empty: bool = False):
    """Decorator for input validation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract input from request
            input_value = kwargs.get(input_field) or getattr(args[0], input_field, None)

            # Validate input (implementation depends on security hardening instance)
            if not hasattr(wrapper, 'security_hardening'):
                return {"error": "Security hardening not configured"}

            validation_result = wrapper.security_hardening.validate_input(input_value, input_type, allow_empty)

            if not validation_result.is_valid:
                return {"error": validation_result.error_message}

            # Update the input with sanitized value
            if input_field in kwargs:
                kwargs[input_field] = validation_result.sanitized_value
            elif hasattr(args[0], input_field):
                setattr(args[0], input_field, validation_result.sanitized_value)

            return await func(*args, **kwargs)

        return wrapper
    return decorator