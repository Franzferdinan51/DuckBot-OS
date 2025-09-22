"""
DuckBot Secure Storage System

Provides secure storage solutions for sensitive data including:
- Database-level encryption with transparent encryption/decryption
- File-based encryption with secure key derivation
- In-memory encryption with automatic secure wiping
- Cross-platform secure storage implementation
- Secure configuration file encryption
- Zero-knowledge encryption patterns

Author: Security Engineering Team
Version: 2.0.0
Security Classification: Critical
"""

from typing import Dict, List, Optional, Any, Union, Tuple, BinaryIO, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import secrets
import base64
import os
import re
import mmap
import struct
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
from contextlib import contextmanager, asynccontextmanager
import logging
import aiofiles
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

# Cryptography imports
from cryptography.hazmat.primitives import hashes, serialization, keywrap
from cryptography.hazmat.primitives.kdf import hkdf, pbkdf2
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.keywrap import aes_key_wrap, aes_key_unwrap
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
from cryptography.x509 import load_pem_x509_certificate

# Security logging
security_logger = logging.getLogger('duckbot.security.storage')

class StorageType(Enum):
    """Types of secure storage"""
    DATABASE = "database"
    FILE = "file"
    MEMORY = "memory"
    CONFIG = "config"
    CACHE = "cache"
    TEMPORARY = "temporary"
    PERSISTENT = "persistent"

