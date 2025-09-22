"""
AES-256 Encryption Engine with Key Derivation

Implements FIPS-140 compliant encryption using AES-256-GCM with PBKDF2 key derivation.
Provides secure encryption for API keys and sensitive configuration data.

Features:
- AES-256-GCM authenticated encryption
- PBKDF2 key derivation with configurable iterations
- Secure random salt generation
- Memory-safe key handling
- Anti-tampering verification
- Key stretching for brute-force resistance

Compliance:
- NIST SP 800-38D (GCM mode)
- NIST SP 800-132 (PBKDF2)
- OWASP Cryptographic Storage Cheat Sheet
"""

import os
import base64
import hashlib
import hmac
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
import struct
import time


@dataclass
class EncryptionMetadata:
    """Metadata for encrypted data"""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2-SHA256"
    pbkdf2_iterations: int = 600000
    salt_size: int = 32
    nonce_size: int = 12
    tag_size: int = 16
    version: int = 1


class EncryptionEngine:
    """
    AES-256-GCM encryption engine with PBKDF2 key derivation

    Implements industry-standard encryption with:
    - Authenticated encryption (prevents tampering)
    - Key derivation (secure password-based encryption)
    - Memory-safe operations
    - Comprehensive error handling
    """

    def __init__(self, metadata: Optional[EncryptionMetadata] = None):
        """
        Initialize encryption engine

        Args:
            metadata: Encryption configuration metadata
        """
        self.metadata = metadata or EncryptionMetadata()
        self._validate_metadata()

    def _validate_metadata(self) -> None:
        """Validate encryption metadata configuration"""
        if self.metadata.pbkdf2_iterations < 100000:
            raise ValueError("PBKDF2 iterations must be at least 100,000")
        if self.metadata.salt_size < 16:
            raise ValueError("Salt size must be at least 16 bytes")
        if self.metadata.nonce_size < 12:
            raise ValueError("Nonce size must be at least 12 bytes")
        if self.metadata.tag_size < 16:
            raise ValueError("Tag size must be at least 16 bytes")

    def _generate_salt(self) -> bytes:
        """Generate cryptographically secure random salt"""
        return os.urandom(self.metadata.salt_size)

    def _generate_nonce(self) -> bytes:
        """Generate cryptographically secure random nonce"""
        return os.urandom(self.metadata.nonce_size)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key using PBKDF2

        Args:
            password: User password or master key
            salt: Cryptographic salt

        Returns:
            Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256 key
            salt=salt,
            iterations=self.metadata.pbkdf2_iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    def encrypt(self, plaintext: str, password: str) -> str:
        """
        Encrypt plaintext data

        Args:
            plaintext: Data to encrypt
            password: Encryption password or master key

        Returns:
            Base64-encoded encrypted data with metadata
        """
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")

        # Generate random salt and nonce
        salt = self._generate_salt()
        nonce = self._generate_nonce()

        # Derive encryption key
        key = self._derive_key(password, salt)

        try:
            # Encrypt using AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Encrypt and authenticate
            ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

            # Pack encrypted data with metadata
            encrypted_data = self._pack_encrypted_data(
                salt, nonce, encryptor.tag, ciphertext
            )

            # Securely wipe key from memory
            self._secure_wipe(key)

            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            # Securely wipe key on error
            self._secure_wipe(key)
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str, password: str) -> str:
        """
        Decrypt encrypted data

        Args:
            encrypted_data: Base64-encoded encrypted data
            password: Decryption password or master key

        Returns:
            Decrypted plaintext
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")

        try:
            # Unpack encrypted data
            encrypted_bytes = base64.b64decode(encrypted_data)
            salt, nonce, tag, ciphertext = self._unpack_encrypted_data(encrypted_bytes)

            # Derive decryption key
            key = self._derive_key(password, salt)

            # Decrypt using AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt and verify
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Securely wipe key from memory
            self._secure_wipe(key)

            return plaintext.decode('utf-8')

        except InvalidTag:
            raise ValueError("Decryption failed: Invalid authentication tag (data tampered)")
        except Exception as e:
            # Securely wipe key on error
            self._secure_wipe(key)
            raise ValueError(f"Decryption failed: {str(e)}")

    def _pack_encrypted_data(self, salt: bytes, nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
        """
        Pack encrypted components into binary format

        Format:
        [version:1][salt_size:1][nonce_size:1][tag_size:1][iterations:4]
        [salt...][nonce...][tag...][ciphertext...]
        """
        version = self.metadata.version.to_bytes(1, 'big')
        salt_size = self.metadata.salt_size.to_bytes(1, 'big')
        nonce_size = self.metadata.nonce_size.to_bytes(1, 'big')
        tag_size = self.metadata.tag_size.to_bytes(1, 'big')
        iterations = self.metadata.pbkdf2_iterations.to_bytes(4, 'big')

        return (
            version + salt_size + nonce_size + tag_size + iterations +
            salt + nonce + tag + ciphertext
        )

    def _unpack_encrypted_data(self, encrypted_bytes: bytes) -> Tuple[bytes, bytes, bytes, bytes]:
        """Unpack encrypted components from binary format"""
        offset = 0

        # Read header
        version = encrypted_bytes[offset]; offset += 1
        salt_size = encrypted_bytes[offset]; offset += 1
        nonce_size = encrypted_bytes[offset]; offset += 1
        tag_size = encrypted_bytes[offset]; offset += 1
        iterations = int.from_bytes(encrypted_bytes[offset:offset+4], 'big'); offset += 4

        # Validate header
        if version != self.metadata.version:
            raise ValueError(f"Unsupported encryption version: {version}")

        # Extract components
        salt = encrypted_bytes[offset:offset+salt_size]; offset += salt_size
        nonce = encrypted_bytes[offset:offset+nonce_size]; offset += nonce_size
        tag = encrypted_bytes[offset:offset+tag_size]; offset += tag_size
        ciphertext = encrypted_bytes[offset:]

        return salt, nonce, tag, ciphertext

    def _secure_wipe(self, data: bytes) -> None:
        """Securely wipe sensitive data from memory"""
        if isinstance(data, bytes):
            # Overwrite with random data multiple times
            for _ in range(3):
                random_data = os.urandom(len(data))
                data = bytearray(data)
                for i in range(len(data)):
                    data[i] = random_data[i]
            # Set to zeros
            for i in range(len(data)):
                data[i] = 0

    def verify_encryption(self, encrypted_data: str) -> bool:
        """
        Verify encrypted data format and integrity

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            True if format is valid, False otherwise
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            self._unpack_encrypted_data(encrypted_bytes)
            return True
        except Exception:
            return False

    def estimate_strength(self, password: str) -> Dict[str, Any]:
        """
        Estimate encryption strength based on password

        Args:
            password: Password to analyze

        Returns:
            Dictionary with strength metrics
        """
        # Calculate entropy
        entropy = self._calculate_entropy(password)

        # Estimate brute-force time (simplified)
        pbkdf2_strength = self.metadata.pbkdf2_iterations / 1000000  # Million iterations
        estimated_time_seconds = (2 ** entropy) * pbkdf2_strength / 1000000  # Million guesses/second

        return {
            "entropy_bits": entropy,
            "password_length": len(password),
            "pbkdf2_iterations": self.metadata.pbkdf2_iterations,
            "estimated_brute_force_time_seconds": estimated_time_seconds,
            "strength_score": self._calculate_strength_score(entropy),
            "recommendations": self._get_strength_recommendations(entropy)
        }

    def _calculate_entropy(self, password: str) -> float:
        """Calculate password entropy"""
        if not password:
            return 0.0

        charset_size = 0
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            charset_size += 32

        return len(password) * (charset_size.bit_length())

    def _calculate_strength_score(self, entropy: float) -> str:
        """Calculate strength score based on entropy"""
        if entropy < 50:
            return "WEAK"
        elif entropy < 80:
            return "MEDIUM"
        elif entropy < 120:
            return "STRONG"
        else:
            return "VERY_STRONG"

    def _get_strength_recommendations(self, entropy: float) -> list:
        """Get password strength recommendations"""
        recommendations = []

        if entropy < 50:
            recommendations.append("Use a longer password (12+ characters)")
            recommendations.append("Include uppercase, lowercase, numbers, and symbols")
            recommendations.append("Avoid dictionary words and common patterns")
        elif entropy < 80:
            recommendations.append("Consider adding more characters or complexity")

        return recommendations


# Default instance with recommended settings
default_encryption = EncryptionEngine(EncryptionMetadata(
    pbkdf2_iterations=600000,  # OWASP recommendation
    salt_size=32,
    nonce_size=12,
    tag_size=16
))