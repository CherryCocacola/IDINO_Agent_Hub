#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career 전체 테이블 데이터 생성 스크립트
실제 테이블 구조에 맞춰 데이터 생성
"""

import psycopg2
import random
import uuid
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
import argparse
import json
import sys
import os

# 현재 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': '2012'
}
SCHEMA = 'idino_career'

GRADE_DISTRIBUTION = [
    ('A+', 4.5, 0.10), ('A0', 4.0, 0.15), ('B+', 3.5, 0.20),
    ('B0', 3.0, 0.25), ('C+', 2.5, 0.15), ('C0', 2.0, 0.10),
    ('D+', 1.5, 0.03), ('D0', 1.0, 0.02),
]

CERTIFICATIONS = [
    ('정보처리기사', '한국산업인력공단', 'certification'),
    ('SQLD', '한국데이터산업진흥원', 'certification'),
    ('빅데이터분석기사', '한국데이터산업진흥원', 'certification'),
    ('AWS Solutions Architect', 'Amazon', 'certification'),
    ('TOEIC 800+', 'ETS', 'language'),
    ('교내 해커톤 대상', '대학교', 'award'),
]


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_random_grade():
    rand = random.random()
    cumulative = 0
    for grade, point, prob in GRADE_DISTRIBUTION:
        cumulative += prob
        if rand <= cumulative:
            return grade, point
    return 'C0', 2.0


def clear_tables(cur):
    """데이터 삭제"""
    tables = [
        'tb_recommendation_evidence', 'tb_recommendation_item', 'tb_recommendation_run',
        'tb_coaching_checkin', 'tb_coaching_plan', 'tb_coaching_goal',
        'tb_risk_alert', 'tb_advisor_assignment',
        'tb_assessment_result', 'tb_assessment',
        'tb_course_competency_map', 'tb_skill_competency_map', 'tb_skill_gap_analysis',
        'tb_opportunity_application',
        'tb_student_badge', 'tb_worknet_diagnosis', 'tb_constraint_check',
        'tb_prerequisite', 'tb_professor_course',
        'tb_grade_summary', 'tb_grade', 'tb_enrollment', 'tb_course_offering',
        'tb_participation', 'tb_achievement', 'tb_student_skill', 'tb_portfolio',
    ]
    for table in tables:
        try:
            cur.execute(f'DELETE FROM {SCHEMA}.{table}')
            print(f"  [v] {table}")
        except Exception as e:
            pass


# ============ 기본 데이터 생성 ============

def generate_course_offerings(cur):
    """과목 개설 정보"""
    print("\n[1] tb_course_offering...")

    cur.execute(f"SELECT course_cd FROM {SCHEMA}.tb_course")
    courses = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT term_cd FROM {SCHEMA}.tb_term")
    terms = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT professor_cd FROM {SCHEMA}.tb_professor")
    professors = [r[0] for r in cur.fetchall()]

    offerings = []
    offering_map = {}

    for term in terms:
        term_courses = random.sample(courses, int(len(courses) * 0.7))
        for course_cd in term_courses:
            oid = str(uuid.uuid4())
            offerings.append((oid, course_cd, term, random.choice(professors), '01', 40, 0))
            offering_map[(course_cd, term)] = oid

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_course_offering
        (offering_id, course_cd, term_cd, professor_cd, section, capacity, enrolled_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, offerings)
    print(f"  [v] {len(offerings)} rows")
    return offering_map


def generate_enrollments_and_grades(cur, offering_map):
    """수강/성적"""
    print("\n[2] tb_enrollment, tb_grade, tb_grade_summary...")

    cur.execute(f"SELECT student_id, admission_year FROM {SCHEMA}.tb_student")
    students = cur.fetchall()

    cur.execute(f"SELECT term_cd FROM {SCHEMA}.tb_term ORDER BY term_cd")
    terms = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT course_cd, credits FROM {SCHEMA}.tb_course")
    course_credits = dict(cur.fetchall())

    enrollments = []
    grades = []
    summaries = []

    for student_id, adm_year in students:
        for term in terms:
            term_year = int(term.split('-')[0])
            if term_year < adm_year:
                continue

            is_current = (term == '2025-1')
            term_offs = [(k, v) for k, v in offering_map.items() if k[1] == term]

            if len(term_offs) < 5:
                continue

            selected = random.sample(term_offs, min(6, len(term_offs)))
            term_credits = 0
            term_points = 0

            for (course_cd, t), oid in selected:
                eid = str(uuid.uuid4())
                status = 'enrolled' if is_current else 'completed'
                enrollments.append((eid, student_id, oid, status))

                if not is_current:
                    grade, gp = get_random_grade()
                    grades.append((str(uuid.uuid4()), eid, grade, gp, gp >= 1.0))
                    credits = course_credits.get(course_cd, 3)
                    term_credits += credits
                    term_points += gp * credits

            if not is_current and term_credits > 0:
                gpa = round(term_points / term_credits, 2)
                summaries.append((str(uuid.uuid4()), student_id, term, term_credits, term_credits, term_points, gpa, gpa))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_enrollment (enrollment_id, student_id, offering_id, enrollment_status) VALUES (%s,%s,%s,%s)", enrollments)
    print(f"  [v] enrollment: {len(enrollments)}")

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_grade (grade_id, enrollment_id, grade, grade_point, is_pass) VALUES (%s,%s,%s,%s,%s)", grades)
    print(f"  [v] grade: {len(grades)}")

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_grade_summary (summary_id, student_id, term_cd, credits_attempted, credits_earned, grade_points, gpa, major_gpa) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", summaries)
    print(f"  [v] grade_summary: {len(summaries)}")


def generate_participation(cur):
    """비교과 참여"""
    print("\n[3] tb_participation...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT program_cd FROM {SCHEMA}.tb_program")
    programs = [r[0] for r in cur.fetchall()]

    data = []
    for sid in students:
        n = random.randint(1, 3)
        for prog in random.sample(programs, min(n, len(programs))):
            status = random.choice(['completed', 'completed', 'in_progress'])
            start = datetime.now() - timedelta(days=random.randint(30, 365))
            end = start + timedelta(days=90) if status == 'completed' else None
            data.append((str(uuid.uuid4()), sid, prog, status, start, end))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_participation (participation_id, student_id, program_cd, participation_status, started_at, completed_at) VALUES (%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_achievement(cur):
    """자격증/수상"""
    print("\n[4] tb_achievement...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    data = []
    for sid in students:
        n = random.choices([0,1,2,3], weights=[0.3,0.35,0.25,0.1])[0]
        for cert in random.sample(CERTIFICATIONS, min(n, len(CERTIFICATIONS))):
            data.append((str(uuid.uuid4()), sid, cert[2], cert[0], cert[1], datetime.now().date() - timedelta(days=random.randint(0,365)), True))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_achievement (achievement_id, student_id, achievement_type, achievement_nm, issuing_organization, acquired_date, verified) VALUES (%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_student_skill(cur):
    """학생 스킬"""
    print("\n[5] tb_student_skill...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT skill_cd FROM {SCHEMA}.tb_skill")
    skills = [r[0] for r in cur.fetchall()]

    data = []
    trends = ['improving', 'stable', 'declining']

    for sid in students:
        for skill in random.sample(skills, min(5, len(skills))):
            curr = random.randint(1, 4)
            tgt = min(5, curr + random.randint(1, 2))
            data.append((str(uuid.uuid4()), sid, skill, curr, tgt, random.randint(0,5), datetime.now().date(), 'system', random.choice(trends)))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_portfolio(cur):
    """포트폴리오"""
    print("\n[6] tb_portfolio...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    data = []
    selected = random.sample(students, int(len(students) * 0.3))

    for sid in selected:
        data.append((str(uuid.uuid4()), sid, 'github', 'GitHub', f'https://github.com/{sid}', 'Projects', True))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_portfolio (portfolio_id, student_id, artifact_type, title, url, description, is_primary) VALUES (%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


# ============ 추가 테이블 ============

def generate_prerequisite(conn, cur):
    """선수과목"""
    print("\n[7] tb_prerequisite...")

    # 실제 존재하는 과목 코드 조회
    cur.execute(f"SELECT course_cd FROM {SCHEMA}.tb_course")
    existing_courses = set(r[0] for r in cur.fetchall())

    prereqs = [
        ('CS102', 'CS101'), ('CS103', 'CS102'), ('CS201', 'CS101'),
        ('CS202', 'CS201'), ('CS301', 'CS201'), ('CS302', 'CS201'),
    ]

    # 존재하는 과목만 필터링
    valid_prereqs = [(c, p) for c, p in prereqs if c in existing_courses and p in existing_courses]
    data = [(str(uuid.uuid4()), c, p, True) for c, p in valid_prereqs]

    if data:
        try:
            cur.executemany(f"INSERT INTO {SCHEMA}.tb_prerequisite (prerequisite_id, course_cd, prerequisite_course_cd, is_required) VALUES (%s,%s,%s,%s)", data)
            conn.commit()
            print(f"  [v] {len(data)}")
        except Exception as e:
            conn.rollback()
            print(f"  [!] skip: {e}")
    else:
        print("  [!] skip (no valid courses)")


def generate_professor_course(conn, cur):
    """교수-과목 매핑"""
    print("\n[8] tb_professor_course...")

    try:
        cur.execute(f"SELECT professor_cd FROM {SCHEMA}.tb_professor")
        profs = [r[0] for r in cur.fetchall()]

        if not profs:
            print("  [!] skip (no professors)")
            return

        cur.execute(f"SELECT course_cd FROM {SCHEMA}.tb_course")
        courses = [r[0] for r in cur.fetchall()]

        if not courses:
            print("  [!] skip (no courses)")
            return

        data = []
        for c in courses:
            p = random.choice(profs)
            data.append((str(uuid.uuid4()), p, c, True))

        cur.executemany(f"INSERT INTO {SCHEMA}.tb_professor_course (mapping_id, professor_cd, course_cd, is_primary) VALUES (%s,%s,%s,%s)", data)
        conn.commit()
        print(f"  [v] {len(data)}")
    except Exception as e:
        conn.rollback()
        print(f"  [!] error: {e}")


def generate_course_competency_map(cur):
    """과목-역량 매핑 (핵심!)"""
    print("\n[9] tb_course_competency_map...")

    cur.execute(f"SELECT course_cd, course_type FROM {SCHEMA}.tb_course")
    courses = cur.fetchall()

    cur.execute(f"SELECT competency_cd FROM {SCHEMA}.tb_competency")
    comps = [r[0] for r in cur.fetchall()]

    # 과목 유형별 역량 가중치
    weights = {
        '전공필수': [40, 30, 15, 15],
        '전공선택': [35, 35, 15, 15],
        '교양필수': [15, 15, 35, 35],
        '교양선택': [20, 20, 30, 30],
    }

    data = []
    for course_cd, ctype in courses:
        w = weights.get(ctype, [25,25,25,25])
        for i, comp in enumerate(comps[:4]):
            wt = w[i] + random.randint(-5, 5)
            if wt > 0:
                data.append((str(uuid.uuid4()), course_cd, comp, wt))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_course_competency_map (mapping_id, course_cd, competency_cd, contribution_weight) VALUES (%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_skill_competency_map(cur):
    """스킬-역량 매핑"""
    print("\n[10] tb_skill_competency_map...")

    cur.execute(f"SELECT skill_cd FROM {SCHEMA}.tb_skill")
    skills = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT competency_cd FROM {SCHEMA}.tb_competency")
    comps = [r[0] for r in cur.fetchall()]

    data = []
    for skill in skills:
        for comp in random.sample(comps, 2):
            data.append((str(uuid.uuid4()), skill, comp, random.randint(20, 50)))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_skill_competency_map (mapping_id, skill_cd, competency_cd, contribution_weight) VALUES (%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_assessment(cur):
    """역량 평가"""
    print("\n[11] tb_assessment...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    data = []
    types = ['midterm', 'final', 'project', 'quiz']

    for sid in random.sample(students, int(len(students) * 0.5)):
        for t in random.sample(types, 2):
            data.append((str(uuid.uuid4()), sid, t, datetime.now() - timedelta(days=random.randint(0, 180))))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_assessment (assessment_id, student_id, assessment_type, assessment_dt) VALUES (%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")
    return [d[0] for d in data]


def generate_assessment_result(cur, assessment_ids):
    """평가 결과"""
    print("\n[12] tb_assessment_result...")

    cur.execute(f"SELECT competency_cd FROM {SCHEMA}.tb_competency")
    comps = [r[0] for r in cur.fetchall()]

    data = []
    for aid in assessment_ids:
        for comp in comps:
            raw = random.randint(50, 100)
            adj = raw + random.randint(-5, 10)
            acad = random.randint(0, 20)
            extra = random.randint(0, 10)
            final = min(100, adj + acad + extra)
            data.append((str(uuid.uuid4()), aid, comp, raw, adj, acad, extra, final))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_assessment_result (result_id, assessment_id, competency_cd, raw_score, adjusted_score, academic_contribution, extracurricular_boost, final_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_skill_gap_analysis(cur):
    """스킬 갭 분석"""
    print("\n[13] tb_skill_gap_analysis...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT role_cd FROM {SCHEMA}.tb_role")
    roles = [r[0] for r in cur.fetchall()]

    skill_sets = [
        ['python', 'sql'], ['java', 'spring'], ['react', 'typescript'],
        ['python', 'ml', 'data'], ['aws', 'docker', 'k8s']
    ]

    data = []
    for sid in random.sample(students, int(len(students) * 0.4)):
        role = random.choice(roles) if roles else 'ROLE001'
        gap_details = json.dumps({"python": 2, "java": 1, "sql": 3}, ensure_ascii=False)
        # PostgreSQL 배열은 리스트로 전달 (psycopg2가 자동 변환)
        priority_skills = random.choice(skill_sets)
        actions = json.dumps(["온라인 강좌 수강", "프로젝트 참여"], ensure_ascii=False)

        data.append((str(uuid.uuid4()), sid, role, datetime.now().date(), random.randint(20, 80), gap_details, priority_skills, actions))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_skill_gap_analysis (analysis_id, student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_advisor_assignment(cur):
    """지도교수 배정"""
    print("\n[14] tb_advisor_assignment...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    # professor_cd가 있는 사용자 (교수) 조회
    cur.execute(f"SELECT user_id FROM {SCHEMA}.tb_user WHERE professor_cd IS NOT NULL")
    advisors = [r[0] for r in cur.fetchall()]

    if not advisors:
        # 교수 사용자가 없으면 아무 사용자나 선택
        cur.execute(f"SELECT user_id FROM {SCHEMA}.tb_user LIMIT 10")
        advisors = [r[0] for r in cur.fetchall()]

    if not advisors:
        print("  [!] skip (no advisors)")
        return

    data = []
    for sid in students:
        adv = random.choice(advisors)
        data.append((str(uuid.uuid4()), adv, sid, 'academic', datetime.now() - timedelta(days=random.randint(30, 365)), None, 'active'))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_advisor_assignment (assignment_id, advisor_user_id, student_id, assignment_type, assigned_at, expires_at, status) VALUES (%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_coaching_goal(cur):
    """코칭 목표"""
    print("\n[15] tb_coaching_goal...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT role_cd FROM {SCHEMA}.tb_role LIMIT 5")
    roles = [r[0] for r in cur.fetchall()]

    goals = []
    goal_types = ['gpa_improvement', 'certification', 'internship', 'skill_development']

    for sid in random.sample(students, int(len(students) * 0.3)):
        gtype = random.choice(goal_types)
        role = random.choice(roles) if roles else None
        target = json.dumps({"gpa": 3.5, "skills": 3}, ensure_ascii=False)
        current = json.dumps({"gpa": 3.0, "skills": 1}, ensure_ascii=False)
        deadline = (datetime.now() + timedelta(days=random.randint(30, 180))).date()
        # priority는 integer (1=highest, 5=lowest)
        priority = random.randint(1, 5)

        goals.append((str(uuid.uuid4()), sid, gtype, f"{gtype} 목표", "상세 설명", role, target, current, deadline, priority))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_coaching_goal (goal_id, student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", goals)
    print(f"  [v] {len(goals)}")
    return [g[0] for g in goals]


def generate_coaching_plan(cur, goal_ids):
    """코칭 계획"""
    print("\n[16] tb_coaching_plan...")

    data = []
    for gid in goal_ids:
        milestones = json.dumps([{"week": 1, "task": "현황 분석"}, {"week": 2, "task": "실행"}], ensure_ascii=False)
        data.append((str(uuid.uuid4()), gid, 1, milestones, random.randint(5, 15), 1, 12, True, 'active', datetime.now()))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_coaching_plan (plan_id, goal_id, plan_version, milestones, weekly_hours_target, current_week, total_weeks, ai_generated, status, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")
    return [d[0] for d in data]


def generate_coaching_checkin(cur, plan_ids):
    """코칭 체크인"""
    print("\n[17] tb_coaching_checkin...")

    data = []
    for pid in plan_ids:
        for week in range(1, random.randint(2, 5)):
            tasks = json.dumps(["과제1 완료", "스터디 참석"], ensure_ascii=False)
            data.append((str(uuid.uuid4()), pid, week, datetime.now() - timedelta(days=7*(4-week)), tasks, random.randint(3, 10), "없음", "작은 성과", random.randint(3, 5), "잘 진행 중"))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_coaching_checkin (checkin_id, plan_id, week_number, checkin_date, completed_tasks, hours_spent, blockers, wins, mood_score, ai_feedback) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_risk_alert(cur):
    """위험 알림"""
    print("\n[18] tb_risk_alert...")

    cur.execute(f"""
        SELECT s.student_id, COALESCE(AVG(g.grade_point), 3.0) as avg_gpa
        FROM {SCHEMA}.tb_student s
        LEFT JOIN {SCHEMA}.tb_enrollment e ON s.student_id = e.student_id
        LEFT JOIN {SCHEMA}.tb_grade g ON e.enrollment_id = g.enrollment_id
        GROUP BY s.student_id
    """)
    results = cur.fetchall()

    data = []
    for sid, gpa in results:
        gpa_val = float(gpa) if gpa else 3.0
        if gpa_val < 2.5:
            sev = 'critical' if gpa_val < 2.0 else 'high'
            items = json.dumps(["최근 학기 성적 부진"], ensure_ascii=False)
            actions = json.dumps(["튜터링 신청", "상담 예약"], ensure_ascii=False)
            data.append((str(uuid.uuid4()), sid, 'academic_warning', sev, '학사경고 위험', f'현재 GPA {gpa_val:.2f}', items, actions, datetime.now(), 'active'))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_risk_alert (alert_id, student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_opportunity_application(cur):
    """기회 지원"""
    print("\n[19] tb_opportunity_application...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT opportunity_id FROM {SCHEMA}.tb_opportunity")
    opps = [r[0] for r in cur.fetchall()]

    if not opps:
        print("  [!] no opportunities - skip")
        return

    data = []
    statuses = ['applied', 'accepted', 'rejected', 'withdrawn']

    for sid in random.sample(students, int(len(students) * 0.3)):
        for opp in random.sample(opps, min(2, len(opps))):
            status = random.choice(statuses)
            applied = datetime.now() - timedelta(days=random.randint(0, 90))
            decision = applied + timedelta(days=14) if status in ['accepted', 'rejected'] else None
            data.append((str(uuid.uuid4()), sid, opp, applied, status, None, None, None, decision))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_opportunity_application (application_id, student_id, opportunity_id, applied_at, status, cover_letter, attachments, reviewer_notes, decision_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_recommendation(cur):
    """AI 추천"""
    print("\n[20] tb_recommendation_run, item, evidence...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT role_cd FROM {SCHEMA}.tb_role LIMIT 5")
    roles = [r[0] for r in cur.fetchall()]

    # version 컬럼에서 문자열 가져오기
    cur.execute(f"SELECT version FROM {SCHEMA}.tb_model_version LIMIT 1")
    model = cur.fetchone()
    model_ver = model[0] if model else 'v1.0.0'

    cur.execute(f"SELECT version FROM {SCHEMA}.tb_prompt_version LIMIT 1")
    prompt = cur.fetchone()
    prompt_ver = prompt[0] if prompt else 'v1.0.0'

    cur.execute(f"SELECT version FROM {SCHEMA}.tb_policy_version LIMIT 1")
    policy = cur.fetchone()
    policy_ver = policy[0] if policy else 'v1.0.0'

    runs = []
    items = []
    evidences = []

    for sid in random.sample(students, int(len(students) * 0.5)):
        run_id = str(uuid.uuid4())
        role = random.choice(roles) if roles else None
        input_snap = json.dumps({"gpa": 3.5, "skills": ["python"]}, ensure_ascii=False)
        retrieval = json.dumps({"courses": 5, "activities": 3}, ensure_ascii=False)
        output = json.dumps({"recommendations": []}, ensure_ascii=False)

        runs.append((run_id, sid, role, model_ver, prompt_ver, policy_ver, input_snap, retrieval, output, True))

        # items
        action_types = ['course', 'activity', 'certification', 'project']
        for rank in range(1, 4):
            item_id = str(uuid.uuid4())
            atype = random.choice(action_types)
            # rationale은 ARRAY 타입이므로 리스트로 전달
            rationale = [f"근거 {rank}", "역량 향상에 도움"]
            items.append((item_id, run_id, atype, f"추천 {atype} {rank}", "설명", rationale, random.randint(60, 95), random.randint(10, 50), rank, '2025-1'))

            # evidence - source_id, snippet_text, snippet_hash는 NOT NULL
            for er in range(1, 3):
                source_id = f"COMP{random.randint(100,999)}"  # 역량 코드 등
                snippet = f"역량 매칭 근거 {er}: 이 과목은 해당 역량 개발에 기여합니다."
                snippet_hash = hashlib.md5(snippet.encode()).hexdigest()[:16]
                evidences.append((str(uuid.uuid4()), item_id, 'competency_match', source_id, 'v1', snippet, snippet_hash, round(random.uniform(0.7, 0.95), 2), 'semantic_search'))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_recommendation_run (run_id, student_id, target_role_cd, model_version, prompt_version, policy_version, input_snapshot, retrieval_results, output_json, schema_valid) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", runs)
    print(f"  [v] runs: {len(runs)}")

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_recommendation_item (item_id, run_id, action_type, title, description, rationale, impact_score, effort_hours, priority, semester) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", items)
    print(f"  [v] items: {len(items)}")

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_recommendation_evidence (evidence_id, item_id, source_type, source_id, source_version, snippet_text, snippet_hash, retrieval_score, retrieval_method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", evidences)
    print(f"  [v] evidences: {len(evidences)}")


def generate_student_badge(cur):
    """학생 배지"""
    print("\n[21] tb_student_badge...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    cur.execute(f"SELECT badge_cd FROM {SCHEMA}.tb_badge")
    badges = [r[0] for r in cur.fetchall()]

    if not badges:
        print("  [!] no badges - skip")
        return

    data = []
    for sid in random.sample(students, int(len(students) * 0.4)):
        for b in random.sample(badges, min(2, len(badges))):
            items = json.dumps(["과제 완료", "프로젝트 참여"], ensure_ascii=False)
            data.append((str(uuid.uuid4()), sid, b, datetime.now() - timedelta(days=random.randint(0, 180)), items, 'verified', None, 1))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_student_badge (student_badge_id, student_id, badge_cd, earned_at, evidence_items, verification_status, share_url, display_order) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_worknet_diagnosis(cur):
    """워크넷 진단"""
    print("\n[22] tb_worknet_diagnosis...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    data = []
    types = ['interest', 'aptitude', 'values']

    for sid in random.sample(students, int(len(students) * 0.3)):
        dtype = random.choice(types)
        codes = json.dumps(["R", "I", "A"], ensure_ascii=False)
        summary = json.dumps({"top_type": "R", "score": 85}, ensure_ascii=False)
        detail = json.dumps({"categories": {"realistic": 85, "investigative": 70}}, ensure_ascii=False)

        data.append((str(uuid.uuid4()), sid, dtype, datetime.now().date() - timedelta(days=random.randint(0, 180)), codes, summary, detail))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_worknet_diagnosis (diagnosis_id, student_id, diagnosis_type, diagnosis_date, aptitude_codes, result_summary, detailed_result) VALUES (%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def generate_constraint_check(cur):
    """졸업요건 체크"""
    print("\n[23] tb_constraint_check...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [r[0] for r in cur.fetchall()]

    data = []
    check_types = ['graduation_credits', 'major_credits', 'liberal_credits', 'foreign_language']

    for sid in students:
        for ctype in check_types:
            input_data = json.dumps({"required": 130, "earned": random.randint(60, 140)}, ensure_ascii=False)
            passed = random.choice([True, True, True, False])
            violations = json.dumps([] if passed else ["부족: 10학점"], ensure_ascii=False)

            data.append((str(uuid.uuid4()), sid, ctype, datetime.now().date(), '2025-1', input_data, passed, violations))

    cur.executemany(f"INSERT INTO {SCHEMA}.tb_constraint_check (check_id, student_id, check_type, check_date, target_term_cd, input_data, result_passed, violations) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", data)
    print(f"  [v] {len(data)}")


def update_competency_scores(cur):
    """역량 점수 업데이트"""
    print("\n[24] tb_student_competency 점수 업데이트...")

    cur.execute(f"""
        UPDATE {SCHEMA}.tb_student_competency sc
        SET current_score = LEAST(100, GREATEST(0,
            (SELECT COALESCE(AVG(gs.gpa) * 20, 50)
             FROM {SCHEMA}.tb_grade_summary gs
             WHERE gs.student_id = sc.student_id)
            + RANDOM() * 20 - 10
        )),
        last_updated = NOW()
        WHERE EXISTS (
            SELECT 1 FROM {SCHEMA}.tb_grade_summary gs
            WHERE gs.student_id = sc.student_id
        )
    """)
    print(f"  [v] updated")


def print_summary(cur):
    """결과 요약"""
    print("\n" + "="*60)
    print("[SUMMARY]")
    print("="*60)

    cur.execute(f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = '{SCHEMA}' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]

    filled = empty = 0
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{t}")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            filled += 1
        else:
            empty += 1

    print(f"  Filled: {filled}, Empty: {empty}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', action='store_true')
    args = parser.parse_args()

    print("="*60)
    print("[*] IDINO Career Full Data Generator")
    print("="*60)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if args.clear:
            print("\n[!] Clearing...")
            clear_tables(cur)

        # Base data
        offering_map = generate_course_offerings(cur)
        generate_enrollments_and_grades(cur, offering_map)
        generate_participation(cur)
        generate_achievement(cur)
        generate_student_skill(cur)
        generate_portfolio(cur)
        conn.commit()

        # Extended data
        generate_prerequisite(conn, cur)
        generate_professor_course(conn, cur)
        generate_course_competency_map(cur)
        generate_skill_competency_map(cur)
        assessment_ids = generate_assessment(cur)
        generate_assessment_result(cur, assessment_ids)
        generate_skill_gap_analysis(cur)
        generate_advisor_assignment(cur)
        goal_ids = generate_coaching_goal(cur)
        plan_ids = generate_coaching_plan(cur, goal_ids)
        generate_coaching_checkin(cur, plan_ids)
        generate_risk_alert(cur)
        generate_opportunity_application(cur)
        generate_recommendation(cur)
        generate_student_badge(cur)
        generate_worknet_diagnosis(cur)
        generate_constraint_check(cur)
        update_competency_scores(cur)

        conn.commit()
        print_summary(cur)
        print("\n[OK] Done!")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