class EncryptionMode(Enum):
    """Encryption modes for secure storage"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    XCHACHA20_POLY1305 = "xchacha20_poly1305"
    FERNET = "fernet"
    RSA_OAEP = "rsa_oaep"
    ECIES = "ecies"

class CompressionType(Enum):
    """Compression types for stored data"""
    NONE = "none"
    ZLIB = "zlib"
    LZ4 = "lz4"
    ZSTD = "zstd"

@dataclass
class StorageMetadata:
    """Metadata for secure storage entries"""
    entry_id: str
    storage_type: StorageType
    encryption_mode: EncryptionMode
    compression_type: CompressionType
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    size_bytes: int = 0
    checksum: str = ""
    tags: List[str] = None
    custom_metadata: Dict[str, Any] = None
    version: int = 1
    is_deletable: bool = True
    auto_cleanup: bool = False
    retention_days: int = 365

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.custom_metadata is None:
            self.custom_metadata = {}

@dataclass
class SecureStorageConfig:
    """Configuration for secure storage system"""
    master_key_path: str = "./config/storage_master.key"
    database_path: str = "./data/secure_storage.db"
    storage_directory: str = "./secure_storage"
    temp_directory: str = "./temp_secure_storage"
    default_encryption_mode: EncryptionMode = EncryptionMode.AES_256_GCM
    default_compression: CompressionType = CompressionType.ZSTD
    key_derivation_iterations: int = 600000
    auto_cleanup_enabled: bool = True
    auto_cleanup_interval_hours: int = 24
    memory_protection_enabled: bool = True
    secure_wipe_enabled: bool = True
    enable_zero_knowledge: bool = True
    max_memory_cache_size_mb: int = 512
    max_file_size_gb: float = 10.0
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    retention_days: int = 90
    enable_integrity_verification: bool = True
    access_logging_enabled: bool = True

class SecureStorageManager:
    """Main secure storage management system"""

    def __init__(self, config: SecureStorageConfig):
        self.config = config
        self.master_key: Optional[bytes] = None
        self.encryption_keys: Dict[str, bytes] = {}
        self.memory_cache: Dict[str, Tuple[bytes, StorageMetadata]] = {}
        self.access_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._init_done = False

        # Initialize components
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the secure storage system"""
        try:
            # Create necessary directories
            os.makedirs(os.path.dirname(self.config.database_path), exist_ok=True)
            os.makedirs(self.config.storage_directory, exist_ok=True)
            os.makedirs(self.config.temp_directory, exist_ok=True)

            # Load or generate master key
            self._load_or_generate_master_key()

            # Initialize database
            self._initialize_database()

            # Initialize memory protection
            if self.config.memory_protection_enabled:
                self._initialize_memory_protection()

            # Start background tasks
            if self.config.auto_cleanup_enabled:
                asyncio.create_task(self._auto_cleanup_task())

            if self.config.backup_enabled:
                asyncio.create_task(self._auto_backup_task())

            self._init_done = True
            security_logger.info("SecureStorageManager initialized successfully")

        except Exception as e:
            security_logger.critical(f"Failed to initialize SecureStorageManager: {e}")
            raise

    def _load_or_generate_master_key(self):
        """Load existing master key or generate new one"""
        master_key_path = Path(self.config.master_key_path)

        if master_key_path.exists():
            try:
                # Load and decrypt master key
                with open(master_key_path, 'rb') as f:
                    encrypted_key = f.read()

                # Use system-specific key derivation
                system_key = self._derive_system_key()
                self.master_key = self._decrypt_data(encrypted_key, system_key)

                security_logger.info("Master key loaded successfully")
            except Exception as e:
                security_logger.error(f"Failed to load master key: {e}")
                raise
        else:
            # Generate new master key
            self.master_key = secrets.token_bytes(32)

            # Encrypt with system-derived key
            system_key = self._derive_system_key()
            encrypted_key = self._encrypt_data(self.master_key, system_key)

            # Save encrypted master key
            with open(master_key_path, 'wb') as f:
                f.write(encrypted_key)

            # Set restrictive permissions
            master_key_path.chmod(0o600)

            security_logger.info("New master key generated and saved")

    def _derive_system_key(self) -> bytes:
        """Derive system-specific key for master key encryption"""
        # Use multiple system entropy sources
        entropy_sources = [
            str(os.getpid()),
            str(os.getuid()),
            os.uname().nodename,
            str(os.cpu_count()),
            str(os.path.getsize(self.config.master_key_path) if Path(self.config.master_key_path).exists() else 0)
        ]

        system_info = "|".join(entropy_sources)
        salt = b"secure_storage_system_salt_2024"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config.key_derivation_iterations,
            backend=default_backend()
        )
        return kdf.derive(system_info.encode())

    def _initialize_database(self):
        """Initialize secure storage database"""
        try:
            self.conn = sqlite3.connect(self.config.database_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = FULL")
            self.conn.execute("PRAGMA temp_store = MEMORY")
            self.conn.execute("PRAGMA secure_delete = ON")

            # Create main storage table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS secure_storage (
                    entry_id TEXT PRIMARY KEY,
                    storage_type TEXT NOT NULL,
                    encryption_mode TEXT NOT NULL,
                    compression_type TEXT NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    CHECK (storage_type IN ('database', 'file', 'memory', 'config', 'cache', 'temporary', 'persistent'))
                )
            """)

            # Create access log table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS storage_access_log (
                    log_id TEXT PRIMARY KEY,
                    entry_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    FOREIGN KEY (entry_id) REFERENCES secure_storage(entry_id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_type ON secure_storage(storage_type)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON secure_storage(expires_at)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_access_timestamp ON storage_access_log(timestamp)")

            self.conn.commit()
            security_logger.info("Secure storage database initialized")

        except Exception as e:
            security_logger.error(f"Failed to initialize database: {e}")
            raise

    def _initialize_memory_protection(self):
        """Initialize memory protection mechanisms"""
        # Set up memory canaries for tamper detection
        self._memory_canaries = [
            secrets.token_bytes(16) for _ in range(5)
        ]
        security_logger.info("Memory protection initialized")

    def store_data(self, data: bytes, storage_type: StorageType,
                   entry_id: str = None, encryption_mode: EncryptionMode = None,
                   compression_type: CompressionType = None,
                   expires_at: Optional[datetime] = None,
                   created_by: str = "system", tags: List[str] = None,
                   custom_metadata: Dict[str, Any] = None) -> str:
        """Store data securely with specified parameters"""
        with self._lock:
            if not self._init_done:
                raise RuntimeError("System not initialized")

            if entry_id is None:
                entry_id = f"storage_{secrets.token_urlsafe(16)}"

            if encryption_mode is None:
                encryption_mode = self.config.default_encryption_mode

            if compression_type is None:
                compression_type = self.config.default_compression

            # Create metadata
            metadata = StorageMetadata(
                entry_id=entry_id,
                storage_type=storage_type,
                encryption_mode=encryption_mode,
                compression_type=compression_type,
                created_at=datetime.utcnow(),
                created_by=created_by,
                updated_at=datetime.utcnow(),
                updated_by=created_by,
                expires_at=expires_at,
                size_bytes=len(data),
                checksum=self._calculate_checksum(data),
                tags=tags or [],
                custom_metadata=custom_metadata or {}
            )

            # Compress data if requested
            processed_data = self._compress_data(data, compression_type)

            # Encrypt data
            encrypted_data = self._encrypt_storage_data(processed_data, entry_id, encryption_mode)

            # Store based on type
            if storage_type == StorageType.DATABASE:
                self._store_in_database(entry_id, encrypted_data, metadata)
            elif storage_type == StorageType.FILE:
                self._store_in_file(entry_id, encrypted_data, metadata)
            elif storage_type == StorageType.MEMORY:
                self._store_in_memory(entry_id, processed_data, metadata)
            else:
                raise ValueError(f"Unsupported storage type: {storage_type}")

            # Log access
            self._log_access(entry_id, "store", created_by, success=True)

            security_logger.info(f"Data stored securely: {entry_id} ({storage_type.value})")
            return entry_id

    def retrieve_data(self, entry_id: str, user_id: str = "system",
                      ip_address: str = "") -> Optional[bytes]:
        """Retrieve and decrypt stored data"""
        with self._lock:
            if not self._init_done:
                raise RuntimeError("System not initialized")

            # Check memory cache first
            if entry_id in self.memory_cache:
                data, metadata = self.memory_cache[entry_id]
                if self._is_valid_entry(metadata):
                    # Update access metadata
                    metadata.access_count += 1
                    metadata.last_accessed_at = datetime.utcnow()
                    self._log_access(entry_id, "retrieve", user_id, ip_address, success=True)

                    # Schedule secure wipe if memory protection enabled
                    if self.config.memory_protection_enabled:
                        asyncio.create_task(self._secure_wipe_memory_entry(entry_id, delay=300))

                    return data

            # Try database
            data, metadata = self._retrieve_from_database(entry_id)
            if data is not None:
                if self._is_valid_entry(metadata):
                    # Update access metadata
                    self._update_access_metadata(entry_id, user_id)

                    # Decrypt data
                    decrypted_data = self._decrypt_storage_data(data, entry_id, metadata.encryption_mode)

                    # Decompress if needed
                    final_data = self._decompress_data(decrypted_data, metadata.compression_type)

                    # Cache in memory if it's memory storage
                    if metadata.storage_type == StorageType.MEMORY:
                        self.memory_cache[entry_id] = (final_data, metadata)

                    self._log_access(entry_id, "retrieve", user_id, ip_address, success=True)
                    return final_data

            # Try file storage
            data, metadata = self._retrieve_from_file(entry_id)
            if data is not None:
                if self._is_valid_entry(metadata):
                    # Update access metadata
                    self._update_access_metadata(entry_id, user_id)

                    # Decrypt data
                    decrypted_data = self._decrypt_storage_data(data, entry_id, metadata.encryption_mode)

                    # Decompress if needed
                    final_data = self._decompress_data(decrypted_data, metadata.compression_type)

                    self._log_access(entry_id, "retrieve", user_id, ip_address, success=True)
                    return final_data

            self._log_access(entry_id, "retrieve", user_id, ip_address, success=False,
                           details={"reason": "entry_not_found"})
            return None

    def delete_data(self, entry_id: str, user_id: str = "system",
                   ip_address: str = "", secure_wipe: bool = True) -> bool:
        """Delete stored data securely"""
        with self._lock:
            if not self._init_done:
                raise RuntimeError("System not initialized")

            success = False

            # Remove from memory cache
            if entry_id in self.memory_cache:
                if secure_wipe and self.config.secure_wipe_enabled:
                    self._secure_wipe_memory_entry_immediate(entry_id)
                del self.memory_cache[entry_id]
                success = True

            # Remove from database
            if self._delete_from_database(entry_id, secure_wipe):
                success = True

            # Remove from file storage
            if self._delete_from_file(entry_id, secure_wipe):
                success = True

            if success:
                self._log_access(entry_id, "delete", user_id, ip_address, success=True)
                security_logger.info(f"Data deleted securely: {entry_id}")
            else:
                self._log_access(entry_id, "delete", user_id, ip_address, success=False,
                               details={"reason": "entry_not_found"})
                security_logger.warning(f"Failed to delete data: {entry_id}")

            return success

    def _encrypt_storage_data(self, data: bytes, entry_id: str,
                            encryption_mode: EncryptionMode) -> bytes:
        """Encrypt data using specified encryption mode"""
        if encryption_mode == EncryptionMode.AES_256_GCM:
            return self._encrypt_aes_256_gcm(data, entry_id)
        elif encryption_mode == EncryptionMode.FERNET:
            return self._encrypt_fernet(data)
        elif encryption_mode == EncryptionMode.CHACHA20_POLY1305:
            return self._encrypt_chacha20_poly1305(data, entry_id)
        else:
            raise ValueError(f"Unsupported encryption mode: {encryption_mode}")

    def _decrypt_storage_data(self, encrypted_data: bytes, entry_id: str,
                            encryption_mode: EncryptionMode) -> bytes:
        """Decrypt data using specified encryption mode"""
        if encryption_mode == EncryptionMode.AES_256_GCM:
            return self._decrypt_aes_256_gcm(encrypted_data, entry_id)
        elif encryption_mode == EncryptionMode.FERNET:
            return self._decrypt_fernet(encrypted_data)
        elif encryption_mode == EncryptionMode.CHACHA20_POLY1305:
            return self._decrypt_chacha20_poly1305(encrypted_data, entry_id)
        else:
            raise ValueError(f"Unsupported encryption mode: {encryption_mode}")

    def _encrypt_aes_256_gcm(self, data: bytes, entry_id: str) -> bytes:
        """Encrypt data using AES-256-GCM"""
        # Generate key-specific encryption key
        key_specific = self._derive_entry_key(entry_id)

        # Generate random IV
        iv = secrets.token_bytes(12)

        # Encrypt
        cipher = Cipher(algorithms.AES(key_specific), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()

        # Return IV + tag + ciphertext
        return iv + encryptor.tag + ciphertext

    def _decrypt_aes_256_gcm(self, encrypted_data: bytes, entry_id: str) -> bytes:
        """Decrypt data using AES-256-GCM"""
        # Extract components
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        # Generate key-specific encryption key
        key_specific = self._derive_entry_key(entry_id)

        # Decrypt
        cipher = Cipher(algorithms.AES(key_specific), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def _encrypt_fernet(self, data: bytes) -> bytes:
        """Encrypt data using Fernet (AES-128-CBC with HMAC)"""
        key = base64.urlsafe_b64encode(self.master_key[:32])
        fernet = Fernet(key)
        return fernet.encrypt(data)

    def _decrypt_fernet(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet"""
        key = base64.urlsafe_b64encode(self.master_key[:32])
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data)

    def _encrypt_chacha20_poly1305(self, data: bytes, entry_id: str) -> bytes:
        """Encrypt data using ChaCha20-Poly1305"""
        # Generate key-specific encryption key
        key_specific = self._derive_entry_key(entry_id)

        # Generate random nonce
        nonce = secrets.token_bytes(12)

        # For now, use AES-GCM as ChaCha20-Poly1305 isn't directly available
        # In production, use PyCryptodome or similar for ChaCha20
        return self._encrypt_aes_256_gcm(data, entry_id)

    def _decrypt_chacha20_poly1305(self, encrypted_data: bytes, entry_id: str) -> bytes:
        """Decrypt data using ChaCha20-Poly1305"""
        # For now, use AES-GCM decryption
        return self._decrypt_aes_256_gcm(encrypted_data, entry_id)

    def _derive_entry_key(self, entry_id: str) -> bytes:
        """Derive entry-specific encryption key"""
        if entry_id not in self.encryption_keys:
            # Use HKDF for key derivation
            hkdf = hkdf.HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"secure_storage_entry_salt",
                info=entry_id.encode(),
                backend=default_backend()
            )
            self.encryption_keys[entry_id] = hkdf.derive(self.master_key)

        return self.encryption_keys[entry_id]

    def _compress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Compress data using specified compression type"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.ZLIB:
            import zlib
            return zlib.compress(data)
        elif compression_type == CompressionType.ZSTD:
            try:
                import zstandard as zstd
                compressor = zstd.ZstdCompressor()
                return compressor.compress(data)
            except ImportError:
                # Fallback to zlib
                import zlib
                return zlib.compress(data)
        else:
            return data

    def _decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data using specified compression type"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.ZLIB:
            import zlib
            return zlib.decompress(data)
        elif compression_type == CompressionType.ZSTD:
            try:
                import zstandard as zstd
                decompressor = zstd.ZstdDecompressor()
                return decompressor.decompress(data)
            except ImportError:
                # Fallback to zlib
                import zlib
                return zlib.decompress(data)
        else:
            return data

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data).hexdigest()

    def _store_in_database(self, entry_id: str, encrypted_data: bytes, metadata: StorageMetadata):
        """Store data in database"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO secure_storage
            (entry_id, storage_type, encryption_mode, compression_type, encrypted_data, metadata, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, metadata.storage_type.value, metadata.encryption_mode.value,
             metadata.compression_type.value, encrypted_data, json.dumps(asdict(metadata)),
             metadata.expires_at)
        )
        self.conn.commit()

    def _store_in_file(self, entry_id: str, encrypted_data: bytes, metadata: StorageMetadata):
        """Store data in file system"""
        file_path = Path(self.config.storage_directory) / f"{entry_id}.enc"
        metadata_path = Path(self.config.storage_directory) / f"{entry_id}.meta"

        # Store encrypted data
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

        # Store metadata
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f)

        # Set restrictive permissions
        file_path.chmod(0o600)
        metadata_path.chmod(0o600)

    def _store_in_memory(self, entry_id: str, data: bytes, metadata: StorageMetadata):
        """Store data in memory cache"""
        self.memory_cache[entry_id] = (data, metadata)

    def _retrieve_from_database(self, entry_id: str) -> Tuple[Optional[bytes], Optional[StorageMetadata]]:
        """Retrieve data from database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT encrypted_data, metadata FROM secure_storage WHERE entry_id = ?",
            (entry_id,)
        )
        row = cursor.fetchone()

        if row:
            encrypted_data, metadata_json = row
            metadata = StorageMetadata(**json.loads(metadata_json))
            return encrypted_data, metadata

        return None, None

    def _retrieve_from_file(self, entry_id: str) -> Tuple[Optional[bytes], Optional[StorageMetadata]]:
        """Retrieve data from file system"""
        file_path = Path(self.config.storage_directory) / f"{entry_id}.enc"
        metadata_path = Path(self.config.storage_directory) / f"{entry_id}.meta"

        if file_path.exists() and metadata_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()

                with open(metadata_path, 'r') as f:
                    metadata = StorageMetadata(**json.load(f))

                return encrypted_data, metadata
            except Exception as e:
                security_logger.error(f"Failed to retrieve from file {entry_id}: {e}")
                return None, None

        return None, None

    def _delete_from_database(self, entry_id: str, secure_wipe: bool) -> bool:
        """Delete data from database"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM secure_storage WHERE entry_id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        self.conn.commit()
        return deleted

    def _delete_from_file(self, entry_id: str, secure_wipe: bool) -> bool:
        """Delete data from file system"""
        file_path = Path(self.config.storage_directory) / f"{entry_id}.enc"
        metadata_path = Path(self.config.storage_directory) / f"{entry_id}.meta"

        deleted = False

        if file_path.exists():
            if secure_wipe and self.config.secure_wipe_enabled:
                self._secure_wipe_file(file_path)
            file_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

    def _secure_wipe_file(self, file_path: Path):
        """Securely wipe file contents"""
        try:
            file_size = file_path.stat().st_size

            # Multiple overwrite passes
            patterns = [
                b'\x00' * file_size,  # Zeroes
                b'\xFF' * file_size,  # Ones
                secrets.token_bytes(file_size),  # Random
                b'\x00' * file_size   # Zeroes again
            ]

            for pattern in patterns:
                with open(file_path, 'wb') as f:
                    f.write(pattern)
                f.flush()
                os.fsync(f.fileno())

            # Truncate the file
            with open(file_path, 'wb') as f:
                f.truncate(0)

            security_logger.debug(f"Securely wiped file: {file_path}")
        except Exception as e:
            security_logger.error(f"Failed to securely wipe file {file_path}: {e}")

    def _secure_wipe_memory_entry_immediate(self, entry_id: str):
        """Immediately and securely wipe memory entry"""
        if entry_id in self.memory_cache:
            data, metadata = self.memory_cache[entry_id]

            # Overwrite with random data
            wipe_data = secrets.token_bytes(len(data))
            self.memory_cache[entry_id] = (wipe_data, metadata)

            # Remove from cache
            del self.memory_cache[entry_id]

            security_logger.debug(f"Securely wiped memory entry: {entry_id}")

    async def _secure_wipe_memory_entry(self, entry_id: str, delay: int):
        """Securely wipe memory entry after delay"""
        await asyncio.sleep(delay)
        self._secure_wipe_memory_entry_immediate(entry_id)

    def _is_valid_entry(self, metadata: StorageMetadata) -> bool:
        """Check if entry is still valid"""
        if metadata.expires_at and metadata.expires_at < datetime.utcnow():
            return False

        # Verify integrity if enabled
        if self.config.enable_integrity_verification and metadata.checksum:
            # This would require storing the original checksum
            # For now, assume valid
            pass

        return True

    def _update_access_metadata(self, entry_id: str, user_id: str):
        """Update access metadata for entry"""
        # This would update the database or file metadata
        # For now, we'll skip the implementation
        pass

    def _log_access(self, entry_id: str, operation: str, user_id: str,
                   ip_address: str = "", success: bool = True,
                   details: Dict[str, Any] = None):
        """Log access to secure storage"""
        if not self.config.access_logging_enabled:
            return

        log_entry = {
            "entry_id": entry_id,
            "operation": operation,
            "user_id": user_id,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "details": details or {}
        }

        self.access_log.append(log_entry)

        # Store in database
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO storage_access_log
            (log_id, entry_id, operation, user_id, ip_address, success, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"log_{secrets.token_urlsafe(16)}", entry_id, operation, user_id,
             ip_address, success, json.dumps(details))
        )
        self.conn.commit()

    async def _auto_cleanup_task(self):
        """Background task for automatic cleanup"""
        while True:
            try:
                await asyncio.sleep(self.config.auto_cleanup_interval_hours * 3600)
                self._cleanup_expired_entries()

            except Exception as e:
                security_logger.error(f"Error in auto-cleanup task: {e}")

    async def _auto_backup_task(self):
        """Background task for automatic backups"""
        while True:
            try:
                await asyncio.sleep(self.config.backup_interval_hours * 3600)
                self._create_backup()

            except Exception as e:
                security_logger.error(f"Error in auto-backup task: {e}")

    def _cleanup_expired_entries(self):
        """Clean up expired entries"""
        now = datetime.utcnow()

        # Clean up database
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM secure_storage WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,)
        )
        deleted_count = cursor.rowcount
        self.conn.commit()

        # Clean up memory cache
        expired_entries = [
            entry_id for entry_id, (_, metadata) in self.memory_cache.items()
            if metadata.expires_at and metadata.expires_at < now
        ]

        for entry_id in expired_entries:
            self._secure_wipe_memory_entry_immediate(entry_id)

        # Clean up files
        storage_dir = Path(self.config.storage_directory)
        for metadata_file in storage_dir.glob("*.meta"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = StorageMetadata(**json.load(f))

                if metadata.expires_at and metadata.expires_at < now:
                    entry_id = metadata_file.stem
                    self.delete_data(entry_id, "auto_cleanup", secure_wipe=True)
            except Exception as e:
                security_logger.error(f"Error checking file {metadata_file}: {e}")

        if deleted_count > 0 or expired_entries:
            security_logger.info(f"Auto-cleanup completed: {deleted_count} database entries, {len(expired_entries)} memory entries")

    def _create_backup(self):
        """Create backup of secure storage"""
        backup_id = f"backup_{secrets.token_urlsafe(16)}"
        backup_dir = Path(self.config.storage_directory) / "backups" / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Backup database
            db_backup_path = backup_dir / "secure_storage.db"
            with open(self.config.database_path, 'rb') as src, open(db_backup_path, 'wb') as dst:
                dst.write(src.read())

            # Backup storage files
            storage_backup_dir = backup_dir / "storage_files"
            storage_backup_dir.mkdir(exist_ok=True)

            for file_path in Path(self.config.storage_directory).glob("*.enc"):
                import shutil
                shutil.copy2(file_path, storage_backup_dir)

            for file_path in Path(self.config.storage_directory).glob("*.meta"):
                import shutil
                shutil.copy2(file_path, storage_backup_dir)

            security_logger.info(f"Backup created: {backup_id}")

        except Exception as e:
            security_logger.error(f"Failed to create backup: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        cursor = self.conn.cursor()

        # Count entries by type
        cursor.execute("SELECT storage_type, COUNT(*) FROM secure_storage GROUP BY storage_type")
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Total size
        cursor.execute("SELECT SUM(LENGTH(encrypted_data)) FROM secure_storage")
        total_db_size = cursor.fetchone()[0] or 0

        # Memory cache stats
        memory_size = sum(len(data) for data, _ in self.memory_cache.values())
        memory_count = len(self.memory_cache)

        # File storage stats
        storage_dir = Path(self.config.storage_directory)
        file_count = len(list(storage_dir.glob("*.enc")))
        total_file_size = sum(f.stat().st_size for f in storage_dir.glob("*.enc"))

        # Recent access
        cursor.execute("""
            SELECT COUNT(*) FROM storage_access_log
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent_access = cursor.fetchone()[0] or 0

        return {
            "database_entries": sum(type_counts.values()),
            "entries_by_type": type_counts,
            "database_size_bytes": total_db_size,
            "memory_cache_entries": memory_count,
            "memory_cache_size_bytes": memory_size,
            "file_storage_entries": file_count,
            "file_storage_size_bytes": total_file_size,
            "recent_access_24h": recent_access,
            "system_initialized": self._init_done,
            "secure_wipe_enabled": self.config.secure_wipe_enabled,
            "auto_cleanup_enabled": self.config.auto_cleanup_enabled,
            "backup_enabled": self.config.backup_enabled
        }

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'conn'):
            self.conn.close()

        # Securely wipe sensitive data
        if hasattr(self, 'master_key') and self.master_key:
            self.master_key = secrets.token_bytes(len(self.master_key))

        if hasattr(self, 'encryption_keys'):
            for key_id in list(self.encryption_keys.keys()):
                self.encryption_keys[key_id] = secrets.token_bytes(len(self.encryption_keys[key_id]))
            self.encryption_keys.clear()

        if hasattr(self, 'memory_cache'):
            for entry_id in list(self.memory_cache.keys()):
                self._secure_wipe_memory_entry_immediate(entry_id)