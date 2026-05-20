"""FastAPI router for organisation and department management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role

from .schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    DepartmentUpdate,
    OrganizationQuotasCurrentResponse,
    OrganizationResponse,
    OrganizationUpdate,
    QuotaStatusResponse,
    QuotaUpdateRequest,
)
from .service import (
    DEFAULT_MONTHLY_LIMIT,
    DepartmentService,
    OrganizationService,
    QuotaService,
    _current_year_month,
)

router = APIRouter(prefix="", tags=["organizations"])


# ---------------------------------------------------------------------------
# Organisation endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organisation",
)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Retrieve an organisation by its ID."""
    org = await OrganizationService.get_organization(db, org_id)
    return OrganizationResponse.model_validate(org)


@router.put(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organisation",
)
async def update_organization(
    org_id: UUID,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Update an organisation's name, description, or settings."""
    org = await OrganizationService.update_organization(db, org_id, data)
    return OrganizationResponse.model_validate(org)


# ---------------------------------------------------------------------------
# Department endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{org_id}/departments",
    response_model=list[DepartmentTreeResponse] | list[DepartmentResponse],
    summary="List departments",
)
async def list_departments(
    org_id: UUID,
    tree: bool = Query(False, description="Return nested tree structure when true"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Return departments for an organisation, either flat or as a nested tree.

    트랙 #106 결함 2': 데이터 소스는 AgentHub ``AIAgentManagement.Departments``
    + ``Users`` (read-only). member_count 는 각 부서별 ``Users.DepartmentId``
    카운트로 계산된다. 부서장(head_user) 컬럼은 AgentHub schema 에 없어 null.
    """
    if tree:
        return await DepartmentService.get_department_tree(db, org_id)

    departments = await DepartmentService.get_departments(db, org_id)
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.post(
    "/{org_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    org_id: UUID,
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Create a new department under the given organisation."""
    department = await DepartmentService.create_department(db, org_id, data)
    return DepartmentResponse.model_validate(department)


@router.put(
    "/{org_id}/departments/{dept_id}",
    response_model=DepartmentResponse,
    summary="Update department",
)
async def update_department(
    org_id: UUID,
    dept_id: UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Update a department's name or parent."""
    department = await DepartmentService.update_department(db, dept_id, data)

    # Verify the department belongs to the specified organisation
    if department.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{dept_id}' not found in organisation '{org_id}'.",
        )

    return DepartmentResponse.model_validate(department)


@router.delete(
    "/{org_id}/departments/{dept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete department",
)
async def delete_department(
    org_id: UUID,
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role(["admin", "super_admin"])),
):
    """Delete a department and all its children (cascade).

    트랙 #106 결함 2' 이후: read 경로는 AgentHub 마스터로 옮겼지만 본 write
    경로는 DocUtil ``tb_departments`` 를 그대로 사용한다. AgentHub schema
    에 대한 write 권한은 별도 트랙에서 다루며, 현재 운영 콘솔에서는 부서
    삭제 트리거가 사실상 호출되지 않는다.
    """
    # AgentHub 마스터 기준 존재 여부 확인.
    departments = await DepartmentService.get_departments(db, org_id)
    dept_ids = {d["id"] for d in departments}
    if str(dept_id) not in dept_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{dept_id}' not found in organisation '{org_id}'.",
        )

    await DepartmentService.delete_department(db, dept_id)


# ---------------------------------------------------------------------------
# Department members
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Quota endpoints (Phase 4 S3 D5)
# ---------------------------------------------------------------------------


