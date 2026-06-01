"""DocUtil 15 admin 페이지 → AgentHub redirect 회귀 검증 (트랙 A1 Phase E)."""
import io
import json
import sys
from pathlib import Path

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DU = "http://192.168.10.39:3040"
OUT = Path(__file__).resolve().parents[1].parent / "user_mig" / "DOCUTIL_REDIRECT.json"

REDIRECTS = [
    ("/admin-accounts", "/admin/docutil-users"),
    ("/departments", "/admin/docutil-departments"),
    ("/projects", "/admin/docutil-projects"),
    ("/dashboard", "/admin/docutil-dashboard"),
    ("/api-keys", "/admin/docutil-api-keys"),
    ("/agents", "/admin/docutil-doc-agents"),
    ("/documents", "/admin/docutil-documents-v2"),
    ("/templates", "/admin/docutil-templates"),
    ("/search-scopes", "/admin/docutil-search-scopes"),
    ("/evaluation", "/admin/docutil-evaluation"),
    ("/help", "/admin/docutil-faq"),
    ("/settings", "/admin/docutil-settings"),
    ("/quick-guide", "/admin/docutil-quick-guide"),
    ("/search-test", "/admin/docutil-search-test"),
    ("/quotas", "/admin/docutil-departments"),
]


def main() -> None:
    results = []
    for src, expected in REDIRECTS:
        r = httpx.get(f"{DU}{src}", follow_redirects=False, verify=False, timeout=15)
        loc = r.headers.get("location") or ""
        ok = r.status_code in (301, 302, 307, 308) and expected in loc
        status = "PASS" if ok else "FAIL"
        icon = "[ OK ]" if ok else "[FAIL]"
        print(f"{icon} {src:25s} → http={r.status_code} location={loc[:80]}")
        results.append(
            {
                "path": src,
                "expected_destination": expected,
                "status": status,
                "detail": f"http={r.status_code} location={loc[:120]}",
            }
        )

    pass_n = sum(1 for r in results if r["status"] == "PASS")
    fail_n = sum(1 for r in results if r["status"] == "FAIL")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"summary": {"pass": pass_n, "fail": fail_n, "total": len(results)}, "results": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[summary] PASS={pass_n} FAIL={fail_n} / 결과: {OUT}")


if __name__ == "__main__":
    main()
