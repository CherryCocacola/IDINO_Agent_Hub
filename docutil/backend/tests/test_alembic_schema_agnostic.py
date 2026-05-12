"""트랙 #70 — alembic 마이그레이션 schema-agnostic 강제 검증.

ADR-18 (trace #66/#67) 의 핵심 원칙:

    alembic 마이그레이션 파일은 PostgreSQL schema 를 **알지 못해야** 한다.
    schema 격리는 ``alembic/env.py`` 의 5중 안전 (CREATE SCHEMA IF NOT EXISTS
    + SET LOCAL search_path) 에 일임한다.

본 테스트는 ``versions/*.py`` 안에서 다음 위반 패턴을 차단한다:

1. ``schema='...'`` 인자 (op.create_table / op.create_index / Column FK 등)
2. ``CREATE/DROP/ALTER TABLE/INDEX schema.identifier`` 형태의 raw SQL
   (op.execute() 안의 schema-qualified DDL)

위반 발생 시 마이그레이션이 DB_SCHEMA 환경 변수와 무관하게 hard-coded
schema 로 향하는 사고가 재발할 수 있다 (트랙 #63 — public 잔존 + 트랙 #66
보고서 §3.2 시나리오 C).

참조:
- ``docs/DB_MIGRATION.md`` v1.1 §10.2 (schema 격리 원칙)
- ``user_mig/TECHSPEC.md`` §20 ADR-18 (alembic schema-agnostic)
- 트랙 #66 분석 + 트랙 #67 강제 (db_schema validator)
- 트랙 #70 (CI 게이트 도입)

검증 대상: ``docutil/backend/alembic/versions/*.py`` (8 파일, 2026-05-12 기준)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 대상 파일 탐색
# ---------------------------------------------------------------------------

# tests/ 에서 backend/alembic/versions 까지 ../ 한 단계
_VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _migration_files() -> list[Path]:
    """``versions/*.py`` 파일 목록 (이름순)."""
    if not _VERSIONS_DIR.is_dir():
        return []
    return sorted(p for p in _VERSIONS_DIR.glob("*.py") if p.name != "__init__.py")


# ---------------------------------------------------------------------------
# 위반 패턴 regex
# ---------------------------------------------------------------------------

# Pattern A: schema='...' / schema="..." kwarg
#   매칭: schema='AIAgentManagement', schema="public", schema= 'x'
#   허용: schema_translate_map (SQLAlchemy 표준, 다른 의미) — \b 가 _ 를 word 로 취급하므로
#         schema_translate_map 의 `schema_` 다음 `t` 는 `\s*=\s*['\"]` 와 mismatch (안전)
#   허용: idx_schema_x 같은 식별자 (= 가 따라오지 않음, 자연 mismatch)
_SCHEMA_ARG_RE = re.compile(r"\bschema\s*=\s*['\"]")

# Pattern B: schema-qualified DDL in raw SQL
#   매칭: CREATE TABLE foo.bar, DROP INDEX schema.idx_x,
#         ALTER TABLE "public"."tb_y"
#   허용: SET LOCAL search_path, BEGIN, SELECT col.attr (DML 은 검사 안함)
#   설계 결정: DDL 키워드 (CREATE/DROP/ALTER) + 객체 타입 (TABLE/INDEX/...) +
#             선택적 IF (NOT) EXISTS + 따옴표 선택 식별자 + dot
_QUALIFIED_DDL_RE = re.compile(
    r"\b(CREATE|DROP|ALTER)\s+"
    r"(TABLE|INDEX|SEQUENCE|VIEW|MATERIALIZED\s+VIEW|TYPE|FUNCTION)\s+"
    r"(IF\s+(NOT\s+)?EXISTS\s+)?"
    r"[\"']?[a-zA-Z_][a-zA-Z0-9_]*[\"']?\s*\.",
    re.IGNORECASE,
)


def _strip_python_strings_and_comments(source: str) -> tuple[str, str]:
    """raw 코드를 (code_only, raw_strings_only) 로 분리.

    - 주석(`#`) 제거 → code 검사에 미포함
    - 그러나 raw SQL 검사는 string literal 내부를 봐야 하므로 raw_strings_only
      에는 string literal 만 모음 (실용적 휴리스틱: 큰 따옴표 + 작은 따옴표 +
      삼중 따옴표 블록).

    완벽한 Python parser 가 아닌 휴리스틱이지만, alembic 마이그레이션의
    op.execute() 패턴에는 충분히 정확하다.
    """
    code_lines: list[str] = []
    string_buf: list[str] = []
    in_triple_single = False
    in_triple_double = False

    for line in source.splitlines():
        # 1) 삼중 따옴표 블록 안이면 string_buf 에만 누적
        stripped = line.lstrip()
        if in_triple_single:
            string_buf.append(line)
            if "'''" in line:
                in_triple_single = False
            continue
        if in_triple_double:
            string_buf.append(line)
            if '"""' in line:
                in_triple_double = False
            continue

        # 2) 삼중 따옴표 시작 검출 (한 줄 내 close 없는 경우만)
        if stripped.startswith("'''") and stripped.count("'''") == 1:
            in_triple_single = True
            string_buf.append(line)
            continue
        if stripped.startswith('"""') and stripped.count('"""') == 1:
            in_triple_double = True
            string_buf.append(line)
            continue

        # 3) 단일 라인 주석 제거 (string 안의 # 는 단순화로 제거 안함)
        # 휴리스틱: 라인 첫 nonws 가 # 이면 전체 제거
        if stripped.startswith("#"):
            continue

        code_lines.append(line)
        # 라인 내 string literal 도 string_buf 에 포함 (raw SQL 검사용)
        string_buf.append(line)

    return ("\n".join(code_lines), "\n".join(string_buf))


# ---------------------------------------------------------------------------
# 사전 검증: versions 디렉토리 존재
# ---------------------------------------------------------------------------


def test_versions_directory_exists():
    """``alembic/versions`` 디렉토리가 존재하고 마이그레이션이 1개 이상 있다."""
    assert _VERSIONS_DIR.is_dir(), f"alembic versions 디렉토리 부재: {_VERSIONS_DIR}"
    files = _migration_files()
    assert len(files) >= 1, f"alembic 마이그레이션 파일이 없음: {_VERSIONS_DIR}"


# ---------------------------------------------------------------------------
# 게이트 1: schema= kwarg 차단
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "migration_path",
    _migration_files(),
    ids=lambda p: p.name,
)
def test_migration_has_no_schema_kwarg(migration_path: Path):
    """``op.create_table('x', schema='...')`` 류 schema kwarg 차단.

    ADR-18: alembic 작업은 unqualified 식별자만 사용하고 schema 격리는
    env.py 의 search_path 강제에 일임한다. schema= 인자가 들어가면
    DB_SCHEMA 환경 변수와 무관하게 hard-coded schema 로 향한다 (트랙 #63 사고).
    """
    source = migration_path.read_text(encoding="utf-8")
    code_only, _ = _strip_python_strings_and_comments(source)

    violations: list[tuple[int, str]] = []
    for idx, line in enumerate(code_only.splitlines(), start=1):
        if _SCHEMA_ARG_RE.search(line):
            violations.append((idx, line.rstrip()))

    if violations:
        details = "\n".join(f"  line {ln}: {text}" for ln, text in violations)
        pytest.fail(
            f"{migration_path.name}: schema= kwarg 발견 (ADR-18 위반)\n"
            f"{details}\n"
            "→ env.py 의 search_path 강제에 일임. "
            "op.create_table('tb_X') / op.create_index('idx_X', 'tb_X', ...) "
            "만 사용하세요."
        )


# ---------------------------------------------------------------------------
# 게이트 2: schema-qualified DDL (raw SQL) 차단
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "migration_path",
    _migration_files(),
    ids=lambda p: p.name,
)
def test_migration_has_no_qualified_ddl(migration_path: Path):
    """``op.execute('CREATE INDEX schema.idx_X ...')`` 류 qualified DDL 차단.

    ADR-18: raw SQL 안에서도 schema 한정자를 사용하지 않는다. search_path
    가 모든 DDL/DML 의 schema 를 결정하도록 한다.

    검출 패턴: ``(CREATE|DROP|ALTER) (TABLE|INDEX|...) [IF EXISTS] ident.``
    """
    source = migration_path.read_text(encoding="utf-8")
    _, string_only = _strip_python_strings_and_comments(source)

    violations: list[tuple[int, str]] = []
    for idx, line in enumerate(string_only.splitlines(), start=1):
        if _QUALIFIED_DDL_RE.search(line):
            violations.append((idx, line.rstrip()))

    if violations:
        details = "\n".join(f"  line {ln}: {text}" for ln, text in violations)
        pytest.fail(
            f"{migration_path.name}: schema-qualified DDL 발견 (ADR-18 위반)\n"
            f"{details}\n"
            "→ unqualified 만 사용. 예: "
            "'DROP INDEX idx_X' (O), 'DROP INDEX public.idx_X' (X). "
            "schema 격리는 env.py 의 SET LOCAL search_path 에 일임하세요."
        )


# ---------------------------------------------------------------------------
# 통계 출력 (참고용, fail 하지 않음)
# ---------------------------------------------------------------------------


def test_migration_count_summary(capsys):
    """검증된 마이그레이션 개수를 stdout 으로 출력 (회귀 추적용)."""
    files = _migration_files()
    print(f"\n[track-70] alembic schema-agnostic 게이트: {len(files)} 마이그레이션 검증 통과")
    for f in files:
        print(f"  - {f.name}")
    assert len(files) >= 1
