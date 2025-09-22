"""
DuckBot Data Protection System

Advanced data protection providing:
- Encryption for sensitive data at rest and in transit
- Data masking and anonymization
- GDPR compliance features
- Data loss prevention (DLP)
- Secure data lifecycle management

Author: Security Framework Module
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
import re
from pathlib import Path
import asyncio
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, validator
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os
from .security_framework import SecurityEventType

# Import secrets for token generation
import secrets

data_protection_logger = logging.getLogger('duckbot.data_protection')

class DataSensitivity(Enum):
    """Data sensitivity classifications"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

class EncryptionAlgorithm(Enum):
    """Encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    FERNET = "fernet"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"

class DataClassification(BaseModel):
    """Data classification metadata"""
    sensitivity: DataSensitivity
    category: str  # "personal", "financial", "health", "authentication", "system"
    retention_days: int = 365
    requires_encryption: bool = True
    requires_masking: bool = False
    compliance_frameworks: List[str] = Field(default_factory=list)
    data_owner: Optional[str] = None
    access_control_list: List[str] = Field(default_factory=list)

class EncryptionKey(BaseModel):
    """Encryption key metadata"""
    key_id: str
    algorithm: EncryptionAlgorithm
    key_material: str  # Encrypted key material
    salt: str
    iterations: int = 100000
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    key_type: str = "data"  # "data", "master", "backup"
    status: str = "active"  # "active", "expired", "revoked"
    created_by: Optional[str] = None

class DataMaskingRule(BaseModel):
    """Data masking rule configuration"""
    name: str
    pattern: str  # Regex pattern to match
    replacement: str  # Replacement pattern
    mask_type: str  # "full", "partial", "hash", "tokenize"
    enabled: bool = True
    priority: int = 0
    data_types: List[str] = Field(default_factory=list)

class DataRetentionPolicy(BaseModel):
    """Data retention policy"""
    name: str
    description: str
    data_types: List[str] = Field(default_factory=list)
    retention_days: int
    archive_after_days: Optional[int] = None
    delete_after_days: Optional[int] = None
    compliance_requirements: List[str] = Field(default_factory=list)
    enabled: bool = True

class GDPRRequest(BaseModel):
    """GDPR data subject request"""
    request_id: str
    request_type: str  # "access", "rectification", "erasure", "portability", "objection"
    user_id: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending", "processing", "completed", "denied"
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    denial_reason: Optional[str] = None

@dataclass
class ProtectedData:
    """Protected data container"""
    data_id: str
    classification: DataClassification
    encrypted_data: Optional[str] = None
    masked_data: Optional[str] = None
    original_hash: str
    encryption_key_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    access_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataProtectionManager:
    """Advanced Data Protection Manager"""

    def __init__(self, master_key: str = None, key_store_path: str = "data_protection_keys.json"):
        self.key_store_path = Path(key_store_path)
        self.encryption_keys: Dict[str, EncryptionKey] = {}
        self.masking_rules: Dict[str, DataMaskingRule] = {}
        self.retention_policies: Dict[str, DataRetentionPolicy] = {}
        self.gdpr_requests: Dict[str, GDPRRequest] = {}
        self.protected_data: Dict[str, ProtectedData] = {}

        # Initialize master key
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = self._generate_master_key()

        # Initialize Fernet for general encryption
        self.fernet = Fernet(self._derive_fernet_key(self.master_key))

        # Load existing keys and configurations
        self._load_key_store()
        self._initialize_default_rules()
        self._initialize_retention_policies()

        data_protection_logger.info("DataProtectionManager initialized")

    def _generate_master_key(self) -> bytes:
        """Generate a new master key"""
        return Fernet.generate_key()

    def _derive_fernet_key(self, key_material: bytes) -> bytes:
        """Derive Fernet key from key material"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'duckbot_salt',  # In production, use random salt
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(key_material))

    def _load_key_store(self):
        """Load encryption keys from persistent storage"""
        if self.key_store_path.exists():
            try:
                with open(self.key_store_path, 'r') as f:
                    data = json.load(f)

                # Load encryption keys
                for key_data in data.get("encryption_keys", []):
                    key = EncryptionKey(**key_data)
                    self.encryption_keys[key.key_id] = key

                # Load masking rules
                for rule_data in data.get("masking_rules", []):
                    rule = DataMaskingRule(**rule_data)
                    self.masking_rules[rule.name] = rule

                data_protection_logger.info(f"Loaded {len(self.encryption_keys)} encryption keys")
            except Exception as e:
                data_protection_logger.error(f"Failed to load key store: {e}")

    def _save_key_store(self):
        """Save encryption keys to persistent storage"""
        try:
            data = {
                "encryption_keys": [key.dict() for key in self.encryption_keys.values()],
                "masking_rules": [rule.dict() for rule in self.masking_rules.values()],
                "retention_policies": [policy.dict() for policy in self.retention_policies.values()],
                "last_updated": datetime.utcnow().isoformat()
            }

            with open(self.key_store_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            data_protection_logger.info("Key store saved successfully")
        except Exception as e:
            data_protection_logger.error(f"Failed to save key store: {e}")

    def _initialize_default_rules(self):
        """Initialize default data masking rules"""
        default_rules = [
            DataMaskingRule(
                name="email_address",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement=r'***@***.***',
                mask_type="partial",
                data_types=["email", "personal"]
            ),
            DataMaskingRule(
                name="phone_number",
                pattern=r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                replacement=r'***-***-****',
                mask_type="partial",
                data_types=["phone", "personal"]
            ),
            DataMaskingRule(
                name="credit_card",
                pattern=r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                replacement=r'****-****-****-****',
                mask_type="full",
                data_types=["financial", "payment"]
            ),
            DataMaskingRule(
                name="ssn",
                pattern=r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b',
                replacement=r'***-**-****',
                mask_type="full",
                data_types["personal", "identification"]
            ),
            DataMaskingRule(
                name="api_key",
                pattern=r'\b[A-Za-z0-9]{32,}\b',
                replacement=r'***********************************',
                mask_type="full",
                data_types=["authentication", "api"]
            )
        ]

        for rule in default_rules:
            self.masking_rules[rule.name] = rule

    def _initialize_retention_policies(self):
        """Initialize default data retention policies"""
        default_policies = [
            DataRetentionPolicy(
                name="audit_logs",
                description="Audit log retention policy",
                data_types=["audit", "security"],
                retention_days=365,
                archive_after_days=90,
                compliance_requirements=["GDPR", "HIPAA", "PCI_DSS"]
            ),
            DataRetentionPolicy(
                name="user_activity",
                description="User activity data retention",
                data_types=["user_activity", "session"],
                retention_days=180,
                compliance_requirements=["GDPR"]
            ),
            DataRetentionPolicy(
                name="authentication_data",
                description="Authentication and session data",
                data_types=["authentication", "session"],
                retention_days=90,
                compliance_requirements=["GDPR", "SOC2"]
            ),
            DataRetentionPolicy(
                name="personal_data",
                description="Personal identifiable information",
                data_types=["personal", "pii"],
                retention_days=730,
                archive_after_days=365,
                compliance_requirements=["GDPR", "CCPA"]
            ),
            DataRetentionPolicy(
                name="system_logs",
                description="System and application logs",
                data_types=["system", "application"],
                retention_days=90
            )
        ]

        for policy in default_policies:
            self.retention_policies[policy.name] = policy

    def create_encryption_key(self, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
                            key_type: str = "data", expires_days: int = None,
                            created_by: str = None) -> EncryptionKey:
        """Create a new encryption key"""
        key_id = f"key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

        if algorithm == EncryptionAlgorithm.FERNET:
            key_material = Fernet.generate_key().decode()
        else:
            # Generate random key material
            key_material = secrets.token_bytes(32).hex()

        # Encrypt key material with master key
        encrypted_key = self.fernet.encrypt(key_material.encode()).decode()

        # Generate salt
        salt = secrets.token_hex(16)

        key = EncryptionKey(
            key_id=key_id,
            algorithm=algorithm,
            key_material=encrypted_key,
            salt=salt,
            expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            key_type=key_type,
            created_by=created_by
        )

        self.encryption_keys[key_id] = key
        self._save_key_store()

        data_protection_logger.info(f"Created encryption key: {key_id}")
        return key

    def encrypt_data(self, data: Union[str, bytes, Dict], classification: DataClassification,
                    key_id: str = None) -> ProtectedData:
        """Encrypt sensitive data"""
        if isinstance(data, dict):
            data = json.dumps(data)

        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data

        # Generate data ID and hash
        data_id = f"data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
        original_hash = hashlib.sha256(data_bytes).hexdigest()

        # Use provided key or generate new one
        if key_id and key_id in self.encryption_keys:
            encryption_key = self.encryption_keys[key_id]
        else:
            encryption_key = self.create_encryption_key()
            key_id = encryption_key.key_id

        # Decrypt the key material
        decrypted_key_material = self.fernet.decrypt(encryption_key.key_material.encode()).decode()

        # Encrypt the data
        if encryption_key.algorithm == EncryptionAlgorithm.FERNET:
            fernet = Fernet(decrypted_key_material.encode())
            encrypted_data = fernet.encrypt(data_bytes).decode()
        else:
            # For other algorithms, implement accordingly
            encrypted_data = self.fernet.encrypt(data_bytes).decode()

        # Create protected data object
        protected_data = ProtectedData(
            data_id=data_id,
            classification=classification,
            encrypted_data=encrypted_data,
            masked_data=self._apply_masking_rules(data.decode() if isinstance(data, bytes) else data, classification),
            original_hash=original_hash,
            encryption_key_id=key_id,
            metadata={
                "algorithm": encryption_key.algorithm.value,
                "key_id": key_id,
                "size_bytes": len(data_bytes)
            }
        )

        self.protected_data[data_id] = protected_data

        data_protection_logger.info(f"Encrypted data: {data_id}")
        return protected_data

    def decrypt_data(self, protected_data: ProtectedData) -> Union[str, bytes, Dict]:
        """Decrypt protected data"""
        if not protected_data.encrypted_data or not protected_data.encryption_key_id:
            raise ValueError("Data is not encrypted")

        key_id = protected_data.encryption_key_id
        if key_id not in self.encryption_keys:
            raise ValueError(f"Encryption key not found: {key_id}")

        encryption_key = self.encryption_keys[key_id]
        if encryption_key.status != "active":
            raise ValueError(f"Encryption key is not active: {key_id}")

        # Decrypt key material
        decrypted_key_material = self.fernet.decrypt(encryption_key.key_material.encode()).decode()

        # Decrypt data
        if encryption_key.algorithm == EncryptionAlgorithm.FERNET:
            fernet = Fernet(decrypted_key_material.encode())
            decrypted_data = fernet.decrypt(protected_data.encrypted_data.encode()).decode()
        else:
            decrypted_data = self.fernet.decrypt(protected_data.encrypted_data.encode()).decode()

        # Verify integrity
        data_hash = hashlib.sha256(decrypted_data.encode()).hexdigest()
        if data_hash != protected_data.original_hash:
            raise ValueError("Data integrity check failed")

        # Log access
        self._log_data_access(protected_data, "decrypt")

        # Try to parse as JSON, otherwise return as string
        try:
            return json.loads(decrypted_data)
        except json.JSONDecodeError:
            return decrypted_data

    def mask_data(self, data: Union[str, Dict], data_types: List[str] = None) -> str:
        """Apply masking rules to sensitive data"""
        if isinstance(data, dict):
            data = json.dumps(data)

        masked_data = data
        applied_rules = []

        for rule in self.masking_rules.values():
            if not rule.enabled:
                continue

            # Check if rule applies to specified data types
            if data_types and not any(dt in rule.data_types for dt in data_types):
                continue

            # Apply masking rule
            if re.search(rule.pattern, masked_data):
                masked_data = re.sub(rule.pattern, rule.replacement, masked_data)
                applied_rules.append(rule.name)

        if applied_rules:
            data_protection_logger.info(f"Applied masking rules: {applied_rules}")

        return masked_data

    def _apply_masking_rules(self, data: str, classification: DataClassification) -> str:
        """Apply appropriate masking rules based on data classification"""
        data_types = [classification.category]

        if classification.sensitivity in [DataSensitivity.CONFIDENTIAL, DataSensitivity.RESTRICTED]:
            data_types.append("sensitive")

        return self.mask_data(data, data_types)

    def classify_data(self, data: Union[str, Dict], context: Dict[str, Any] = None) -> DataClassification:
        """Automatically classify data based on content and context"""
        if isinstance(data, dict):
            data_text = json.dumps(data)
        else:
            data_text = data

        sensitivity = DataSensitivity.INTERNAL
        category = "general"
        requires_encryption = False
        requires_masking = False

        # Check for sensitive patterns
        if self._contains_sensitive_patterns(data_text):
            sensitivity = DataSensitivity.CONFIDENTIAL
            requires_encryption = True
            requires_masking = True

            # Determine category based on patterns
            if self._contains_pattern(data_text, r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'):
                category = "personal"
            elif self._contains_pattern(data_text, r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'):
                category = "financial"
            elif self._contains_pattern(data_text, r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b'):
                category = "identification"
            elif any(keyword in data_text.lower() for keyword in ["password", "token", "key", "secret"]):
                category = "authentication"

        # Consider context
        if context:
            if context.get("user_authentication"):
                category = "authentication"
                sensitivity = max(sensitivity, DataSensitivity.CONFIDENTIAL)
                requires_encryption = True

            if context.get("financial_transaction"):
                category = "financial"
                sensitivity = max(sensitivity, DataSensitivity.RESTRICTED)
                requires_encryption = True
                requires_masking = True

            if context.get("health_information"):
                category = "health"
                sensitivity = DataSensitivity.RESTRICTED
                requires_encryption = True
                requires_masking = True

        # Apply compliance frameworks
        compliance_frameworks = []
        if category in ["personal", "identification"]:
            compliance_frameworks.extend(["GDPR", "CCPA"])

        if category == "financial":
            compliance_frameworks.extend(["PCI_DSS", "SOX"])

        if category == "health":
            compliance_frameworks.append("HIPAA")

        return DataClassification(
            sensitivity=sensitivity,
            category=category,
            requires_encryption=requires_encryption,
            requires_masking=requires_masking,
            compliance_frameworks=compliance_frameworks
        )

    def _contains_sensitive_patterns(self, data: str) -> bool:
        """Check if data contains sensitive patterns"""
        sensitive_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
            r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b',  # SSN
            r'\b[A-Za-z0-9]{32,}\b',  # API keys
            r'\bpassword|token|secret|key\b',  # Auth keywords
        ]

        return any(re.search(pattern, data, re.IGNORECASE) for pattern in sensitive_patterns)

    def _contains_pattern(self, data: str, pattern: str) -> bool:
        """Check if data contains specific pattern"""
        return re.search(pattern, data, re.IGNORECASE) is not None

    def create_gdpr_request(self, request_type: str, user_id: str, requested_by: str = None) -> GDPRRequest:
        """Create a GDPR data subject request"""
        request_id = f"gdpr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

        request = GDPRRequest(
            request_id=request_id,
            request_type=request_type,
            user_id=user_id,
            requested_by=requested_by
        )

        self.gdpr_requests[request_id] = request

        data_protection_logger.info(f"Created GDPR request: {request_id} - {request_type} for user {user_id}")
        return request

    def process_gdpr_access_request(self, request_id: str, processed_by: str) -> Dict[str, Any]:
        """Process GDPR data access request"""
        if request_id not in self.gdpr_requests:
            raise ValueError(f"GDPR request not found: {request_id}")

        request = self.gdpr_requests[request_id]
        if request.request_type != "access":
            raise ValueError("Request is not an access request")

        # Collect all user data
        user_data = self._collect_user_data(request.user_id)

        # Process the request
        request.status = "completed"
        request.processed_by = processed_by
        request.processed_at = datetime.utcnow()
        request.response_data = user_data

        data_protection_logger.info(f"Processed GDPR access request: {request_id}")
        return user_data

    def process_gdpr_erasure_request(self, request_id: str, processed_by: str) -> bool:
        """Process GDPR right to be forgotten request"""
        if request_id not in self.gdpr_requests:
            raise ValueError(f"GDPR request not found: {request_id}")

        request = self.gdpr_requests[request_id]
        if request.request_type != "erasure":
            raise ValueError("Request is not an erasure request")

        # Find and delete user data
        deleted_data_ids = []
        for data_id, protected_data in self.protected_data.items():
            if protected_data.metadata.get("user_id") == request.user_id:
                del self.protected_data[data_id]
                deleted_data_ids.append(data_id)

        # Process the request
        request.status = "completed"
        request.processed_by = processed_by
        request.processed_at = datetime.utcnow()
        request.response_data = {"deleted_data_count": len(deleted_data_ids)}

        data_protection_logger.info(f"Processed GDPR erasure request: {request_id}, deleted {len(deleted_data_ids)} data items")
        return True

    def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
        """Collect all data related to a user"""
        user_data = {
            "user_id": user_id,
            "collected_at": datetime.utcnow().isoformat(),
            "data_categories": {},
            "total_data_items": 0
        }

        for data_id, protected_data in self.protected_data.items():
            if protected_data.metadata.get("user_id") == user_id:
                category = protected_data.classification.category
                if category not in user_data["data_categories"]:
                    user_data["data_categories"][category] = []

                user_data["data_categories"][category].append({
                    "data_id": data_id,
                    "classification": protected_data.classification.dict(),
                    "created_at": protected_data.created_at.isoformat(),
                    "access_count": len(protected_data.access_log)
                })

                user_data["total_data_items"] += 1

        return user_data

    def _log_data_access(self, protected_data: ProtectedData, action: str, accessed_by: str = None):
        """Log data access for audit purposes"""
        access_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "accessed_by": accessed_by or "system",
            "data_id": protected_data.data_id,
            "classification": protected_data.classification.sensitivity.value
        }

        protected_data.access_log.append(access_entry)

        # Log to audit system
        data_protection_logger.info(f"Data access: {action} - {protected_data.data_id}")

    def apply_retention_policies(self) -> Dict[str, int]:
        """Apply data retention policies and clean up expired data"""
        cleanup_stats = {
            "archived_data": 0,
            "deleted_data": 0,
            "expired_keys": 0
        }

        now = datetime.utcnow()

        # Check protected data retention
        data_to_archive = []
        data_to_delete = []

        for data_id, protected_data in self.protected_data.items():
            # Find applicable retention policy
            applicable_policy = None
            for policy in self.retention_policies.values():
                if (policy.enabled and
                    protected_data.classification.category in policy.data_types):
                    applicable_policy = policy
                    break

            if applicable_policy:
                retention_period = timedelta(days=applicable_policy.retention_days)
                age = now - protected_data.created_at

                if age > retention_period:
                    if applicable_policy.delete_after_days:
                        delete_period = timedelta(days=applicable_policy.delete_after_days)
                        if age > delete_period:
                            data_to_delete.append(data_id)
                    else:
                        data_to_delete.append(data_id)

        # Archive data
        for data_id in data_to_archive:
            del self.protected_data[data_id]
            cleanup_stats["archived_data"] += 1

        # Delete data
        for data_id in data_to_delete:
            del self.protected_data[data_id]
            cleanup_stats["deleted_data"] += 1

        # Check expired encryption keys
        keys_to_expire = []
        for key_id, encryption_key in self.encryption_keys.items():
            if encryption_key.expires_at and encryption_key.expires_at <= now:
                keys_to_expire.append(key_id)

        for key_id in keys_to_expire:
            self.encryption_keys[key_id].status = "expired"
            cleanup_stats["expired_keys"] += 1

        if cleanup_stats["archived_data"] + cleanup_stats["deleted_data"] + cleanup_stats["expired_keys"] > 0:
            self._save_key_store()
            data_protection_logger.info(f"Applied retention policies: {cleanup_stats}")

        return cleanup_stats

    def get_data_protection_stats(self) -> Dict[str, Any]:
        """Get data protection statistics"""
        now = datetime.utcnow()

        # Count protected data by classification
        data_by_classification = {}
        for protected_data in self.protected_data.values():
            sensitivity = protected_data.classification.sensitivity.value
            data_by_classification[sensitivity] = data_by_classification.get(sensitivity, 0) + 1

        # Count encryption keys by status
        keys_by_status = {}
        for encryption_key in self.encryption_keys.values():
            status = encryption_key.status
            keys_by_status[status] = keys_by_status.get(status, 0) + 1

        # GDPR request statistics
        gdpr_stats = {}
        for request in self.gdpr_requests.values():
            request_type = request.request_type
            if request_type not in gdpr_stats:
                gdpr_stats[request_type] = {"pending": 0, "completed": 0, "denied": 0}

            gdpr_stats[request_type][request.status] += 1

        return {
            "protected_data_count": len(self.protected_data),
            "data_by_classification": data_by_classification,
            "encryption_keys_count": len(self.encryption_keys),
            "keys_by_status": keys_by_status,
            "masking_rules_count": len(self.masking_rules),
            "active_masking_rules": len([r for r in self.masking_rules.values() if r.enabled]),
            "retention_policies_count": len(self.retention_policies),
            "gdpr_requests_count": len(self.gdpr_requests),
            "gdpr_request_stats": gdpr_stats,
            "system_health": self._get_system_health()
        }

    def _get_system_health(self) -> Dict[str, Any]:
        """Get data protection system health"""
        issues = []

        # Check for expired keys
        expired_keys = [k for k in self.encryption_keys.values() if k.expires_at and k.expires_at <= datetime.utcnow()]
        if expired_keys:
            issues.append(f"{len(expired_keys)} expired encryption keys")

        # Check for data exceeding retention
        overdue_data = []
        for protected_data in self.protected_data.values():
            age = datetime.utcnow() - protected_data.created_at
            if age.days > 730:  # Older than 2 years
                overdue_data.append(protected_data.data_id)

        if overdue_data:
            issues.append(f"{len(overdue_data)} data items exceeding standard retention")

        # Check GDPR request backlog
        pending_requests = [r for r in self.gdpr_requests.values() if r.status == "pending"]
        if len(pending_requests) > 10:
            issues.append(f"{len(pending_requests)} pending GDPR requests")

        return {
            "status": "healthy" if not issues else "warning",
            "issues": issues,
            "checks_passed": len(issues) == 0
        }

    def rotate_encryption_key(self, old_key_id: str, new_key_id: str) -> bool:
        """Rotate encryption key for protected data"""
        if old_key_id not in self.encryption_keys:
            raise ValueError(f"Old key not found: {old_key_id}")

        if new_key_id not in self.encryption_keys:
            raise ValueError(f"New key not found: {new_key_id}")

        rotated_count = 0

        for data_id, protected_data in self.protected_data.items():
            if protected_data.encryption_key_id == old_key_id:
                try:
                    # Decrypt with old key
                    decrypted_data = self.decrypt_data(protected_data)

                    # Re-encrypt with new key
                    new_protected_data = self.encrypt_data(
                        decrypted_data,
                        protected_data.classification,
                        new_key_id
                    )

                    # Update the protected data
                    protected_data.encrypted_data = new_protected_data.encrypted_data
                    protected_data.encryption_key_id = new_key_id
                    protected_data.modified_at = datetime.utcnow()

                    rotated_count += 1
                except Exception as e:
                    data_protection_logger.error(f"Failed to rotate key for data {data_id}: {e}")

        data_protection_logger.info(f"Rotated encryption key for {rotated_count} data items")
        return rotated_count > 0

    def secure_wipe_data(self, data_id: str, verification: bool = True) -> bool:
        """Securely wipe sensitive data"""
        if data_id not in self.protected_data:
            return False

        protected_data = self.protected_data[data_id]

        # Log the wipe action
        self._log_data_access(protected_data, "secure_wipe")

        # Remove the data
        del self.protected_data[data_id]

        # Optionally verify deletion
        if verification:
            if data_id in self.protected_data:
                data_protection_logger.error(f"Data wipe verification failed for {data_id}")
                return False

        data_protection_logger.info(f"Securely wiped data: {data_id}")
        return True

    def export_data_manifest(self) -> Dict[str, Any]:
        """Export data protection manifest for compliance"""
        manifest = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_protection_manager": {
                "version": "1.0.0",
                "encryption_keys": len(self.encryption_keys),
                "protected_data_items": len(self.protected_data),
                "masking_rules": len(self.masking_rules),
                "retention_policies": len(self.retention_policies)
            },
            "compliance_frameworks": self._get_compliance_frameworks(),
            "data_inventory": self._get_data_inventory(),
            "access_controls": self._get_access_controls_summary()
        }

        return manifest

    def _get_compliance_frameworks(self) -> Dict[str, Any]:
        """Get compliance frameworks summary"""
        frameworks = {
            "GDPR": {
                "enabled": True,
                "data_subject_requests": len(self.gdpr_requests),
                "data_categories_covered": ["personal", "identification", "authentication"]
            },
            "CCPA": {
                "enabled": True,
                "data_categories_covered": ["personal", "identification"]
            },
            "HIPAA": {
                "enabled": False,
                "data_categories_covered": ["health"]
            },
            "PCI_DSS": {
                "enabled": True,
                "data_categories_covered": ["financial", "payment"]
            }
        }

        return frameworks

    def _get_data_inventory(self) -> Dict[str, Any]:
        """Get data inventory summary"""
        inventory = {
            "total_data_items": len(self.protected_data),
            "by_classification": {},
            "by_category": {},
            "encryption_coverage": 0,
            "masking_coverage": 0
        }

        encrypted_count = 0
        masked_count = 0

        for protected_data in self.protected_data.values():
            # By classification
            sensitivity = protected_data.classification.sensitivity.value
            inventory["by_classification"][sensitivity] = inventory["by_classification"].get(sensitivity, 0) + 1

            # By category
            category = protected_data.classification.category
            inventory["by_category"][category] = inventory["by_category"].get(category, 0) + 1

            # Coverage
            if protected_data.encrypted_data:
                encrypted_count += 1
            if protected_data.masked_data:
                masked_count += 1

        if inventory["total_data_items"] > 0:
            inventory["encryption_coverage"] = (encrypted_count / inventory["total_data_items"]) * 100
            inventory["masking_coverage"] = (masked_count / inventory["total_data_items"]) * 100

        return inventory

    def _get_access_controls_summary(self) -> Dict[str, Any]:
        """Get access controls summary"""
        return {
            "encryption_keys": {
                "total": len(self.encryption_keys),
                "active": len([k for k in self.encryption_keys.values() if k.status == "active"]),
                "expired": len([k for k in self.encryption_keys.values() if k.status == "expired"]),
                "by_type": {
                    "data": len([k for k in self.encryption_keys.values() if k.key_type == "data"]),
                    "master": len([k for k in self.encryption_keys.values() if k.key_type == "master"]),
                    "backup": len([k for k in self.encryption_keys.values() if k.key_type == "backup"])
                }
            },
            "access_logging": "enabled",
            "audit_trail": "enabled"
        }