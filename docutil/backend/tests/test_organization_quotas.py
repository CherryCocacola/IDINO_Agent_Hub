"""tb_organization_quotas / QuotaService 테스트.

DocUtil 테스트 환경은 SQLite in-memory 이며, `tb_organizations.settings`
컬럼이 PostgreSQL 전용 JSONB 타입이라 ``Base.metadata.create_all`` 이
SQLite 방언에서 컴파일 실패한다. 따라서 실제 DB INSERT 기반 검증은
PostgreSQL 통합 테스트(Phase 4 S3 D10 QA)로 미루고, 본 파일은:

1. ORM 정의/제약 메타데이터 검증 (table name, columns, CheckConstraint 이름,
   UniqueConstraint 컬럼, FK ondelete).
2. QuotaService 의 순수 파이썬 로직 (현재 월 포맷 계산, amount 검증) 단위 테스트.
3. Alembic 009 migration 파일의 메타데이터 검증 (revision id, down_revision).

통합 테스트에서 검증되어야 할 항목 (SQLite 불가):
  * (org, type, year_month) UNIQUE → IntegrityError
  * monthly_limit < 0 → IntegrityError (CheckConstraint)
  * check_and_consume_quota() 한도 내 / 초과 동작
  * year_month regex CHECK 제약
  * FOR UPDATE 행 락 (동시성)
"""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

import pytest

from app.modules.organizations.models import OrganizationQuota
from app.modules.organizations.service import (
    DEFAULT_MONTHLY_LIMIT,
    QuotaService,
    _current_year_month,
)


# ===========================================================================
# 1. ORM 테이블 / 컬럼 정의
# ===========================================================================
def test_organization_quota_tablename_and_columns():
    """테이블명과 핵심 컬럼 6종이 정의되어 있다."""

    table = OrganizationQuota.__table__
    assert table.name == "tb_organization_quotas"

    cols = {c.name for c in table.columns}
    # Base 로부터 audit 6종 + UUIDMixin 의 id 까지 포함.
    expected_core = {
        "id",
        "organization_id",
        "quota_type",
        "year_month",
        "monthly_limit",
        "used_count",
        "ins_dt",
        "ins_user",
        "ins_ip",
        "upd_dt",
        "upd_user",
        "upd_ip",
    }
    missing = expected_core - cols
    assert not missing, f"누락된 컬럼: {missing}"


def test_organization_quota_column_nullability_and_defaults():
    """NOT NULL / default 값이 명시되어 있다."""

    table = OrganizationQuota.__table__

    cols = {c.name: c for c in table.columns}
    assert cols["organization_id"].nullable is False
    assert cols["quota_type"].nullable is False
    assert cols["year_month"].nullable is False
    assert cols["monthly_limit"].nullable is False
    assert cols["used_count"].nullable is False

    # Python-side default
    assert cols["monthly_limit"].default.arg == 100
    assert cols["used_count"].default.arg == 0


def test_organization_quota_column_types():
    """String 길이 / Integer 타입 확인."""

    from sqlalchemy import Integer, String

    table = OrganizationQuota.__table__
    cols = {c.name: c for c in table.columns}

    assert isinstance(cols["quota_type"].type, String)
    assert cols["quota_type"].type.length == 50
    assert isinstance(cols["year_month"].type, String)
    assert cols["year_month"].type.length == 7
    assert isinstance(cols["monthly_limit"].type, Integer)
    assert isinstance(cols["used_count"].type, Integer)


