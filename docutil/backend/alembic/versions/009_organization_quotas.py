"""009 — 조직별 월 쿼터 관리 테이블 (DALL-E / Unsplash).

Revision ID: 009_organization_quotas
Revises: 007_documents_v2
Create Date: 2026-04-22 00:00:00.000000

NOTE ON NUMBERING
    008 번호는 `docs/phase4_s2_d6_alembic_008_skip_rationale.md` 에서 명시적으로
    skip 되었다 (외부 고객사 온보딩 시 `tb_organizations.organization_type`
    컬럼 추가 용도로 예약). 본 migration 은 009 로 승격해 진행한다.

Scope (phase3_execution_roadmap.md §2.3 S3 D4):
    1. tb_organization_quotas — 조직별 월 단위 외부 이미지 생성 API 쿼터 관리
       - quota_type: `dalle_monthly` (과금), `unsplash_monthly` (통계/한도 추적)
       - year_month: 'YYYY-MM' 형식. 매월 레코드 on-demand 생성.
       - 동시성: UNIQUE + INSERT...ON CONFLICT 패턴 또는 FOR UPDATE lock 전제.
       - 조직 삭제 시 쿼터 이력 CASCADE drop. 장기 보존이 필요하면
         별도 `tb_organization_quota_history` 아카이브 테이블을 추후 도입.

실제 마이그레이션 실행 일정:
    - 본 파일은 작성만 완료된 상태이며 ``alembic upgrade head`` 는 Phase 4
      S3 D5 통합 단계 또는 S3 D10 배포 시에 수행한다 (로드맵 §2.3).

Downgrade:
    - 인덱스 2종 drop → 테이블 drop 순서. FK 참조 없으므로 단순.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# -- Alembic 리비전 식별자 --------------------------------------------------
revision: str = "009_organization_quotas"
down_revision: str | None = "007_documents_v2"  # 008 skip
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
# 허용 quota_type. 신규 타입 추가 시 CHECK 제약 갱신 migration 필요.
QUOTA_TYPES: tuple[str, ...] = (
    "dalle_monthly",
    "unsplash_monthly",
)


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """tb_organization_quotas 테이블 및 인덱스 생성."""

    op.create_table(
        "tb_organization_quotas",
        # -- 기본 컬럼 --
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="쿼터 레코드 PK (UUID v4).",
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
            comment="쿼터 소유 조직. 조직 삭제 시 이력 일괄 삭제.",
        ),
        sa.Column(
            "quota_type",
            sa.String(50),
            nullable=False,
            comment="쿼터 유형. dalle_monthly / unsplash_monthly 등.",
        ),
        sa.Column(
            "year_month",
            sa.String(7),
            nullable=False,
            comment="적용 월 ('YYYY-MM'). 서비스 계층에서 현재 월 기준 생성/조회.",
        ),
        sa.Column(
            "monthly_limit",
            sa.Integer,
            nullable=False,
            server_default=sa.text("100"),
            comment="월별 최대 허용 횟수. 기본 100 (DALL-E 가정).",
        ),
        sa.Column(
            "used_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
            comment="해당 월 누적 사용량. 초과 시 서비스 계층에서 403 반환.",
        ),
        # -- audit columns (AuditMixin 과 정합) --
        sa.Column(
            "ins_dt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ins_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("ins_ip", sa.String(45), nullable=True),
        sa.Column(
            "upd_dt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("upd_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("upd_ip", sa.String(45), nullable=True),
        # -- 제약조건 --
        sa.UniqueConstraint(
            "organization_id",
            "quota_type",
            "year_month",
            name="uq_tb_organization_quotas_org_type_month",
        ),
        sa.CheckConstraint(
            "monthly_limit >= 0",
            name="ck_tb_organization_quotas_monthly_limit_positive",
        ),
        sa.CheckConstraint(
            "used_count >= 0",
            name="ck_tb_organization_quotas_used_count_positive",
        ),
        sa.CheckConstraint(
            "quota_type IN (" + ",".join(f"'{t}'" for t in QUOTA_TYPES) + ")",
            name="ck_tb_organization_quotas_quota_type",
        ),
        sa.CheckConstraint(
            # 'YYYY-MM' 형식 강제 (숫자 4자리 + '-' + 숫자 2자리).
            "year_month ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
            name="ck_tb_organization_quotas_year_month_format",
        ),
    )

    # -- 인덱스 --
    # 1) 조직별 월별 조회 — 관리자 대시보드 (월 단위 쿼터 사용량 조회).
    op.create_index(
        "idx_tb_organization_quotas_org_month",
        "tb_organization_quotas",
        ["organization_id", "year_month"],
    )
    # 2) 룩업 인덱스 — 서비스 계층 check_and_consume_quota() 핫패스.
    #    UNIQUE 제약으로 이미 인덱스가 생성되지만, 명시적 네이밍 확보를 위해 유지.
    op.create_index(
        "idx_tb_organization_quotas_lookup",
        "tb_organization_quotas",
        ["organization_id", "quota_type", "year_month"],
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """tb_organization_quotas 제거 (인덱스 → 테이블 순)."""

    op.drop_index(
        "idx_tb_organization_quotas_lookup",
        table_name="tb_organization_quotas",
    )
    op.drop_index(
        "idx_tb_organization_quotas_org_month",
        table_name="tb_organization_quotas",
    )
    op.drop_table("tb_organization_quotas")
