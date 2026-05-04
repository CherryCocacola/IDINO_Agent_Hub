#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career 테스트 데이터 생성 스크립트

생성 대상 테이블:
1. tb_course_offering - 과목 개설 정보
2. tb_enrollment - 수강신청
3. tb_grade - 성적
4. tb_grade_summary - 학기별 성적 요약
5. tb_participation - 비교과활동 참여
6. tb_achievement - 자격증/수상 내역
7. tb_student_skill - 학생 스킬
8. tb_portfolio - 포트폴리오

실행: python generate_test_data.py [--clear]
  --clear: 기존 데이터 삭제 후 재생성
"""

import psycopg2
import random
import uuid
from datetime import datetime, timedelta
import argparse

# DB 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': '2012'
}
SCHEMA = 'idino_career'

# 성적 분포 (현실적인 분포)
GRADE_DISTRIBUTION = [
    ('A+', 4.5, 0.10),  # 10%
    ('A0', 4.0, 0.15),  # 15%
    ('B+', 3.5, 0.20),  # 20%
    ('B0', 3.0, 0.25),  # 25%
    ('C+', 2.5, 0.15),  # 15%
    ('C0', 2.0, 0.10),  # 10%
    ('D+', 1.5, 0.03),  # 3%
    ('D0', 1.0, 0.02),  # 2%
]

# 자격증 목록
CERTIFICATIONS = [
    ('정보처리기사', '한국산업인력공단', 'certification'),
    ('정보처리산업기사', '한국산업인력공단', 'certification'),
    ('SQLD', '한국데이터산업진흥원', 'certification'),
    ('SQLP', '한국데이터산업진흥원', 'certification'),
    ('ADsP', '한국데이터산업진흥원', 'certification'),
    ('빅데이터분석기사', '한국데이터산업진흥원', 'certification'),
    ('리눅스마스터 2급', '한국정보통신진흥협회', 'certification'),
    ('리눅스마스터 1급', '한국정보통신진흥협회', 'certification'),
    ('네트워크관리사 2급', '한국정보통신자격협회', 'certification'),
    ('AWS Solutions Architect', 'Amazon', 'certification'),
    ('AWS Developer Associate', 'Amazon', 'certification'),
    ('TOEIC 800+', 'ETS', 'language'),
    ('TOEIC 900+', 'ETS', 'language'),
    ('OPIC IH', 'ACTFL', 'language'),
    ('JLPT N2', '일본국제교류기금', 'language'),
    ('교내 해커톤 대상', '대학교', 'award'),
    ('교내 해커톤 최우수상', '대학교', 'award'),
    ('교내 프로그래밍 경시대회 입상', '대학교', 'award'),
    ('SW마에스트로 수료', '과학기술정보통신부', 'program'),
    ('TOPCIT 3수준', '한국정보통신진흥협회', 'certification'),
]

# 스킬 레벨 분포
SKILL_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']


def get_connection():
    """DB 연결"""
    return psycopg2.connect(**DB_CONFIG)


def get_random_grade():
    """가중치 기반 랜덤 성적 생성"""
    rand = random.random()
    cumulative = 0
    for grade, point, prob in GRADE_DISTRIBUTION:
        cumulative += prob
        if rand <= cumulative:
            return grade, point
    return 'C0', 2.0


def clear_tables(cur):
    """기존 데이터 삭제 (역순으로)"""
    tables = [
        'tb_grade_summary',
        'tb_grade',
        'tb_enrollment',
        'tb_course_offering',
        'tb_participation',
        'tb_achievement',
        'tb_student_skill',
        'tb_portfolio'
    ]
    for table in tables:
        cur.execute(f'DELETE FROM {SCHEMA}.{table}')
        print(f"  [v] {table} 삭제 완료")


def generate_course_offerings(cur):
    """과목 개설 정보 생성"""
    print("\n[1/7] tb_course_offering 생성 중...")

    # 기존 데이터 조회
    cur.execute(f"SELECT course_cd FROM {SCHEMA}.tb_course")
    courses = [row[0] for row in cur.fetchall()]

    cur.execute(f"SELECT term_cd FROM {SCHEMA}.tb_term")
    terms = [row[0] for row in cur.fetchall()]

    cur.execute(f"SELECT professor_cd FROM {SCHEMA}.tb_professor")
    professors = [row[0] for row in cur.fetchall()]

    offerings = []
    offering_map = {}  # (course_cd, term_cd) -> offering_id

    for term in terms:
        # 각 학기마다 랜덤하게 과목 선택 (70% 개설)
        term_courses = random.sample(courses, int(len(courses) * 0.7))
        for course_cd in term_courses:
            offering_id = str(uuid.uuid4())
            professor_cd = random.choice(professors)
            section = random.choice(['01', '02'])
            capacity = random.choice([30, 40, 50, 60])

            offerings.append((
                offering_id, course_cd, term, professor_cd, section,
                capacity, 0, '월수 10:00-11:30', f'{random.randint(1,5)}층 {random.randint(101,110)}호'
            ))
            offering_map[(course_cd, term)] = offering_id

    # 삽입
    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_course_offering
        (offering_id, course_cd, term_cd, professor_cd, section, capacity, enrolled_count, schedule, classroom)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, offerings)

    print(f"  [v] {len(offerings)}건 생성 완료")
    return offering_map


def generate_enrollments_and_grades(cur, offering_map):
    """수강신청 및 성적 생성"""
    print("\n[2/7] tb_enrollment & tb_grade 생성 중...")

    # 학생 목록 조회
    cur.execute(f"SELECT student_id, admission_year FROM {SCHEMA}.tb_student")
    students = cur.fetchall()

    # 학기 목록
    cur.execute(f"SELECT term_cd FROM {SCHEMA}.tb_term ORDER BY term_cd")
    terms = [row[0] for row in cur.fetchall()]

    # 과목 학점 정보
    cur.execute(f"SELECT course_cd, credits FROM {SCHEMA}.tb_course")
    course_credits = dict(cur.fetchall())

    enrollments = []
    grades = []
    grade_summaries = []

    for student_id, admission_year in students:
        student_grades_by_term = {}

        # 학생의 입학 연도부터 현재까지 학기 수강
        for term in terms:
            term_year = int(term.split('-')[0])
            term_sem = int(term.split('-')[1])

            # 입학 전 학기는 스킵
            if term_year < admission_year:
                continue
            # 현재 학기(2025-1)는 진행중으로 처리
            is_current = (term == '2025-1')

            # 학기당 5-7개 과목 수강
            num_courses = random.randint(5, 7)
            term_offerings = [(k, v) for k, v in offering_map.items() if k[1] == term]

            if len(term_offerings) < num_courses:
                continue

            selected = random.sample(term_offerings, min(num_courses, len(term_offerings)))

            term_credits = 0
            term_grade_points = 0

            for (course_cd, t), offering_id in selected:
                enrollment_id = str(uuid.uuid4())
                status = 'enrolled' if is_current else 'completed'

                enrollments.append((
                    enrollment_id, student_id, offering_id, status
                ))

                # 현재 학기가 아닌 경우에만 성적 부여
                if not is_current:
                    grade, grade_point = get_random_grade()
                    is_pass = grade_point >= 1.0

                    grades.append((
                        str(uuid.uuid4()), enrollment_id, grade, grade_point, is_pass
                    ))

                    credits = course_credits.get(course_cd, 3)
                    term_credits += credits
                    term_grade_points += grade_point * credits

            # 학기 성적 요약 (현재 학기 제외)
            if not is_current and term_credits > 0:
                gpa = round(term_grade_points / term_credits, 2)
                grade_summaries.append((
                    str(uuid.uuid4()), student_id, term,
                    term_credits, term_credits, term_grade_points, gpa, gpa
                ))

    # 삽입
    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_enrollment
        (enrollment_id, student_id, offering_id, enrollment_status)
        VALUES (%s, %s, %s, %s)
    """, enrollments)
    print(f"  [v] tb_enrollment: {len(enrollments)}건")

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_grade
        (grade_id, enrollment_id, grade, grade_point, is_pass)
        VALUES (%s, %s, %s, %s, %s)
    """, grades)
    print(f"  [v] tb_grade: {len(grades)}건")

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_grade_summary
        (summary_id, student_id, term_cd, credits_attempted, credits_earned, grade_points, gpa, major_gpa)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, grade_summaries)
    print(f"  [v] tb_grade_summary: {len(grade_summaries)}건")


def generate_participations(cur):
    """비교과활동 참여 생성"""
    print("\n[3/7] tb_participation 생성 중...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [row[0] for row in cur.fetchall()]

    cur.execute(f"SELECT program_cd, program_nm FROM {SCHEMA}.tb_program")
    programs = cur.fetchall()

    participations = []
    roles = ['참가자', '팀원', '팀장', '멘티', '발표자']
    statuses = ['completed', 'completed', 'completed', 'in_progress', 'registered']

    for student_id in students:
        # 학생당 1-4개 활동 참여
        num_activities = random.randint(1, 4)
        selected_programs = random.sample(programs, min(num_activities, len(programs)))

        for program_cd, program_nm in selected_programs:
            status = random.choice(statuses)
            role = random.choice(roles)

            # 시작일은 최근 2년 내 랜덤
            start_date = datetime.now() - timedelta(days=random.randint(30, 730))
            # 완료된 경우 종료일 설정
            end_date = start_date + timedelta(days=random.randint(30, 180)) if status == 'completed' else None

            participations.append((
                str(uuid.uuid4()), student_id, program_cd, status, role,
                start_date, end_date
            ))

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_participation
        (participation_id, student_id, program_cd, participation_status, role, started_at, completed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, participations)
    print(f"  [v] {len(participations)}건 생성 완료")


def generate_achievements(cur):
    """자격증/수상 내역 생성"""
    print("\n[4/7] tb_achievement 생성 중...")

    cur.execute(f"SELECT student_id, admission_year FROM {SCHEMA}.tb_student")
    students = cur.fetchall()

    achievements = []

    for student_id, admission_year in students:
        # 학생당 0-4개 자격증/수상
        num_achievements = random.choices([0, 1, 2, 3, 4], weights=[0.2, 0.3, 0.25, 0.15, 0.1])[0]

        if num_achievements == 0:
            continue

        selected_certs = random.sample(CERTIFICATIONS, min(num_achievements, len(CERTIFICATIONS)))

        for cert_name, issuer, cert_type in selected_certs:
            # 취득일은 입학 후 ~ 현재 사이
            days_since_admission = (datetime.now().year - admission_year) * 365
            if days_since_admission > 0:
                acquired_date = datetime.now() - timedelta(days=random.randint(0, min(days_since_admission, 1095)))
            else:
                acquired_date = datetime.now() - timedelta(days=random.randint(0, 365))

            # 점수 (해당되는 경우)
            score = None
            if 'TOEIC' in cert_name:
                score = str(random.randint(700, 990))
            elif 'TOPCIT' in cert_name:
                score = str(random.randint(300, 600))

            achievements.append((
                str(uuid.uuid4()), student_id, cert_type, cert_name, issuer,
                acquired_date.date(), None, score, True
            ))

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_achievement
        (achievement_id, student_id, achievement_type, achievement_nm, issuing_organization,
         acquired_date, expiry_date, score, verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, achievements)
    print(f"  [v] {len(achievements)}건 생성 완료")


def generate_student_skills(cur):
    """학생 스킬 생성"""
    print("\n[5/7] tb_student_skill 생성 중...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [row[0] for row in cur.fetchall()]

    cur.execute(f"SELECT skill_cd, skill_nm FROM {SCHEMA}.tb_skill")
    skills = cur.fetchall()

    student_skills = []
    trends = ['improving', 'stable', 'declining']

    for student_id in students:
        # 학생당 3-8개 스킬 보유
        num_skills = random.randint(3, 8)
        selected_skills = random.sample(skills, min(num_skills, len(skills)))

        for skill_cd, skill_nm in selected_skills:
            current_level = random.randint(1, 5)  # 1-5 레벨
            target_level = min(5, current_level + random.randint(0, 2))
            evidence_count = random.randint(0, 10)
            trend = random.choices(trends, weights=[0.5, 0.35, 0.15])[0]
            last_verified = datetime.now() - timedelta(days=random.randint(0, 180))

            student_skills.append((
                str(uuid.uuid4()), student_id, skill_cd,
                current_level, target_level, evidence_count,
                last_verified.date(), 'auto', trend
            ))

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_student_skill
        (student_skill_id, student_id, skill_cd, current_level, target_level,
         evidence_count, last_verified_date, verification_source, trend)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, student_skills)
    print(f"  [v] {len(student_skills)}건 생성 완료")


def generate_portfolios(cur):
    """포트폴리오 생성"""
    print("\n[6/7] tb_portfolio 생성 중...")

    cur.execute(f"SELECT student_id FROM {SCHEMA}.tb_student")
    students = [row[0] for row in cur.fetchall()]

    portfolios = []
    artifact_types = ['github', 'blog', 'project', 'paper', 'video']

    # 상위 30% 학생만 포트폴리오 보유
    portfolio_students = random.sample(students, int(len(students) * 0.3))

    for student_id in portfolio_students:
        # 학생당 1-3개 포트폴리오
        num_items = random.randint(1, 3)

        for i in range(num_items):
            artifact_type = random.choice(artifact_types)
            is_primary = (i == 0)  # 첫 번째가 대표 포트폴리오

            if artifact_type == 'github':
                title = f"GitHub 프로필"
                url = f"https://github.com/student{student_id[-4:]}"
                desc = "개인 프로젝트 및 오픈소스 기여 내역"
            elif artifact_type == 'blog':
                title = f"기술 블로그"
                url = f"https://velog.io/@student{student_id[-4:]}"
                desc = "개발 학습 기록 및 프로젝트 회고"
            elif artifact_type == 'project':
                titles = ['웹 쇼핑몰 프로젝트', 'AI 챗봇 개발', '모바일 앱 개발',
                         '데이터 분석 프로젝트', 'IoT 시스템 구축']
                title = random.choice(titles)
                url = f"https://github.com/student{student_id[-4:]}/project-{i+1}"
                desc = f"{title} 상세 설명 및 기술 스택"
            else:
                title = f"포트폴리오 {i+1}"
                url = f"https://notion.so/student{student_id[-4:]}/portfolio-{i+1}"
                desc = "프로젝트 결과물"

            portfolios.append((
                str(uuid.uuid4()), student_id, artifact_type, title, url, desc, is_primary
            ))

    cur.executemany(f"""
        INSERT INTO {SCHEMA}.tb_portfolio
        (portfolio_id, student_id, artifact_type, title, url, description, is_primary)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, portfolios)
    print(f"  [v] {len(portfolios)}건 생성 완료")