def test_organization_quota_foreign_key_cascade():
    """organization_id FK 는 tb_organizations.id → CASCADE."""

    table = OrganizationQuota.__table__
    org_col = table.c.organization_id
    fks = list(org_col.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "tb_organizations"
    assert fk.column.name == "id"
    assert fk.ondelete == "CASCADE"


# ===========================================================================
# 2. 제약 메타데이터 (이름/컬럼) — migration 과 1:1 정합
# ===========================================================================
def test_organization_quota_unique_constraint_name_and_columns():
    """(org, quota_type, year_month) UNIQUE 제약 존재."""

    from sqlalchemy import UniqueConstraint

    table = OrganizationQuota.__table__
    uniq = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    names = {c.name for c in uniq}
    assert "uq_tb_organization_quotas_org_type_month" in names

    target = next(c for c in uniq if c.name == "uq_tb_organization_quotas_org_type_month")
    cols = [col.name for col in target.columns]
    assert cols == ["organization_id", "quota_type", "year_month"]


def test_organization_quota_check_constraints_present():
    """4종 CheckConstraint 이 정의되어 있다 (이름 기준).

    NOTE: SQLAlchemy naming_convention 이 ``ck_%(table_name)s_%(constraint_name)s``
    패턴으로 이름을 합성하므로, ORM 에서는 짧은 접미 이름만 지정하고 최종 풀
    이름은 convention 을 통해 생성된다. Alembic 009 migration 은 convention 을
    거치지 않고 풀 이름을 직접 기재한다 (§D4-a 참조).
    """

    from sqlalchemy import CheckConstraint

    table = OrganizationQuota.__table__
    checks = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}

    # naming_convention 합성 결과
    assert "ck_tb_organization_quotas_monthly_limit_positive" in checks
    assert "ck_tb_organization_quotas_used_count_positive" in checks
    assert "ck_tb_organization_quotas_quota_type" in checks
    assert "ck_tb_organization_quotas_year_month_format" in checks


# ===========================================================================
# 3. QuotaService 순수 로직
# ===========================================================================
def test_current_year_month_format():
    """``YYYY-MM`` 형식 (길이 7, 정규식 매칭)."""

    import re

    ym = _current_year_month()
    assert len(ym) == 7
    assert re.match(r"^[0-9]{4}-(0[1-9]|1[0-2])$", ym) is not None


def test_default_monthly_limit_contains_required_types():
    """DALL-E 와 Unsplash 기본 한도가 정의되어 있다."""

    assert DEFAULT_MONTHLY_LIMIT["dalle_monthly"] == 100
    assert "unsplash_monthly" in DEFAULT_MONTHLY_LIMIT
    assert DEFAULT_MONTHLY_LIMIT["unsplash_monthly"] > 0


@pytest.mark.anyio
async def test_check_and_consume_quota_rejects_non_positive_amount():
    """amount <= 0 은 ValueError."""

    with pytest.raises(ValueError, match="positive"):
        await QuotaService.check_and_consume_quota(
            db=None,  # type: ignore[arg-type]
            organization_id=uuid.uuid4(),
            quota_type="dalle_monthly",
            amount=0,
        )

    with pytest.raises(ValueError, match="positive"):
        await QuotaService.check_and_consume_quota(
            db=None,  # type: ignore[arg-type]
            organization_id=uuid.uuid4(),
            quota_type="dalle_monthly",
            amount=-1,
        )


