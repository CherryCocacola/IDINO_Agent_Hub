"""documents_v2 ORM models.

Phase 1 에서는 두 개의 신규 테이블을 정의한다.

- ``DocumentV2`` -> ``tb_documents_v2``
    DocumentSchema(JSONB) 와 메타데이터를 저장하는 "생성된 문서" 본체.

- ``DocumentV2Template`` -> ``tb_documents_v2_templates``
    Mode B 양식 채우기용 템플릿. ``locked=true`` 컴포넌트가 포함된
    DocumentSchema skeleton 을 저장한다.

``Base`` 는 ``UUIDMixin`` 과 ``AuditMixin`` 을 자동 주입하므로 각 모델은
``id``, ``ins_dt``, ``ins_user``, ``ins_ip``, ``upd_dt``, ``upd_user``, ``upd_ip``
컬럼을 별도로 선언하지 않는다.

주의: 실제 Alembic 적용은 Phase 4 에서 수행된다. 본 모듈은 설계 기준선 확정용
draft 이며, 임포트 체인이 깨지지 않도록 service/router 는 아직 두지 않는다.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ---------------------------------------------------------------------------
# DocumentV2
# ---------------------------------------------------------------------------


class DocumentV2(Base):
    """생성된 문서 (보고서/회의록/제안서/자유문서 통합 엔티티).

    ``document_schema`` 컬럼에 DocumentSchema(JSONB) 전체가 저장된다.
    JSONB 내부 구조는 ``schemas.DocumentSchema`` 와 1:1 매칭되며,
    상위 컬럼은 색인·필터·권한 판정용으로 비정규화된 사본을 갖는다.

    비정규화 근거:
        1. JSONB 내부 필드 (예: ``type``, ``mode``) 를 거의 모든 목록 API 에서
           필터 조건으로 사용한다. GIN 인덱스로도 처리 가능하지만 B-tree 보다
           카디널리티 대비 조회 비용이 높다.
        2. organization scope, ownership 은 RBAC 의 기본 축이다.
    """

    __tablename__ = "tb_documents_v2"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('slide_report','docx_report','proposal','minutes',"
            "'one_pager','weekly_status','freeform_doc')",
            name="ck_tb_documents_v2_document_type",
        ),
        CheckConstraint(
            "mode IN ('free_generation','template_fill')",
            name="ck_tb_documents_v2_mode",
        ),
        CheckConstraint(
            "status IN ('draft','generating','completed','error','archived')",
            name="ck_tb_documents_v2_status",
        ),
        CheckConstraint(
            "schema_version >= 1",
            name="ck_tb_documents_v2_schema_version",
        ),
        # (mode='template_fill') <=> (template_id IS NOT NULL)
        CheckConstraint(
            "(mode = 'template_fill' AND template_id IS NOT NULL) OR "
            "(mode = 'free_generation' AND template_id IS NULL)",
            name="ck_tb_documents_v2_template_consistency",
        ),
        Index("idx_tb_documents_v2_org_created", "organization_id", "ins_dt"),
        Index("idx_tb_documents_v2_user_created", "generated_by_user_id", "ins_dt"),
        Index("idx_tb_documents_v2_document_type", "document_type"),
        Index("idx_tb_documents_v2_mode", "mode"),
        Index("idx_tb_documents_v2_status", "status"),
        Index("idx_tb_documents_v2_agent_id", "agent_id"),
        Index("idx_tb_documents_v2_template_id", "template_id"),
        # GIN 인덱스는 Alembic migration 에서 ``USING gin`` 으로 별도 생성한다.
        # (Index(postgresql_using='gin') 은 async 런타임에서 동작하지만 migration
        #  파일에서 명시적으로 관리하는 편이 기록·롤백 추적에 유리하다.)
    )

    # ── 스키마 버저닝 ──────────────────────────────────────────────
    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="DocumentSchema 메이저 버전. JSONB 해석기 분기에 사용.",
    )

    # ── 분류 (JSONB 값의 비정규화 사본) ────────────────────────────
    document_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="slide_report / docx_report / proposal / minutes / "
        "one_pager / weekly_status / freeform_doc",
    )
    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="free_generation | template_fill",
    )

    # ── 소유/조직 ────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="문서를 생성한 사용자. SET NULL 로 사용자 탈퇴 시에도 문서 보존.",
    )

    # ── 에이전트/템플릿 참조 ─────────────────────────────────────
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_agents.id", ondelete="SET NULL"),
        nullable=True,
        comment="생성에 사용된 에이전트. 에이전트 삭제되어도 이력 보존.",
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_documents_v2_templates.id", ondelete="RESTRICT"),
        nullable=True,
        comment="mode='template_fill' 인 경우 반드시 채워짐 (CHECK 로 강제).",
    )

    # ── 채팅 세션 ────────────────────────────────────────────────
    source_chat_session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── 출처 문서 (업로드 원본 참조 목록) ─────────────────────────
    source_document_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=True,
        comment="RAG 인용에 사용된 업로드 원본 문서 ID 목록. "
        "FK 제약 대신 ARRAY + 애플리케이션 레벨 검증.",
    )

    # ── 상태/제목 ────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="문서 제목. JSONB 의 pages[0].title 또는 metadata 에서 파생.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
        comment="draft | generating | completed | error | archived",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── LLM 통계 (JSONB metadata 의 사본이지만 집계 쿼리용) ──────
    llm_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── DocumentSchema 본체 ──────────────────────────────────────
    document_schema: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="DocumentSchema v1 전체. schemas.DocumentSchema 와 1:1.",
    )

    def __repr__(self) -> str:  # pragma: no cover - 디버깅용
        return (
            f"<DocumentV2 id={self.id!s} type={self.document_type!r} "
            f"mode={self.mode!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# DocumentV2Template
# ---------------------------------------------------------------------------


class DocumentV2Template(Base):
    """Mode B 양식 채우기 템플릿.

    DocumentSchema skeleton 을 저장하며, 내부 컴포넌트는 ``locked=true``
    를 통해 LLM 이 편집 불가한 영역을 표시한다. ``slot_definitions`` 에
    slot 별 카테고리 메타데이터(session_auto / user_input / ai_generated)
    를 둔다.
    """

    __tablename__ = "tb_documents_v2_templates"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('slide_report','docx_report','proposal','minutes',"
            "'one_pager','weekly_status','freeform_doc')",
            name="ck_tb_documents_v2_templates_document_type",
        ),
        CheckConstraint(
            "schema_version >= 1",
            name="ck_tb_documents_v2_templates_schema_version",
        ),
        UniqueConstraint(
            "organization_id", "name",
            name="uq_tb_documents_v2_templates_org_name",
        ),
        Index(
            "idx_tb_documents_v2_templates_org_type",
            "organization_id", "document_type",
        ),
        Index("idx_tb_documents_v2_templates_is_active", "is_active"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="이 템플릿이 생성하는 문서의 타입.",
    )
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )

    # ── Skeleton (locked 페이지 포함) ─────────────────────────────
    skeleton_schema: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="DocumentSchema skeleton. mode=template_fill 이 사용한다. "
        "locked=true 컴포넌트는 LLM 편집 금지.",
    )

    # ── Slot 정의 (카테고리/프롬프트/기본값) ─────────────────────
    slot_definitions: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="[{anchor, category, description, default_value, required}]. "
        "category in ('session_auto','user_input','ai_generated').",
    )

    # ── 샘플 프롬프트 (Mode B 호출 시 LLM 유도 문구) ──────────────
    sample_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── 운영 플래그 ──────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - 디버깅용
        return (
            f"<DocumentV2Template id={self.id!s} name={self.name!r} "
            f"type={self.document_type!r}>"
        )
