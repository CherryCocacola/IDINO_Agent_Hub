"""
Shared pytest fixtures for the Document Utilization System backend tests.

Uses an in-memory SQLite database (via aiosqlite) so that tests do not
require a running PostgreSQL instance.  External services (Qdrant, MinIO,
Redis, RabbitMQ) are mocked at the dependency-injection level.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# IMPORTANT: Set environment variables BEFORE any app imports
# This ensures Settings() validation passes during module import
# ---------------------------------------------------------------------------
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-jwt-signing-purposes-only")
os.environ.setdefault("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
os.environ.setdefault("CORS_ORIGINS", '["*"]')
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET", "documents")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6333")

# ---------------------------------------------------------------------------
# Now safe to import the rest
# ---------------------------------------------------------------------------
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import TokenData, TokenType, create_access_token

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ---------------------------------------------------------------------------
# Reusable identifiers
# ---------------------------------------------------------------------------
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_MEMBER_EMAIL = "member@test.com"


# ---------------------------------------------------------------------------
# SQLite async engine (in-memory, no Postgres dependency)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def async_engine():
    """Create a shared in-memory SQLite engine for the test session."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session that rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def _make_token_data(
    role: str = "admin",
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    email: str | None = None,
) -> TokenData:
    return TokenData(
        user_id=user_id or TEST_USER_ID,
        email=email or TEST_ADMIN_EMAIL,
        role=role,
        token_type=TokenType.ACCESS,
        organization_id=org_id or TEST_ORG_ID,
        scopes=[],
    )


