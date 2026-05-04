#!/usr/bin/env python3
"""
Structure linter — enforces file naming conventions across the project.

Purpose: Any AI model (Claude, Codex, Gemini) generates files into identical structure.
This is "harness engineering" — structural enforcement for idempotent output.

Exit code 0 = all clean, 1 = violations found.
"""

import io
import os
import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKEND_MODULES_DIR = PROJECT_ROOT / "backend" / "app" / "modules"
FRONTEND_SRC_DIR = PROJECT_ROOT / "frontend" / "src"

BACKEND_ALLOWED_FILES = {
    "__init__.py",
    "router.py",
    "service.py",
    "schemas.py",
    "models.py",
    "utils.py",
    "constants.py",
    "exceptions.py",
}

FRONTEND_ROUTE_ALLOWED = {
    "page.tsx",
    "page.test.tsx",
    "layout.tsx",
    "loading.tsx",
    "error.tsx",
    "not-found.tsx",
}

# Regex patterns
KEBAB_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*\.(tsx|ts)$")
CAMEL_CASE_RE = re.compile(r"^[a-z][a-zA-Z0-9]*\.(ts|tsx)$")

# Directories to skip
SKIP_DIRS = {"__pycache__", "node_modules", ".next", ".git"}


# ──────────────────────────────────────────────
# Checks
# ──────────────────────────────────────────────


def lint_backend_modules() -> list[str]:
    """Backend modules: only allowed filenames in each module directory."""
    violations = []
    if not BACKEND_MODULES_DIR.exists():
        return violations

    for module_dir in sorted(BACKEND_MODULES_DIR.iterdir()):
        if not module_dir.is_dir():
            continue
        if module_dir.name in SKIP_DIRS:
            continue

        for f in sorted(module_dir.iterdir()):
            if not f.is_file():
                continue
            if f.name in SKIP_DIRS:
                continue
            # Skip .pyc and other non-Python files
            if f.suffix == ".pyc":
                continue
            if f.name not in BACKEND_ALLOWED_FILES:
                rel = f.relative_to(PROJECT_ROOT)
                violations.append(
                    f"[backend] 허용되지 않은 파일: {rel}  "
                    f"(허용: {', '.join(sorted(BACKEND_ALLOWED_FILES))})"
                )

    return violations


def _find_route_dirs(base: Path) -> list[Path]:
    """Recursively find Next.js route directories (contain page.tsx or layout.tsx)."""
    route_dirs = []
    if not base.exists():
        return route_dirs

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        # A route dir is any dir under src/app/
        if any(f.endswith(".tsx") or f.endswith(".ts") for f in files):
            route_dirs.append(root_path)

    return route_dirs


def lint_frontend_routes() -> list[str]:
    """Frontend route dirs: only page.tsx, layout.tsx, loading.tsx, error.tsx, not-found.tsx."""
    violations = []
    app_dir = FRONTEND_SRC_DIR / "app"
    if not app_dir.exists():
        return violations

    for root, dirs, files in os.walk(app_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)

        for f in sorted(files):
            # Only check .tsx/.ts files
            if not (f.endswith(".tsx") or f.endswith(".ts")):
                # Allow .css etc.
                continue
            if f in FRONTEND_ROUTE_ALLOWED:
                continue
            rel = (root_path / f).relative_to(PROJECT_ROOT)
            violations.append(
                f"[frontend/route] 허용되지 않은 파일: {rel}  "
                f"(허용: {', '.join(sorted(FRONTEND_ROUTE_ALLOWED))})"
            )

    return violations


def lint_frontend_components() -> list[str]:
    """Frontend components: kebab-case.tsx only."""
    violations = []
    components_dir = FRONTEND_SRC_DIR / "components"
    if not components_dir.exists():
        return violations

    for root, dirs, files in os.walk(components_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)

        for f in sorted(files):
            if not (f.endswith(".tsx") or f.endswith(".ts")):
                continue
            if not KEBAB_CASE_RE.match(f):
                rel = (root_path / f).relative_to(PROJECT_ROOT)
                violations.append(
                    f"[frontend/component] kebab-case 위반: {rel}  "
                    f"(예: my-component.tsx)"
                )

    return violations


def lint_frontend_lib() -> list[str]:
    """Frontend lib: camelCase.ts only."""
    violations = []
    lib_dir = FRONTEND_SRC_DIR / "lib"
    if not lib_dir.exists():
        return violations

    for root, dirs, files in os.walk(lib_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)

        for f in sorted(files):
            if not (f.endswith(".tsx") or f.endswith(".ts")):
                continue
            # Allow test files with dot notation (e.g., client.test.ts)
            base_name = f
            is_test = ".test." in f
            if is_test:
                base_name = f.replace(".test.", ".")
            if not CAMEL_CASE_RE.match(base_name):
                rel = (root_path / f).relative_to(PROJECT_ROOT)
                violations.append(
                    f"[frontend/lib] camelCase 위반: {rel}  "
                    f"(예: useAuth.ts, apiClient.ts)"
                )

    return violations


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────


def main() -> int:
    print("=" * 60)
    print("  Structure Lint — 파일 명명 규칙 검사")
    print("=" * 60)

    all_violations: list[str] = []

    checks = [
        ("Backend modules", lint_backend_modules),
        ("Frontend routes", lint_frontend_routes),
        ("Frontend components", lint_frontend_components),
        ("Frontend lib", lint_frontend_lib),
    ]

    for name, check_fn in checks:
        violations = check_fn()
        if violations:
            print(f"\n❌ {name}: {len(violations)} violation(s)")
            for v in violations:
                print(f"   • {v}")
            all_violations.extend(violations)
        else:
            print(f"\n✅ {name}: OK")

    print("\n" + "=" * 60)
    if all_violations:
        print(f"  FAIL — {len(all_violations)} total violation(s)")
        print("=" * 60)
        return 1
    else:
        print("  PASS — all structure checks passed")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