def update_student_competency_scores(cur):
    """학생 역량 점수 업데이트 (성적/활동 기반)"""
    print("\n[7/7] tb_student_competency 점수 업데이트 중...")

    # 기존 데이터가 있으면 GPA 기반으로 점수 조정
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
    print(f"  [v] 역량 점수 업데이트 완료")


def print_summary(cur):
    """결과 요약 출력"""
    print("\n" + "="*50)
    print("[SUMMARY] 데이터 생성 결과 요약")
    print("="*50)

    tables = [
        ('tb_course_offering', '과목 개설'),
        ('tb_enrollment', '수강신청'),
        ('tb_grade', '성적'),
        ('tb_grade_summary', '학기별 성적'),
        ('tb_participation', '비교과활동'),
        ('tb_achievement', '자격증/수상'),
        ('tb_student_skill', '학생 스킬'),
        ('tb_portfolio', '포트폴리오'),
    ]

    for table, desc in tables:
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
        count = cur.fetchone()[0]
        print(f"  {desc:15} ({table}): {count:,}건")


def main():
    parser = argparse.ArgumentParser(description='IDINO Career 테스트 데이터 생성')
    parser.add_argument('--clear', action='store_true', help='기존 데이터 삭제 후 재생성')
    args = parser.parse_args()

    print("="*50)
    print("[*] IDINO Career 테스트 데이터 생성기")
    print("="*50)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if args.clear:
            print("\n[!] 기존 데이터 삭제 중...")
            clear_tables(cur)

        # 데이터 생성
        offering_map = generate_course_offerings(cur)
        generate_enrollments_and_grades(cur, offering_map)
        generate_participations(cur)
        generate_achievements(cur)
        generate_student_skills(cur)
        generate_portfolios(cur)
        update_student_competency_scores(cur)

        # 커밋
        conn.commit()

        # 결과 요약
        print_summary(cur)

        print("\n[OK] 데이터 생성 완료!")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 오류 발생: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
