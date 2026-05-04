"""Templates and Agents: document templates, AI agents, session/report linking.

Revision ID: 003_templates_agents
Revises: 002_dept_proj_restructure
Create Date: 2026-03-21 00:00:00.000000

This migration adds:

- tb_document_templates (organization-scoped document generation templates)
- tb_agents (organization-scoped AI agent configurations)
- agent_id FK on tb_chat_sessions and tb_generated_reports
- Indexes on organization_id and type columns for both new tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_templates_agents"
down_revision: str | None = "002_dept_proj_restructure"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list:
    """Return the standard audit columns for all tables."""
    return [
        sa.Column("ins_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ins_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("ins_ip", sa.String(45), nullable=True),
        sa.Column("upd_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("upd_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("upd_ip", sa.String(45), nullable=True),
    ]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create tb_document_templates
    # ------------------------------------------------------------------
    op.create_table(
        "tb_document_templates",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("template_type", sa.String(20), nullable=False, comment="'report' or 'proposal'"),
        sa.Column("tone", sa.String(20), nullable=False, server_default="formal"),
        sa.Column("output_format", sa.String(20), nullable=False),
        sa.Column("schema", JSONB, nullable=True),
        sa.Column("sample_prompt", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", PG_UUID(as_uuid=True), nullable=False),
        *_audit_columns(),
    )
    op.create_index(
        "idx_tb_document_templates_organization_id",
        "tb_document_templates",
        ["organization_id"],
    )
    op.create_index(
        "idx_tb_document_templates_template_type",
        "tb_document_templates",
        ["template_type"],
    )

    # ------------------------------------------------------------------
    # 2. Create tb_agents
    # ------------------------------------------------------------------
    op.create_table(
        "tb_agents",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("agent_type", sa.String(20), nullable=False, comment="'chatbot', 'report', or 'proposal'"),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("llm_model", sa.String(255), nullable=False, server_default="gpt-4o"),
        sa.Column("temperature", sa.Float, nullable=False, server_default=sa.text("0.1")),
        sa.Column("max_tokens", sa.Integer, nullable=False, server_default=sa.text("4096")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", PG_UUID(as_uuid=True), nullable=False),
        *_audit_columns(),
    )
    op.create_index(
        "idx_tb_agents_organization_id",
        "tb_agents",
        ["organization_id"],
    )
    op.create_index(
        "idx_tb_agents_agent_type",
        "tb_agents",
        ["agent_type"],
    )

    # ------------------------------------------------------------------
    # 3. Add agent_id FK to tb_chat_sessions
    # ------------------------------------------------------------------
    op.add_column(
        "tb_chat_sessions",
        sa.Column(
            "agent_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------------
    # 4. Add agent_id FK to tb_generated_reports
    # ------------------------------------------------------------------
    op.add_column(
        "tb_generated_reports",
        sa.Column(
            "agent_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # 4. Remove agent_id from tb_generated_reports
    op.drop_column("tb_generated_reports", "agent_id")

    # 3. Remove agent_id from tb_chat_sessions
    op.drop_column("tb_chat_sessions", "agent_id")

    # 2. Drop tb_agents
    op.drop_index("idx_tb_agents_agent_type", table_name="tb_agents")
    op.drop_index("idx_tb_agents_organization_id", table_name="tb_agents")
    op.drop_table("tb_agents")

    # 1. Drop tb_document_templates
    op.drop_index("idx_tb_document_templates_template_type", table_name="tb_document_templates")
    op.drop_index("idx_tb_document_templates_organization_id", table_name="tb_document_templates")
    op.drop_table("tb_document_templates")
