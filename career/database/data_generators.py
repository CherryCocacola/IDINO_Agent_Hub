#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career Data Generators

Excel 스펙 기반 테이블별 테스트 데이터 생성기
"""

import uuid
import random
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

from migration_config import (
    GRADE_DISTRIBUTION, KOREAN_SURNAMES, KOREAN_GIVEN_NAMES,
    ACTIVITY_TYPES, ACHIEVEMENT_TYPES, COMPETENCY_CODES,
    RISK_TYPES, GOAL_TYPES, SCENARIO_TYPES, OPPORTUNITY_TYPES,
    ASSIGNMENT_TYPES, NOTE_TYPES, BADGE_CATEGORIES, BADGE_LEVELS,
    SKILL_CATEGORIES, TARGET_ROW_COUNTS
)


def gen_uuid() -> str:
    """UUID 생성"""
    return str(uuid.uuid4())


def random_date(start_year: int = 2020, end_year: int = 2025) -> date:
    """랜덤 날짜 생성"""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    random_days = random.randint(0, delta)
    return start + timedelta(days=random_days)


def random_datetime(start_year: int = 2020, end_year: int = 2025) -> datetime:
    """랜덤 datetime 생성"""
    d = random_date(start_year, end_year)
    return datetime.combine(d, datetime.min.time()) + timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )


def get_random_grade() -> Tuple[str, float]:
    """가중치 기반 랜덤 성적 생성"""
    rand = random.random()
    cumulative = 0
    for grade, point, prob in GRADE_DISTRIBUTION:
        cumulative += prob
        if rand <= cumulative:
            return grade, point
    return 'C0', 2.0


def korean_name() -> Tuple[str, str]:
    """한국어 이름 생성 (성, 이름)"""
    surname = random.choice(KOREAN_SURNAMES)
    given = random.choice(KOREAN_GIVEN_NAMES)
    return surname, given


class DataGenerator:
    """테이블별 데이터 생성기"""

    def __init__(self, conn=None):
        # 생성된 데이터 캐시 (FK 참조용)
        self.cache = {}
        self.conn = conn

    # ==========================================
    # Level 1: Independent Tables
    # ==========================================

    def gen_university(self) -> List[Dict]:
        """대학교 (1개)"""
        return [{
            'university_cd': 'UNIV01',
            'university_nm': 'IDINO University',
            'university_nm_en': 'IDINO University',
            'address': '서울특별시 강남구 테헤란로 123',
            'website': 'https://www.idino.edu',
            'use_fg': 'Y',
            'ins_user_id': 'SEED',
        }]

    def gen_competency(self) -> List[Dict]:
        """역량 정의 (6개)"""
        competencies = [
            ('COMP01', 'Problem Solving', '문제해결력', '복잡한 문제를 분석하고 해결하는 능력'),
            ('COMP02', 'Communication', '의사소통력', '효과적인 구두 및 서면 의사소통 능력'),
            ('COMP03', 'Teamwork', '협업능력', '팀 내 협력과 대인관계 능력'),
            ('COMP04', 'Leadership', '리더십', '조직을 이끌고 동기부여하는 능력'),
            ('COMP05', 'Critical Thinking', '비판적 사고', '정보를 분석하고 평가하는 능력'),
            ('COMP06', 'Creativity', '창의성', '새로운 아이디어를 생성하는 능력'),
        ]
        result = []
        weights = [0.20, 0.18, 0.17, 0.15, 0.15, 0.15]
        for i, (cd, nm_en, nm, defn) in enumerate(competencies):
            result.append({
                'competency_cd': cd,
                'competency_nm': nm,
                'competency_nm_en': nm_en,
                'definition': defn,
                'weight': weights[i],
                'max_score': 100,
                'ins_user_id': 'SEED',
            })
        self.cache['competencies'] = [c['competency_cd'] for c in result]
        return result

    def gen_skill(self) -> List[Dict]:
        """스킬 정의 (15개)"""
        skills = [
            ('SK01', 'Python', 'Python', 'technical', 2),
            ('SK02', 'Java', 'Java', 'technical', 3),
            ('SK03', 'SQL', 'SQL', 'technical', 2),
            ('SK04', 'JavaScript', 'JavaScript', 'technical', 2),
            ('SK05', 'React', 'React', 'technical', 3),
            ('SK06', 'Machine Learning', '머신러닝', 'technical', 4),
            ('SK07', 'Data Analysis', '데이터 분석', 'technical', 3),
            ('SK08', 'Cloud Computing', '클라우드', 'technical', 4),
            ('SK09', 'Communication', '의사소통', 'soft', 2),
            ('SK10', 'Leadership', '리더십', 'soft', 4),
            ('SK11', 'Teamwork', '팀워크', 'soft', 2),
            ('SK12', 'Project Management', 'PM', 'soft', 4),
            ('SK13', 'English', '영어', 'domain', 3),
            ('SK14', 'Presentation', '발표', 'soft', 3),
            ('SK15', 'Problem Solving', '문제해결', 'soft', 3),
        ]
        result = []
        for cd, nm_en, nm, cat, diff in skills:
            result.append({
                'skill_cd': cd,
                'skill_nm': nm,
                'skill_nm_en': nm_en,
                'category': cat,
                'difficulty': diff,
                'ins_user_id': 'SEED',
            })
        self.cache['skills'] = [s['skill_cd'] for s in result]
        return result

    def gen_term(self) -> List[Dict]:
        """학기 (12개: 2020-1 ~ 2025-2)"""
        terms = []
        for year in range(2020, 2026):
            for sem in [1, 2]:
                term_cd = f'{year}-{sem}'
                if sem == 1:
                    start = date(year, 3, 1)
                    end = date(year, 6, 30)
                    reg_start = date(year, 2, 15)
                    reg_end = date(year, 2, 28)
                else:
                    start = date(year, 9, 1)
                    end = date(year, 12, 20)
                    reg_start = date(year, 8, 15)
                    reg_end = date(year, 8, 31)

                terms.append({
                    'term_cd': term_cd,
                    'term_nm': f'{year} {"Spring" if sem == 1 else "Fall"}',
                    'start_date': start,
                    'end_date': end,
                    'registration_start': reg_start,
                    'registration_end': reg_end,
                    'ins_user_id': 'SEED',
                })
        self.cache['terms'] = [t['term_cd'] for t in terms]
        return terms

    def gen_badge(self) -> List[Dict]:
        """뱃지 정의"""
        badges = []
        badge_names = [
            ('Academic Excellence', 'academic', 'gold'),
            ('Skill Master', 'skill', 'platinum'),
            ('Activity Champion', 'activity', 'silver'),
            ('Team Player', 'achievement', 'bronze'),
            ('Innovation Award', 'special', 'gold'),
            ('Research Pioneer', 'academic', 'silver'),
            ('Code Warrior', 'skill', 'gold'),
            ('Community Leader', 'activity', 'gold'),
            ('Quick Learner', 'achievement', 'bronze'),
            ('Career Ready', 'special', 'platinum'),
        ]
        for i, (name, cat, level) in enumerate(badge_names, 1):
            points = {'bronze': 10, 'silver': 25, 'gold': 50, 'platinum': 100}[level]
            badges.append({
                'badge_id': gen_uuid(),
                'badge_cd': f'BADGE{i:03d}',
                'badge_nm': name,
                'badge_nm_en': name,
                'category': cat,
                'level': level,
                'points': points,
                'criteria': json.dumps({'type': cat, 'level': level}),
                'ins_user_id': 'SEED',
            })
        self.cache['badges'] = [(b['badge_id'], b['badge_cd']) for b in badges]
        return badges

    def gen_role(self) -> List[Dict]:
        """직무/진로 (15개)"""
        roles_data = [
            ('ROLE01', 'Software Engineer', '소프트웨어 엔지니어', 'IT', 75000000, 5.5),
            ('ROLE02', 'Data Scientist', '데이터 사이언티스트', 'IT', 80000000, 8.2),
            ('ROLE03', 'Product Manager', '프로덕트 매니저', 'IT', 85000000, 6.3),
            ('ROLE04', 'UX Designer', 'UX 디자이너', 'Design', 65000000, 4.8),
            ('ROLE05', 'DevOps Engineer', '데브옵스 엔지니어', 'IT', 78000000, 9.1),
            ('ROLE06', 'AI Engineer', 'AI 엔지니어', 'IT', 90000000, 12.5),
            ('ROLE07', 'Backend Developer', '백엔드 개발자', 'IT', 72000000, 5.8),
            ('ROLE08', 'Frontend Developer', '프론트엔드 개발자', 'IT', 68000000, 5.2),
            ('ROLE09', 'Data Analyst', '데이터 분석가', 'IT', 60000000, 6.0),
            ('ROLE10', 'Security Engineer', '보안 엔지니어', 'IT', 82000000, 7.5),
            ('ROLE11', 'Consultant', '컨설턴트', 'Business', 70000000, 3.2),
            ('ROLE12', 'Marketing Manager', '마케팅 매니저', 'Business', 65000000, 2.8),
            ('ROLE13', 'Financial Analyst', '재무 분석가', 'Finance', 75000000, 4.0),
            ('ROLE14', 'Research Scientist', '연구원', 'Research', 70000000, 3.5),
            ('ROLE15', 'Project Manager', 'PM', 'Management', 80000000, 4.5),
        ]
        roles = []
        for cd, nm_en, nm, cat, salary, growth in roles_data:
            roles.append({
                'role_cd': cd,
                'role_nm': nm,
                'role_nm_en': nm_en,
                'category': cat,
                'average_salary': salary,
                'growth_rate': growth,
                'ins_user_id': 'SEED',
            })
        self.cache['roles'] = [r['role_cd'] for r in roles]
        return roles

    def gen_program(self) -> List[Dict]:
        """비교과 프로그램"""
        program_types = ['seminar', 'contest', 'club', 'volunteer', 'certificate', 'internship']
        programs = []
        for i in range(1, TARGET_ROW_COUNTS.get('tb_program', 30) + 1):
            ptype = program_types[(i - 1) % len(program_types)]
            programs.append({
                'program_cd': f'PROG{i:03d}',
                'program_nm': f'{ptype.title()} Program {i}',
                'program_type': ptype,
                'organizer': f'Organization {i}',
                'start_date': random_date(2023, 2024),
                'end_date': random_date(2024, 2025),
                'ins_user_id': 'SEED',
            })
        self.cache['programs'] = [p['program_cd'] for p in programs]
        return programs

    # ==========================================
    # Level 2: References Level 1
    # ==========================================

    def gen_college(self) -> List[Dict]:
        """단과대학 (8개)"""
        colleges_data = [
            ('COL01', 'College of Engineering', '공과대학'),
            ('COL02', 'College of Business', '경영대학'),
            ('COL03', 'College of Natural Sciences', '자연과학대학'),
            ('COL04', 'College of Humanities', '인문대학'),
            ('COL05', 'College of Social Sciences', '사회과학대학'),
            ('COL06', 'College of Arts', '예술대학'),
            ('COL07', 'College of Medicine', '의과대학'),
            ('COL08', 'College of Education', '교육대학'),
        ]
        colleges = []
        for i, (cd, nm_en, nm) in enumerate(colleges_data, 1):
            colleges.append({
                'college_cd': cd,
                'university_cd': 'UNIV01',
                'college_nm': nm,
                'college_nm_en': nm_en,
                'sort_order': i,
                'ins_user_id': 'SEED',
            })
        self.cache['colleges'] = [c['college_cd'] for c in colleges]
        return colleges

    def gen_role_skill_map(self) -> List[Dict]:
        """직무-스킬 매핑"""
        roles = self.cache.get('roles', [f'ROLE{i:02d}' for i in range(1, 16)])
        skills = self.cache.get('skills', [f'SK{i:02d}' for i in range(1, 16)])

        mappings = []
        importance_levels = ['critical', 'important', 'nice_to_have']
        trends = ['growing', 'stable', 'declining']

        for role in roles:
            num_skills = random.randint(3, 6)
            selected_skills = random.sample(skills, num_skills)
            for skill in selected_skills:
                mappings.append({
                    'map_id': gen_uuid(),
                    'role_cd': role,
                    'skill_cd': skill,
                    'required_level': random.randint(2, 5),
                    'importance': random.choice(importance_levels),
                    'market_demand_score': round(random.uniform(30, 90), 2),
                    'growth_trend': random.choice(trends),
                    'ins_user_id': 'SEED',
                })
        return mappings[:TARGET_ROW_COUNTS.get('tb_role_skill_map', 60)]

    def gen_skill_competency_map(self) -> List[Dict]:
        """스킬-역량 매핑"""
        skills = self.cache.get('skills', [])
        competencies = self.cache.get('competencies', [])

        mappings = []
        for skill in skills:
            num_comp = random.randint(1, 3)
            selected_comps = random.sample(competencies, min(num_comp, len(competencies)))
            for comp in selected_comps:
                mappings.append({
                    'map_id': gen_uuid(),
                    'skill_cd': skill,
                    'competency_cd': comp,
                    'weight': round(random.uniform(0.5, 1.5), 2),
                    'ins_user_id': 'SEED',
                })
        return mappings[:TARGET_ROW_COUNTS.get('tb_skill_competency_map', 45)]

    def gen_skill_relation(self) -> List[Dict]:
        """스킬 관계"""
        skills = self.cache.get('skills', [])
        relation_types = ['prerequisite', 'related', 'complementary', 'advanced']
        relations = []
        used_keys = set()  # (from, to, type) 중복 방지

        target = TARGET_ROW_COUNTS.get('tb_skill_relation', 30)
        attempts = 0
        while len(relations) < target and attempts < target * 10:
            attempts += 1
            s1, s2 = random.sample(skills, 2)
            rel_type = random.choice(relation_types)
            key = (s1, s2, rel_type)
            if key not in used_keys:
                used_keys.add(key)
                relations.append({
                    'relation_id': gen_uuid(),
                    'skill_cd_from': s1,
                    'skill_cd_to': s2,
                    'relation_type': rel_type,
                    'strength': round(random.uniform(0.3, 1.0), 2),
                    'ins_user_id': 'SEED',
                })
        return relations

    # ==========================================
    # Level 3: References Level 2
    # ==========================================

    def gen_department(self) -> List[Dict]:
        """학과 (30개)"""
        dept_data = [
            # COL01 - Engineering
            ('DEPT01', 'COL01', 'Computer Science', '컴퓨터공학과', 140),
            ('DEPT02', 'COL01', 'Electrical Engineering', '전자공학과', 130),
            ('DEPT03', 'COL01', 'Mechanical Engineering', '기계공학과', 130),
            ('DEPT04', 'COL01', 'Chemical Engineering', '화학공학과', 130),
            ('DEPT05', 'COL01', 'Civil Engineering', '건축공학과', 140),
            ('DEPT06', 'COL01', 'Industrial Engineering', '산업공학과', 130),
            ('DEPT07', 'COL01', 'Software Engineering', '소프트웨어학과', 130),
            # COL02 - Business
            ('DEPT08', 'COL02', 'Business Administration', '경영학과', 120),
            ('DEPT09', 'COL02', 'Accounting', '회계학과', 120),
            ('DEPT10', 'COL02', 'Finance', '금융학과', 120),
            ('DEPT11', 'COL02', 'Marketing', '마케팅학과', 120),
            # COL03 - Natural Sciences
            ('DEPT12', 'COL03', 'Mathematics', '수학과', 120),
            ('DEPT13', 'COL03', 'Physics', '물리학과', 120),
            ('DEPT14', 'COL03', 'Chemistry', '화학과', 120),
            ('DEPT15', 'COL03', 'Biology', '생명과학과', 120),
            ('DEPT16', 'COL03', 'Statistics', '통계학과', 120),
            # COL04 - Humanities
            ('DEPT17', 'COL04', 'Korean Literature', '국어국문학과', 120),
            ('DEPT18', 'COL04', 'English Literature', '영어영문학과', 120),
            ('DEPT19', 'COL04', 'Philosophy', '철학과', 120),
            ('DEPT20', 'COL04', 'History', '사학과', 120),
            # COL05 - Social Sciences
            ('DEPT21', 'COL05', 'Sociology', '사회학과', 120),
            ('DEPT22', 'COL05', 'Psychology', '심리학과', 120),
            ('DEPT23', 'COL05', 'Political Science', '정치외교학과', 120),
            ('DEPT24', 'COL05', 'Economics', '경제학과', 120),
            # COL06 - Arts
            ('DEPT25', 'COL06', 'Design', '디자인학과', 130),
            ('DEPT26', 'COL06', 'Music', '음악학과', 130),
            ('DEPT27', 'COL06', 'Fine Arts', '미술학과', 130),
            # COL07 - Medicine
            ('DEPT28', 'COL07', 'Pre-Medicine', '의예과', 140),
            ('DEPT29', 'COL07', 'Nursing', '간호학과', 140),
            # COL08 - Education
            ('DEPT30', 'COL08', 'Education', '교육학과', 130),
        ]
        departments = []
        for i, (cd, col, nm_en, nm, credits) in enumerate(dept_data, 1):
            departments.append({
                'department_cd': cd,
                'college_cd': col,
                'department_nm': nm,
                'department_nm_en': nm_en,
                'graduation_credits': credits,
                'sort_order': i,
                'ins_user_id': 'SEED',
            })
        self.cache['departments'] = [d['department_cd'] for d in departments]
        return departments

    def gen_course(self) -> List[Dict]:
        """교과목"""
        courses = []
        course_types = ['major_required', 'major_elective', 'general_required', 'general_elective']
        departments = self.cache.get('departments', [])

        # 학과별 과목 생성
        course_num = 1
        for dept in departments[:15]:  # 주요 학과에만 과목 배정
            for grade in range(1, 5):
                for j in range(2):  # 학년당 2개
                    courses.append({
                        'course_cd': f'CRS{course_num:03d}',
                        'course_nm': f'Course {course_num}',
                        'course_nm_en': f'Course {course_num}',
                        'department_cd': dept,
                        'credits': random.choice([2, 3, 3, 3, 4]),
                        'course_type': random.choice(course_types),
                        'grade_level': grade,
                        'ins_user_id': 'SEED',
                    })
                    course_num += 1

        courses = courses[:TARGET_ROW_COUNTS.get('tb_course', 100)]
        self.cache['courses'] = [c['course_cd'] for c in courses]
        return courses

    # ==========================================
    # Level 4: References Level 3
    # ==========================================

    def gen_professor(self) -> List[Dict]:
        """교수"""
        professors = []
        departments = self.cache.get('departments', [])
        positions = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer']

        for i in range(1, TARGET_ROW_COUNTS.get('tb_professor', 50) + 1):
            surname, given = korean_name()
            professors.append({
                'professor_cd': f'PROF{i:03d}',
                'professor_nm': f'{surname}{given}',
                'professor_nm_en': f'{given} {surname}',
                'department_cd': random.choice(departments),
                'email': f'prof{i}@idino.edu',
                'position': random.choice(positions),
                'ins_user_id': 'SEED',
            })
        self.cache['professors'] = [p['professor_cd'] for p in professors]
        return professors

    def gen_advisor(self) -> List[Dict]:
        """지도교수/상담사"""
        advisors = []
        departments = self.cache.get('departments', [])

        for i in range(1, TARGET_ROW_COUNTS.get('tb_advisor', 20) + 1):
            surname, given = korean_name()
            advisors.append({
                'advisor_id': gen_uuid(),
                'advisor_cd': f'ADV{i:03d}',
                'advisor_nm': f'{surname} {given}',
                'department_cd': random.choice(departments),
                'email': f'advisor{i}@idino.edu',
                'max_students': random.randint(20, 40),
                'ins_user_id': 'SEED',
            })
        self.cache['advisors'] = [(a['advisor_id'], a['advisor_cd']) for a in advisors]
        return advisors

    def gen_student(self) -> List[Dict]:
        """학생 (204명)"""
        students = []
        departments = self.cache.get('departments', [])
        statuses = ['enrolled', 'enrolled', 'enrolled', 'graduated', 'leave_of_absence']
        genders = ['M', 'F']

        target = TARGET_ROW_COUNTS.get('tb_student', 204)

        for i in range(target):
            admission_year = 2020 + (i % 5)  # 2020-2024
            dept_idx = i % len(departments)
            dept = departments[dept_idx]

            # 학번: 입학년도(4) + 학과순번(2) + 순번(4)
            student_id = f'{admission_year}{(dept_idx + 1):02d}{(i % 100):04d}'

            surname, given = korean_name()
            years_enrolled = 2025 - admission_year
            current_grade = min(4, years_enrolled + 1)
            current_semester = min(8, years_enrolled * 2 + 1)

            students.append({
                'student_id': student_id,
                'student_nm': f'{surname}{given}',
                'student_nm_en': f'{given} {surname}',
                'university_cd': 'UNIV01',
                'department_cd': dept,
                'admission_year': admission_year,
                'current_grade': current_grade,
                'current_semester': current_semester,
                'email': f'{student_id}@idino.edu',
                'gender': random.choice(genders),
                'status': random.choice(statuses) if current_grade == 4 else 'enrolled',
                'ins_user_id': 'SEED',
            })
        self.cache['students'] = [s['student_id'] for s in students]
        return students

    def gen_prerequisite(self) -> List[Dict]:
        """선수과목"""
        courses = self.cache.get('courses', [])
        prereqs = []
        used_keys = set()  # (course_cd, prerequisite_course_cd) 중복 방지

        target = min(TARGET_ROW_COUNTS.get('tb_prerequisite', 50), len(courses) - 1)
        attempts = 0
        while len(prereqs) < target and attempts < target * 10:
            attempts += 1
            c1, c2 = random.sample(courses, 2)
            key = (c1, c2)
            if key not in used_keys:
                used_keys.add(key)
                prereqs.append({
                    'prerequisite_id': gen_uuid(),
                    'course_cd': c1,
                    'prerequisite_course_cd': c2,
                    'prerequisite_type': random.choice(['required', 'recommended']),
                    'ins_user_id': 'SEED',
                })
        return prereqs

    def gen_prerequisite_rule(self) -> List[Dict]:
        """선수과목 규칙"""
        courses = self.cache.get('courses', [])
        rules = []

        for i in range(TARGET_ROW_COUNTS.get('tb_prerequisite_rule', 30)):
            rules.append({
                'rule_id': gen_uuid(),
                'course_cd': random.choice(courses),
                'prerequisite_type': random.choice(['required', 'alternative', 'conditional']),
                'condition_expr': json.dumps({'min_grade': 'C0', 'credits': 3}),
                'is_strict': random.choice([True, False]),
                'ins_user_id': 'SEED',
            })
        return rules

    def gen_course_competency_map(self) -> List[Dict]:
        """과목-역량 매핑"""
        courses = self.cache.get('courses', [])
        competencies = self.cache.get('competencies', [])
        mappings = []

        for course in courses:
            num_comp = random.randint(1, 4)
            selected = random.sample(competencies, min(num_comp, len(competencies)))
            for comp in selected:
                mappings.append({
                    'map_id': gen_uuid(),
                    'course_cd': course,
                    'competency_cd': comp,
                    'contribution_weight': round(random.uniform(0.1, 0.5), 2),
                    'ins_user_id': 'SEED',
                })
        return mappings[:TARGET_ROW_COUNTS.get('tb_course_competency_map', 300)]

    def gen_alumni_cohort(self) -> List[Dict]:
        """동문 코호트"""
        departments = self.cache.get('departments', [])
        cohorts = []

        for dept in departments:
            for year in range(2018, 2024):
                cohorts.append({
                    'cohort_id': gen_uuid(),
                    'department_cd': dept,
                    'graduation_year': year,
                    'cohort_size': random.randint(20, 80),
                    'avg_gpa': round(random.uniform(2.8, 3.8), 2),
                    'employment_rate': round(random.uniform(70, 98), 2),
                    'avg_salary': random.randint(35000000, 80000000),
                    'ins_user_id': 'SEED',
                })
        return cohorts[:TARGET_ROW_COUNTS.get('tb_alumni_cohort', 150)]

    def gen_success_pattern(self) -> List[Dict]:
        """성공 패턴"""
        departments = self.cache.get('departments', [])
        roles = self.cache.get('roles', [])
        patterns = []

        for i in range(TARGET_ROW_COUNTS.get('tb_success_pattern', 45)):
            patterns.append({
                'pattern_id': gen_uuid(),
                'pattern_nm': f'Path to {random.choice(["Success", "Excellence", "Achievement"])} {i+1}',
                'pattern_type': random.choice(['academic', 'career', 'hybrid']),
                'department_cd': random.choice(departments),
                'role_cd': random.choice(roles),
                'description': f'Typical path for career success pattern {i+1}',
                'typical_gpa_range': f'{random.uniform(3.0, 3.5):.1f}-{random.uniform(3.6, 4.2):.1f}',
                'success_rate': round(random.uniform(60, 90), 2),
                'sample_size': random.randint(50, 300),
                'ins_user_id': 'SEED',
            })
        return patterns

    # ==========================================
    # Level 5: References Level 4
    # ==========================================

    def gen_user(self) -> List[Dict]:
        """사용자"""
        students = self.cache.get('students', [])
        users = []

        # Admin user
        users.append({
            'user_id': gen_uuid(),
            'login_id': 'admin',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.4QvKBjFz4Zj2Xu',
            'user_nm': 'Administrator',
            'email': 'admin@idino.edu',
            'user_type': 'admin',
            'role': 'admin',
            'status': 'active',
            'mfa_enabled': False,
            'ins_user_id': 'SEED',
        })

        # Student users
        for student_id in students:
            users.append({
                'user_id': gen_uuid(),
                'login_id': student_id,
                'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.4QvKBjFz4Zj2Xu',
                'user_nm': f'Student {student_id}',
                'email': f'{student_id}@idino.edu',
                'user_type': 'student',
                'student_id': student_id,
                'role': 'user',
                'status': 'active',
                'mfa_enabled': False,
                'ins_user_id': 'SEED',
            })

        self.cache['users'] = [(u['user_id'], u['login_id']) for u in users]
        return users

    def gen_course_offering(self) -> List[Dict]:
        """개설 교과목"""
        courses = self.cache.get('courses', [])
        terms = self.cache.get('terms', [])
        professors = self.cache.get('professors', [])
        offerings = []

        for term in terms:
            # 각 학기에 과목의 70% 개설
            num_courses = int(len(courses) * 0.7)
            selected = random.sample(courses, num_courses)
            for course in selected:
                offerings.append({
                    'offering_id': gen_uuid(),
                    'course_cd': course,
                    'term_cd': term,
                    'professor_cd': random.choice(professors),
                    'class_no': random.randint(1, 3),
                    'capacity': random.randint(30, 60),
                    'enrolled_count': random.randint(15, 50),
                    'ins_user_id': 'SEED',
                })

        offerings = offerings[:TARGET_ROW_COUNTS.get('tb_course_offering', 600)]
        self.cache['offerings'] = [(o['offering_id'], o['term_cd'], o['course_cd']) for o in offerings]
        return offerings

    def gen_professor_course(self) -> List[Dict]:
        """교수-과목 매핑"""
        professors = self.cache.get('professors', [])
        courses = self.cache.get('courses', [])
        mappings = []

        for prof in professors:
            num_courses = random.randint(2, 5)
            selected = random.sample(courses, min(num_courses, len(courses)))
            for i, course in enumerate(selected):
                mappings.append({
                    'professor_course_id': gen_uuid(),
                    'professor_cd': prof,
                    'course_cd': course,
                    'is_primary': 'Y' if i == 0 else 'N',
                    'ins_user_id': 'SEED',
                })

        return mappings[:TARGET_ROW_COUNTS.get('tb_professor_course', 150)]

    def gen_advisor_assignment(self) -> List[Dict]:
        """상담 배정"""
        advisors = self.cache.get('advisors', [])
        students = self.cache.get('students', [])
        assignments = []

        for student in students:
            advisor_id, _ = random.choice(advisors)
            assignments.append({
                'assignment_id': gen_uuid(),
                'advisor_id': advisor_id,
                'student_id': student,
                'assignment_type': random.choice(ASSIGNMENT_TYPES),
                'status': random.choice(['active', 'active', 'active', 'paused', 'completed']),
                'priority': random.randint(1, 3),
                'ins_user_id': 'SEED',
            })

        assignments = assignments[:TARGET_ROW_COUNTS.get('tb_advisor_assignment', 200)]
        self.cache['advisor_assignments'] = [(a['assignment_id'], a['advisor_id'], a['student_id']) for a in assignments]
        return assignments

    def gen_opportunity(self) -> List[Dict]:
        """기회 (인턴/장학)"""
        opportunities = []
        statuses = ['open', 'open', 'open', 'closed', 'draft']

        for i in range(TARGET_ROW_COUNTS.get('tb_opportunity', 50)):
            opp_type = random.choice(OPPORTUNITY_TYPES)
            start = random_date(2025, 2026)
            end = start + timedelta(days=random.randint(30, 90))

            opportunities.append({
                'opportunity_id': gen_uuid(),
                'opportunity_type': opp_type,
                'title': f'{opp_type.title()} Opportunity {i+1}',
                'organization': f'Company {i+1}',
                'description': f'Great {opp_type} opportunity for students',
                'application_start': start,
                'application_end': end,
                'location': random.choice(['Seoul', 'Daejeon', 'Busan', 'Remote']),
                'remote_available': random.choice([True, False]),
                'slots': random.randint(5, 20),
                'status': random.choice(statuses),
                'ins_user_id': 'SEED',
            })
        self.cache['opportunities'] = [o['opportunity_id'] for o in opportunities]
        return opportunities

    # ==========================================
    # Level 6: References Level 5
    # ==========================================

    def gen_enrollment(self) -> List[Dict]:
        """수강신청"""
        students = self.cache.get('students', [])
        offerings = self.cache.get('offerings', [])
        enrollments = []

        for student in students:
            # 학생당 평균 20개 수강
            num_enroll = random.randint(15, 25)
            selected = random.sample(offerings, min(num_enroll, len(offerings)))
            for offering_id, term_cd, course_cd in selected:
                enrollments.append({
                    'enrollment_id': gen_uuid(),
                    'student_id': student,
                    'course_offering_id': offering_id,
                    'term_cd': term_cd,
                    'status_cd': 'completed' if term_cd < '2025-1' else 'enrolled',
                    'ins_user_id': 'SEED',
                })

        enrollments = enrollments[:TARGET_ROW_COUNTS.get('tb_enrollment', 4000)]
        self.cache['enrollments'] = [(e['enrollment_id'], e['student_id'], e['term_cd'], e['status_cd']) for e in enrollments]
        return enrollments

    def gen_student_skill(self) -> List[Dict]:
        """학생 스킬"""
        students = self.cache.get('students', [])
        skills = self.cache.get('skills', [])
        student_skills = []
        trends = ['up', 'stable', 'down']

        for student in students:
            num_skills = random.randint(5, 10)
            selected = random.sample(skills, min(num_skills, len(skills)))
            for skill in selected:
                current = random.randint(1, 4)
                target = min(5, current + random.randint(1, 2))
                student_skills.append({
                    'student_skill_id': gen_uuid(),
                    'student_id': student,
                    'skill_cd': skill,
                    'current_level': current,
                    'target_level': target,
                    'evidence_count': random.randint(0, 10),
                    'trend': random.choices(trends, weights=[0.5, 0.35, 0.15])[0],
                    'ins_user_id': 'SEED',
                })

        return student_skills[:TARGET_ROW_COUNTS.get('tb_student_skill', 1500)]

    def gen_student_competency(self) -> List[Dict]:
        """학생 역량 현황"""
        students = self.cache.get('students', [])
        competencies = self.cache.get('competencies', [])
        student_comps = []
        statuses = ['excellent', 'good', 'average', 'improve', 'focus']
        trends = ['up', 'stable', 'down']

        for student in students:
            for comp in competencies:
                current = round(random.uniform(40, 95), 2)
                target = 85.0
                gap = max(0, target - current)
                status = 'excellent' if current >= 85 else ('good' if current >= 70 else 'improve')

                student_comps.append({
                    'student_competency_id': gen_uuid(),
                    'student_id': student,
                    'competency_cd': comp,
                    'current_score': current,
                    'target_score': target,
                    'gap_score': round(gap, 2),
                    'status': status,
                    'trend': random.choice(trends),
                    'ins_user_id': 'SEED',
                })

        return student_comps[:TARGET_ROW_COUNTS.get('tb_student_competency', 1224)]

    def gen_student_badge(self) -> List[Dict]:
        """학생 뱃지"""
        students = self.cache.get('students', [])
        badges = self.cache.get('badges', [])
        student_badges = []

        for student in students:
            num_badges = random.randint(1, 5)
            selected = random.sample(badges, min(num_badges, len(badges)))
            for badge_id, badge_cd in selected:
                student_badges.append({
                    'student_badge_id': gen_uuid(),
                    'student_id': student,
                    'badge_id': badge_id,
                    'earned_at': random_datetime(2022, 2025),
                    'earned_level': random.randint(1, 3),
                    'ins_user_id': 'SEED',
                })

        return student_badges[:TARGET_ROW_COUNTS.get('tb_student_badge', 700)]

    def gen_skill_passport(self) -> List[Dict]:
        """스킬 패스포트 (학생당 1개)"""
        students = self.cache.get('students', [])
        passports = []

        for student in students:
            passports.append({
                'passport_id': gen_uuid(),
                'student_id': student,
                'overall_score': round(random.uniform(30, 95), 2),
                'total_badges': random.randint(1, 10),
                'total_skills': random.randint(5, 15),
                'verified_skills': random.randint(1, 10),
                'is_public': random.choice([True, False]),
                'ins_user_id': 'SEED',
            })

        return passports

    def gen_coaching_goal(self) -> List[Dict]:
        """코칭 목표"""
        students = self.cache.get('students', [])
        roles = self.cache.get('roles', [])
        skills = self.cache.get('skills', [])
        goals = []
        statuses = ['draft', 'active', 'active', 'paused', 'completed', 'abandoned']

        for i in range(TARGET_ROW_COUNTS.get('tb_coaching_goal', 300)):
            student = random.choice(students)
            goal_type = random.choice(GOAL_TYPES)
            goals.append({
                'goal_id': gen_uuid(),
                'std_id': student,
                'title': f'{goal_type.title()} Goal {i+1}',
                'description': f'Description for {goal_type} goal',
                'goal_type': goal_type,
                'priority': random.randint(1, 3),
                'target_date': random_date(2025, 2027),
                'target_role_cd': random.choice(roles),
                'related_skills': random.sample(skills, min(3, len(skills))),  # text[] array
                'success_criteria': f'Achieve {random.randint(70, 100)}% proficiency',
                'motivation': random.choice(['career_growth', 'skill_improvement', 'personal_interest']),
                'status': random.choice(statuses),
                'progress_percentage': round(random.uniform(0, 100), 2),
                'ins_user_id': 'SEED',
            })

        self.cache['coaching_goals'] = [g['goal_id'] for g in goals]
        return goals

    def gen_activity(self) -> List[Dict]:
        """활동"""
        students = self.cache.get('students', [])
        programs = self.cache.get('programs', [])
        activities = []
        statuses = ['completed', 'ongoing', 'registered']

        for i in range(TARGET_ROW_COUNTS.get('tb_activity', 400)):
            student = random.choice(students)
            start = random_date(2023, 2025)
            activities.append({
                'activity_id': gen_uuid(),
                'student_id': student,
                'program_cd': random.choice(programs),
                'activity_type': random.choice(ACTIVITY_TYPES),
                'title': f'{random.choice(ACTIVITY_TYPES).title()} Activity {i+1}',
                'start_date': start,
                'end_date': start + timedelta(days=random.randint(30, 180)),
                'hours': random.randint(10, 200),
                'status': random.choice(statuses),
                'ins_user_id': 'SEED',
            })

        return activities

    def gen_achievement(self) -> List[Dict]:
        """성과/자격증"""
        students = self.cache.get('students', [])
        achievements = []
        levels = ['bronze', 'silver', 'gold', 'platinum']

        for i in range(TARGET_ROW_COUNTS.get('tb_achievement', 300)):
            student = random.choice(students)
            ach_type = random.choice(ACHIEVEMENT_TYPES)
            achievements.append({
                'achievement_id': gen_uuid(),
                'student_id': student,
                'achievement_type': ach_type,
                'title': f'{ach_type.title()} Achievement {i+1}',
                'issuer': 'Issuer Organization',
                'issue_date': random_date(2022, 2025),
                'level': random.choice(levels),
                'verified': 'Y',
                'ins_user_id': 'SEED',
            })

        return achievements

    def gen_risk_alert(self) -> List[Dict]:
        """위험 알림"""
        students = self.cache.get('students', [])
        alerts = []
        severities = ['low', 'medium', 'high', 'critical']
        statuses = ['active', 'resolved', 'dismissed']

        for i in range(TARGET_ROW_COUNTS.get('tb_risk_alert', 100)):
            risk_type = random.choice(RISK_TYPES)
            alerts.append({
                'alert_id': gen_uuid(),
                'student_id': random.choice(students),
                'risk_type': risk_type,
                'severity': random.choice(severities),
                'title': f'{risk_type.replace("_", " ").title()} Alert',
                'trigger_value': round(random.uniform(1.5, 3.0), 2),
                'threshold_value': 2.5,
                'status': random.choice(statuses),
                'ins_user_id': 'SEED',
            })

        return alerts

    def gen_simulation_scenario(self) -> List[Dict]:
        """시뮬레이션 시나리오"""
        students = self.cache.get('students', [])
        scenarios = []

        for i in range(TARGET_ROW_COUNTS.get('tb_simulation_scenario', 200)):
            student = random.choice(students)
            scenario_type = random.choice(SCENARIO_TYPES)
            scenarios.append({
                'scenario_id': gen_uuid(),
                'student_id': student,
                'scenario_type': scenario_type,
                'title': f'{scenario_type.title()} What-If Scenario {i+1}',
                'base_state': json.dumps({'gpa': round(random.uniform(2.5, 4.0), 2)}),
                'changes': json.dumps({'add_course': f'CRS{random.randint(1,100):03d}'}),
                'confidence_level': round(random.uniform(0.5, 0.95), 2),
                'ins_user_id': 'SEED',
            })

        self.cache['scenarios'] = [s['scenario_id'] for s in scenarios]
        return scenarios

    def gen_recommendation_run(self) -> List[Dict]:
        """추천 실행"""
        students = self.cache.get('students', [])
        runs = []
        run_types = ['course', 'skill', 'career', 'opportunity']
        statuses = ['completed', 'completed', 'failed', 'processing']

        for i in range(TARGET_ROW_COUNTS.get('tb_recommendation_run', 200)):
            runs.append({
                'run_id': gen_uuid(),
                'student_id': random.choice(students),
                'run_type': random.choice(run_types),
                'model_version': 'v1.0',
                'prompt_tokens': random.randint(100, 500),
                'completion_tokens': random.randint(200, 1000),
                'latency_ms': random.randint(500, 3000),
                'status': random.choice(statuses),
                'run_dt': random_datetime(2024, 2025),
            })

        self.cache['recommendation_runs'] = [r['run_id'] for r in runs]
        return runs

    def gen_opportunity_recommendation(self) -> List[Dict]:
        """기회 추천"""
        students = self.cache.get('students', [])
        opportunities = self.cache.get('opportunities', [])
        recs = []
        used_keys = set()  # (student_id, opportunity_id) 중복 방지
        statuses = ['recommended', 'viewed', 'applied', 'dismissed']

        target = TARGET_ROW_COUNTS.get('tb_opportunity_recommendation', 400)
        attempts = 0
        while len(recs) < target and attempts < target * 10:
            attempts += 1
            student = random.choice(students)
            opp = random.choice(opportunities)
            key = (student, opp)
            if key not in used_keys:
                used_keys.add(key)
                recs.append({
                    'recommendation_id': gen_uuid(),
                    'student_id': student,
                    'opportunity_id': opp,
                    'match_score': round(random.uniform(50, 98), 2),
                    'status': random.choice(statuses),
                    'ins_user_id': 'SEED',
                })

        return recs

    def gen_opportunity_application(self) -> List[Dict]:
        """기회 지원"""
        students = self.cache.get('students', [])
        opportunities = self.cache.get('opportunities', [])
        apps = []
        used_keys = set()  # (student_id, opportunity_id) 중복 방지
        statuses = ['submitted', 'reviewing', 'accepted', 'rejected', 'withdrawn']

        target = TARGET_ROW_COUNTS.get('tb_opportunity_application', 300)
        attempts = 0
        while len(apps) < target and attempts < target * 10:
            attempts += 1
            student = random.choice(students)
            opp = random.choice(opportunities)
            key = (student, opp)
            if key not in used_keys:
                used_keys.add(key)
                apps.append({
                    'application_id': gen_uuid(),
                    'student_id': student,
                    'opportunity_id': opp,
                    'applied_at': random_datetime(2024, 2025),
                    'status': random.choice(statuses),
                    'ins_user_id': 'SEED',
                })

        return apps

    def gen_user_session(self) -> List[Dict]:
        """사용자 세션"""
        users = self.cache.get('users', [])
        sessions = []

        for i in range(TARGET_ROW_COUNTS.get('tb_user_session', 500)):
            user_id, _ = random.choice(users)
            created = random_datetime(2024, 2025)
            sessions.append({
                'session_id': gen_uuid(),
                'user_id': user_id,
                'refresh_token': gen_uuid(),
                'device_info': f'Browser/{random.choice(["Chrome", "Firefox", "Safari"])}',
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'expires_at': created + timedelta(days=7),
                'is_active': random.choice([True, True, False]),
                'ins_dt': created,
            })

        return sessions

    def gen_cohort_snapshot(self) -> List[Dict]:
        """코호트 스냅샷"""
        departments = self.cache.get('departments', [])
        snapshots = []

        for dept in departments:
            for year in range(2023, 2026):
                for month in [3, 6, 9, 12]:
                    if year == 2025 and month > 6:
                        continue
                    for grade in range(1, 5):
                        snapshots.append({
                            'snapshot_id': gen_uuid(),
                            'department_cd': dept,
                            'snapshot_date': date(year, month, 1),
                            'grade_level': grade,
                            'total_students': random.randint(30, 80),
                            'at_risk_count': random.randint(0, 10),
                            'avg_gpa': round(random.uniform(2.5, 3.8), 2),
                            'avg_completion_rate': round(random.uniform(60, 95), 2),
                            'ins_user_id': 'SEED',
                        })

        return snapshots[:TARGET_ROW_COUNTS.get('tb_cohort_snapshot', 500)]

    def gen_advisor_intervention(self) -> List[Dict]:
        """상담 개입"""
        assignments = self.cache.get('advisor_assignments', [])
        interventions = []
        types = ['meeting', 'call', 'email', 'referral', 'emergency']
        statuses = ['scheduled', 'completed', 'cancelled', 'no_show']

        for i in range(TARGET_ROW_COUNTS.get('tb_advisor_intervention', 100)):
            assign_id, _, _ = random.choice(assignments)
            interventions.append({
                'intervention_id': gen_uuid(),
                'assignment_id': assign_id,
                'intervention_type': random.choice(types),
                'scheduled_at': random_datetime(2024, 2025),
                'status': random.choice(statuses),
                'follow_up_required': random.choice([True, False]),
                'ins_user_id': 'SEED',
            })

        return interventions

    def gen_advisor_note(self) -> List[Dict]:
        """상담 메모"""
        assignments = self.cache.get('advisor_assignments', [])
        notes = []

        for i in range(TARGET_ROW_COUNTS.get('tb_advisor_note', 300)):
            assign_id, _, _ = random.choice(assignments)
            note_type = random.choice(NOTE_TYPES)
            notes.append({
                'note_id': gen_uuid(),
                'assignment_id': assign_id,
                'note_type': note_type,
                'content': f'Sample {note_type} note content for this student session.',
                'is_private': random.choice([True, False, False]),
                'ins_user_id': 'SEED',
            })

        return notes

    # ==========================================
    # Level 7: Deepest Dependencies
    # ==========================================

    def gen_grade(self) -> List[Dict]:
        """성적 (completed enrollment만)"""
        enrollments = self.cache.get('enrollments', [])
        courses = self.cache.get('courses', [])
        grades = []

        # completed enrollment만 성적 생성
        completed = [e for e in enrollments if e[3] == 'completed']

        for enroll_id, student_id, term_cd, _ in completed:
            grade_letter, grade_point = get_random_grade()
            course_cd = random.choice(courses) if courses else None
            grades.append({
                'grade_id': gen_uuid(),
                'enrollment_id': enroll_id,
                'student_id': student_id,
                'course_cd': course_cd,
                'term_cd': term_cd,
                'grade_letter': grade_letter,
                'grade_point': grade_point,
                'credits_earned': random.choice([2, 3, 3, 3, 4]),
                'ins_user_id': 'SEED',
            })

        return grades[:TARGET_ROW_COUNTS.get('tb_grade', 4000)]

    def gen_grade_summary(self) -> List[Dict]:
        """학기 성적 요약"""
        students = self.cache.get('students', [])
        terms = self.cache.get('terms', [])
        summaries = []

        for student in students:
            # 2025-1 이전 학기만 요약 생성
            past_terms = [t for t in terms if t < '2025-1']
            for term in past_terms[:random.randint(4, 8)]:
                gpa = round(random.uniform(2.0, 4.5), 2)
                credits = random.randint(12, 21)
                summaries.append({
                    'summary_id': gen_uuid(),
                    'student_id': student,
                    'term_cd': term,
                    'total_credits': credits,
                    'earned_credits': credits,
                    'gpa': gpa,
                    'major_gpa': round(gpa + random.uniform(-0.3, 0.3), 2),
                    'ins_user_id': 'SEED',
                })

        return summaries[:TARGET_ROW_COUNTS.get('tb_grade_summary', 1500)]

    def gen_cumulative_summary(self) -> List[Dict]:
        """누적 성적 요약 (학생당 1개)"""
        students = self.cache.get('students', [])
        summaries = []

        for student in students:
            total_earned = random.randint(60, 140)
            major_earned = int(total_earned * 0.5)
            liberal_earned = int(total_earned * 0.25)

            summaries.append({
                'summary_id': gen_uuid(),
                'student_id': student,
                'total_credits_required': 130,
                'total_credits_earned': total_earned,
                'major_credits_required': 60,
                'major_credits_earned': major_earned,
                'liberal_credits_required': 30,
                'liberal_credits_earned': liberal_earned,
                'cumulative_gpa': round(random.uniform(2.0, 4.3), 2),
                'major_gpa': round(random.uniform(2.0, 4.5), 2),
                'completion_rate': round(total_earned / 130 * 100, 2),
                'ins_user_id': 'SEED',
            })

        return summaries

    def gen_coaching_plan(self) -> List[Dict]:
        """코칭 계획 (goal당 여러 개 가능)"""
        goals = self.cache.get('coaching_goals', [])
        skills = self.cache.get('skills', [])
        plans = []

        for goal_id in goals:
            # 각 목표당 2~4개 계획
            num_plans = random.randint(2, 4)
            for idx in range(num_plans):
                is_completed = random.random() < 0.3
                plans.append({
                    'plan_id': gen_uuid(),
                    'goal_id': goal_id,
                    'title': f'Plan {idx+1} for Goal',
                    'description': f'Description for plan step {idx+1}',
                    'order_index': idx + 1,
                    'due_date': random_date(2025, 2026),
                    'estimated_hours': random.randint(5, 30),
                    'related_skill_cd': random.choice(skills) if skills else None,
                    'is_completed': is_completed,
                    'completed_at': random_datetime(2025, 2026) if is_completed else None,
                    'actual_hours': random.randint(3, 35) if is_completed else None,
                    'notes': f'Notes for plan {idx+1}' if random.random() > 0.5 else None,
                    'ins_user_id': 'SEED',
                })

        self.cache['coaching_plans'] = [p['plan_id'] for p in plans]
        return plans

    def gen_coaching_checkin(self) -> List[Dict]:
        """코칭 체크인"""
        goals = self.cache.get('coaching_goals', [])
        checkins = []
        moods = ['happy', 'motivated', 'neutral', 'stressed', 'frustrated']

        for goal_id in goals:
            num_checkins = random.randint(2, 4)
            for _ in range(num_checkins):
                checkins.append({
                    'checkin_id': gen_uuid(),
                    'goal_id': goal_id,
                    'mood': random.choice(moods),
                    'progress_note': f'Progress note for checkin',
                    'blockers': random.choice([None, 'Time management', 'Resource constraints', 'Motivation']),
                    'next_steps': 'Continue working on goals',
                    'reflection': random.choice([None, 'Good progress this week', 'Need to improve pace']),
                    'ai_feedback': random.choice([None, 'AI suggests focusing on key skills']),
                    'ai_suggestions': random.choice([None, ['Practice more', 'Review materials']]),  # text[] array
                    'ins_user_id': 'SEED',
                })

        return checkins[:TARGET_ROW_COUNTS.get('tb_coaching_checkin', 600)]

    def gen_coaching_retrospective(self) -> List[Dict]:
        """코칭 회고"""
        goals = self.cache.get('coaching_goals', [])
        retros = []

        well_options = ['Achieved milestone targets', 'Improved technical skills', 'Better collaboration', 'Met deadlines']
        improve_options = ['Better time management', 'More focus on details', 'Communication skills', 'Work-life balance']
        lessons = ['Consistency is key', 'Planning helps execution', 'Ask for help early', 'Break down large tasks']
        next_goals_options = ['Continue skill development', 'Take on leadership role', 'Complete certification', 'Expand network']

        for i in range(TARGET_ROW_COUNTS.get('tb_coaching_retrospective', 150)):
            goal_id = random.choice(goals)
            retros.append({
                'retrospective_id': gen_uuid(),
                'goal_id': goal_id,
                'what_went_well': random.choice(well_options),
                'what_could_improve': random.choice(improve_options),
                'lessons_learned': random.choice(lessons),
                'next_goals': random.choice(next_goals_options),
                'satisfaction_rating': random.randint(1, 5),
                'ai_analysis': random.choice([None, 'Good progress observed', 'Needs improvement in focus areas']),
                'ai_recommendations': random.choice([None, ['Set clearer goals', 'Track progress weekly']]),  # text[] array
                'created_at': random_datetime(2024, 2026),
                'ins_user_id': 'SEED',
            })

        return retros

    def gen_recommendation_item(self) -> List[Dict]:
        """추천 항목"""
        runs = self.cache.get('recommendation_runs', [])
        items = []
        item_types = ['course', 'skill', 'activity', 'opportunity']
        priorities = ['high', 'medium', 'low']

        for run_id in runs:
            num_items = random.randint(2, 5)
            for j in range(num_items):
                items.append({
                    'item_id': gen_uuid(),
                    'run_id': run_id,
                    'item_type': random.choice(item_types),
                    'title': f'Recommendation Item {len(items) + 1}',
                    'priority': random.choice(priorities),
                    'confidence_score': round(random.uniform(0.5, 0.98), 2),
                    'ins_dt': random_datetime(2024, 2025),
                })

        return items[:TARGET_ROW_COUNTS.get('tb_recommendation_item', 500)]

    def gen_eval_feedback(self) -> List[Dict]:
        """평가 피드백"""
        runs = self.cache.get('recommendation_runs', [])
        users = self.cache.get('users', [])
        feedbacks = []
        types = ['helpful', 'not_helpful', 'neutral', 'error_report']

        for i in range(TARGET_ROW_COUNTS.get('tb_eval_feedback', 500)):
            user_id, _ = random.choice(users)
            feedbacks.append({
                'feedback_id': gen_uuid(),
                'run_id': random.choice(runs) if runs else None,
                'user_id': user_id,
                'feedback_type': random.choice(types),
                'rating': random.randint(1, 5),
                'is_helpful': random.choice([True, True, False]),
                'ins_dt': random_datetime(2024, 2025),
            })

        return feedbacks

    def gen_scenario_comparison(self) -> List[Dict]:
        """시나리오 비교"""
        from psycopg2.extensions import AsIs
        students = self.cache.get('students', [])
        scenarios = self.cache.get('scenarios', [])
        comparisons = []

        for i in range(TARGET_ROW_COUNTS.get('tb_scenario_comparison', 150)):
            student = random.choice(students)
            num_scenarios = random.randint(2, 4)
            scenario_id_strings = random.sample(scenarios, min(num_scenarios, len(scenarios))) if scenarios else []
            # Format as PostgreSQL uuid[] literal with explicit cast
            uuid_array_literal = "ARRAY[" + ",".join(f"'{s}'::uuid" for s in scenario_id_strings) + "]::uuid[]"

            comparisons.append({
                'comparison_id': gen_uuid(),
                'student_id': student,
                'scenario_ids': AsIs(uuid_array_literal),  # Use AsIs for raw SQL literal
                'comparison_metrics': json.dumps({
                    'gpa_diff': round(random.uniform(-0.5, 0.5), 2),
                    'skill_improvement': random.randint(1, 5)
                }),
                'recommendation': 'Based on analysis, scenario 1 is recommended',
                'ai_analysis': json.dumps({
                    'confidence': round(random.uniform(0.7, 0.95), 2),
                    'factors': ['career_fit', 'skill_match', 'market_demand']
                }),
                'created_at': random_datetime(2024, 2026),
                'ins_user_id': 'SEED',
            })

        return comparisons

    def gen_skill_gap_analysis(self) -> List[Dict]:
        """스킬 갭 분석"""
        students = self.cache.get('students', [])
        roles = self.cache.get('roles', [])
        skills = self.cache.get('skills', [])
        analyses = []

        for i in range(TARGET_ROW_COUNTS.get('tb_skill_gap_analysis', 1000)):
            student = random.choice(students)
            top_skills = random.sample(skills, min(3, len(skills)))

            analyses.append({
                'analysis_id': gen_uuid(),
                'student_id': student,
                'target_role_cd': random.choice(roles),
                'analysis_date': random_datetime(2024, 2025),
                'overall_gap_score': round(random.uniform(10, 60), 2),
                'gap_details': json.dumps({
                    skill: random.randint(1, 3) for skill in top_skills
                }),
                'top_priority_skills': top_skills,
                'ins_user_id': 'SEED',
            })

        return analyses
