"""Tenant-keyed envelope encryption module using standard AES-GCM-256."""

import os
import base64
import hashlib
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("app.crypto")

# In-memory DEK cache, using sha256 to deterministically derive keys from a master secret for mocks
_MOCK_KMS_KEYS = {}


def get_tenant_dek(tenant_id: str) -> bytes:
    """Retrieves or derives the symmetric Data Encryption Key (DEK) for the tenant from KMS."""
    if tenant_id not in _MOCK_KMS_KEYS:
        # Master secret is combined with the tenant_id to derive a tenant-isolated 32-byte AES key
        master_secret = b"GXP_ENVELOPE_ENCRYPTION_MASTER_KEY_SECRET"
        hasher = hashlib.sha256(master_secret + tenant_id.encode())
        _MOCK_KMS_KEYS[tenant_id] = hasher.digest()
    return _MOCK_KMS_KEYS[tenant_id]


def encrypt_tenant_field(data: str, tenant_id: str) -> str:
    """Encrypts raw data using the tenant's AES-GCM-256 key, returning a base64-encoded string.

    Args:
        data: Plaintext string to encrypt.
        tenant_id: Target tenant identifier.
    """
    key = get_tenant_dek(tenant_id)
    aesgcm = AESGCM(key)
    
    # Generate random 12-byte initialization vector (nonce)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)
    
    # Combine nonce and ciphertext to permit simple base64 serialization
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("utf-8")


def decrypt_tenant_field(ciphertext: str, tenant_id: str, audit_logger=None) -> str:
    """Decrypts base64-encoded ciphertext using the tenant's AES-GCM-256 key.

    Args:
        ciphertext: Base64-encoded combined nonce + encrypted data.
        tenant_id: Target tenant identifier.
        audit_logger: Optional AuditLogger instance to record security violation alerts.
    """
    try:
        combined = base64.b64decode(ciphertext.encode("utf-8"))
        if len(combined) < 12:
            raise ValueError("Invalid payload length.")
            
        nonce = combined[:12]
        encrypted_data = combined[12:]
        
        key = get_tenant_dek(tenant_id)
        aesgcm = AESGCM(key)
        
        decrypted_bytes = aesgcm.decrypt(nonce, encrypted_data, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        msg = f"DECRYPTION_FAILURE: Unauthorized decryption attempt or key mismatch for tenant '{tenant_id}'. Error: {e}"
        logger.error(msg)
        if audit_logger:
            audit_logger.log_step("Security:CRITICAL_ALERT", msg)
        raise ValueError("Cryptographic decryption failed. Access denied.")