# ===========================================================================
# 4. Alembic 009 migration 메타데이터 검증
# ===========================================================================
def _load_migration_module():
    """009 migration 파일을 독립 모듈로 로드."""

    backend_dir = Path(__file__).resolve().parent.parent
    path = backend_dir / "alembic" / "versions" / "009_organization_quotas.py"
    spec = importlib.util.spec_from_file_location("alembic_009", path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_alembic_009_revision_metadata():
    """009 revision / down_revision 이 008 skip 방침을 따른다."""

    m = _load_migration_module()
    assert m.revision == "009_organization_quotas"
    # 008 skip → 직접 007 을 참조해야 한다.
    assert m.down_revision == "007_documents_v2"
    assert m.branch_labels is None
    assert m.depends_on is None


def test_alembic_009_quota_types_constants():
    """허용 quota_type 은 dalle_monthly + unsplash_monthly 2종."""

    m = _load_migration_module()
    assert set(m.QUOTA_TYPES) == {"dalle_monthly", "unsplash_monthly"}


def test_alembic_009_has_upgrade_and_downgrade():
    """upgrade / downgrade 함수가 모두 정의되어 있다."""

    m = _load_migration_module()
    assert callable(m.upgrade)
    assert callable(m.downgrade)


# ===========================================================================
# 5. Phase 4 S3 D5 — get_all_quotas_current_month
# ===========================================================================
@pytest.mark.anyio
async def test_get_all_quotas_current_month_returns_all_types():
    """DEFAULT_MONTHLY_LIMIT 의 모든 quota_type 을 on-demand 로 생성한다."""

    from unittest.mock import AsyncMock, patch

    org_id = uuid.uuid4()

    # get_or_create_quota 를 mock — 호출된 quota_type 별로 서로 다른 quota 반환.
    def _fake_quota_factory(_db, _org, quota_type, **_kwargs):
        fake = OrganizationQuota(
            organization_id=_org,
            quota_type=quota_type,
            year_month="2026-04",
            monthly_limit=DEFAULT_MONTHLY_LIMIT[quota_type],
            used_count=5,
        )
        return fake

    mock_get_or_create = AsyncMock(side_effect=_fake_quota_factory)

    with patch(
        "app.modules.organizations.service.QuotaService.get_or_create_quota",
        new=mock_get_or_create,
    ):
        result = await QuotaService.get_all_quotas_current_month(
            db=None,  # type: ignore[arg-type]
            organization_id=org_id,
            year_month="2026-04",
        )

    # 모든 quota_type 에 대해 호출되었고, 각각 quota 를 반환.
    assert set(result.keys()) == set(DEFAULT_MONTHLY_LIMIT.keys())
    assert result["dalle_monthly"].monthly_limit == DEFAULT_MONTHLY_LIMIT["dalle_monthly"]
    assert result["dalle_monthly"].used_count == 5
    # 호출 횟수 = quota_type 갯수.
    assert mock_get_or_create.await_count == len(DEFAULT_MONTHLY_LIMIT)


# ===========================================================================
# 6. Phase 4 S3 D5 — GET /organizations/{org_id}/quotas/current 라우터
# ===========================================================================
@pytest.mark.anyio
async def test_quotas_current_endpoint_returns_status_map():
    """라우터가 QuotaStatusResponse 맵을 반환한다. super_admin 은 모든 조직 조회."""

    from unittest.mock import AsyncMock, MagicMock, patch

    from app.modules.organizations.router import get_current_quotas
    from app.modules.organizations.schemas import OrganizationQuotasCurrentResponse

    org_id = uuid.uuid4()

    # 조직 존재 확인용 mock
    fake_org = MagicMock()
    fake_org.id = org_id

    def _fake_quota(quota_type, used):
        return OrganizationQuota(
            organization_id=org_id,
            quota_type=quota_type,
            year_month="2026-04",
            monthly_limit=DEFAULT_MONTHLY_LIMIT[quota_type],
            used_count=used,
        )

    fake_quotas = {
        "dalle_monthly": _fake_quota("dalle_monthly", 23),
        "unsplash_monthly": _fake_quota("unsplash_monthly", 1000),
    }

    # super_admin 사용자.
    current_user = MagicMock()
    current_user.role = "super_admin"
    current_user.organization_id = uuid.uuid4()  # 다른 조직이어도 super_admin 은 OK.

    with (
        patch(
            "app.modules.organizations.router.OrganizationService.get_organization",
            new=AsyncMock(return_value=fake_org),
        ),
        patch(
            "app.modules.organizations.router.QuotaService.get_all_quotas_current_month",
            new=AsyncMock(return_value=fake_quotas),
        ),
        patch(
            "app.modules.organizations.router._current_year_month",
            return_value="2026-04",
        ),
    ):
        response = await get_current_quotas(
            org_id=org_id,
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert isinstance(response, OrganizationQuotasCurrentResponse)
    assert response.organization_id == org_id
    assert response.year_month == "2026-04"

    dalle = response.quotas["dalle_monthly"]
    assert dalle.monthly_limit == DEFAULT_MONTHLY_LIMIT["dalle_monthly"]
    assert dalle.used_count == 23
    assert dalle.remaining == DEFAULT_MONTHLY_LIMIT["dalle_monthly"] - 23
    assert dalle.year_month == "2026-04"

    unsplash = response.quotas["unsplash_monthly"]
    assert unsplash.used_count == 1000


@pytest.mark.anyio
async def test_quotas_current_endpoint_rejects_other_org_for_non_super_admin():
    """admin/org_admin 이어도 다른 조직 쿼터 조회는 403."""

    from unittest.mock import MagicMock

    from fastapi import HTTPException

    from app.modules.organizations.router import get_current_quotas

    org_id = uuid.uuid4()
    other_org = uuid.uuid4()

    current_user = MagicMock()
    current_user.role = "admin"
    current_user.organization_id = other_org  # 요청 org_id 와 불일치.

    with pytest.raises(HTTPException) as exc_info:
        await get_current_quotas(
            org_id=org_id,
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403
    assert "권한" in exc_info.value.detail


@pytest.mark.anyio
async def test_quotas_current_endpoint_allows_member_of_same_org():
    """같은 조직 소속이면 super_admin 이 아니어도 조회 가능."""

    from unittest.mock import AsyncMock, MagicMock, patch

    from app.modules.organizations.router import get_current_quotas

    org_id = uuid.uuid4()

    fake_org = MagicMock()
    fake_org.id = org_id

    current_user = MagicMock()
    current_user.role = "org_admin"
    current_user.organization_id = org_id  # 일치.

    fake_quotas = {
        "dalle_monthly": OrganizationQuota(
            organization_id=org_id,
            quota_type="dalle_monthly",
            year_month="2026-04",
            monthly_limit=100,
            used_count=0,
        ),
        "unsplash_monthly": OrganizationQuota(
            organization_id=org_id,
            quota_type="unsplash_monthly",
            year_month="2026-04",
            monthly_limit=10000,
            used_count=0,
        ),
    }

    with (
        patch(
            "app.modules.organizations.router.OrganizationService.get_organization",
            new=AsyncMock(return_value=fake_org),
        ),
        patch(
            "app.modules.organizations.router.QuotaService.get_all_quotas_current_month",
            new=AsyncMock(return_value=fake_quotas),
        ),
    ):
        response = await get_current_quotas(
            org_id=org_id,
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert response.organization_id == org_id
    assert "dalle_monthly" in response.quotas
    assert response.quotas["dalle_monthly"].remaining == 100


# ===========================================================================
# 7. Phase 4 S3 D6 — PUT /organizations/{org_id}/quotas/{quota_type}
# ===========================================================================
@pytest.mark.anyio
async def test_update_quota_limit_rejects_unknown_quota_type():
    """지원하지 않는 quota_type 은 400 으로 차단된다."""

    from unittest.mock import MagicMock

    from fastapi import HTTPException

    from app.modules.organizations.router import update_quota_limit
    from app.modules.organizations.schemas import QuotaUpdateRequest

    current_user = MagicMock()
    current_user.role = "super_admin"
    current_user.organization_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await update_quota_limit(
            org_id=uuid.uuid4(),
            quota_type="unknown_type",
            data=QuotaUpdateRequest(monthly_limit=50),
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert exc_info.value.status_code == 400
    assert "지원하지 않는" in exc_info.value.detail


@pytest.mark.anyio
async def test_update_quota_limit_rejects_other_org_for_non_super_admin():
    """org_admin 이 타 조직 쿼터를 수정하려 하면 403."""

    from unittest.mock import MagicMock

    from fastapi import HTTPException

    from app.modules.organizations.router import update_quota_limit
    from app.modules.organizations.schemas import QuotaUpdateRequest

    org_id = uuid.uuid4()
    other_org = uuid.uuid4()

    current_user = MagicMock()
    current_user.role = "org_admin"
    current_user.organization_id = other_org

    with pytest.raises(HTTPException) as exc_info:
        await update_quota_limit(
            org_id=org_id,
            quota_type="dalle_monthly",
            data=QuotaUpdateRequest(monthly_limit=50),
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_update_quota_limit_rejects_non_admin_roles():
    """member / viewer 등 관리자 아닌 역할은 403."""

    from unittest.mock import MagicMock

    from fastapi import HTTPException

    from app.modules.organizations.router import update_quota_limit
    from app.modules.organizations.schemas import QuotaUpdateRequest

    org_id = uuid.uuid4()

    current_user = MagicMock()
    current_user.role = "member"
    current_user.organization_id = org_id  # 같은 조직이어도 역할 부족.

    with pytest.raises(HTTPException) as exc_info:
        await update_quota_limit(
            org_id=org_id,
            quota_type="dalle_monthly",
            data=QuotaUpdateRequest(monthly_limit=50),
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_update_quota_limit_super_admin_can_update_any_org():
    """super_admin 은 타 조직 쿼터도 수정 가능. 응답은 QuotaStatusResponse."""

    from unittest.mock import AsyncMock, MagicMock, patch

    from app.modules.organizations.router import update_quota_limit
    from app.modules.organizations.schemas import QuotaStatusResponse, QuotaUpdateRequest

    org_id = uuid.uuid4()

    fake_org = MagicMock()
    fake_org.id = org_id

    updated_quota = OrganizationQuota(
        organization_id=org_id,
        quota_type="dalle_monthly",
        year_month="2026-04",
        monthly_limit=250,
        used_count=17,
    )

    current_user = MagicMock()
    current_user.role = "super_admin"
    current_user.organization_id = uuid.uuid4()  # 타 조직이지만 super_admin 은 OK.

    with (
        patch(
            "app.modules.organizations.router.OrganizationService.get_organization",
            new=AsyncMock(return_value=fake_org),
        ),
        patch(
            "app.modules.organizations.router.QuotaService.update_monthly_limit",
            new=AsyncMock(return_value=updated_quota),
        ),
    ):
        response = await update_quota_limit(
            org_id=org_id,
            quota_type="dalle_monthly",
            data=QuotaUpdateRequest(monthly_limit=250),
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert isinstance(response, QuotaStatusResponse)
    assert response.monthly_limit == 250
    assert response.used_count == 17
    assert response.remaining == 233


@pytest.mark.anyio
async def test_update_quota_limit_org_admin_same_org_allowed():
    """org_admin 이 본인 조직 쿼터를 수정하면 성공."""

    from unittest.mock import AsyncMock, MagicMock, patch

    from app.modules.organizations.router import update_quota_limit
    from app.modules.organizations.schemas import QuotaUpdateRequest

    org_id = uuid.uuid4()

    fake_org = MagicMock()
    fake_org.id = org_id

    updated_quota = OrganizationQuota(
        organization_id=org_id,
        quota_type="unsplash_monthly",
        year_month="2026-04",
        monthly_limit=5000,
        used_count=0,
    )

    current_user = MagicMock()
    current_user.role = "org_admin"
    current_user.organization_id = org_id  # 일치.

    with (
        patch(
            "app.modules.organizations.router.OrganizationService.get_organization",
            new=AsyncMock(return_value=fake_org),
        ),
        patch(
            "app.modules.organizations.router.QuotaService.update_monthly_limit",
            new=AsyncMock(return_value=updated_quota),
        ),
    ):
        response = await update_quota_limit(
            org_id=org_id,
            quota_type="unsplash_monthly",
            data=QuotaUpdateRequest(monthly_limit=5000),
            db=None,  # type: ignore[arg-type]
            current_user=current_user,
        )

    assert response.monthly_limit == 5000
    assert response.remaining == 5000


@pytest.mark.anyio
async def test_update_quota_limit_service_rejects_negative_limit():
    """QuotaService.update_monthly_limit 는 음수 입력에 ValueError."""

    with pytest.raises(ValueError, match="non-negative"):
        await QuotaService.update_monthly_limit(
            db=None,  # type: ignore[arg-type]
            organization_id=uuid.uuid4(),
            quota_type="dalle_monthly",
            new_limit=-1,
        )
