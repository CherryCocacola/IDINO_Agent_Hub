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


# ---------------------------------------------------------------------------
# 트랙 1-5 SSO 옵션 A — AgentHub JWT 호환 디코더
# ---------------------------------------------------------------------------
#
# AgentHub (.NET 8) 가 발급하는 JWT 의 claim 형식 (System.IdentityModel.Tokens.Jwt 기본):
#
#   "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier" : "12"     # int UserId
#   "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"   : "u@e"
#   "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"          : "Admin" # 단일 또는 배열
#   "iss": "AIAgentManagement"
#   "aud": "AIAgentManagementUsers"
#   "exp", "nbf", "iat", "jti"  — 표준
#   ("type" claim 없음)
#
# DocUtil (FastAPI + python-jose) 가 발급하는 JWT:
#   "sub"   : "<uuid>"
#   "email" : "..."
#   "role"  : "admin|member|...." (단일 str)
#   "type"  : "access|refresh"
#   "org"   : "<uuid>" | None
#   "dept"  : "<uuid>" | None
#   "scopes": [...]
#   "exp", "iat", "jti"
#
# 두 형식 모두 같은 SecretKey (HS256) 로 서명되면 본 디코더 하나로 수용한다.
# AgentHub JWT 의 sub (int UserId) → DocUtil tb_users VIEW (= AGENT_HUB.Users alias)
# 의 OriginalDocutilUuid (uuid) 로 변환해야 DocUtil 내부 SQLAlchemy 모델과 호환된다.

# Microsoft ClaimTypes URI (.NET 가 JWT 에 그대로 사용)
_MS_CLAIM_NAMEID = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
_MS_CLAIM_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
_MS_CLAIM_ROLE = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"

# AgentHub Role (Admin/SuperAdmin/User/Member ...) → DocUtil role (admin/user/member ...)
_AGENTHUB_ROLE_MAP: dict[str, str] = {
    "superadmin": "super_admin",
    "super_admin": "super_admin",
    "admin": "admin",
    "developer": "admin",  # Developer 는 DocUtil 에 대응 역할 없음 → admin 로 매핑
    "user": "user",
    "member": "member",
    "viewer": "viewer",
    "org_admin": "org_admin",
    "manager": "manager",
}


def _extract_email(payload: dict[str, Any]) -> str:
    """email claim 추출 — DocUtil('email') 또는 AgentHub(ClaimTypes.Email URI) 모두 수용."""
    return payload.get("email") or payload.get(_MS_CLAIM_EMAIL) or ""


def _extract_role(payload: dict[str, Any]) -> str:
    """role claim 추출 + AgentHub → DocUtil 매핑.

    우선순위:
      1. DocUtil 형식: payload['role'] (단일 str)
      2. AgentHub 형식: payload[ClaimTypes.Role] (str 또는 list)
      3. payload['roles'] (list — 옵션)
      4. fallback: 'member'
    """
    raw: str | list[str] | None = (
        payload.get("role")
        or payload.get(_MS_CLAIM_ROLE)
        or payload.get("roles")
        or "member"
    )

    # ClaimTypes.Role 가 다중 role 일 때는 list 가 됨. 첫 번째 우선.
    if isinstance(raw, list):
        raw_str = raw[0] if raw else "member"
    else:
        raw_str = str(raw)

    return _AGENTHUB_ROLE_MAP.get(raw_str.lower(), raw_str.lower())


class _AgentHubMapping(BaseModel):
    """AgentHub User row 의 일부 — SSO decode 단계에서 필요한 컬럼만."""

    user_uuid: uuid.UUID
    organization_id: uuid.UUID | None = None


def _lookup_agenthub_user_mapping(user_id_int: int) -> _AgentHubMapping | None:
    """AgentHub User.UserId (int) → (OriginalDocutilUuid, OrganizationId) 변환.

    DocUtil 코드 전반은 사용자를 uuid 로 식별하고, 다수의 endpoint 는
    ``current_user.organization_id`` 를 사용해 org-scoped 쿼리를 수행한다.
    AgentHub JWT 에는 둘 다 없으므로 본 함수에서 한 번의 DB lookup 으로 양쪽을 채운다.

    DocUtil 컨테이너에는 asyncpg 와 psycopg(3) 만 설치되어 있으므로 psycopg2 기반의
    SQLAlchemy sync engine 은 쓸 수 없다. 가장 가벼운 경로 = psycopg3 sync API 직접
    사용. 인증 미들웨어에서 매 요청 1회 호출되므로 connection 1회 + 즉시 close.

    settings.database_url 은 ``postgresql+asyncpg://AGENT_HUB:...@postgres:5432/AGENT_HUB``
    형식 — psycopg 가 받아들이는 표준 URI 로 normalize 한다.

    OriginalDocutilUuid 가 NULL 이면 SSO 매핑이 없는 사용자 → None 반환.
    Lookup 결과 캐싱은 의도적으로 하지 않는다 (mapping 변경 시 즉시 반영 + 데이터
    셋이 작아 성능 부담 없음).
    """
    settings = get_settings()
    raw_url = settings.database_url

    # SQLAlchemy 스타일 dialect prefix 제거 → psycopg native URI
    if raw_url.startswith("postgresql+asyncpg://"):
        pg_url = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif raw_url.startswith("postgresql+psycopg://"):
        pg_url = raw_url.replace("postgresql+psycopg://", "postgresql://", 1)
    else:
        pg_url = raw_url

    try:
        import psycopg  # psycopg3 sync — 컨테이너에 항상 설치되어 있음

        with psycopg.connect(pg_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "OriginalDocutilUuid", "OrganizationId" '
                    'FROM "AIAgentManagement"."Users" '
                    'WHERE "UserId" = %s LIMIT 1',
                    (user_id_int,),
                )
                row = cur.fetchone()
        if row is None or row[0] is None:
            return None

        user_val = row[0]
        org_val = row[1]
        user_uuid = user_val if isinstance(user_val, uuid.UUID) else uuid.UUID(str(user_val))
        org_uuid: uuid.UUID | None = None
        if org_val is not None:
            org_uuid = org_val if isinstance(org_val, uuid.UUID) else uuid.UUID(str(org_val))
        return _AgentHubMapping(user_uuid=user_uuid, organization_id=org_uuid)
    except Exception:  # noqa: BLE001 — DB lookup 실패는 인증 실패로 전파
        return None


