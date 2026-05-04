"""
Security utilities: password hashing, JWT tokens, and AES-256-GCM encryption.

* Passwords -- bcrypt with cost factor 12.
* JWTs      -- RS256 when RSA keys are available, HS256 otherwise.
* API keys  -- AES-256-GCM authenticated encryption at rest.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Password hashing (bcrypt, cost 12)
# ---------------------------------------------------------------------------
import bcrypt as _bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from .config import get_settings

_BCRYPT_ROUNDS = 12


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    # Truncate to 72 bytes (bcrypt limit) and encode
    password_bytes = plain.encode("utf-8")[:72]
    salt = _bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return _bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` when *plain* matches the bcrypt *hashed* value."""
    try:
        password_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return _bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenData(BaseModel):
    """Decoded token payload exposed to application code."""

    user_id: uuid.UUID
    email: str
    role: str
    token_type: TokenType
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    scopes: list[str] = Field(default_factory=list)


class TokenPayload(BaseModel):
    """Raw JWT claims (``sub``, ``exp``, etc.)."""

    sub: str  # user id
    email: str
    role: str
    type: str
    org: str | None = None
    dept: str | None = None
    scopes: list[str] = Field(default_factory=list)
    exp: datetime
    iat: datetime
    jti: str


class TokenResponse(BaseModel):
    """Schema returned to the client after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def _load_key(path: str | None) -> str | None:
    """Read a PEM key file and return its contents, or ``None``."""
    if path is None:
        return None
    key_path = Path(path)
    if not key_path.is_file():
        return None
    return key_path.read_text(encoding="utf-8")


def _signing_key() -> str:
    """Return the key material used for *signing* JWTs."""
    settings = get_settings()
    private_key = _load_key(settings.jwt_private_key_path)
    if private_key is not None:
        return private_key
    # Fallback: symmetric HS256
    return settings.jwt_secret_key


def _verification_key() -> str:
    """Return the key material used for *verifying* JWTs."""
    settings = get_settings()
    public_key = _load_key(settings.jwt_public_key_path)
    if public_key is not None:
        return public_key
    return settings.jwt_secret_key


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed access JWT."""
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))

    claims: dict[str, Any] = {
        **data,
        "type": TokenType.ACCESS,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(
        claims,
        _signing_key(),
        algorithm=settings.effective_jwt_algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed refresh JWT."""
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))

    claims: dict[str, Any] = {
        **data,
        "type": TokenType.REFRESH,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(
        claims,
        _signing_key(),
        algorithm=settings.effective_jwt_algorithm,
    )


def create_token_pair(
    user_id: uuid.UUID,
    email: str,
    role: str,
    organization_id: uuid.UUID | None = None,
    department_id: uuid.UUID | None = None,
    scopes: list[str] | None = None,
) -> TokenResponse:
    """Issue an access + refresh token pair for the given user."""
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "org": str(organization_id) if organization_id else None,
        "dept": str(department_id) if department_id else None,
        "scopes": scopes or [],
    }

    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT, returning structured ``TokenData``.

    Raises ``JWTError`` on any validation failure (expiry, bad signature, ...).
    """
    get_settings()

    # Try all plausible algorithms so RS256 -> HS256 fallback is transparent.
    algorithms = ["RS256", "HS256"]

    try:
        payload = jwt.decode(
            token,
            _verification_key(),
            algorithms=algorithms,
        )
    except JWTError:
        raise

    return TokenData(
        user_id=uuid.UUID(payload["sub"]),
        email=payload["email"],
        role=payload["role"],
        token_type=TokenType(payload["type"]),
        organization_id=(uuid.UUID(payload["org"]) if payload.get("org") else None),
        department_id=(uuid.UUID(payload["dept"]) if payload.get("dept") else None),
        scopes=payload.get("scopes", []),
    )


# ---------------------------------------------------------------------------
# AES-256-GCM encryption for API keys
# ---------------------------------------------------------------------------
_NONCE_BYTES = 12  # 96-bit nonce recommended for AES-GCM


def _get_aes_key() -> bytes:
    """Derive the 32-byte AES key from the hex-encoded config value."""
    return bytes.fromhex(get_settings().encryption_key)


def encrypt_api_key(plaintext: str) -> bytes:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns ``nonce || ciphertext_with_tag`` as raw bytes.
    """
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_api_key(encrypted: bytes) -> str:
    """Decrypt a value previously produced by ``encrypt_api_key``.

    Raises ``cryptography.exceptions.InvalidTag`` on tampered data.
    """
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = encrypted[:_NONCE_BYTES]
    ciphertext = encrypted[_NONCE_BYTES:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def encrypt_api_key_hex(plaintext: str) -> str:
    """Convenience wrapper that returns the ciphertext as a hex string."""
    return encrypt_api_key(plaintext).hex()


def decrypt_api_key_hex(hex_ciphertext: str) -> str:
    """Convenience wrapper that accepts a hex-encoded ciphertext."""
    return decrypt_api_key(bytes.fromhex(hex_ciphertext))


# ---------------------------------------------------------------------------
# Aliases used by the auth module
# ---------------------------------------------------------------------------

# ``get_password_hash`` is an alias kept for convenience -- the auth service
# imports it by this name.
get_password_hash = hash_password


def verify_token(token: str) -> dict[str, Any] | None:
    """Low-level JWT decode that returns the *raw claims dict* or ``None``.

    Unlike ``decode_token`` (which returns a structured ``TokenData``),
    this helper is used by the auth module for token-blacklisting and
    refresh flows where only the raw payload is needed.
    """
    get_settings()
    algorithms = ["RS256", "HS256"]
    try:
        payload = jwt.decode(
            token,
            _verification_key(),
            algorithms=algorithms,
        )
        return payload
    except JWTError:
        return None