@router.get(
    "/{org_id}/quotas/current",
    response_model=OrganizationQuotasCurrentResponse,
    summary="현재 월 조직 쿼터 현황",
)
async def get_current_quotas(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> OrganizationQuotasCurrentResponse:
    """조직 월 쿼터 현황 조회.

    Phase 4 S3 D5: FE ImageForm 이 DALL-E 잔여량을 표시하기 위해 호출한다.
    ``DEFAULT_MONTHLY_LIMIT`` 에 정의된 모든 quota_type 레코드를 on-demand 로
    생성한 뒤, 현재 사용량과 잔여 가능량을 반환한다.

    권한 정책:
        - super_admin: 모든 조직 조회 허용.
        - admin / org_admin / 기타: 본인 소속 조직만 조회 허용.
        - 그 외 조직 조회는 403 반환.

    Returns:
        OrganizationQuotasCurrentResponse — quota_type 을 key 로 한 맵.
    """

    # 조직 접근 권한 검증 — super_admin 을 제외하고는 본인 소속 조직만.
    if current_user.role != "super_admin" and (
        current_user.organization_id is None or current_user.organization_id != org_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본 조직의 쿼터를 조회할 권한이 없습니다.",
        )

    # 조직 존재 여부 확인 — 404 매핑.
    await OrganizationService.get_organization(db, org_id)

    ym = _current_year_month()
    quotas = await QuotaService.get_all_quotas_current_month(db, org_id, year_month=ym)

    status_map: dict[str, QuotaStatusResponse] = {}
    for quota_type, quota in quotas.items():
        remaining = max(quota.monthly_limit - quota.used_count, 0)
        status_map[quota_type] = QuotaStatusResponse(
            quota_type=quota_type,
            monthly_limit=quota.monthly_limit,
            used_count=quota.used_count,
            remaining=remaining,
            year_month=quota.year_month,
        )

    return OrganizationQuotasCurrentResponse(
        organization_id=org_id,
        year_month=ym,
        quotas=status_map,
    )


@router.put(
    "/{org_id}/quotas/{quota_type}",
    response_model=QuotaStatusResponse,
    summary="조직 월 쿼터 한도 수정",
)
async def update_quota_limit(
    org_id: UUID,
    quota_type: str,
    data: QuotaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> QuotaStatusResponse:
    """현재 월 쿼터의 ``monthly_limit`` 을 수정한다.

    Phase 4 S3 D6: 관리자 UI (``/quotas``) 에서 조직 월 한도를 조정할 때 호출.

    권한 정책:
        * super_admin: 모든 조직 수정 허용.
        * org_admin / admin: 본인 소속 조직만 허용.
        * 그 외 역할: 403.

    ``quota_type`` 은 ``DEFAULT_MONTHLY_LIMIT`` 에 정의된 값만 허용 — 그 외
    문자열은 400 으로 차단 (불특정 type 생성을 막는다).

    Returns:
        QuotaStatusResponse — 수정 후 상태 (used_count 는 변하지 않음).
    """

    # 1) quota_type 유효성 검사 (whitelist).
    if quota_type not in DEFAULT_MONTHLY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 quota_type 입니다: '{quota_type}'.",
        )

    # 2) 권한 검증 — super_admin / admin / org_admin 만, 그리고 타조직 금지.
    allowed_roles = {"super_admin", "admin", "org_admin"}
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="쿼터를 수정할 권한이 없습니다.",
        )
    if current_user.role != "super_admin" and (
        current_user.organization_id is None or current_user.organization_id != org_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본 조직의 쿼터만 수정할 수 있습니다.",
        )

    # 3) 조직 존재 여부 확인 — 404 매핑.
    await OrganizationService.get_organization(db, org_id)

    # 4) 한도 수정 (서비스 계층에 위임).
    try:
        quota = await QuotaService.update_monthly_limit(
            db,
            org_id,
            quota_type,
            data.monthly_limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    remaining = max(quota.monthly_limit - quota.used_count, 0)
    return QuotaStatusResponse(
        quota_type=quota.quota_type,
        monthly_limit=quota.monthly_limit,
        used_count=quota.used_count,
        remaining=remaining,
        year_month=quota.year_month,
    )


@router.get(
    "/{org_id}/departments/{dept_id}/members",
    summary="List department members",
)
async def list_department_members(
    org_id: UUID,
    dept_id: str = Path(
        ...,
        description="AgentHub Department PK (int) as string. e.g. '40'.",
    ),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Return users belonging to a specific department.

    트랙 #106 결함 2': DocUtil ``tb_users`` VIEW.department_id 가 NULL 로
    하드코딩되어 있어 정상 조회 불가. 대신 AgentHub ``Users.DepartmentId``
    (int) 를 직접 조회한다. ``dept_id`` 는 AgentHub int 를 문자열로 받으며
    서비스 계층이 int 변환 + 검증 (400) 을 담당한다.
    """
    return await DepartmentService.list_department_members(db, org_id, dept_id)
