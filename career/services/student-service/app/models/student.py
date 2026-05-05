"""
Student-related SQLAlchemy models.
Matches database schema: idino_career
Updated to match actual database schema.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    CHAR,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..database import Base


class College(Base):
    """College model - tb_college (matches actual DB schema)"""
    __tablename__ = "tb_college"

    college_cd = Column(String(20), primary_key=True)
    university_cd = Column(String(20))
    college_nm = Column(String(100), nullable=False)
    college_nm_en = Column(String(100))
    use_fg = Column(CHAR(1), default='Y')
    sort_order = Column(Integer, default=0)
    # Audit columns
    ins_user_id = Column(String(50))
    ins_user_ip = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    ins_system_gcd = Column(String(10))
    ins_menu_cd = Column(String(20))
    upd_user_id = Column(String(50))
    upd_user_ip = Column(String(50))
    upd_dt = Column(DateTime)
    upd_system_gcd = Column(String(10))
    upd_menu_cd = Column(String(20))

    # Relationships
    departments = relationship("Department", back_populates="college")


class Department(Base):
    """Department model - tb_department (matches actual DB schema)"""
    __tablename__ = "tb_department"

    department_cd = Column(String(20), primary_key=True)
    college_cd = Column(String(20), ForeignKey("tb_college.college_cd"))
    department_nm = Column(String(100), nullable=False)
    department_nm_en = Column(String(100))
    dept_type = Column(String(20), default='major')
    graduation_credits = Column(Integer, default=130)
    use_fg = Column(CHAR(1), default='Y')
    sort_order = Column(Integer, default=0)
    # Audit columns
    ins_user_id = Column(String(50))
    ins_user_ip = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    ins_system_gcd = Column(String(10))
    ins_menu_cd = Column(String(20))
    upd_user_id = Column(String(50))
    upd_user_ip = Column(String(50))
    upd_dt = Column(DateTime)
    upd_system_gcd = Column(String(10))
    upd_menu_cd = Column(String(20))

    # Relationships
    college = relationship("College", back_populates="departments")
    students = relationship("Student", back_populates="department")


class Student(Base):
    """Student model - tb_student (matches actual seeded data)"""
    __tablename__ = "tb_student"

    student_id = Column(String(20), primary_key=True)
    student_nm = Column(String(50), nullable=False)
    student_nm_en = Column(String(100))
    university_cd = Column(String(20))
    department_cd = Column(String(20), ForeignKey("tb_department.department_cd"))
    admission_year = Column(Integer, nullable=False)
    current_grade = Column(Integer, nullable=False)
    current_semester = Column(Integer, nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    birth_date = Column(Date)
    gender = Column(CHAR(1))
    status = Column(String(20), default='enrolled')
    career_goal = Column(String(200))
    # Audit columns
    ins_user_id = Column(String(50))
    ins_user_ip = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    ins_system_gcd = Column(String(10))
    ins_menu_cd = Column(String(20))
    upd_user_id = Column(String(50))
    upd_user_ip = Column(String(50))
    upd_dt = Column(DateTime)
    upd_system_gcd = Column(String(10))
    upd_menu_cd = Column(String(20))
    # Legacy columns (for compatibility)
    std_id = Column(String(20))
    std_nm = Column(String(50))

    # Relationships
    department = relationship("Department", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student")
    achievements = relationship("Achievement", back_populates="student")


class Term(Base):
    """Term model - tb_term (matches actual DB schema)"""
    __tablename__ = "tb_term"

    term_cd = Column(String(20), primary_key=True)
    term_nm = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    registration_start = Column(Date)
    registration_end = Column(Date)
    use_fg = Column(CHAR(1), default='Y')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)


class Course(Base):
    """Course model - tb_course (matches actual DB schema)"""
    __tablename__ = "tb_course"

    course_cd = Column(String(20), primary_key=True)
    course_nm = Column(String(100), nullable=False)
    course_nm_en = Column(String(100))
    department_cd = Column(String(20), ForeignKey("tb_department.department_cd"))
    credits = Column(Integer, nullable=False)
    course_type = Column(String(20))
    course_category = Column(String(50))
    grade_level = Column(Integer)
    description = Column(Text)
    use_fg = Column(CHAR(1), default='Y')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)


class CourseOffering(Base):
    """Course Offering model - tb_course_offering (matches actual DB schema)"""
    __tablename__ = "tb_course_offering"

    offering_id = Column(UUID(as_uuid=True), primary_key=True)  # DDL uses UUID
    course_cd = Column(String(20), ForeignKey("tb_course.course_cd"))
    term_cd = Column(String(10), ForeignKey("tb_term.term_cd"))  # DDL uses VARCHAR(10)
    professor_cd = Column(String(20))
    class_no = Column(Integer, default=1)  # DDL uses INT, not String
    capacity = Column(Integer, default=40)
    enrolled_count = Column(Integer, default=0)
    schedule = Column(String(200))
    classroom = Column(String(100))  # DDL uses VARCHAR(100)
    use_fg = Column(CHAR(1), default='Y')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="course_offering")
    course = relationship("Course")
    term = relationship("Term")


class Enrollment(Base):
    """Enrollment model - tb_enrollment (matches actual DB schema)"""
    __tablename__ = "tb_enrollment"

    enrollment_id = Column(UUID(as_uuid=True), primary_key=True)
    student_id = Column(String(20), ForeignKey("tb_student.student_id"))
    course_offering_id = Column(UUID(as_uuid=True), ForeignKey("tb_course_offering.offering_id"))
    term_cd = Column(String(10))
    status_cd = Column(String(20), default='enrolled')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    course_offering = relationship("CourseOffering", back_populates="enrollments", foreign_keys=[course_offering_id])
    grade = relationship("Grade", back_populates="enrollment", uselist=False)


class Grade(Base):
    """Grade model - tb_grade (matches actual DB schema)"""
    __tablename__ = "tb_grade"

    grade_id = Column(UUID(as_uuid=True), primary_key=True)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("tb_enrollment.enrollment_id"))
    student_id = Column(String(20))
    course_cd = Column(String(20))
    term_cd = Column(String(20))
    grade_letter = Column(String(5))  # DB uses grade_letter, not letter_grade
    grade_point = Column(Numeric(3, 2))
    credits_earned = Column(Integer)
    is_retake = Column(CHAR(1), default='N')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="grade")


class Program(Base):
    """Program model - tb_program (matches actual DB schema)"""
    __tablename__ = "tb_program"

    program_cd = Column(String(20), primary_key=True)
    program_nm = Column(String(100), nullable=False)
    program_type = Column(String(50))
    organizer = Column(String(100))  # DB uses organizer, not host_organization
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)
    competency_contributions = Column(JSONB)
    use_fg = Column(CHAR(1), default='Y')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)


# Activity model - tb_activity (replaces non-existent tb_program_participation)
class Activity(Base):
    """Activity model - tb_activity (actual table in database)"""
    __tablename__ = "tb_activity"

    activity_id = Column(UUID(as_uuid=True), primary_key=True)
    student_id = Column(String(20), ForeignKey("tb_student.student_id"))
    program_cd = Column(String(20), ForeignKey("tb_program.program_cd"))
    activity_type = Column(String(50), nullable=False)
    title = Column(String(200))
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    hours = Column(Numeric(6, 1))
    achievement = Column(Text)
    status = Column(String(20), default='completed')
    verified = Column(CHAR(1), default='N')
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    student = relationship("Student")
    program = relationship("Program")


class Achievement(Base):
    """Achievement model - tb_achievement (matches actual DB schema)"""
    __tablename__ = "tb_achievement"

    achievement_id = Column(UUID(as_uuid=True), primary_key=True)  # DDL uses UUID
    student_id = Column(String(20), ForeignKey("tb_student.student_id"))
    achievement_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)  # DB uses title, not achievement_nm
    issuer = Column(String(200))  # DB uses issuer, not issuing_org (VARCHAR 200)
    issue_date = Column(Date)
    expire_date = Column(Date)  # DB uses expire_date, not expiry_date
    level = Column(String(50))
    score = Column(String(50))
    competency_contributions = Column(JSONB)
    verified = Column(CHAR(1), default='N')  # DB uses verified, not verified_fg
    ins_user_id = Column(String(50))
    ins_dt = Column(DateTime, default=datetime.utcnow)
    upd_user_id = Column(String(50))
    upd_dt = Column(DateTime)

    # Relationships
    student = relationship("Student", back_populates="achievements")


# Note: tb_student_summary table does not exist in database
# Commented out to prevent errors
# class StudentSummary(Base):
#     """Student Summary model - tb_student_summary"""
#     __tablename__ = "tb_student_summary"