# 하위 호환: 기존 시그니처 (uuid only) 가 필요하면 wrapper 로 노출
def _lookup_agenthub_user_uuid(user_id_int: int) -> uuid.UUID | None:
    """Backward-compat shim — 신규 코드는 `_lookup_agenthub_user_mapping` 사용."""
    m = _lookup_agenthub_user_mapping(user_id_int)
    return m.user_uuid if m else None


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT, returning structured ``TokenData``.

    Accepts both DocUtil-native JWT (sub = uuid) and AgentHub JWT (sub = int UserId).
    For AgentHub tokens the sub is resolved to the DocUtil user uuid via the
    ``AIAgentManagement.Users.OriginalDocutilUuid`` mapping column.

    Raises ``JWTError`` on signature/expiry failure or when the AgentHub user
    has no DocUtil uuid mapping.
    """
    get_settings()

    # Try all plausible algorithms so RS256 -> HS256 fallback is transparent.
    algorithms = ["RS256", "HS256"]

    try:
        # issuer/audience 검증 우회 — AgentHub("AIAgentManagement"/"AIAgentManagementUsers") 와
        # DocUtil(iss/aud 없음) 양쪽을 모두 수용해야 하므로 jose 의 기본 issuer/audience
        # 검증을 끈다. 서명/만료는 그대로 검증된다.
        payload = jwt.decode(
            token,
            _verification_key(),
            algorithms=algorithms,
            options={"verify_aud": False, "verify_iss": False},
        )
    except JWTError:
        raise

    # ---- sub claim 분기 ----
    # DocUtil JWT 는 sub 가 uuid 문자열. AgentHub JWT 는 sub 가 int (또는 int-like str).
    sub_raw = payload.get("sub") or payload.get(_MS_CLAIM_NAMEID)
    if sub_raw is None:
        raise JWTError("Token missing subject identifier (sub).")
    sub_str = str(sub_raw)

    # AgentHub JWT 의 경우 mapping lookup 으로 organization_id 도 채워야 함
    agenthub_mapping: _AgentHubMapping | None = None
    try:
        user_uuid = uuid.UUID(sub_str)
    except (ValueError, AttributeError):
        # AgentHub JWT 경로 — sub 가 정수일 때
        try:
            user_id_int = int(sub_str)
        except ValueError as err:
            raise JWTError(f"Invalid 'sub' claim format: {sub_str!r}") from err

        agenthub_mapping = _lookup_agenthub_user_mapping(user_id_int)
        if agenthub_mapping is None:
            raise JWTError(
                f"AgentHub user {user_id_int} has no DocUtil uuid mapping "
                "(OriginalDocutilUuid is NULL)."
            )
        user_uuid = agenthub_mapping.user_uuid

    # ---- type claim 분기 ----
    # AgentHub JWT 에는 'type' 이 없음 → ACCESS 로 간주.
    token_type_raw = payload.get("type", TokenType.ACCESS.value)
    try:
        token_type = TokenType(token_type_raw)
    except ValueError:
        token_type = TokenType.ACCESS

    # ---- org / dept claim 분기 ----
    # 우선순위: payload claim → AgentHub mapping lookup (sub 가 int 였을 때만 채워짐).
    # AgentHub JWT 는 org/dept claim 이 없으므로 사실상 mapping 의 OrganizationId 사용.
    org_raw = payload.get("org")
    dept_raw = payload.get("dept")
    org_uuid: uuid.UUID | None = None
    dept_uuid: uuid.UUID | None = None
    if org_raw:
        try:
            org_uuid = uuid.UUID(str(org_raw))
        except ValueError:
            org_uuid = None
    elif agenthub_mapping is not None:
        org_uuid = agenthub_mapping.organization_id
    if dept_raw:
        try:
            dept_uuid = uuid.UUID(str(dept_raw))
        except ValueError:
            dept_uuid = None
    # NOTE: AgentHub.Users.DepartmentId 는 int FK 라 DocUtil UUID 와 형식 호환되지 않음.
    # DocUtil 측 endpoint 중 department_id 가 필요한 곳은 별도 lookup (현재는 미사용).

    return TokenData(
        user_id=user_uuid,
        email=_extract_email(payload),
        role=_extract_role(payload),
        token_type=token_type,
        organization_id=org_uuid,
        department_id=dept_uuid,
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
