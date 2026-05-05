"""
Competency-related SQLAlchemy models.
Matches database schema: idino_career
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CHAR,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Competency(Base):
    """Competency definition model - tb_competency (matches actual DB)"""
    __tablename__ = "tb_competency"

    competency_cd = Column(String(20), primary_key=True)
    competency_nm = Column(String(100), nullable=False)
    competency_nm_en = Column(String(100))
    definition = Column(Text)  # 역량 정의 설명
    category = Column(String(50))  # 역량 카테고리
    weight = Column(Numeric(5, 2), default=0)
    max_score = Column(Integer, default=100)
    use_fg = Column(CHAR(1), default='Y')  # 사용 여부
    # Audit columns
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    student_competencies = relationship("StudentCompetency", back_populates="competency")


class StudentCompetency(Base):
    """Student competency score model - tb_student_competency (matches actual DB)"""
    __tablename__ = "tb_student_competency"

    student_competency_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(String(20), nullable=False)
    competency_cd = Column(String(20), ForeignKey("tb_competency.competency_cd"))
    current_score = Column(Numeric(10, 2), default=0)
    target_score = Column(Numeric(10, 2), default=85)
    gap_score = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='improve')  # excellent, good, average, improve, focus
    last_assessment_date = Column(Date)
    trend = Column(String(20))  # improving, stable, declining
    # Audit columns
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    competency = relationship("Competency", back_populates="student_competencies")
