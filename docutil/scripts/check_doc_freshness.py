#!/usr/bin/env python3
"""
Documentation Freshness Check — Compare project_status.md with actual modules.

Usage:
    python scripts/check_doc_freshness.py

Compares the feature table in user_mig/project_status.md with the actual
backend module directories. Warns about undocumented or stale modules.
Exit code 0 = all clean, 1 = warnings found (advisory, not blocking).
"""

import io
import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_MODULES_DIR = PROJECT_ROOT / "backend" / "app" / "modules"
PROJECT_STATUS_PATH = PROJECT_ROOT / "user_mig" / "project_status.md"

# Modules that are infrastructure/internal — not expected in feature docs
INFRA_MODULES = {"__init__", "__pycache__"}

# Map from feature doc keywords to module directory names
# This helps match documented features to their backend modules
KEYWORD_TO_MODULE = {
    "인증": "auth",
    "인가": "auth",
    "jwt": "auth",
    "로그인": "auth",
    "사용자": "users",
    "부서": "organizations",
    "조직": "organizations",
    "프로젝트": "projects",
    "문서": "documents",
    "업로드": "documents",
    "검색": "search",
    "검색범위": "search_scopes",
    "챗봇": "chat",
    "채팅": "chat",
    "보고서": "reports",
    "제안서": "reports",
    "감사": "audit",
    "로그": "audit",
    "api 키": "api_keys",
    "api키": "api_keys",
    "faq": "faq",
    "관리자": "admin",
    "설정": "admin",
    "에이전트": "agents",
    "템플릿": "templates",
}


def get_actual_modules() -> set[str]:
    """Get set of actual backend module directory names."""
    if not BACKEND_MODULES_DIR.exists():
        return set()

    modules = set()
    for d in BACKEND_MODULES_DIR.iterdir():
        if d.is_dir() and d.name not in INFRA_MODULES:
            modules.add(d.name)
    return modules


def get_documented_modules() -> set[str]:
    """Extract module names referenced in project_status.md feature tables."""
    if not PROJECT_STATUS_PATH.exists():
        return set()

    content = PROJECT_STATUS_PATH.read_text(encoding="utf-8").lower()
    documented = set()

    for keyword, module in KEYWORD_TO_MODULE.items():
        if keyword.lower() in content:
            documented.add(module)

    # Also look for module names directly mentioned (e.g., in code paths)
    module_path_pattern = re.compile(r"modules/(\w+)")
    for match in module_path_pattern.finditer(content):
        name = match.group(1)
        if name not in INFRA_MODULES:
            documented.add(name)

    return documented


def main() -> int:
    print("=" * 60)
    print("  Doc Freshness Check — 문서 최신성 검사")
    print("=" * 60)

    if not PROJECT_STATUS_PATH.exists():
        print(f"\n  ⚠ project_status.md를 찾을 수 없음: {PROJECT_STATUS_PATH}")
        print("  검사를 건너뜁니다.")
        return 0

    actual = get_actual_modules()
    documented = get_documented_modules()

    print(f"\n  실제 백엔드 모듈 ({len(actual)}): {', '.join(sorted(actual))}")
    print(f"  문서화된 모듈 ({len(documented)}): {', '.join(sorted(documented))}")

    warnings = []

    # Modules that exist but aren't documented
    undocumented = sorted(actual - documented)
    if undocumented:
        for mod in undocumented:
            msg = f"모듈 '{mod}'이(가) 코드에 존재하지만 project_status.md에 문서화되지 않음"
            warnings.append(msg)
            print(f"\n  ⚠ {msg}")
            # Check if module has meaningful content (not just __init__.py)
            mod_dir = BACKEND_MODULES_DIR / mod
            files = [f.name for f in mod_dir.iterdir() if f.is_file() and f.name != "__init__.py"]
            if files:
                print(f"     파일: {', '.join(sorted(files))}")

    # Modules documented but no longer exist
    stale = sorted(documented - actual)
    if stale:
        for mod in stale:
            msg = f"모듈 '{mod}'이(가) project_status.md에 문서화되어 있지만 코드에 존재하지 않음"
            warnings.append(msg)
            print(f"\n  ⚠ {msg}")

    # Check project_status.md modification date vs latest module change
    status_mtime = PROJECT_STATUS_PATH.stat().st_mtime
    latest_module_mtime = 0.0
    latest_module_name = ""
    for mod_dir in BACKEND_MODULES_DIR.iterdir():
        if not mod_dir.is_dir() or mod_dir.name in INFRA_MODULES:
            continue
        for f in mod_dir.iterdir():
            if f.is_file() and f.stat().st_mtime > latest_module_mtime:
                latest_module_mtime = f.stat().st_mtime
                latest_module_name = f"{mod_dir.name}/{f.name}"

    if latest_module_mtime > status_mtime and latest_module_name:
        from datetime import datetime

        doc_date = datetime.fromtimestamp(status_mtime).strftime("%Y-%m-%d %H:%M")
        code_date = datetime.fromtimestamp(latest_module_mtime).strftime("%Y-%m-%d %H:%M")
        msg = (
            f"코드가 문서보다 최신 — 마지막 변경: {latest_module_name} ({code_date}), "
            f"문서: {doc_date}"
        )
        warnings.append(msg)
        print(f"\n  ⚠ {msg}")

    print("\n" + "=" * 60)
    if warnings:
        print(f"  {len(warnings)} warning(s) — 문서 업데이트를 검토하세요")
        print("=" * 60)
        return 1
    else:
        print("  PASS — 문서가 코드와 동기화되어 있습니다")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
