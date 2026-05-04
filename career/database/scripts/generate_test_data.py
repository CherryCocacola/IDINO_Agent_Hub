# -*- coding: utf-8 -*-
"""
IDINO Career - Test Data Generator
Generates test data with proper foreign key relations
Designed to avoid memory issues with batch processing
"""

import os
import sys
import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# ============================================
# Configuration
# ============================================

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
BATCH_SIZE = 50  # Records per INSERT statement
SCHEMA = "idino_career"

# Random seed for reproducibility
random.seed(42)

# ============================================
# Data Templates (ASCII-safe to avoid encoding issues)
# ============================================

COLLEGES = [
    ("COL01", "College of Engineering", "ENG"),
    ("COL02", "College of Business", "BUS"),
    ("COL03", "College of Natural Sciences", "SCI"),
    ("COL04", "College of Liberal Arts", "LIB"),
    ("COL05", "College of Social Sciences", "SOC"),
    ("COL06", "College of Information Technology", "IT"),
    ("COL07", "College of Design", "DES"),
    ("COL08", "College of Education", "EDU"),
]

DEPARTMENTS = [
    # Engineering
    ("DEPT01", "COL01", "Computer Science", "CS"),
    ("DEPT02", "COL01", "Electrical Engineering", "EE"),
    ("DEPT03", "COL01", "Mechanical Engineering", "ME"),
    ("DEPT04", "COL01", "Civil Engineering", "CE"),
    # Business
    ("DEPT05", "COL02", "Business Administration", "BA"),
    ("DEPT06", "COL02", "Accounting", "ACC"),
    ("DEPT07", "COL02", "Finance", "FIN"),
    ("DEPT08", "COL02", "Marketing", "MKT"),
    # Natural Sciences
    ("DEPT09", "COL03", "Mathematics", "MATH"),
    ("DEPT10", "COL03", "Physics", "PHY"),
    ("DEPT11", "COL03", "Chemistry", "CHEM"),
    ("DEPT12", "COL03", "Biology", "BIO"),
    # Information Technology
    ("DEPT13", "COL06", "Software Engineering", "SE"),
    ("DEPT14", "COL06", "Data Science", "DS"),
    ("DEPT15", "COL06", "Artificial Intelligence", "AI"),
    ("DEPT16", "COL06", "Cybersecurity", "SEC"),
    # Social Sciences
    ("DEPT17", "COL05", "Psychology", "PSY"),
    ("DEPT18", "COL05", "Sociology", "SOC"),
    # Liberal Arts
    ("DEPT19", "COL04", "English Literature", "ENG"),
    ("DEPT20", "COL04", "Philosophy", "PHIL"),
    # Design
    ("DEPT21", "COL07", "Industrial Design", "ID"),
    ("DEPT22", "COL07", "Visual Communication", "VC"),
    # Education
    ("DEPT23", "COL08", "Educational Technology", "ET"),
    ("DEPT24", "COL08", "Curriculum Studies", "CUR"),
]

COMPETENCIES = [
    ("COMP01", "Problem Solving", "Ability to analyze and solve complex problems"),
    ("COMP02", "Communication", "Effective written and verbal communication"),
    ("COMP03", "Teamwork", "Collaborative work and interpersonal skills"),
    ("COMP04", "Technical Skills", "Domain-specific technical competencies"),
    ("COMP05", "Leadership", "Ability to lead and manage teams"),
    ("COMP06", "Critical Thinking", "Logical analysis and decision making"),
]

SKILLS = [
    ("SK01", "Python", "technical", 2),
    ("SK02", "Java", "technical", 3),
    ("SK03", "SQL", "technical", 2),
    ("SK04", "Machine Learning", "technical", 4),
    ("SK05", "Data Analysis", "technical", 3),
    ("SK06", "Project Management", "soft", 3),
    ("SK07", "Public Speaking", "soft", 2),
    ("SK08", "Technical Writing", "soft", 2),
    ("SK09", "Cloud Computing", "technical", 4),
    ("SK10", "Web Development", "technical", 3),
    ("SK11", "Mobile Development", "technical", 3),
    ("SK12", "DevOps", "technical", 4),
    ("SK13", "Agile Methodology", "soft", 2),
    ("SK14", "UX Design", "domain", 3),
    ("SK15", "Database Design", "technical", 3),
]

