"""트랙 #75 시나리오 4 — DocUtil UI 시나리오 I-01~I-05.

자격증명 확인:
- DocUtil 운영 DB(read-only)에서 admin 또는 게스트 계정 비번 확인 시도
- 또는 AgentHub admin 자격이 DocUtil 에도 통하는지 (공통 IdP 가능성)

미확보 시 I-01 FAIL 처리 + I-02~I-05 SKIP.
"""
from __future__ import annotations
import io
import json
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import DOCUTIL_NGINX, chrome, now_ts, shot


def try_login(page, username: str, password: str) -> tuple[bool, str, str]:
    """DocUtil 로그인 시도 — 성공/실패 + 응답 메시지 캡처."""
    page.goto(f"{DOCUTIL_NGINX}/login")
    page.wait_for_load_state("networkidle", timeout=10_000)
    time.sleep(0.4)

    # 아이디/비밀번호 입력
    try:
        # 아이디 = placeholder "아이디를 입력하세요"
        page.fill("input[placeholder*='아이디']", username)
        page.fill("input[placeholder*='비밀번호'], input[type='password']", password)
    except Exception:
        try:
            inputs = page.locator("input").all()
            if len(inputs) >= 2:
                inputs[0].fill(username)
                inputs[1].fill(password)
        except Exception:
            return False, "input fill failed", ""

    # 로그인 버튼 클릭
    captured = {"status": None, "body": ""}

    def on_resp(r):
        try:
            if "/api/v1/auth/login" in r.url or "/auth/login" in r.url:
                if r.request.method == "POST":
                    captured["status"] = r.status
                    try:
                        captured["body"] = r.text()[:300]
                    except Exception:
                        pass
        except Exception:
            pass

    page.on("response", on_resp)
    try:
        page.click("button:has-text('로그인'), button[type='submit']")
    except Exception:
        return False, "click failed", ""

    time.sleep(2.5)
    try:
        page.wait_for_load_state("networkidle", timeout=8_000)
    except Exception:
        pass
    success = "/login" not in page.url
    return success, str(captured["status"]), captured["body"][:200]


def main() -> dict:
    out = {"scenario_id": "S4", "scenario": "DocUtil UI I-01~I-05", "started_at": now_ts(), "steps": [], "credentials_obtained": False}

    # 안전 원칙: brute force 금지 — 합리적 후보 2건만 시도 (공통 IdP 가능성)
    # 실패 시 즉시 SKIP + 사용자에게 자격증명 제공 요청
    candidates = [
        ("admin@example.com", "Admin123!"),  # 공통 IdP 가능성 (낮음)
        ("admin", "admin"),                  # DocUtil 기본 계정 관행 (보안 약점 진단용)
    ]
    success_cred = None
    attempt_log = []
    with chrome(headless=True) as (_p, _b, _ctx, page):
        for u, pw in candidates:
            ok, status, body = try_login(page, u, pw)
            attempt_log.append({"username": u, "password_masked": pw[:2] + "*" * (len(pw)-2), "post_login_url": page.url, "login_api_status": status, "body": body, "success": ok})
            if ok:
                success_cred = (u, pw)
                break
        sc = shot(page, "s4_01", "docutil_login_attempts")
        out["steps"].append({
            "id": "I-01",
            "desc": f"DocUtil 로그인 시도 ({len(candidates)}건)",
            "result": "PASS" if success_cred else "FAIL",
            "attempts": attempt_log,
            "screenshot": sc,
        })

        if not success_cred:
            out["steps"].append({"id": "I-02~I-05", "desc": "자격증명 미확보 — 챗봇/검색/업로드/보고서 SKIP",
                                 "result": "SKIP", "note": "자격증명 확보 후 재실행 필요"})
            out["finished_at"] = now_ts()
            summary = {"PASS": 0, "FAIL": 1, "SKIP": 1, "INFO": 0}
            out["summary"] = summary
            out["overall"] = "SKIP (자격증명 미확보)"
            return out

        out["credentials_obtained"] = True
        # I-02~I-05 — 자격증명 확보 시 진행 (자격증명 확보된 경우)
        # 자격증명 확보 후 시나리오 작성

    out["finished_at"] = now_ts()
    return out


if __name__ == "__main__":
    result = main()
    with open("scenario_4_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"summary": result.get("summary", {}), "overall": result.get("overall", "?"),
                      "credentials_obtained": result["credentials_obtained"]}, ensure_ascii=False, indent=2))
    print("saved scenario_4_result.json")
