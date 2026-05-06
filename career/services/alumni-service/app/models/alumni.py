"""
Alumni Service SQLAlchemy Models.
Matches database schema: idino_career
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Phase 4.4 — pgvector(1536D) 임베딩 컬럼 매핑용
# pgvector 패키지는 requirements.txt 에 추가됨 (Phase 4.4)
from pgvector.sqlalchemy import Vector

from ..database import Base


class AlumniCohort(Base):
    """Alumni cohort statistics (k-anonymized aggregates)."""
    __tablename__ = "tb_alumni_cohort"

    cohort_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    department_cd = Column(String(20), nullable=False, index=True)
    graduation_year = Column(Integer, nullable=False)
    cohort_size = Column(Integer, default=0)
    avg_gpa = Column(Numeric(3, 2))
    employment_rate = Column(Numeric(5, 2))  # Percentage
    avg_salary = Column(Numeric(12, 0))
    top_employers = Column(JSONB)  # Top employer companies (array)
    top_roles = Column(JSONB)  # Top job roles (array)
    avg_competency_scores = Column(JSONB, default=dict)
    avg_extras = Column(JSONB, default=dict)  # avg_credits, avg_certifications, avg_activities
    # Audit columns
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)


class SuccessPattern(Base):
    """Success patterns mined from alumni career data."""
    __tablename__ = "tb_success_pattern"

    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_nm = Column(String(100), nullable=False)  # Pattern name
    pattern_type = Column(String(50))  # Pattern type
    department_cd = Column(String(20), index=True)
    role_cd = Column(String(20))  # Target job/role
    description = Column(Text)  # Human-readable description
    typical_gpa_range = Column(String(20))
    key_courses = Column(JSONB)  # Array of course codes
    key_activities = Column(JSONB)  # Array of activity names
    key_skills = Column(JSONB)  # Array of skill codes
    timeline = Column(JSONB)  # Timeline structure
    success_rate = Column(Numeric(5, 2))
    sample_size = Column(Integer, default=0)
    # Phase 4.4 — 성공 패턴 RAG 임베딩 (text-embedding-3-small 1536D, ADR-10)
    # IVFFlat cosine 인덱스: ix_tb_success_pattern_embedding
    embedding = Column(Vector(1536), nullable=True)
    # Audit columns
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)
