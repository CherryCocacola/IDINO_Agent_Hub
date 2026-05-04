"""멀티 AI 프로바이더: 에이전트별 LLM 프로바이더 선택 지원.

Revision ID: 005_multi_provider
Revises: 004_jinja2_template_system
Create Date: 2026-03-27 00:00:00.000000

tb_agents 테이블에 llm_provider 컬럼을 추가하여
에이전트별로 다른 AI 프로바이더(OpenAI, Azure, Gemini, Claude 등)를
선택할 수 있도록 한다. NULL이면 시스템 기본 프로바이더를 사용한다.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "005_multi_provider"
down_revision = "004_jinja2_template_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """tb_agents에 llm_provider 컬럼 추가."""
    op.add_column(
        "tb_agents",
        sa.Column(
            "llm_provider",
            sa.String(50),
            nullable=True,
            comment="openai, azure_openai, gemini, anthropic 등. NULL이면 시스템 기본값",
        ),
    )


def downgrade() -> None:
    """llm_provider 컬럼 제거."""
    op.drop_column("tb_agents", "llm_provider")
