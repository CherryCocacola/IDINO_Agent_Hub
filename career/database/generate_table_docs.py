#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career 테이블 정의서 생성 스크립트

PostgreSQL idino_career 스키마의 모든 테이블 메타데이터를 추출하여
Markdown 형식의 테이블 정의서를 생성합니다.

Usage:
    python generate_table_docs.py

Output:
    docs/TABLE_DEFINITIONS.md
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 패키지가 필요합니다.")
    print("설치: pip install psycopg2-binary")
    sys.exit(1)

# ============================================================
# 설정
# ============================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "2012"),
}

SCHEMA_NAME = os.getenv("DB_SCHEMA", "idino_career")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "TABLE_DEFINITIONS.md")

# 테이블 카테고리 분류
TABLE_CATEGORIES = {
    "Academic Base": [
        "tb_university", "tb_college", "tb_department", "tb_professor",
        "tb_course", "tb_course_offering", "tb_prerequisite",
        "tb_professor_course", "tb_curriculum_rule"
    ],
    "Student & Enrollment": [
        "tb_student", "tb_term", "tb_enrollment", "tb_grade",
        "tb_grade_summary", "tb_cumulative_summary", "tb_timetable"
    ],
    "Competency & Skill": [
        "tb_competency", "tb_skill", "tb_skill_competency_map",
        "tb_course_competency_map", "tb_assessment", "tb_assessment_result",
        "tb_student_competency", "tb_student_skill", "tb_skill_gap_analysis"
    ],
    "Activity & Achievement": [
        "tb_program", "tb_participation", "tb_achievement",
        "tb_portfolio", "tb_opportunity", "tb_opportunity_application"
    ],
    "Job & Alumni": [
        "tb_role", "tb_role_requirement", "tb_alumni_cohort",
        "tb_success_pattern", "tb_worknet_diagnosis", "tb_worknet_job"
    ],
    "Career": [
        "tb_student_career", "tb_career_history"
    ],
    "Coaching & Risk": [
        "tb_coaching_goal", "tb_coaching_session", "tb_coaching_action",
        "tb_risk_indicator", "tb_risk_alert", "tb_risk_intervention"
    ],
    "Badge & Simulation": [
        "tb_badge_definition", "tb_student_badge",
        "tb_simulation_scenario", "tb_simulation_result"
    ],
    "Advisor": [
        "tb_advisor", "tb_advisor_student", "tb_advisor_intervention"
    ],
    "Authentication": [
        "tb_user", "tb_auth_session", "tb_auth_otp",
        "tb_auth_backup_code", "tb_login_history", "tb_user_device"
    ],
    "AI Ops": [
        "tb_recommendation_run", "tb_recommendation_item",
        "tb_recommendation_evidence", "tb_feedback_event",
        "tb_prompt_version", "tb_policy_version", "tb_model_version",
        "tb_eval_case", "tb_eval_result", "tb_ai_agent", "tb_ai_agent_config"
    ],
}


# ============================================================
# SQL 쿼리
# ============================================================
SQL_GET_TABLES = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = %s
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
"""

SQL_GET_TABLE_COMMENT = """
SELECT obj_description(
    (SELECT oid FROM pg_class WHERE relname = %s AND relnamespace =
        (SELECT oid FROM pg_namespace WHERE nspname = %s)),
    'pg_class'
) as table_comment;
"""

SQL_GET_COLUMNS = """
SELECT
    c.ordinal_position,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.numeric_precision,
    c.numeric_scale,
    c.is_nullable,
    c.column_default,
    c.udt_name,
    pgd.description as column_comment
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st
    ON st.schemaname = c.table_schema AND st.relname = c.table_name
LEFT JOIN pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema = %s AND c.table_name = %s
ORDER BY c.ordinal_position;
"""

SQL_GET_CONSTRAINTS = """
SELECT
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
    AND tc.table_schema = ccu.table_schema
