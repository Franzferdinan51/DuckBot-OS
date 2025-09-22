"""
DuckBot Security Module

Provides comprehensive API key encryption and secure storage capabilities.
Implements AES-256 encryption with key derivation, secure configuration management,
and centralized key lifecycle management.

Components:
- EncryptionEngine: Core AES-256 encryption with PBKDF2 key derivation
- SecureKeyManager: Centralized key storage with access control
- SecureConfig: Encrypted configuration file management
- SecureEnv: Secure environment variable handling
- KeyRotator: Automated key rotation and lifecycle management
- SecurityAuditor: Comprehensive audit trail system
- MemoryProtector: Secure memory handling for decrypted keys
- AntiTamper: File integrity and tamper detection
"""

from .encryption_engine import EncryptionEngine
from .secure_key_manager import SecureKeyManager
from .secure_config import SecureConfig
from .secure_env import SecureEnv
from .key_rotator import KeyRotator
from .security_auditor import SecurityAuditor
from .memory_protector import MemoryProtector
from .anti_tamper import AntiTamper
from .security_config import SecurityConfig

__version__ = "1.0.0"
__all__ = [
    "EncryptionEngine",
    "SecureKeyManager",
    "SecureConfig",
    "SecureEnv",
    "KeyRotator",
    "SecurityAuditor",
    "MemoryProtector",
    "AntiTamper",
    "SecurityConfig"
]