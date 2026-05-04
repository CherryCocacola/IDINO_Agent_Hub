"""
ReportTemplate and GeneratedReport ORM models.

주의 (Phase 4 S2 D6 — ISSUE-D2-1 해소):
---------------------------------------
``GeneratedReport`` 모델의 ``__tablename__`` 는 **Alembic 007** 에서 리네이밍된
``tb_generated_reports_archive`` 를 가리킨다. 007 이후 이 테이블은 "소프트 폐기"
상태이며 신규 INSERT/UPDATE 는 어플리케이션 레벨에서 차단된다 (router.py 가
410 Gone 을 반환). 읽기 전용 조회(GET /api/v1/reports, GET /api/v1/reports/{id})
만 유지되며, 이는 기존 57건의 이력 보고서를 UI 에 노출하기 위한 과도기 조치다.

신규 보고서 생성 경로는 ``/api/v1/v2/documents`` (``tb_documents_v2``) 로
이관되었다. S7 (Phase 4 최종 스프린트) 에서 본 모듈 전체(router/service/
schemas/models)와 ``tb_generated_reports_archive``, ``tb_report_templates`` 를
함께 drop 할 예정이다 (``docs/phase2_transition_plan.md`` §2.6 D4/D5).

※ 새 Alembic migration 을 추가하지 않는다. 테이블 리네이밍은 이미 007 에서
완료됐으며, 본 세션의 변경은 ORM tablename 과 라우터/서비스의 읽기 전용 처리
뿐이다.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ReportFormat(str, enum.Enum):
    """Supported output formats for report templates."""

    hwp = "hwp"
    hwpx = "hwpx"
    docx = "docx"
    pdf = "pdf"
    html = "html"


class ReportStatus(str, enum.Enum):
    """Status of a generated report."""

    pending = "pending"
    generating = "generating"
    completed = "completed"
    error = "error"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ReportTemplate(Base):
    """Organization-level report template definition.

    Inherits ``id`` and audit columns from ``Base``.
    """

    __tablename__ = "tb_report_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    template_storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    schema_: Mapped[Optional[dict]] = mapped_column(
        "schema",
        JSONB,
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ReportTemplate id={self.id!s} name={self.name!r}>"


class GeneratedReport(Base):
    """Archive view of legacy reports (Alembic 007 이후 읽기 전용).

    Inherits ``id`` and audit columns from ``Base``.

    **읽기 전용 (S7 완전 제거 예정)**
        - ``__tablename__`` 은 Alembic 007 에서 리네이밍된
          ``tb_generated_reports_archive`` 를 가리킨다.
        - 신규 INSERT/UPDATE 는 라우터(410 Gone)와 서비스 레이어에서 차단된다.
        - UI 는 기존 57건의 보고서를 히스토리 목적으로만 조회한다.
        - 신규 생성은 ``/api/v1/v2/documents`` (``tb_documents_v2``) 를 사용한다.
        - S7 에서 본 모델과 테이블을 함께 drop 할 예정이다.
    """

    __tablename__ = "tb_generated_reports_archive"

    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_report_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    output_format: Mapped[str] = mapped_column(String(20), nullable=False)
    output_storage_path: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )
    source_document_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=True,
    )
    source_chat_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    generation_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Alembic 004_jinja2_template_system 에서 DB에 추가된 컬럼을 ORM에 노출한다.
    # 렌더링 방식 기록용. "jinja2" / "structured" / "regex" 등의 값을 가진다.
    rendering_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Jinja2 렌더링 시 실제 사용된 변수 값. 재생성·디버깅 용도로 보관한다.
    jinja2_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_users.id", ondelete="SET NULL"),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<GeneratedReport id={self.id!s} title={self.title!r} status={self.status!r}>"
