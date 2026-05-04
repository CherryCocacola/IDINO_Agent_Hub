"""
Evaluation ORM models.

tb_evaluation_logs  — individual evaluation run results
tb_evaluation_configs — per-organization metric weight configuration
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EvaluationLog(Base):
    """Single evaluation run result for one question."""

    __tablename__ = "tb_evaluation_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Groups all questions in one evaluation run",
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    contexts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Metric scores (0.0 ~ 1.0)
    context_relevancy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    answer_faithfulness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    answer_relevancy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hallucination_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    has_hallucination: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hallucination_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Weighted composite score
    composite_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Judge reasoning for each metric
    judge_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Run metadata
    run_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        comment="scheduled | manual",
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<EvaluationLog id={self.id!s} run={self.run_id!r} score={self.composite_score:.2f}>"


class EvaluationConfig(Base):
    """Per-organization metric weight configuration."""

    __tablename__ = "tb_evaluation_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    context_relevancy_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.25)
    answer_faithfulness_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.30)
    answer_relevancy_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.25)
    hallucination_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.20)

    def __repr__(self) -> str:
        return f"<EvaluationConfig org={self.organization_id!s}>"