def auth_headers(
    role: str = "admin",
    user_id: uuid.UUID | None = None,
    org_id: uuid.UUID | None = None,
    email: str | None = None,
) -> dict[str, str]:
    """Return ``Authorization: Bearer <jwt>`` headers for the given role."""
    uid = user_id or TEST_USER_ID
    oid = org_id or TEST_ORG_ID
    token = create_access_token(
        data={
            "sub": str(uid),
            "email": email or (TEST_ADMIN_EMAIL if role == "admin" else TEST_MEMBER_EMAIL),
            "role": role,
            "org": str(oid),
            "scopes": [],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    """JWT headers for an admin user."""
    return auth_headers(role="admin")


@pytest.fixture()
def member_headers() -> dict[str, str]:
    """JWT headers for a regular member."""
    return auth_headers(role="member")


@pytest.fixture()
def viewer_headers() -> dict[str, str]:
    """JWT headers for a viewer."""
    return auth_headers(role="viewer")


@pytest.fixture()
def admin_token_data() -> TokenData:
    return _make_token_data(role="admin")


@pytest.fixture()
def member_token_data() -> TokenData:
    return _make_token_data(role="member", email=TEST_MEMBER_EMAIL)


# ---------------------------------------------------------------------------
# Patch external integrations used at import-time by the app
# ---------------------------------------------------------------------------
def _patch_prometheus():
    """Prevent Prometheus instrumentator from failing in test context."""
    mock_instrumentator = MagicMock()
    mock_instrumentator.instrument.return_value = mock_instrumentator
    mock_instrumentator.expose.return_value = mock_instrumentator
    return mock_instrumentator


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------
@pytest.fixture()
async def client(db_session, admin_token_data) -> AsyncGenerator[AsyncClient, None]:
    """Provide an ``httpx.AsyncClient`` wired to the FastAPI app.

    Overrides:
    * ``get_db`` / ``get_db_session`` → test ``db_session`` (SQLite)
    * ``get_current_user`` → returns ``admin_token_data``
    """
    with (
        patch("app.core.database.get_settings") as mock_db_settings,
        patch("app.core.config.get_settings") as mock_cfg_settings,
        patch(
            "prometheus_fastapi_instrumentator.Instrumentator",
            return_value=_patch_prometheus(),
        ),
    ):
        # Provide minimal settings so the app can start
        settings = MagicMock()
        settings.database_url = "sqlite+aiosqlite://"
        settings.db_echo = False
        settings.db_pool_size = 5
        settings.db_max_overflow = 0
        settings.db_pool_timeout = 30
        settings.cors_origins = ["*"]
        settings.jwt_secret_key = "test-secret-key-for-jwt-signing"
        settings.jwt_algorithm = "HS256"
        settings.jwt_private_key_path = None
        settings.jwt_public_key_path = None
        settings.jwt_access_token_expire_minutes = 15
        settings.jwt_refresh_token_expire_days = 7
        settings.effective_jwt_algorithm = "HS256"
        settings.encryption_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        settings.debug = False
        settings.environment = "development"
        settings.app_name = "Test"
        settings.app_version = "0.0.1"
        settings.max_upload_size_bytes = 100 * 1024 * 1024
        settings.redis_url = "redis://localhost:6379/0"
        settings.minio_endpoint = "localhost:9000"
        settings.minio_access_key = "minioadmin"
        settings.minio_secret_key = "minioadmin"
        settings.minio_bucket = "documents"
        settings.minio_secure = False
        settings.qdrant_host = "localhost"
        settings.qdrant_port = 6333
        settings.qdrant_api_key = None
        settings.openai_api_key = None
        settings.llm_model = "gpt-4o"
        settings.llm_temperature = 0.1
        settings.llm_max_tokens = 4096
        settings.embedding_model = "test-embedding"
        settings.embedding_dimension = 1024

        mock_db_settings.return_value = settings
        mock_cfg_settings.return_value = settings

        # Force re-import of the app with patched settings
        import importlib

        import app.main as main_module

        importlib.reload(main_module)
        test_app = main_module.app

        # Override dependencies
        from app.core.database import get_db
        from app.core.dependencies import get_current_user, get_db_session

        async def _override_db():
            yield db_session

        test_app.dependency_overrides[get_db] = _override_db
        test_app.dependency_overrides[get_db_session] = _override_db
        test_app.dependency_overrides[get_current_user] = lambda: admin_token_data

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        test_app.dependency_overrides.clear()


@pytest.fixture()
async def unauth_client() -> AsyncGenerator[AsyncClient, None]:
    """Client with NO dependency overrides — for testing auth rejection."""
    with (
        patch("app.core.database.get_settings") as mock_db_settings,
        patch("app.core.config.get_settings") as mock_cfg_settings,
        patch(
            "prometheus_fastapi_instrumentator.Instrumentator",
            return_value=_patch_prometheus(),
        ),
    ):
        settings = MagicMock()
        settings.database_url = "sqlite+aiosqlite://"
        settings.db_echo = False
        settings.db_pool_size = 5
        settings.db_max_overflow = 0
        settings.db_pool_timeout = 30
        settings.cors_origins = ["*"]
        settings.jwt_secret_key = "test-secret-key-for-jwt-signing"
        settings.jwt_algorithm = "HS256"
        settings.jwt_private_key_path = None
        settings.jwt_public_key_path = None
        settings.jwt_access_token_expire_minutes = 15
        settings.jwt_refresh_token_expire_days = 7
        settings.effective_jwt_algorithm = "HS256"
        settings.encryption_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        settings.debug = False
        settings.environment = "development"
        settings.app_name = "Test"
        settings.app_version = "0.0.1"
        settings.max_upload_size_bytes = 100 * 1024 * 1024
        settings.redis_url = "redis://localhost:6379/0"

        mock_db_settings.return_value = settings
        mock_cfg_settings.return_value = settings

        import importlib

        import app.main as main_module

        importlib.reload(main_module)
        test_app = main_module.app

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        test_app.dependency_overrides.clear()


@pytest.fixture()
async def rbac_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Client with DB override but real auth - for testing RBAC (role-based access).

    Use this when you need to test that different roles get different access levels.
    Pass actual JWT headers using auth_headers() helper.
    """
    with (
        patch("app.core.database.get_settings") as mock_db_settings,
        patch("app.core.config.get_settings") as mock_cfg_settings,
        patch(
            "prometheus_fastapi_instrumentator.Instrumentator",
            return_value=_patch_prometheus(),
        ),
    ):
        settings = MagicMock()
        settings.database_url = "sqlite+aiosqlite://"
        settings.db_echo = False
        settings.db_pool_size = 5
        settings.db_max_overflow = 0
        settings.db_pool_timeout = 30
        settings.cors_origins = ["*"]
        settings.cors_allow_credentials = True
        settings.cors_allow_methods = ["*"]
        settings.cors_allow_headers = ["*"]
        settings.jwt_secret_key = "test-secret-key-for-jwt-signing"
        settings.jwt_algorithm = "HS256"
        settings.jwt_private_key_path = None
        settings.jwt_public_key_path = None
        settings.jwt_access_token_expire_minutes = 15
        settings.jwt_refresh_token_expire_days = 7
        settings.effective_jwt_algorithm = "HS256"
        settings.encryption_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        settings.debug = False
        settings.environment = "development"
        settings.app_name = "Test"
        settings.app_version = "0.0.1"
        settings.max_upload_size_bytes = 100 * 1024 * 1024
        settings.redis_url = "redis://localhost:6379/0"
        settings.minio_endpoint = "localhost:9000"
        settings.minio_access_key = "minioadmin"
        settings.minio_secret_key = "minioadmin"
        settings.minio_bucket = "documents"
        settings.minio_secure = False
        settings.qdrant_host = "localhost"
        settings.qdrant_port = 6333
        settings.qdrant_api_key = None
        settings.openai_api_key = None
        settings.llm_model = "gpt-4o"
        settings.llm_temperature = 0.1
        settings.llm_max_tokens = 4096
        settings.embedding_model = "test-embedding"
        settings.embedding_dimension = 1024

        mock_db_settings.return_value = settings
        mock_cfg_settings.return_value = settings

        import importlib

        import app.main as main_module

        importlib.reload(main_module)
        test_app = main_module.app

        # Override only DB - NOT get_current_user (so JWT headers work)
        from app.core.database import get_db
        from app.core.dependencies import get_db_session

        async def _override_db():
            yield db_session

        test_app.dependency_overrides[get_db] = _override_db
        test_app.dependency_overrides[get_db_session] = _override_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        test_app.dependency_overrides.clear()
