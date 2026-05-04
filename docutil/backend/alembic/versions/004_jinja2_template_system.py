"""Jinja2 Template System: DOCX 템플릿 렌더링을 위한 컬럼 추가.

Revision ID: 004_jinja2_template_system
Revises: 003_templates_agents
Create Date: 2026-03-24 00:00:00.000000

이 마이그레이션은 Jinja2 기반 문서 생성 시스템(Phase 1)을 위해 아래 변경을 수행합니다:

- tb_document_templates 테이블에 Jinja2 렌더링 관련 컬럼 추가
  (template_storage_path, original_file_path, jinja2_variables,
   rendering_mode, image_generation_config)
- tb_document_templates.template_type 컬럼 길이 확장 (20 → 100)
- tb_generated_reports 테이블에 렌더링 모드/컨텍스트 컬럼 추가
  (rendering_mode, jinja2_context)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# -- Alembic 리비전 식별자 --------------------------------------------------
revision: str = "004_jinja2_template_system"
down_revision: str | None = "003_templates_agents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. tb_document_templates 에 Jinja2 렌더링 관련 컬럼 추가
    # ------------------------------------------------------------------

    # MinIO 등 오브젝트 스토리지에 업로드된 DOCX 템플릿 파일 경로
    op.add_column(
        "tb_document_templates",
        sa.Column("template_storage_path", sa.String(1024), nullable=True),
    )

    # 사용자가 업로드한 원본 파일의 경로 (원본 보존용)
    op.add_column(
        "tb_document_templates",
        sa.Column("original_file_path", sa.String(1024), nullable=True),
    )

    # Jinja2 템플릿에서 사용 가능한 변수 목록 (JSON 형태로 저장)
    # 예: {"title": "string", "author": "string", "items": "list"}
    op.add_column(
        "tb_document_templates",
        sa.Column("jinja2_variables", JSONB, nullable=True),
    )

    # 렌더링 방식 — 'jinja2'(DOCX 템플릿) 또는 'structured'(LLM 생성) 등
    op.add_column(
        "tb_document_templates",
        sa.Column(
            "rendering_mode",
            sa.String(20),
            nullable=False,
            server_default="jinja2",
        ),
    )

    # 이미지 자동 생성 설정 (DALL-E 등 이미지 생성 AI 연동 시 사용)
    # 예: {"enabled": true, "model": "dall-e-3", "size": "1024x1024"}
    op.add_column(
        "tb_document_templates",
        sa.Column("image_generation_config", JSONB, nullable=True),
    )

    # ------------------------------------------------------------------
    # 2. template_type 컬럼 길이 확장 (VARCHAR(20) → VARCHAR(100))
    #    기존 'report', 'proposal' 외에 더 긴 타입명을 허용하기 위함
    # ------------------------------------------------------------------
    op.alter_column(
        "tb_document_templates",
        "template_type",
        existing_type=sa.String(20),
        type_=sa.String(100),
        existing_nullable=False,
    )

    # ------------------------------------------------------------------
    # 3. tb_generated_reports 에 렌더링 관련 컬럼 추가
    # ------------------------------------------------------------------

    # 이 보고서가 어떤 방식으로 생성되었는지 기록 ('jinja2' / 'structured' 등)
    op.add_column(
        "tb_generated_reports",
        sa.Column("rendering_mode", sa.String(20), nullable=True),
    )

    # Jinja2 렌더링 시 사용된 변수 값 (재생성 시 동일 컨텍스트 재사용 가능)
    op.add_column(
        "tb_generated_reports",
        sa.Column("jinja2_context", JSONB, nullable=True),
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # 역순으로 변경 사항을 되돌립니다
    # ------------------------------------------------------------------

    # 3. tb_generated_reports 에서 추가 컬럼 제거
    op.drop_column("tb_generated_reports", "jinja2_context")
    op.drop_column("tb_generated_reports", "rendering_mode")

    # 2. template_type 컬럼 길이를 원래대로 복원 (VARCHAR(100) → VARCHAR(20))
    op.alter_column(
        "tb_document_templates",
        "template_type",
        existing_type=sa.String(100),
        type_=sa.String(20),
        existing_nullable=False,
    )

    # 1. tb_document_templates 에서 추가 컬럼 제거
    op.drop_column("tb_document_templates", "image_generation_config")
    op.drop_column("tb_document_templates", "rendering_mode")
    op.drop_column("tb_document_templates", "jinja2_variables")
    op.drop_column("tb_document_templates", "original_file_path")
    op.drop_column("tb_document_templates", "template_storage_path")
