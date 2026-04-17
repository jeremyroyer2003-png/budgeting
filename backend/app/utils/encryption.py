"""
encryption.py — AES token encryption for stored provider access tokens.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the cryptography library.
The key is derived from ENCRYPTION_KEY in the environment using SHA-256,
producing a stable 32-byte key regardless of the input length.

In production: set ENCRYPTION_KEY to a long random string and store it
in a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.).
Never commit the key to source control.
"""

import base64
import os
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken


def _build_fernet() -> Fernet:
    raw_key = os.environ.get(
        "ENCRYPTION_KEY",
        "dev-encryption-key-replace-before-deploying-to-production"
    )
    # SHA-256 → 32 bytes → base64url → valid Fernet key
    derived = sha256(raw_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt an access token string. Returns a URL-safe base64 ciphertext."""
    return _build_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """
    Decrypt a previously encrypted access token.
    Raises ValueError if the ciphertext is invalid or the key has changed.
    """
    try:
        return _build_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt token — wrong key or corrupted data.") from exc