ROLES = [
    ("ROLE01", "Software Engineer", "IT", 75000000),
    ("ROLE02", "Data Scientist", "IT", 80000000),
    ("ROLE03", "Product Manager", "IT", 85000000),
    ("ROLE04", "UX Designer", "Design", 65000000),
    ("ROLE05", "Business Analyst", "Business", 60000000),
    ("ROLE06", "Project Manager", "Management", 70000000),
    ("ROLE07", "DevOps Engineer", "IT", 78000000),
    ("ROLE08", "Machine Learning Engineer", "IT", 90000000),
    ("ROLE09", "Frontend Developer", "IT", 65000000),
    ("ROLE10", "Backend Developer", "IT", 70000000),
    ("ROLE11", "Full Stack Developer", "IT", 75000000),
    ("ROLE12", "Cloud Architect", "IT", 100000000),
]

COURSE_TYPES = ["major_required", "major_elective", "general_required", "general_elective"]
GRADE_LETTERS = ["A+", "A0", "B+", "B0", "C+", "C0", "D+", "D0", "F"]
GRADE_POINTS = {"A+": 4.50, "A0": 4.00, "B+": 3.50, "B0": 3.00, "C+": 2.50, "C0": 2.00, "D+": 1.50, "D0": 1.00, "F": 0.00}

FIRST_NAMES = ["Min", "Ji", "Hyun", "Sung", "Young", "Jin", "Soo", "Eun", "Hye", "Jun",
               "Woo", "Seung", "Dong", "Jae", "Chan", "Ho", "Yoon", "Ha", "Na", "Yu"]
LAST_NAMES = ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang", "Lim",
              "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang", "Ahn", "Song", "Yoo", "Hong"]

PROGRAM_TYPES = ["internship", "contest", "club", "volunteer", "certificate", "seminar"]
ACTIVITY_TYPES = ["project", "research", "internship", "competition", "volunteer", "workshop"]
ACHIEVEMENT_TYPES = ["certificate", "award", "publication", "patent", "scholarship"]

OPPORTUNITY_TYPES = ["internship", "project", "lab", "contest", "scholarship", "job"]
GOAL_TYPES = ["career", "competency", "skill", "academic", "activity"]
RISK_TYPES = ["gpa_low", "credit_shortage", "prerequisite_missing", "attendance_low", "deadline_risk"]
BADGE_CATEGORIES = ["skill", "competency", "achievement", "milestone"]
SIMULATION_TYPES = ["course", "career", "skill", "activity"]


def escape_sql(val: Any) -> str:
    """Escape value for SQL"""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (list, dict)):
        import json
        return "'" + json.dumps(val).replace("'", "''") + "'"
    return "'" + str(val).replace("'", "''") + "'"


def gen_uuid() -> str:
    return str(uuid.uuid4())


def gen_date(start_year: int = 2020, end_year: int = 2026) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    random_days = random.randint(0, delta)
    return (start + timedelta(days=random_days)).isoformat()


def gen_timestamp(start_year: int = 2020) -> str:
    dt = datetime(start_year + random.randint(0, 5), random.randint(1, 12),
                  random.randint(1, 28), random.randint(0, 23), random.randint(0, 59))
    return dt.isoformat()