WHERE tc.table_schema = %s AND tc.table_name = %s
ORDER BY tc.constraint_type, tc.constraint_name;
"""

SQL_GET_INDEXES = """
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = %s AND tablename = %s
ORDER BY indexname;
"""


# ============================================================
# 유틸리티 함수
# ============================================================
def format_data_type(row: dict) -> str:
    """데이터 타입을 보기 좋게 포맷팅"""
    data_type = row["data_type"]
    udt_name = row.get("udt_name", "")

    # 배열 타입
    if data_type == "ARRAY":
        return f"{udt_name.lstrip('_')}[]"

    # character varying
    if data_type == "character varying":
        max_len = row.get("character_maximum_length")
        return f"varchar({max_len})" if max_len else "varchar"

    # character
    if data_type == "character":
        max_len = row.get("character_maximum_length")
        return f"char({max_len})" if max_len else "char"

    # numeric/decimal
    if data_type in ("numeric", "decimal"):
        precision = row.get("numeric_precision")
        scale = row.get("numeric_scale")
        if precision and scale:
            return f"decimal({precision},{scale})"
        elif precision:
            return f"decimal({precision})"
        return "decimal"

    # timestamp
    if "timestamp" in data_type:
        return "timestamp"

    # uuid
    if udt_name == "uuid":
        return "uuid"

    # jsonb
    if udt_name == "jsonb":
        return "jsonb"

    # vector (pgvector)
    if "vector" in udt_name.lower():
        return udt_name

    return data_type


def format_default(value: Optional[str]) -> str:
    """기본값을 보기 좋게 포맷팅"""
    if value is None:
        return "-"

    # 긴 기본값 축약
    if len(value) > 40:
        if "uuid_generate" in value:
            return "uuid_generate_v4()"
        if "CURRENT_TIMESTAMP" in value.upper():
            return "CURRENT_TIMESTAMP"
        if "nextval" in value:
            return "nextval(...)"
        return value[:37] + "..."

    return value


def escape_markdown(text: str) -> str:
    """Markdown 특수문자 이스케이프"""
    if not text:
        return ""
    # 파이프 문자는 테이블 구분자이므로 이스케이프 필요
    return text.replace("|", "\\|").replace("\n", " ")


def get_category(table_name: str) -> str:
    """테이블의 카테고리 반환"""
    for category, tables in TABLE_CATEGORIES.items():
        if table_name in tables:
            return category
    return "Other"


# ============================================================
# 메인 로직
# ============================================================
class TableDocGenerator:
    def __init__(self):
        self.conn = None
        self.tables: List[str] = []
        self.table_data: Dict[str, dict] = {}

    def connect(self):
        """데이터베이스 연결"""
        print(f"Connecting to PostgreSQL ({DB_CONFIG['host']}:{DB_CONFIG['port']})...")
        self.conn = psycopg2.connect(**DB_CONFIG)
        print("Connected successfully.")

    def disconnect(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
            print("Disconnected.")

    def fetch_tables(self):
        """테이블 목록 조회"""
        print(f"\nFetching tables from schema '{SCHEMA_NAME}'...")
        with self.conn.cursor() as cur:
            cur.execute(SQL_GET_TABLES, (SCHEMA_NAME,))
            self.tables = [row[0] for row in cur.fetchall()]
        print(f"Found {len(self.tables)} tables.")

    def fetch_table_details(self, table_name: str) -> dict:
        """단일 테이블의 상세 정보 조회"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 테이블 코멘트
            cur.execute(SQL_GET_TABLE_COMMENT, (table_name, SCHEMA_NAME))
            result = cur.fetchone()
            table_comment = result["table_comment"] if result else None

            # 컬럼 정보
            cur.execute(SQL_GET_COLUMNS, (SCHEMA_NAME, table_name))
            columns = cur.fetchall()

            # 제약조건
            cur.execute(SQL_GET_CONSTRAINTS, (SCHEMA_NAME, table_name))
            constraints = cur.fetchall()

            # 인덱스
            cur.execute(SQL_GET_INDEXES, (SCHEMA_NAME, table_name))
            indexes = cur.fetchall()

        return {
            "table_name": table_name,
            "table_comment": table_comment,
            "columns": columns,
            "constraints": constraints,
            "indexes": indexes,
        }

    def fetch_all_details(self):
        """모든 테이블 상세 정보 조회"""
        print("\nFetching table details...")
        for i, table_name in enumerate(self.tables, 1):
            print(f"  [{i}/{len(self.tables)}] {table_name}")
            self.table_data[table_name] = self.fetch_table_details(table_name)

    def generate_markdown(self) -> str:
        """Markdown 문서 생성"""
        lines = []

        # 헤더
        lines.append("# IDINO Career 테이블 정의서")
        lines.append("")
        lines.append(f"> 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"> 스키마: `{SCHEMA_NAME}`")
        lines.append(f"> 테이블 수: {len(self.tables)}개")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 목차
        lines.append("## 목차")
        lines.append("")

        # 카테고리별로 테이블 그룹화
        categorized: Dict[str, List[str]] = defaultdict(list)
        for table_name in self.tables:
            category = get_category(table_name)
            categorized[category].append(table_name)

        # 카테고리 순서 정의
        category_order = list(TABLE_CATEGORIES.keys()) + ["Other"]

        for category in category_order:
            if category in categorized and categorized[category]:
                lines.append(f"### {category}")
                for table_name in sorted(categorized[category]):
                    lines.append(f"- [{table_name}](#{table_name.replace('_', '-')})")
                lines.append("")

        lines.append("---")
        lines.append("")

        # 각 테이블 상세
        for category in category_order:
            if category not in categorized or not categorized[category]:
                continue

            lines.append(f"# {category}")
            lines.append("")

            for table_name in sorted(categorized[category]):
                lines.extend(self._generate_table_section(table_name))
                lines.append("")

        return "\n".join(lines)

    def _generate_table_section(self, table_name: str) -> List[str]:
        """단일 테이블 섹션 생성"""
        data = self.table_data[table_name]
        lines = []

        # 테이블 헤더
        lines.append(f"## {table_name}")
        lines.append("")

        # 테이블 설명
        if data["table_comment"]:
            lines.append(f"**설명**: {data['table_comment']}")
            lines.append("")

        # 컬럼 테이블
        lines.append("### 컬럼 정의")
        lines.append("")
        lines.append("| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |")
        lines.append("|--:|--------|-------------|:----:|--------|------|")

        for col in data["columns"]:
            pos = col["ordinal_position"]
            name = col["column_name"]
            dtype = format_data_type(col)
            nullable = "O" if col["is_nullable"] == "YES" else "X"
            default = format_default(col["column_default"])
            comment = escape_markdown(col["column_comment"] or "")

            lines.append(f"| {pos} | `{name}` | {dtype} | {nullable} | {default} | {comment} |")

        lines.append("")

        # 제약조건
        if data["constraints"]:
            lines.append("### 제약조건")
            lines.append("")

            # PK
            pk_cols = [c["column_name"] for c in data["constraints"] if c["constraint_type"] == "PRIMARY KEY"]
            if pk_cols:
                lines.append(f"- **PK**: `{', '.join(pk_cols)}`")

            # FK
            fk_map: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
            for c in data["constraints"]:
                if c["constraint_type"] == "FOREIGN KEY":
                    fk_map[c["constraint_name"]].append(
                        (c["column_name"], c["foreign_table"], c["foreign_column"])
                    )

            for fk_name, refs in fk_map.items():
                for col, ref_table, ref_col in refs:
                    lines.append(f"- **FK**: `{col}` → `{ref_table}({ref_col})`")

            # UNIQUE
            unique_map: Dict[str, List[str]] = defaultdict(list)
            for c in data["constraints"]:
                if c["constraint_type"] == "UNIQUE":
                    unique_map[c["constraint_name"]].append(c["column_name"])

            for uk_name, cols in unique_map.items():
                lines.append(f"- **UNIQUE**: `{', '.join(cols)}`")

            lines.append("")

        # 인덱스
        if data["indexes"]:
            # PK 인덱스 제외
            non_pk_indexes = [idx for idx in data["indexes"]
                           if not idx["indexname"].endswith("_pkey")]

            if non_pk_indexes:
                lines.append("### 인덱스")
                lines.append("")
                for idx in non_pk_indexes:
                    lines.append(f"- `{idx['indexname']}`")
                lines.append("")

        lines.append("---")

        return lines

    def save(self, content: str):
        """파일 저장"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\nSaved to: {OUTPUT_FILE}")
        print(f"File size: {os.path.getsize(OUTPUT_FILE):,} bytes")

    def run(self):
        """메인 실행"""
        try:
            self.connect()
            self.fetch_tables()
            self.fetch_all_details()

            print("\nGenerating Markdown...")
            content = self.generate_markdown()

            self.save(content)
            print("\nDone!")

        except Exception as e:
            print(f"\nError: {e}")
            raise
        finally:
            self.disconnect()


if __name__ == "__main__":
    generator = TableDocGenerator()
    generator.run()
