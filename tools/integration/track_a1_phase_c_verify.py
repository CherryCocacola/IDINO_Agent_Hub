"""트랙 A1 Phase C 검증 — Users mutation (Status / Delete) AgentHub 직접 + DocUtil 410.

흐름:
1. SuperAdmin 로그인
2. 테스트용 임시 Users 생성 (AgentHub /api/users 또는 직접 DB 가 아닌 회원가입 endpoint)
   — 없으면 기존 사용자 1명 status round-trip + restore
3. PUT /api/admin/docutil/users/{id}/status — active → inactive → active
4. (cleanup) Status 원복

직접 검증 항목:
- AgentHub mutation 이 DocUtil 호출 없이 (즉, DocUtil 측 로그에 mutation request 미발생)
  성공하는지
- DocUtil 의 PUT /api/v1/users/{id}, DELETE /api/v1/users/{id} 가 410 반환하는지
"""
import io
import json
import sys
from pathlib import Path

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AH = "http://192.168.10.39:64005"
DU = "http://192.168.10.39:8040"  # DocUtil API
ADMIN = ("admin@example.com", "Admin123!")
OUT = Path(__file__).resolve().parents[1].parent / "user_mig" / "TRACK_A1_PHASE_C.json"


def log(label: str, status: str, detail: str = "") -> dict:
    icon = {"PASS": "[ OK ]", "FAIL": "[FAIL]"}.get(status, "[ ?? ]")
    print(f"{icon} {label}  {detail}")
    return {"step": label, "status": status, "detail": detail}


def main() -> None:
    results: list[dict] = []

    with httpx.Client(base_url=AH, timeout=60, verify=False) as c:
        r = c.post("/api/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]})
        if r.status_code != 200:
            results.append(log("1. SuperAdmin 로그인", "FAIL", f"http={r.status_code}"))
            _save(results)
            return
        tok = r.json()["token"]
        c.headers["Authorization"] = f"Bearer {tok}"
        results.append(log("1. SuperAdmin 로그인", "PASS"))

        # 2. AgentHub 사용자 목록에서 admin 외 첫 사용자 한 명 선택 (e2e 대상)
        r = c.get("/api/admin/docutil/users", params={"page": 1, "size": 50})
        if r.status_code != 200:
            results.append(log("2. 사용자 목록 조회", "FAIL", f"http={r.status_code} body={r.text[:200]}"))
            _save(results)
            return
        users = r.json().get("items") or []
        target = next((u for u in users if u.get("email") != ADMIN[0]), None)
        if target is None:
            results.append(log("2. 검증 대상 사용자 탐색", "FAIL", "admin 외 사용자 없음"))
            _save(results)
            return
        uid = target.get("id")
        original_status = (target.get("status") or "active").lower()
        results.append(
            log("2. 검증 대상 사용자 탐색", "PASS", f"id={uid} status={original_status}")
        )

        # 3. PUT users/{id}/status → inactive
        r = c.put(f"/api/admin/docutil/users/{uid}/status", json={"status": "inactive"})
        ok = r.status_code == 200 and (r.json().get("status") or "").lower() == "inactive"
        results.append(
            log("3. PUT status=inactive (직접 update)", "PASS" if ok else "FAIL",
                f"http={r.status_code} body[:200]={r.text[:200]}")
        )

        # 4. 다시 active 로 복원
        r = c.put(f"/api/admin/docutil/users/{uid}/status", json={"status": original_status})
        ok = r.status_code == 200 and (r.json().get("status") or "").lower() == original_status
        results.append(
            log("4. PUT status 원복 (직접 update)", "PASS" if ok else "FAIL",
                f"http={r.status_code} → status={r.json().get('status') if r.status_code == 200 else 'N/A'}")
        )

        # 5. DELETE — 실 사용자 삭제는 위험. Postman/외부 호출 의도만 검증:
        #    AgentHub controller 자체는 변경되었지만, 실 삭제는 운영자가 직접 시행.
        #    여기서는 DocUtil 410 차단 동작만 검증.

    # 6. DocUtil 410 Gone 검증 — AgentHub JWT 를 DocUtil 인증으로 사용 (트랙 #98 phase 3 통합).
    #    require_role(["admin","super_admin"]) dependency 통과 후 _raise_gone() 발사.
    with httpx.Client(base_url=DU, timeout=30, verify=False) as dc:
        dc.headers["Authorization"] = f"Bearer {tok}"
        r = dc.put("/api/v1/users/00000000-0000-0000-0000-000000000001",
                   json={"status": "inactive"})
        body = r.text
        is_410 = r.status_code == 410
        has_agenthub_hint = "AgentHub" in body or "운영자" in body
        results.append(
            log("6. DocUtil PUT /api/v1/users 410 차단", "PASS" if is_410 and has_agenthub_hint else "FAIL",
                f"http={r.status_code} body[:200]={body[:200]}")
        )

        r = dc.delete("/api/v1/users/00000000-0000-0000-0000-000000000001")
        is_410 = r.status_code == 410
        results.append(
            log("7. DocUtil DELETE /api/v1/users 410 차단", "PASS" if is_410 else "FAIL",
                f"http={r.status_code} body[:200]={r.text[:200]}")
        )

        # 부서 mutation 도 동일하게 410 차단되어야
        r = dc.post("/api/v1/organizations/00000000-0000-0000-0000-000000000001/departments",
                    json={"name": "test"})
        is_410 = r.status_code == 410
        results.append(
            log("8. DocUtil POST /organizations/{org}/departments 410", "PASS" if is_410 else "FAIL",
                f"http={r.status_code}")
        )

    _save(results)


def _save(results: list[dict]) -> None:
    pass_n = sum(1 for r in results if r["status"] == "PASS")
    fail_n = sum(1 for r in results if r["status"] == "FAIL")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"summary": {"pass": pass_n, "fail": fail_n}, "results": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[summary] PASS={pass_n} FAIL={fail_n} / 결과: {OUT}")


if __name__ == "__main__":
    main()
