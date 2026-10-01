"""
OmniAgent AI — Fernet Encryption Service
Provides symmetric encryption-at-rest for sensitive configs and API secrets,
with automatic key derivation and secret redaction.
"""

import base64
import hashlib
import json
from typing import Any

import structlog
from cryptography.fernet import Fernet

from app.core.config import settings

logger = structlog.get_logger(__name__)

SENSITIVE_KEY_SUBSTRINGS = (
    "key",
    "token",
    "secret",
    "password",
    "cred",
    "auth",
    "private",
    "signature",
)


def _get_fernet() -> Fernet:
    """Derives a deterministic 32-byte url-safe base64 Fernet key from SECRET_KEY."""
    raw_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(raw_hash)
    return Fernet(fernet_key)


def encrypt_config(payload: dict[str, Any]) -> str:
    """Encrypts a configuration dictionary into a Fernet ciphertext string."""
    f = _get_fernet()
    raw_json = json.dumps(payload, sort_keys=True).encode("utf-8")
    return f.encrypt(raw_json).decode("utf-8")


def decrypt_config(ciphertext: str) -> dict[str, Any]:
    """Decrypts a Fernet ciphertext string back into a configuration dictionary."""
    if not ciphertext:
        return {}
    f = _get_fernet()
    decrypted_bytes = f.decrypt(ciphertext.encode("utf-8"))
    return json.loads(decrypted_bytes.decode("utf-8"))


def redact_config(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively returns a copy of the dictionary with sensitive fields redacted.
    Protects API keys and secrets from leaking in API responses or logs.
    """
    redacted: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, dict):
            redacted[k] = redact_config(v)
        elif any(sub in k.lower() for sub in SENSITIVE_KEY_SUBSTRINGS):
            if isinstance(v, str) and len(v) > 8:
                redacted[k] = f"{v[:3]}...{v[-3:]}"
            else:
                redacted[k] = "********"
        else:
            redacted[k] = v
    return redacted
