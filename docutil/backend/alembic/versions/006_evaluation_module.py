"""
006 — Evaluation module tables.

tb_evaluation_logs: stores individual evaluation results per question
tb_evaluation_configs: per-organization metric weight configuration

Revision ID: 006_evaluation
Revises: 005_multi_provider
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision: str = "006_evaluation"
down_revision: str = "005_multi_provider"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_columns() -> list:
    """Standard audit columns shared across all tables."""
    return [
        sa.Column("ins_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ins_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("ins_ip", sa.String(45), nullable=True),
        sa.Column("upd_dt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("upd_user", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("upd_ip", sa.String(45), nullable=True),
    ]


def upgrade() -> None:
    # ── tb_evaluation_logs ──
    op.create_table(
        "tb_evaluation_logs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("run_id", sa.String(64), nullable=False, comment="Groups all questions in one evaluation run"),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("contexts", JSONB, nullable=True),
        # Metric scores
        sa.Column("context_relevancy", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("answer_faithfulness", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("answer_relevancy", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("hallucination_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("has_hallucination", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("hallucination_evidence", JSONB, nullable=True),
        # Composite
        sa.Column("composite_score", sa.Float, nullable=False, server_default="0.0"),
        # Judge details
        sa.Column("judge_details", JSONB, nullable=True),
        # Run metadata
        sa.Column("run_type", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("question_index", sa.Integer, nullable=False, server_default="0"),
        *_audit_columns(),
    )
    op.create_index("idx_eval_logs_org_id", "tb_evaluation_logs", ["organization_id"])
    op.create_index("idx_eval_logs_run_id", "tb_evaluation_logs", ["run_id"])
    op.create_index("idx_eval_logs_ins_dt", "tb_evaluation_logs", ["ins_dt"])

    # ── tb_evaluation_configs ──
    op.create_table(
        "tb_evaluation_configs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "organization_id",
            PG_UUID(as_uuid=True),
            sa.ForeignKey("tb_organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("context_relevancy_weight", sa.Float, nullable=False, server_default="0.25"),
        sa.Column("answer_faithfulness_weight", sa.Float, nullable=False, server_default="0.30"),
        sa.Column("answer_relevancy_weight", sa.Float, nullable=False, server_default="0.25"),
        sa.Column("hallucination_weight", sa.Float, nullable=False, server_default="0.20"),
        *_audit_columns(),
    )
    op.create_index("idx_eval_configs_org_id", "tb_evaluation_configs", ["organization_id"])


def downgrade() -> None:
    op.drop_table("tb_evaluation_configs")
    op.drop_table("tb_evaluation_logs")
