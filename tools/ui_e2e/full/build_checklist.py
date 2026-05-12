"""트랙 #88-7 — e2e 결과 통합 + 체크리스트 마크다운 생성."""
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent
LIVE = json.load(open(ROOT / "live_results.json", encoding="utf-8"))
DOCU = json.load(open(ROOT / "docutil_skip_resolved.json", encoding="utf-8"))

# 카테고리화
categories = {
    "AgentHub Public (인증 불필요)": [],
    "AgentHub Protected (admin 인증)": [],
    "AgentHub Anonymous Redirect (5건 샘플)": [],
    "DocUtil Public (anonymous)": [],
    "DocUtil 인증 의존 (admin/user)": [],
}

for r in LIVE.get("results", []):
    cp = r.get("case_prefix", "")
    path = r.get("path", "")
    status = r.get("status", "")
    role = r.get("role", "")
    duration = r.get("duration_ms", 0)
    note = r.get("note", "")

    if cp.startswith("Public_") or cp.startswith("AH_") and role == "anon":
        categories["AgentHub Public (인증 불필요)"].append(r)
    elif cp.startswith("AH_") and role == "admin":
        categories["AgentHub Protected (admin 인증)"].append(r)
    elif cp.startswith("AnonRedirect_"):
        categories["AgentHub Anonymous Redirect (5건 샘플)"].append(r)
    elif cp.startswith("DU_") and role == "anon":
        categories["DocUtil Public (anonymous)"].append(r)
    else:
        # SKIP 또는 docutil_skip_resolved 에서 갈아끼울 항목
        pass

# DocUtil 22건은 resolved 결과로 갈아끼움
for r in DOCU.get("results", []):
    categories["DocUtil 인증 의존 (admin/user)"].append(r)


def status_icon(s):
    return {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭", "PARTIAL": "⚠️", "LOGIN_FAILED": "❌"}.get(s, "❓")


# 통계
all_results = [r for v in categories.values() for r in v]
total = len(all_results)
pass_n = sum(1 for r in all_results if r.get("status") == "PASS")
fail_n = sum(1 for r in all_results if r.get("status") == "FAIL")
other_n = total - pass_n - fail_n

print(f"# 트랙 #88-7 — 전수 e2e 체크리스트")
print()
print(f"**총 {total} 케이스 | PASS {pass_n} | FAIL {fail_n} | 기타 {other_n}**")
print()
print(f"수행 시각: {LIVE.get('started_at', '?')} ~ {LIVE.get('finished_at', '?')}")
print(f"DocUtil 부분: {DOCU.get('started_at', '?')} ~ {DOCU.get('finished_at', '?')}")
print()
print(f"AgentHub: http://192.168.10.39:64005 / DocUtil: http://192.168.10.39:8041")
print(f"자격증명: admin@example.com / Admin123!")
print()

for cat, items in categories.items():
    p = sum(1 for r in items if r.get("status") == "PASS")
    print(f"## {cat} — {p}/{len(items)} PASS")
    print()
    print("| ☐ | Path | Role | 상태 | DOM | console 오류 | 4xx/5xx | 소요(ms) |")
    print("|---|------|------|------|-----|--------------|---------|----------|")
    for r in items:
        st = r.get("status", "?")
        icon = "☑" if st == "PASS" else "☐"
        path = r.get("path", "?")
        role = r.get("role", "?")
        dom = "✓" if r.get("dom_mounted") else ("-" if r.get("dom_mounted") is None else "✗")
        ce = len(r.get("console_errors", []))
        ne = len(r.get("network_4xx_5xx", []))
        dur = r.get("duration_ms", 0)
        print(f"| {icon} | `{path}` | {role} | {status_icon(st)} {st} | {dom} | {ce} | {ne} | {dur} |")
    print()

# 결과 저장
out = "D:/workspace/IDINO_Agent_Hub/tmp/track88_checklist.md"
import contextlib
with open(out, "w", encoding="utf-8") as f:
    with contextlib.redirect_stdout(f):
        print(f"# 트랙 #88-7 — 전수 e2e 체크리스트\n")
        print(f"**총 {total} 케이스 | PASS {pass_n} | FAIL {fail_n} | 기타 {other_n}**\n")
        for cat, items in categories.items():
            p = sum(1 for r in items if r.get("status") == "PASS")
            print(f"## {cat} — {p}/{len(items)} PASS\n")
            print("| ☐ | Path | Role | 상태 | DOM | console | 4xx/5xx | ms |")
            print("|---|------|------|------|-----|---------|---------|-----|")
            for r in items:
                st = r.get("status", "?")
                icon = "☑" if st == "PASS" else "☐"
                path = r.get("path", "?")
                role = r.get("role", "?")
                dom = "✓" if r.get("dom_mounted") else "-"
                ce = len(r.get("console_errors", []))
                ne = len(r.get("network_4xx_5xx", []))
                dur = r.get("duration_ms", 0)
                print(f"| {icon} | `{path}` | {role} | {st} | {dom} | {ce} | {ne} | {dur} |")
            print()

print(f"\n저장: {out}")
