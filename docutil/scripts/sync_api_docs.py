#!/usr/bin/env python3
"""
API Documentation Sync — Extract OpenAPI schema from FastAPI and track changes.

Usage:
    python scripts/sync_api_docs.py              # direct import (CI / Docker)
    python scripts/sync_api_docs.py --url URL    # fetch from running server

Extracts the OpenAPI JSON schema from the FastAPI app, saves it to
docs/api-spec.json, and prints a diff summary of changed endpoints.
Exit code 0 = success, 1 = error during extraction.
"""

import argparse
import io
import json
import sys
from pathlib import Path
from urllib.request import urlopen

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
API_SPEC_PATH = DOCS_DIR / "api-spec.json"

# Add backend to path so we can import the app
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def extract_endpoints(spec: dict) -> dict[str, list[str]]:
    """Extract {path: [methods]} from OpenAPI spec."""
    endpoints: dict[str, list[str]] = {}
    for path, methods in spec.get("paths", {}).items():
        ops = sorted(
            m.upper()
            for m in methods
            if m.lower() in ("get", "post", "put", "patch", "delete", "head", "options")
        )
        if ops:
            endpoints[path] = ops
    return endpoints


def diff_endpoints(
    old: dict[str, list[str]], new: dict[str, list[str]]
) -> tuple[list[str], list[str], list[str]]:
    """Compare old and new endpoint maps. Returns (added, removed, changed)."""
    old_paths = set(old.keys())
    new_paths = set(new.keys())

    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)

    changed = []
    for path in sorted(old_paths & new_paths):
        if old[path] != new[path]:
            changed.append(path)

    return added, removed, changed


def fetch_via_http(url: str) -> dict:
    """Fetch OpenAPI spec from a running server."""
    with urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_via_import() -> dict:
    """Import FastAPI app directly and extract OpenAPI spec."""
    import os

    os.environ.setdefault("JWT_SECRET_KEY", "sync-docs-dummy-key")
    os.environ.setdefault("ENCRYPTION_KEY", "0123456789abcdef" * 4)

    from app.main import app

    return app.openapi()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync API docs from OpenAPI spec")
    parser.add_argument(
        "--url",
        default=None,
        help="Fetch spec from running server (e.g., http://localhost:8040/api/openapi.json)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  API Docs Sync — OpenAPI 스키마 추출 및 변경 비교")
    print("=" * 60)

    # Load previous spec if exists
    old_spec: dict = {}
    if API_SPEC_PATH.exists():
        try:
            old_spec = json.loads(API_SPEC_PATH.read_text(encoding="utf-8"))
            print(f"\n  기존 스키마 로드: {API_SPEC_PATH}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"\n  ⚠ 기존 스키마 파싱 실패: {e}")

    # Extract current OpenAPI schema
    new_spec: dict = {}
    if args.url:
        try:
            print(f"\n  서버에서 스키마 가져오기: {args.url}")
            new_spec = fetch_via_http(args.url)
        except Exception as e:
            print(f"\n  ❌ HTTP 요청 실패: {e}")
            return 1
    else:
        try:
            new_spec = fetch_via_import()
        except Exception as e:
            print(f"\n  ❌ FastAPI 앱에서 OpenAPI 스키마 추출 실패: {e}")
            print("     힌트: --url http://localhost:8040/api/openapi.json 으로 실행하거나")
            print("           Docker 컨테이너 내에서 실행하세요.")
            return 1

    # Ensure docs directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Write new spec
    API_SPEC_PATH.write_text(
        json.dumps(new_spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"  ✅ 스키마 저장: {API_SPEC_PATH}")

    # Diff
    old_endpoints = extract_endpoints(old_spec)
    new_endpoints = extract_endpoints(new_spec)
    added, removed, changed = diff_endpoints(old_endpoints, new_endpoints)

    total_endpoints = len(new_endpoints)
    print(f"\n  총 엔드포인트 수: {total_endpoints}")

    if not (added or removed or changed):
        print("  변경사항 없음")
    else:
        if added:
            print(f"\n  ➕ 추가된 엔드포인트 ({len(added)}):")
            for path in added:
                methods = ", ".join(new_endpoints[path])
                print(f"     {methods} {path}")

        if removed:
            print(f"\n  ➖ 제거된 엔드포인트 ({len(removed)}):")
            for path in removed:
                methods = ", ".join(old_endpoints[path])
                print(f"     {methods} {path}")

        if changed:
            print(f"\n  🔄 메서드 변경된 엔드포인트 ({len(changed)}):")
            for path in changed:
                old_m = ", ".join(old_endpoints[path])
                new_m = ", ".join(new_endpoints[path])
                print(f"     {path}: {old_m} → {new_m}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
