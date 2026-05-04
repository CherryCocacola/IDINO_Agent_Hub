"""007 — documents_v2 신규 테이블 + 템플릿 통합 + agent_type 확장.

Revision ID: 007_documents_v2
Revises: 006_evaluation
Create Date: 2026-04-19 00:00:00.000000

NOTE ON NUMBERING
    사용자 요청 원문은 "Alembic 006 draft" 였으나, 기존 저장소에 이미
    006_evaluation_module 이 존재하여 번호 충돌을 피하기 위해 007 로 승격했다.
    내용·범위는 phase1_architecture.md §부록 E.1 과 동일하다.

Scope (phase1_architecture.md 부록 E.1):
    1. tb_documents_v2              — DocumentSchema JSONB + 비정규화 필터 컬럼
    2. tb_documents_v2_templates    — Mode B 양식 채우기 템플릿
    3. tb_agents.agent_type CHECK   — freeform_doc 추가 (기존 chatbot/report/
                                      proposal/minutes 와 함께)
    4. tb_generated_reports 리네이밍 -> tb_generated_reports_archive
       (Phase 4 S7 에서 완전 제거)

Phase 1 DRAFT 주의사항:
    - 본 파일은 ``alembic upgrade head`` 로 즉시 실행되면 안 된다.
    - 실제 이관은 Phase 4 스프린트 일정에서 수행된다.
    - 데이터 이관 (tb_document_templates -> tb_documents_v2_templates 변환) 은
      본 마이그레이션에 포함하지 않고, 별도 데이터 스크립트(S4) 에서 수행한다.

Downgrade:
    - tb_generated_reports_archive 를 tb_generated_reports 로 원복.
    - freeform_doc CHECK 제약을 이전 상태로 복귀 (단, 제약이 원래 없었으므로
      downgrade 에서는 제약을 drop 하고 새 제약을 달지 않는다).
    - tb_documents_v2_templates, tb_documents_v2 순으로 drop (FK 방향 고려).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# -- Alembic 리비전 식별자 --------------------------------------------------
revision: str = "007_documents_v2"
down_revision: str | None = "006_evaluation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _audit_columns() -> list:
    """공통 audit columns (003 에서 사용된 패턴 재활용)."""

    return [
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
    ]


DOCUMENT_TYPES = (
    "slide_report",
    "docx_report",
    "proposal",
    "minutes",
    "one_pager",
    "weekly_status",
    "freeform_doc",
)

AGENT_TYPES_NEW = (
    "chatbot",
    "report",
    "proposal",
    "minutes",
    "freeform_doc",
)


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # =====================================================================
    # 1. tb_documents_v2_templates 먼저 생성 (tb_documents_v2 가 FK 참조)
    # =====================================================================
    op.create_table(
        "tb_documents_v2_templates",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "document_type",
            sa.String(32),
            nullable=False,
            comment="slide_report / docx_report / proposal / minutes / "
            "one_pager / weekly_status / freeform_doc",
        ),
        sa.Column(
            "schema_version",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "skeleton_schema",
            JSONB,
            nullable=False,
            comment="DocumentSchema skeleton (locked 컴포넌트 포함).",
        ),
        sa.Column(
            "slot_definitions",
            JSONB,
            nullable=True,
            comment="[{anchor, category, description, default_value, required}]",
        ),
        sa.Column("sample_prompt", sa.Text, nullable=True),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_by_user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_users.id", ondelete="SET NULL"),
            nullable=False,
        ),
        *_audit_columns(),
        sa.CheckConstraint(
            "document_type IN (" + ",".join(f"'{t}'" for t in DOCUMENT_TYPES) + ")",
            name="ck_tb_documents_v2_templates_document_type",
        ),
        sa.CheckConstraint(
            "schema_version >= 1",
            name="ck_tb_documents_v2_templates_schema_version",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "name",
            name="uq_tb_documents_v2_templates_org_name",
        ),
    )
    op.create_index(
        "idx_tb_documents_v2_templates_org_type",
        "tb_documents_v2_templates",
        ["organization_id", "document_type"],
    )
    op.create_index(
        "idx_tb_documents_v2_templates_is_active",
        "tb_documents_v2_templates",
        ["is_active"],
    )
    # JSONB skeleton 에 대한 GIN 인덱스 (anchor / locked 필터용).
    op.execute(
        "CREATE INDEX idx_tb_documents_v2_templates_skeleton_gin "
        "ON tb_documents_v2_templates USING gin (skeleton_schema jsonb_path_ops)"
    )

    # =====================================================================
    # 2. tb_documents_v2 생성
    # =====================================================================
    op.create_table(
        "tb_documents_v2",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "schema_version",
            sa.Integer,
            nullable=False,
            server_default="1",
            comment="DocumentSchema 메이저 버전. JSONB 해석기 분기용.",
        ),
        sa.Column(
            "document_type",
            sa.String(32),
            nullable=False,
            comment="JSONB type 필드의 비정규화 사본.",
        ),
        sa.Column(
            "mode",
            sa.String(20),
            nullable=False,
            comment="free_generation | template_fill",
        ),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "generated_by_user_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "agent_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "template_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_documents_v2_templates.id", ondelete="RESTRICT"),
            nullable=True,
            comment="mode='template_fill' 인 경우 NOT NULL (CHECK).",
        ),
        sa.Column(
            "source_chat_session_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_chat_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "source_document_ids",
            ARRAY(PG_UUID(as_uuid=True)),
            nullable=True,
            comment="RAG 인용 원본 문서 ID. FK 대신 ARRAY + 애플리케이션 검증.",
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
            comment="draft | generating | completed | error | archived",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("llm_provider", sa.String(32), nullable=True),
        sa.Column("llm_model", sa.String(128), nullable=True),
        sa.Column("prompt_tokens", sa.Integer, nullable=True),
        sa.Column("completion_tokens", sa.Integer, nullable=True),
        sa.Column(
            "document_schema",
            JSONB,
            nullable=False,
            comment="DocumentSchema v1 전체 (루트 포함).",
        ),
        *_audit_columns(),
        sa.CheckConstraint(
            "document_type IN (" + ",".join(f"'{t}'" for t in DOCUMENT_TYPES) + ")",
            name="ck_tb_documents_v2_document_type",
        ),
        sa.CheckConstraint(
            "mode IN ('free_generation','template_fill')",
            name="ck_tb_documents_v2_mode",
        ),
        sa.CheckConstraint(
            "status IN ('draft','generating','completed','error','archived')",
            name="ck_tb_documents_v2_status",
        ),
        sa.CheckConstraint(
            "schema_version >= 1",
            name="ck_tb_documents_v2_schema_version",
        ),
        sa.CheckConstraint(
            "(mode = 'template_fill' AND template_id IS NOT NULL) OR "
            "(mode = 'free_generation' AND template_id IS NULL)",
            name="ck_tb_documents_v2_template_consistency",
        ),
    )
    # ── B-tree 인덱스 (빈번한 필터/정렬) ──
    op.create_index(
        "idx_tb_documents_v2_org_created",
        "tb_documents_v2",
        ["organization_id", sa.text("ins_dt DESC")],
    )
    op.create_index(
        "idx_tb_documents_v2_user_created",
        "tb_documents_v2",
        ["generated_by_user_id", sa.text("ins_dt DESC")],
    )
    op.create_index(
        "idx_tb_documents_v2_document_type",
        "tb_documents_v2",
        ["document_type"],
    )
    op.create_index("idx_tb_documents_v2_mode", "tb_documents_v2", ["mode"])
    op.create_index("idx_tb_documents_v2_status", "tb_documents_v2", ["status"])
    op.create_index("idx_tb_documents_v2_agent_id", "tb_documents_v2", ["agent_id"])
    op.create_index("idx_tb_documents_v2_template_id", "tb_documents_v2", ["template_id"])

    # ── GIN 인덱스 (JSONB 쿼리: 컴포넌트 타입 / anchor / locked 등) ──
    # jsonb_path_ops 는 @> 연산자만 지원하지만 인덱스 크기가 작고 쓰기 비용도 낮다.
    op.execute(
        "CREATE INDEX idx_tb_documents_v2_schema_gin "
        "ON tb_documents_v2 USING gin (document_schema jsonb_path_ops)"
    )

    # 함수 기반 인덱스: JSONB metadata.citations 길이(인용 유무) 필터링 고성능화.
    # pg_stat_statements 관찰 후 필요 시 활성 (draft 로는 주석 처리).
    # op.execute(
    #     "CREATE INDEX idx_tb_documents_v2_has_citations "
    #     "ON tb_documents_v2 ((jsonb_array_length(document_schema->'metadata'->'citations') > 0)) "
    #     "WHERE jsonb_array_length(document_schema->'metadata'->'citations') > 0"
    # )

    # =====================================================================
    # 3. tb_agents.agent_type CHECK 확장
    #    - 003 migration 에서 CHECK 제약 없이 String(20) 으로 생성되었음 확인.
    #    - 여기서 CHECK 제약을 새로 추가하여 freeform_doc 을 포함한 5 개로 고정.
    #    - String 길이는 20 이므로 'freeform_doc'(12자) 수용 가능.
    # =====================================================================
    op.create_check_constraint(
        "ck_tb_agents_agent_type",
        "tb_agents",
        "agent_type IN (" + ",".join(f"'{t}'" for t in AGENT_TYPES_NEW) + ")",
    )

    # =====================================================================
    # 4. tb_generated_reports 리네이밍 -> tb_generated_reports_archive
    #    - 소프트 폐기. 읽기 전용으로만 유지하고 신규 insert 는 없음.
    #    - FK / index 는 PostgreSQL 이 자동으로 따라온다. 제약 이름은 그대로.
    #    - Phase 4 S7 에서 tb_report_templates 와 함께 완전 drop.
    # =====================================================================
    op.rename_table("tb_generated_reports", "tb_generated_reports_archive")

    # (참고) 인덱스/제약 이름에 테이블명이 포함되어 있다면 재명명이 이상적이나,
    # 소프트 폐기 의도상 S7 에서 통째로 drop 되므로 이름 불일치는 허용한다.


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    # 4. 테이블 이름 복구
    op.rename_table("tb_generated_reports_archive", "tb_generated_reports")

    # 3. agent_type CHECK 제거 (003 이전 상태로 — 제약 없음)
    op.drop_constraint("ck_tb_agents_agent_type", "tb_agents", type_="check")

    # 2. tb_documents_v2 관련 인덱스 및 테이블 drop
    op.execute("DROP INDEX IF EXISTS idx_tb_documents_v2_schema_gin")
    op.drop_index("idx_tb_documents_v2_template_id", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_agent_id", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_status", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_mode", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_document_type", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_user_created", table_name="tb_documents_v2")
    op.drop_index("idx_tb_documents_v2_org_created", table_name="tb_documents_v2")
    op.drop_table("tb_documents_v2")

    # 1. templates drop (documents_v2 가 FK 참조하므로 반드시 뒤에)
    op.execute("DROP INDEX IF EXISTS idx_tb_documents_v2_templates_skeleton_gin")
    op.drop_index(
        "idx_tb_documents_v2_templates_is_active",
        table_name="tb_documents_v2_templates",
    )
    op.drop_index(
        "idx_tb_documents_v2_templates_org_type",
        table_name="tb_documents_v2_templates",
    )
    op.drop_table("tb_documents_v2_templates")