class DataGenerator:
    def __init__(self):
        self.sql_lines: List[str] = []
        self.students: List[str] = []
        self.offerings: List[str] = []
        self.enrollments: List[str] = []
        self.programs: List[str] = []
        self.opportunities: List[str] = []
        self.goals: List[str] = []
        self.plans: List[str] = []
        self.badges: List[str] = []
        self.advisors: List[str] = []
        self.assignments: List[str] = []
        self.scenarios: List[str] = []
        self.alerts: List[str] = []

    def add_sql(self, sql: str):
        self.sql_lines.append(sql)

    def write_header(self):
        self.add_sql("-- ============================================")
        self.add_sql("-- IDINO Career - Test Data (Auto-generated)")
        self.add_sql(f"-- Generated: {datetime.now().isoformat()}")
        self.add_sql("-- ============================================")
        self.add_sql("")
        self.add_sql(f"SET search_path TO {SCHEMA};")
        self.add_sql("")
        self.add_sql("-- Disable foreign key checks during bulk insert")
        self.add_sql("SET session_replication_role = replica;")
        self.add_sql("")

    def write_footer(self):
        self.add_sql("")
        self.add_sql("-- Re-enable foreign key checks")
        self.add_sql("SET session_replication_role = DEFAULT;")
        self.add_sql("")
        self.add_sql("-- Analyze tables for query optimization")
        self.add_sql("ANALYZE;")
        self.add_sql("")
        self.add_sql("-- ============================================")
        self.add_sql("-- Data generation complete!")
        self.add_sql("-- ============================================")

    def gen_university(self):
        self.add_sql("-- University")
        self.add_sql("INSERT INTO tb_university (university_cd, university_nm, university_nm_en, use_fg, ins_user_id) VALUES")
        self.add_sql("('UNIV01', 'IDINO University', 'IDINO University', 'Y', 'SEED');")
        self.add_sql("")

    def gen_colleges(self):
        self.add_sql("-- Colleges")
        self.add_sql("INSERT INTO tb_college (college_cd, university_cd, college_nm, college_nm_en, sort_order, ins_user_id) VALUES")
        values = []
        for i, (cd, nm, abbr) in enumerate(COLLEGES):
            values.append(f"('{cd}', 'UNIV01', '{nm}', '{nm}', {i+1}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_departments(self):
        self.add_sql("-- Departments")
        self.add_sql("INSERT INTO tb_department (department_cd, college_cd, department_nm, department_nm_en, graduation_credits, sort_order, ins_user_id) VALUES")
        values = []
        for i, (dept_cd, col_cd, nm, abbr) in enumerate(DEPARTMENTS):
            credits = random.choice([120, 130, 140])
            values.append(f"('{dept_cd}', '{col_cd}', '{nm}', '{nm}', {credits}, {i+1}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_professors(self, count: int = 50):
        self.add_sql("-- Professors")
        self.add_sql("INSERT INTO tb_professor (professor_cd, professor_nm, professor_nm_en, department_cd, email, position, ins_user_id) VALUES")
        values = []
        positions = ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"]
        for i in range(count):
            cd = f"PROF{i+1:03d}"
            name = f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"
            dept = random.choice(DEPARTMENTS)[0]
            email = f"prof{i+1}@idino.edu"
            pos = random.choice(positions)
            values.append(f"('{cd}', '{name}', '{name}', '{dept}', '{email}', '{pos}', 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_terms(self):
        self.add_sql("-- Terms")
        self.add_sql("INSERT INTO tb_term (term_cd, term_nm, start_date, end_date, ins_user_id) VALUES")
        values = []
        for year in range(2020, 2027):
            for sem in [1, 2]:
                cd = f"{year}-{sem}"
                nm = f"{year} {'Spring' if sem == 1 else 'Fall'}"
                start = f"{year}-0{sem*3}-01"
                end = f"{year}-0{sem*3+5}-30"
                values.append(f"('{cd}', '{nm}', '{start}', '{end}', 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_courses(self, count: int = 100):
        self.add_sql("-- Courses")
        self.add_sql("INSERT INTO tb_course (course_cd, course_nm, course_nm_en, department_cd, credits, course_type, grade_level, ins_user_id) VALUES")
        values = []
        course_names = [
            "Introduction to", "Advanced", "Fundamentals of", "Applied", "Theory of",
            "Principles of", "Topics in", "Seminar on", "Workshop in", "Research Methods for"
        ]
        subjects = [
            "Programming", "Data Structures", "Algorithms", "Database Systems", "Software Engineering",
            "Machine Learning", "Web Development", "Mobile Computing", "Cloud Computing", "Networking",
            "Statistics", "Calculus", "Linear Algebra", "Economics", "Marketing", "Finance",
            "Management", "Communication", "Design Thinking", "Project Management"
        ]
        for i in range(count):
            cd = f"CRS{i+1:03d}"
            nm = f"{random.choice(course_names)} {random.choice(subjects)}"
            dept = random.choice(DEPARTMENTS)[0]
            credits = random.choice([2, 3, 3, 3, 4])
            ctype = random.choice(COURSE_TYPES)
            grade = random.randint(1, 4)
            values.append(f"('{cd}', '{nm}', '{nm}', '{dept}', {credits}, '{ctype}', {grade}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_students(self, count: int = 200):
        self.add_sql("-- Students")
        for batch_start in range(0, count, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, count)
            self.add_sql(f"INSERT INTO tb_student (student_id, student_nm, student_nm_en, university_cd, department_cd, admission_year, current_grade, current_semester, email, gender, status, ins_user_id) VALUES")
            values = []
            for i in range(batch_start, batch_end):
                year = 2020 + (i % 5)
                student_id = f"{year}{(i % 24) + 1:02d}{(i % 100):04d}"
                self.students.append(student_id)
                name = f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"
                dept = DEPARTMENTS[i % len(DEPARTMENTS)][0]
                grade = min(4, (2026 - year))
                semester = grade * 2
                email = f"student{i+1}@idino.edu"
                gender = random.choice(["M", "F"])
                status = random.choices(["enrolled", "leave", "graduated"], [0.85, 0.05, 0.10])[0]
                values.append(f"('{student_id}', '{name}', '{name}', 'UNIV01', '{dept}', {year}, {grade}, {semester}, '{email}', '{gender}', '{status}', 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_competencies(self):
        self.add_sql("-- Competencies")
        self.add_sql("INSERT INTO tb_competency (competency_cd, competency_nm, competency_nm_en, definition, weight, max_score, ins_user_id) VALUES")
        values = []
        for cd, nm, desc in COMPETENCIES:
            weight = round(random.uniform(0.1, 0.3), 2)
            values.append(f"('{cd}', '{nm}', '{nm}', '{desc}', {weight}, 100, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_skills(self):
        self.add_sql("-- Skills")
        self.add_sql("INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, ins_user_id) VALUES")
        values = []
        for cd, nm, cat, diff in SKILLS:
            values.append(f"('{cd}', '{nm}', '{nm}', '{cat}', {diff}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_roles(self):
        self.add_sql("-- Roles (Careers)")
        self.add_sql("INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, average_salary, growth_rate, ins_user_id) VALUES")
        values = []
        for cd, nm, cat, salary in ROLES:
            growth = round(random.uniform(2.0, 15.0), 2)
            values.append(f"('{cd}', '{nm}', '{nm}', '{cat}', {salary}, {growth}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_programs(self, count: int = 30):
        self.add_sql("-- Programs")
        self.add_sql("INSERT INTO tb_program (program_cd, program_nm, program_type, organizer, start_date, end_date, ins_user_id) VALUES")
        values = []
        for i in range(count):
            cd = f"PROG{i+1:03d}"
            self.programs.append(cd)
            ptype = random.choice(PROGRAM_TYPES)
            nm = f"{ptype.title()} Program {i+1}"
            org = f"Organization {i+1}"
            start = gen_date(2023, 2025)
            end_d = date.fromisoformat(start) + timedelta(days=random.randint(30, 180))
            values.append(f"('{cd}', '{nm}', '{ptype}', '{org}', '{start}', '{end_d.isoformat()}', 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_course_offerings(self, count: int = 300):
        self.add_sql("-- Course Offerings")
        terms = [f"{y}-{s}" for y in range(2020, 2027) for s in [1, 2]]
        for batch_start in range(0, count, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, count)
            self.add_sql(f"INSERT INTO tb_course_offering (offering_id, course_cd, term_cd, professor_cd, class_no, capacity, enrolled_count, ins_user_id) VALUES")
            values = []
            for i in range(batch_start, batch_end):
                oid = gen_uuid()
                self.offerings.append(oid)
                course = f"CRS{(i % 100) + 1:03d}"
                term = terms[i % len(terms)]
                prof = f"PROF{(i % 50) + 1:03d}"
                class_no = (i % 3) + 1
                cap = random.randint(30, 60)
                enrolled = random.randint(20, cap)
                values.append(f"('{oid}', '{course}', '{term}', '{prof}', {class_no}, {cap}, {enrolled}, 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_enrollments(self):
        self.add_sql("-- Enrollments")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_enrollment (enrollment_id, student_id, offering_id, term_cd, status, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # Each student takes 5-8 courses
                for _ in range(random.randint(5, 8)):
                    eid = gen_uuid()
                    self.enrollments.append((eid, student))
                    offering = random.choice(self.offerings)
                    term_idx = random.randint(0, 13)
                    term = f"{2020 + term_idx // 2}-{(term_idx % 2) + 1}"
                    status = random.choices(["completed", "enrolled", "dropped"], [0.8, 0.15, 0.05])[0]
                    values.append(f"('{eid}', '{student}', '{offering}', '{term}', '{status}', 'SEED')")
                    count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total enrollments: {count}")
        self.add_sql("")

    def gen_grades(self):
        self.add_sql("-- Grades")
        for batch_start in range(0, len(self.enrollments), BATCH_SIZE):
            batch_enrollments = self.enrollments[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, ins_user_id) VALUES")
            values = []
            for eid, student in batch_enrollments:
                gid = gen_uuid()
                course = f"CRS{random.randint(1, 100):03d}"
                term_idx = random.randint(0, 13)
                term = f"{2020 + term_idx // 2}-{(term_idx % 2) + 1}"
                letter = random.choices(GRADE_LETTERS, [0.05, 0.15, 0.20, 0.25, 0.15, 0.10, 0.05, 0.03, 0.02])[0]
                point = GRADE_POINTS[letter]
                credits = random.choice([2, 3, 3, 3, 4])
                values.append(f"('{gid}', '{eid}', '{student}', '{course}', '{term}', '{letter}', {point}, {credits}, 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_student_competencies(self):
        self.add_sql("-- Student Competencies")
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                for comp_cd, _, _ in COMPETENCIES:
                    curr = round(random.uniform(40, 95), 2)
                    target = 85.0
                    gap = max(0, round(target - curr, 2))
                    status = "excellent" if curr >= 85 else "good" if curr >= 70 else "average" if curr >= 55 else "improve"
                    trend = random.choice(["up", "down", "stable"])
                    values.append(f"('{student}', '{comp_cd}', {curr}, {target}, {gap}, '{status}', '{trend}', 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_student_skills(self):
        self.add_sql("-- Student Skills")
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # Each student has 5-10 skills
                skill_count = random.randint(5, 10)
                selected_skills = random.sample(SKILLS, skill_count)
                for skill_cd, _, _, _ in selected_skills:
                    curr = random.randint(1, 4)
                    target = min(5, curr + random.randint(1, 2))
                    evidence = random.randint(0, 10)
                    trend = random.choice(["up", "down", "stable"])
                    values.append(f"('{student}', '{skill_cd}', {curr}, {target}, {evidence}, '{trend}', 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_activities(self):
        self.add_sql("-- Activities")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_activity (student_id, program_cd, activity_type, title, start_date, end_date, hours, status, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 1-3 activities per student
                for _ in range(random.randint(1, 3)):
                    prog = random.choice(self.programs)
                    atype = random.choice(ACTIVITY_TYPES)
                    title = f"{atype.title()} Activity"
                    start = gen_date(2022, 2025)
                    end_d = date.fromisoformat(start) + timedelta(days=random.randint(7, 90))
                    hours = random.randint(10, 200)
                    status = random.choice(["completed", "ongoing", "cancelled"])
                    values.append(f"('{student}', '{prog}', '{atype}', '{title}', '{start}', '{end_d.isoformat()}', {hours}, '{status}', 'SEED')")
                    count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total activities: {count}")
        self.add_sql("")

    def gen_achievements(self):
        self.add_sql("-- Achievements")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, level, verified, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 0-3 achievements per student
                for _ in range(random.randint(0, 3)):
                    atype = random.choice(ACHIEVEMENT_TYPES)
                    title = f"{atype.title()} Achievement"
                    issuer = f"Issuer Organization"
                    issue = gen_date(2022, 2025)
                    level = random.choice(["gold", "silver", "bronze", "participant", None])
                    verified = random.choice(["Y", "N"])
                    values.append(f"('{student}', '{atype}', '{title}', '{issuer}', '{issue}', {escape_sql(level)}, '{verified}', 'SEED')")
                    count += 1
            if values:
                self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total achievements: {count}")
        self.add_sql("")

    def gen_role_skill_maps(self):
        self.add_sql("-- Role-Skill Maps")
        self.add_sql("INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id) VALUES")
        values = []
        importances = ["critical", "important", "nice_to_have"]
        trends = ["growing", "stable", "declining"]
        for role_cd, _, _, _ in ROLES:
            # Each role requires 4-7 skills
            selected_skills = random.sample(SKILLS, random.randint(4, 7))
            for skill_cd, _, _, _ in selected_skills:
                level = random.randint(2, 5)
                imp = random.choice(importances)
                demand = round(random.uniform(50, 100), 2)
                trend = random.choices(trends, [0.5, 0.4, 0.1])[0]
                values.append(f"('{role_cd}', '{skill_cd}', {level}, '{imp}', {demand}, '{trend}', 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_alumni_cohorts(self):
        self.add_sql("-- Alumni Cohorts")
        self.add_sql("INSERT INTO tb_alumni_cohort (department_cd, graduation_year, cohort_size, avg_gpa, employment_rate, avg_salary, ins_user_id) VALUES")
        values = []
        for dept_cd, _, _, _ in DEPARTMENTS:
            for year in range(2018, 2026):
                size = random.randint(20, 80)
                gpa = round(random.uniform(2.8, 3.8), 2)
                emp_rate = round(random.uniform(70, 98), 2)
                salary = random.randint(35000000, 80000000)
                values.append(f"('{dept_cd}', {year}, {size}, {gpa}, {emp_rate}, {salary}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_success_patterns(self):
        self.add_sql("-- Success Patterns")
        self.add_sql("INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, success_rate, sample_size, ins_user_id) VALUES")
        values = []
        pattern_types = ["academic", "career", "hybrid"]
        for i, (role_cd, role_nm, _, _) in enumerate(ROLES):
            dept = random.choice(DEPARTMENTS)[0]
            ptype = random.choice(pattern_types)
            nm = f"Path to {role_nm}"
            desc = f"Typical path for becoming a {role_nm}"
            gpa = f"{round(random.uniform(3.0, 3.5), 1)}-{round(random.uniform(3.6, 4.5), 1)}"
            rate = round(random.uniform(60, 95), 2)
            sample = random.randint(50, 200)
            values.append(f"('{nm}', '{ptype}', '{dept}', '{role_cd}', '{desc}', '{gpa}', {rate}, {sample}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_opportunities(self, count: int = 100):
        self.add_sql("-- Opportunities")
        for batch_start in range(0, count, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, count)
            self.add_sql(f"INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, application_start, application_end, location, remote_available, slots, status, ins_user_id) VALUES")
            values = []
            for i in range(batch_start, batch_end):
                oid = gen_uuid()
                self.opportunities.append(oid)
                otype = random.choice(OPPORTUNITY_TYPES)
                title = f"{otype.title()} Opportunity {i+1}"
                org = f"Company {i+1}"
                desc = f"Great {otype} opportunity for students"
                start = gen_date(2024, 2026)
                end_d = date.fromisoformat(start) + timedelta(days=random.randint(30, 90))
                loc = random.choice(["Seoul", "Busan", "Daejeon", "Remote"])
                remote = random.choice([True, False])
                slots = random.randint(1, 20)
                status = random.choices(["open", "closed", "filled"], [0.6, 0.2, 0.2])[0]
                values.append(f"('{oid}', '{otype}', '{title}', '{org}', '{desc}', '{start}', '{end_d.isoformat()}', '{loc}', {escape_sql(remote)}, {slots}, '{status}', 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_coaching_goals(self):
        self.add_sql("-- Coaching Goals")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_coaching_goal (goal_id, student_id, goal_type, title, target_role_cd, deadline, priority, status, achievement_rate, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 1-2 goals per student
                for j in range(random.randint(1, 2)):
                    gid = gen_uuid()
                    self.goals.append((gid, student))
                    gtype = random.choice(GOAL_TYPES)
                    title = f"{gtype.title()} Goal {j+1}"
                    role = random.choice(ROLES)[0]
                    deadline = gen_date(2025, 2027)
                    priority = random.randint(1, 3)
                    status = random.choice(["active", "achieved", "paused"])
                    rate = round(random.uniform(0, 100), 2) if status != "active" else round(random.uniform(0, 70), 2)
                    values.append(f"('{gid}', '{student}', '{gtype}', '{title}', '{role}', '{deadline}', {priority}, '{status}', {rate}, 'SEED')")
                    count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total goals: {count}")
        self.add_sql("")

    def gen_coaching_plans(self):
        self.add_sql("-- Coaching Plans")
        for batch_start in range(0, len(self.goals), BATCH_SIZE):
            batch_goals = self.goals[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_coaching_plan (plan_id, goal_id, plan_version, milestones, weekly_hours_target, total_weeks, status, ins_user_id) VALUES")
            values = []
            for gid, _ in batch_goals:
                pid = gen_uuid()
                self.plans.append(pid)
                version = 1
                milestones = [{"week": i, "task": f"Milestone {i}"} for i in range(1, 5)]
                hours = random.randint(5, 15)
                weeks = random.randint(8, 16)
                status = random.choice(["active", "completed"])
                values.append(f"('{pid}', '{gid}', {version}, {escape_sql(milestones)}, {hours}, {weeks}, '{status}', 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_risk_alerts(self):
        self.add_sql("-- Risk Alerts")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_risk_alert (alert_id, student_id, risk_type, severity, title, trigger_value, threshold_value, status, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 30% chance of having a risk alert
                if random.random() < 0.3:
                    aid = gen_uuid()
                    self.alerts.append(aid)
                    rtype = random.choice(RISK_TYPES)
                    severity = random.choice(["critical", "high", "medium", "low"])
                    title = f"{rtype.replace('_', ' ').title()} Alert"
                    trigger = round(random.uniform(1.5, 2.5), 2)
                    threshold = 2.5
                    status = random.choice(["active", "resolved", "dismissed"])
                    values.append(f"('{aid}', '{student}', '{rtype}', '{severity}', '{title}', {trigger}, {threshold}, '{status}', 'SEED')")
                    count += 1
            if values:
                self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total alerts: {count}")
        self.add_sql("")

    def gen_badges(self, count: int = 30):
        self.add_sql("-- Badges")
        self.add_sql(f"INSERT INTO tb_badge (badge_id, badge_cd, badge_nm, badge_nm_en, category, level, points, criteria, ins_user_id) VALUES")
        values = []
        for i in range(count):
            bid = gen_uuid()
            self.badges.append(bid)
            bcd = f"BADGE{i+1:03d}"
            cat = random.choice(BADGE_CATEGORIES)
            level = random.choice(["bronze", "silver", "gold", "platinum"])
            nm = f"{cat.title()} {level.title()} Badge"
            points = {"bronze": 10, "silver": 25, "gold": 50, "platinum": 100}[level]
            criteria = {"type": cat, "level": level}
            values.append(f"('{bid}', '{bcd}', '{nm}', '{nm}', '{cat}', '{level}', {points}, {escape_sql(criteria)}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_student_badges(self):
        self.add_sql("-- Student Badges")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_student_badge (student_id, badge_id, earned_at, earned_level, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 2-5 badges per student
                badge_count = random.randint(2, min(5, len(self.badges)))
                selected_badges = random.sample(self.badges, badge_count)
                for badge in selected_badges:
                    earned = gen_timestamp(2023)
                    level = random.randint(1, 3)
                    values.append(f"('{student}', '{badge}', '{earned}', {level}, 'SEED')")
                    count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total student badges: {count}")
        self.add_sql("")

    def gen_skill_passports(self):
        self.add_sql("-- Skill Passports")
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_skill_passport (student_id, overall_score, total_badges, total_skills, verified_skills, is_public, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                score = round(random.uniform(30, 95), 2)
                badges = random.randint(2, 10)
                skills = random.randint(5, 15)
                verified = random.randint(1, skills)
                public = random.choice([True, False])
                values.append(f"('{student}', {score}, {badges}, {skills}, {verified}, {escape_sql(public)}, 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_simulation_scenarios(self):
        self.add_sql("-- Simulation Scenarios")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, base_state, changes, confidence_level, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                # 1-2 scenarios per student
                for j in range(random.randint(1, 2)):
                    sid = gen_uuid()
                    self.scenarios.append(sid)
                    stype = random.choice(SIMULATION_TYPES)
                    title = f"{stype.title()} What-If Scenario {j+1}"
                    base = {"gpa": round(random.uniform(2.5, 4.0), 2)}
                    changes = {"add_course": f"CRS{random.randint(1, 50):03d}"}
                    conf = round(random.uniform(0.6, 0.95), 2)
                    values.append(f"('{sid}', '{student}', '{stype}', '{title}', {escape_sql(base)}, {escape_sql(changes)}, {conf}, 'SEED')")
                    count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total scenarios: {count}")
        self.add_sql("")

    def gen_advisors(self, count: int = 20):
        self.add_sql("-- Advisors")
        self.add_sql(f"INSERT INTO tb_advisor (advisor_id, advisor_cd, advisor_nm, department_cd, email, max_students, ins_user_id) VALUES")
        values = []
        for i in range(count):
            aid = gen_uuid()
            self.advisors.append(aid)
            acd = f"ADV{i+1:03d}"
            name = f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"
            dept = random.choice(DEPARTMENTS)[0]
            email = f"advisor{i+1}@idino.edu"
            max_stu = random.randint(20, 40)
            values.append(f"('{aid}', '{acd}', '{name}', '{dept}', '{email}', {max_stu}, 'SEED')")
        self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def gen_advisor_assignments(self):
        self.add_sql("-- Advisor Assignments")
        count = 0
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_advisor_assignment (assignment_id, advisor_id, student_id, assignment_type, status, priority, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                asn_id = gen_uuid()
                self.assignments.append(asn_id)
                advisor = random.choice(self.advisors)
                atype = random.choice(["academic", "career", "mentoring"])
                status = random.choice(["active", "completed", "paused"])
                priority = random.randint(1, 3)
                values.append(f"('{asn_id}', '{advisor}', '{student}', '{atype}', '{status}', {priority}, 'SEED')")
                count += 1
            self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total assignments: {count}")
        self.add_sql("")

    def gen_advisor_notes(self):
        self.add_sql("-- Advisor Notes")
        count = 0
        note_types = ["meeting", "observation", "action_item", "progress"]
        for batch_start in range(0, len(self.assignments), BATCH_SIZE):
            batch_assignments = self.assignments[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_advisor_note (assignment_id, note_type, content, is_private, ins_user_id) VALUES")
            values = []
            for asn in batch_assignments:
                # 50% chance of having notes
                if random.random() < 0.5:
                    ntype = random.choice(note_types)
                    content = f"Sample {ntype} note content for this student session."
                    private = random.choice([True, False])
                    values.append(f"('{asn}', '{ntype}', '{content}', {escape_sql(private)}, 'SEED')")
                    count += 1
            if values:
                self.add_sql(",\n".join(values) + ";")
        self.add_sql(f"-- Total notes: {count}")
        self.add_sql("")

    def gen_users(self):
        self.add_sql("-- Users (Auth)")
        # Admin user
        self.add_sql("INSERT INTO tb_user (login_id, password_hash, user_nm, email, user_type, role, status, mfa_enabled, ins_user_id) VALUES")
        # bcrypt hash for password '1234'
        pwd_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.4QHYJ.rDqa8Tmu"
        self.add_sql(f"('admin', '{pwd_hash}', 'Administrator', 'admin@idino.edu', 'admin', 'admin', 'active', FALSE, 'SEED');")
        self.add_sql("")

        # Student users (batch)
        for batch_start in range(0, len(self.students), BATCH_SIZE):
            batch_students = self.students[batch_start:batch_start + BATCH_SIZE]
            self.add_sql(f"INSERT INTO tb_user (login_id, password_hash, user_nm, email, user_type, student_id, role, status, mfa_enabled, ins_user_id) VALUES")
            values = []
            for student in batch_students:
                name = f"Student {student}"
                email = f"{student}@idino.edu"
                values.append(f"('{student}', '{pwd_hash}', '{name}', '{email}', 'student', '{student}', 'user', 'active', FALSE, 'SEED')")
            self.add_sql(",\n".join(values) + ";")
        self.add_sql("")

    def generate(self, student_count: int = 200):
        """Generate all test data"""
        print(f"Generating test data for {student_count} students...")

        self.write_header()

        # Master data
        print("  - University & Colleges...")
        self.gen_university()
        self.gen_colleges()
        self.gen_departments()

        print("  - Professors & Terms...")
        self.gen_professors()
        self.gen_terms()

        print("  - Courses...")
        self.gen_courses()

        print("  - Competencies & Skills & Roles...")
        self.gen_competencies()
        self.gen_skills()
        self.gen_roles()

        print("  - Programs...")
        self.gen_programs()

        # Student data
        print("  - Students...")
        self.gen_students(student_count)

        print("  - Course Offerings...")
        self.gen_course_offerings()

        print("  - Enrollments...")
        self.gen_enrollments()

        print("  - Grades...")
        self.gen_grades()

        print("  - Student Competencies...")
        self.gen_student_competencies()

        print("  - Student Skills...")
        self.gen_student_skills()

        print("  - Activities & Achievements...")
        self.gen_activities()
        self.gen_achievements()

        # Relationship data
        print("  - Role-Skill Maps...")
        self.gen_role_skill_maps()

        print("  - Alumni Cohorts & Success Patterns...")
        self.gen_alumni_cohorts()
        self.gen_success_patterns()

        # P1/P2 Extension data
        print("  - Opportunities...")
        self.gen_opportunities()

        print("  - Coaching Goals & Plans...")
        self.gen_coaching_goals()
        self.gen_coaching_plans()

        print("  - Risk Alerts...")
        self.gen_risk_alerts()

        print("  - Badges...")
        self.gen_badges()
        self.gen_student_badges()
        self.gen_skill_passports()

        print("  - Simulation Scenarios...")
        self.gen_simulation_scenarios()

        print("  - Advisors...")
        self.gen_advisors()
        self.gen_advisor_assignments()
        self.gen_advisor_notes()

        # Auth data
        print("  - Users...")
        self.gen_users()

        self.write_footer()

        return "\n".join(self.sql_lines)

    def save(self, filename: str = "04_generated_test_data.sql"):
        """Save generated SQL to file"""
        sql_content = self.generate()
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Write with UTF-8 encoding (no BOM)
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(sql_content)

        print(f"\nGenerated SQL saved to: {output_path}")
        print(f"Total lines: {len(self.sql_lines)}")
        print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")

        return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate IDINO Career test data')
    parser.add_argument('--students', type=int, default=200, help='Number of students (default: 200)')
    parser.add_argument('--output', type=str, default='04_generated_test_data.sql', help='Output filename')
    args = parser.parse_args()

    generator = DataGenerator()
    generator.save(args.output)

    print("\nData generation complete!")
    print(f"Students: {args.students}")
    print(f"Enrollments: ~{args.students * 6}")
    print(f"Student Competencies: {args.students * 6}")
    print(f"Student Skills: ~{args.students * 7}")


if __name__ == '__main__':
    main()
