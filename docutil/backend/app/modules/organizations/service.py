"""Business logic for organisation, department, and quota management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Department, Organization, OrganizationQuota
from .schemas import (
    DepartmentCreate,
    DepartmentTreeResponse,
    DepartmentUpdate,
    OrganizationUpdate,
)

# ---------------------------------------------------------------------------
# Organisation service
# ---------------------------------------------------------------------------


class OrganizationService:
    """Static service methods for organisation operations."""

    @staticmethod
    async def get_organization(
        db: AsyncSession,
        org_id: UUID,
    ) -> Organization:
        """Return a single organisation by ID or raise 404."""
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )
        return org

    @staticmethod
    async def update_organization(
        db: AsyncSession,
        org_id: UUID,
        data: OrganizationUpdate,
    ) -> Organization:
        """Update an organisation with the supplied fields."""
        org = await OrganizationService.get_organization(db, org_id)

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(org, field, value)

        await db.flush()
        await db.refresh(org)
        return org


# ---------------------------------------------------------------------------
# Department service
# ---------------------------------------------------------------------------


class DepartmentService:
    """Static service methods for department CRUD and tree operations."""

    @staticmethod
    async def create_department(
        db: AsyncSession,
        org_id: UUID,
        data: DepartmentCreate,
    ) -> Department:
        """Create a new department under the given organisation.

        Automatically computes the ``depth`` and materialized ``path``
        from the parent department (if any).
        """
        # Ensure the organisation exists
        org_result = await db.execute(select(Organization).where(Organization.id == org_id))
        if org_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found.",
            )

        depth = 0
        parent_path = "/"

        if data.parent_id is not None:
            parent = await DepartmentService._get_department(db, data.parent_id)

            # Parent must belong to the same organisation
            if parent.organization_id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent department does not belong to this organisation.",
                )

            depth = parent.depth + 1
            parent_path = parent.path

        department = Department(
            organization_id=org_id,
            parent_id=data.parent_id,
            name=data.name,
            depth=depth,
            path="/",  # temporary; updated after flush to get the real id
        )
        db.add(department)
        await db.flush()

        # Build the materialized path now that we have the id
        department.path = f"{parent_path}{department.id}/"
        await db.flush()
        await db.refresh(department)
        return department

    @staticmethod
    async def get_departments(
        db: AsyncSession,
        org_id: UUID,
    ) -> list[Department]:
        """Return a flat list of all departments for an organisation."""
        result = await db.execute(
            select(Department).where(Department.organization_id == org_id).order_by(Department.path)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_department_tree(
        db: AsyncSession,
        org_id: UUID,
    ) -> list[DepartmentTreeResponse]:
        """Build a nested tree structure of departments for an organisation.

        Fetches all departments in one query and assembles the tree in memory.
        """
        departments = await DepartmentService.get_departments(db, org_id)

        # Build lookup tables (avoid ORM lazy-load by constructing manually)
        node_map: dict[UUID, DepartmentTreeResponse] = {}
        for dept in departments:
            node_map[dept.id] = DepartmentTreeResponse(
                id=dept.id,
                organization_id=dept.organization_id,
                parent_id=dept.parent_id,
                name=dept.name,
                depth=dept.depth,
                path=dept.path,
                created_at=dept.ins_dt,
                children=[],
            )

        # Assemble tree
        roots: list[DepartmentTreeResponse] = []
        for node in node_map.values():
            if node.parent_id is not None and node.parent_id in node_map:
                node_map[node.parent_id].children.append(node)
            else:
                roots.append(node)

        return roots

    @staticmethod
    async def update_department(
        db: AsyncSession,
        dept_id: UUID,
        data: DepartmentUpdate,
    ) -> Department:
        """Update a department's name and/or parent.

        If ``parent_id`` changes, the depth and path are recomputed.
        """
        department = await DepartmentService._get_department(db, dept_id)

        update_fields = data.model_dump(exclude_unset=True)

        # Handle parent change -- recompute depth and path
        if "parent_id" in update_fields:
            new_parent_id = update_fields.pop("parent_id")

            if new_parent_id is not None:
                # Prevent circular reference
                if new_parent_id == dept_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="A department cannot be its own parent.",
                    )

                parent = await DepartmentService._get_department(db, new_parent_id)
                if parent.organization_id != department.organization_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent department does not belong to the same organisation.",
                    )

                department.parent_id = new_parent_id
                department.depth = parent.depth + 1
                department.path = f"{parent.path}{department.id}/"
            else:
                department.parent_id = None
                department.depth = 0
                department.path = f"/{department.id}/"

        for field, value in update_fields.items():
            setattr(department, field, value)

        await db.flush()
        await db.refresh(department)
        return department

    @staticmethod
    async def delete_department(
        db: AsyncSession,
        dept_id: UUID,
    ) -> None:
        """Delete a department by ID. Child departments cascade-delete.

        Raises 404 if not found.
        """
        department = await DepartmentService._get_department(db, dept_id)
        await db.delete(department)
        await db.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _get_department(
        db: AsyncSession,
        dept_id: UUID,
    ) -> Department:
        """Fetch a single department or raise 404."""
        result = await db.execute(select(Department).where(Department.id == dept_id))
        department = result.scalar_one_or_none()
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department '{dept_id}' not found.",
            )
        return department


# ---------------------------------------------------------------------------
# Quota service
# ---------------------------------------------------------------------------

#: 기본 월별 한도 (quota_type 별). 조직별 커스텀은 관리자 UI 에서 오버라이드.
DEFAULT_MONTHLY_LIMIT: dict[str, int] = {
    "dalle_monthly": 100,
    "unsplash_monthly": 10_000,  # Unsplash 는 사실상 무제한, 통계 집계용.
}


def _current_year_month() -> str:
    """UTC 기준 현재 연-월을 ``YYYY-MM`` 형식으로 반환."""

    now = datetime.now(UTC)
    return f"{now.year:04d}-{now.month:02d}"


class QuotaService:
    """조직별 월 쿼터 조회/차감 헬퍼.

    설계 요점:

    * 동시성 안전: ``SELECT ... FOR UPDATE`` (pg) 로 레코드 락 후 업데이트.
    * on-demand 생성: 해당 월 레코드가 없으면 INSERT ... ON CONFLICT DO NOTHING
      으로 race-safe 하게 생성 후 재조회.
    * SQLite 테스트 환경: ``FOR UPDATE`` 는 SQLite 에서 no-op 이므로 동작은 하되
      진정한 동시성 보호는 PostgreSQL 한정.
    """

    @staticmethod
    async def get_or_create_quota(
        db: AsyncSession,
        organization_id: UUID,
        quota_type: str,
        *,
        year_month: str | None = None,
    ) -> OrganizationQuota:
        """(org, type, year_month) 레코드 조회. 없으면 기본값으로 생성."""

        ym = year_month or _current_year_month()
        default_limit = DEFAULT_MONTHLY_LIMIT.get(quota_type, 100)

        # on-demand 생성: INSERT ... ON CONFLICT DO NOTHING (PostgreSQL).
        # SQLite 테스트 환경에서도 dialects.postgresql.insert 는 'OR IGNORE' 로
        # 호환되지 않으므로, fallback 으로 단순 SELECT → 없으면 ORM INSERT.
        stmt = select(OrganizationQuota).where(
            OrganizationQuota.organization_id == organization_id,
            OrganizationQuota.quota_type == quota_type,
            OrganizationQuota.year_month == ym,
        )
        result = await db.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota is not None:
            return quota

        # 없으면 신규 생성. IntegrityError 시 재조회 (동시 생성 경쟁 방어).
        quota = OrganizationQuota(
            organization_id=organization_id,
            quota_type=quota_type,
            year_month=ym,
            monthly_limit=default_limit,
            used_count=0,
        )
        db.add(quota)
        try:
            await db.flush()
        except Exception:
            # UNIQUE 경쟁에 패배한 경우 rollback 후 재조회.
            await db.rollback()
            result = await db.execute(stmt)
            quota = result.scalar_one()
        return quota

    @staticmethod
    async def get_all_quotas_current_month(
        db: AsyncSession,
        organization_id: UUID,
        *,
        year_month: str | None = None,
    ) -> dict[str, OrganizationQuota]:
        """이번 달의 모든 quota_type 레코드를 조회한다. 없으면 기본값으로 생성.

        Phase 4 S3 D5: FE ImageForm 이 DALL-E 잔여량을 표시하기 위해 호출하는
        GET /organizations/{org_id}/quotas/current 엔드포인트에서 사용.

        ``DEFAULT_MONTHLY_LIMIT`` 에 정의된 모든 quota_type 에 대해 on-demand
        레코드 생성을 보장한다. 결과는 ``{quota_type: OrganizationQuota}`` 맵.

        Args:
            db: AsyncSession.
            organization_id: 조직 ID.
            year_month: 대상 월. 기본은 UTC 현재 월.

        Returns:
            quota_type 별 OrganizationQuota 인스턴스 맵.
        """

        ym = year_month or _current_year_month()
        result: dict[str, OrganizationQuota] = {}
        for quota_type in DEFAULT_MONTHLY_LIMIT:
            quota = await QuotaService.get_or_create_quota(
                db,
                organization_id,
                quota_type,
                year_month=ym,
            )
            result[quota_type] = quota
        return result

    @staticmethod
    async def update_monthly_limit(
        db: AsyncSession,
        organization_id: UUID,
        quota_type: str,
        new_limit: int,
        *,
        year_month: str | None = None,
    ) -> OrganizationQuota:
        """현재 월 (또는 지정 월) 레코드의 ``monthly_limit`` 을 변경한다.

        Phase 4 S3 D6: 관리자 UI 가 월 쿼터 한도를 조정하기 위해 호출.

        동작:
            * 레코드가 없으면 기본값으로 on-demand 생성 후 한도만 교체.
            * ``used_count`` 는 건드리지 않는다 (소비는 별도 경로).
            * 입력 검증은 호출자(라우터) 가 Pydantic 으로 수행 — 여기서는
              음수 방어만 한 번 더 실행해 DB CHECK 를 타기 전에 에러를 낸다.

        Args:
            db: AsyncSession.
            organization_id: 조직 ID.
            quota_type: 'dalle_monthly' | 'unsplash_monthly'.
            new_limit: 적용할 월 한도. 0 이상.
            year_month: 대상 월. 기본은 UTC 현재 월.

        Returns:
            업데이트된 OrganizationQuota 인스턴스.

        Raises:
            ValueError: new_limit 이 음수일 때.
        """

        if new_limit < 0:
            raise ValueError("monthly_limit must be non-negative.")

        ym = year_month or _current_year_month()

        # 레코드 보장 — 없으면 기본값으로 생성 후 한도만 교체.
        quota = await QuotaService.get_or_create_quota(
            db,
            organization_id,
            quota_type,
            year_month=ym,
        )

        quota.monthly_limit = new_limit
        await db.flush()
        await db.refresh(quota)
        return quota

    @staticmethod
    async def check_and_consume_quota(
        db: AsyncSession,
        organization_id: UUID,
        quota_type: str,
        *,
        amount: int = 1,
        year_month: str | None = None,
    ) -> bool:
        """쿼터 확인 후 가능하면 차감.

        Args:
            db: AsyncSession.
            organization_id: 조직 ID.
            quota_type: 'dalle_monthly' | 'unsplash_monthly'.
            amount: 소비할 수량 (기본 1).
            year_month: 대상 월. 기본은 UTC 현재 월.

        Returns:
            True — 한도 내, used_count 가 ``amount`` 만큼 증가됨.
            False — 한도 초과, used_count 변화 없음.

        Raises:
            ValueError: ``amount`` 가 양수가 아닐 때.
        """

        if amount <= 0:
            raise ValueError("amount must be positive.")

        ym = year_month or _current_year_month()

        # 먼저 레코드 존재 보장.
        await QuotaService.get_or_create_quota(
            db,
            organization_id,
            quota_type,
            year_month=ym,
        )

        # FOR UPDATE 락. PostgreSQL 에서는 행 락, SQLite 에서는 no-op.
        stmt = (
            select(OrganizationQuota)
            .where(
                OrganizationQuota.organization_id == organization_id,
                OrganizationQuota.quota_type == quota_type,
                OrganizationQuota.year_month == ym,
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        quota = result.scalar_one()

        if quota.used_count + amount > quota.monthly_limit:
            return False

        quota.used_count += amount
        await db.flush()
        return True


__all__ = [
    "DepartmentService",
    "OrganizationService",
    "QuotaService",
    "DEFAULT_MONTHLY_LIMIT",
]
