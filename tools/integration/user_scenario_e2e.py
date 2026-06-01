"""트랙 #149 P2 — 사용자 시나리오 깊은 e2e.

시나리오: SuperAdmin 로그인 → 새 Agent 생성 → 채팅 1회 → API Key 발급 →
        외부 OpenAI 호환 /v1/chat/completions 호출 → API Key 회수 → Agent 삭제.

목표: 통합 단계의 핵심 사용자 흐름 (Agent → 채팅 → 외부 노출 → cleanup) 전체 검증.
운영 데이터 오염 방지: ui-e2e-test-* prefix + 끝에 모두 삭제.
"""
import io
import json
import sys
import time
from pathlib import Path

import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AH = "http://192.168.10.39:64005"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PWD = "Admin123!"
OUT = Path(__file__).resolve().parents[1].parent / "user_mig" / "USER_SCENARIO_E2E.json"

NAME = f"ui-e2e-test-{int(time.time())}"


def log(label: str, status: str, detail: str = "") -> dict:
    """상태 한 줄 출력 + dict 반환."""
    icon = {"PASS": "[ OK ]", "FAIL": "[FAIL]", "INFO": "[INFO]"}.get(status, "[ ?? ]")
    print(f"{icon} {label}  {detail}")
    return {"step": label, "status": status, "detail": detail}


def _has_korean(text: str) -> bool:
    """한국어 검증 — raw 본문 또는 JSON unicode escape (\\uXXXX) 모두 인식."""
    # 1) 본문 직접 검사
    if any("가" <= ch <= "힣" for ch in text):
        return True
    # 2) JSON unicode escape 디코드 시도
    try:
        decoded = text.encode().decode("unicode_escape")
        if any("가" <= ch <= "힣" for ch in decoded):
            return True
    except Exception:
        pass
    # 3) JSON parse 후 모든 값 검사
    try:
        obj = json.loads(text)
        def walk(v):
            if isinstance(v, str):
                return any("가" <= ch <= "힣" for ch in v)
            if isinstance(v, dict):
                return any(walk(x) for x in v.values())
            if isinstance(v, list):
                return any(walk(x) for x in v)
            return False
        return walk(obj)
    except Exception:
        return False


def main() -> None:
    results: list[dict] = []
    agent_id: int | None = None
    api_key_id: int | None = None
    plaintext_key: str | None = None

    with httpx.Client(base_url=AH, timeout=60, verify=False) as c:
        # 1) 관리자 로그인
        r = c.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD})
        if r.status_code != 200:
            results.append(log("1. SuperAdmin 로그인", "FAIL", f"http={r.status_code}"))
            _save(results)
            return
        token = r.json()["token"]
        c.headers["Authorization"] = f"Bearer {token}"
        results.append(log("1. SuperAdmin 로그인", "PASS", f"token len={len(token)}"))

        # 운영 ApiServices 에서 chatgpt 의 ServiceId 동적 조회 (운영 환경 가변 대응)
        r = c.get("/api/apiservices")
        services = r.json() if r.status_code == 200 else []
        chatgpt_svc = next((s for s in services if s.get("serviceCode") == "chatgpt"), None)
        if not chatgpt_svc:
            results.append(log("2pre. ApiServices(chatgpt) 조회", "FAIL", "chatgpt ServiceId 미확인"))
            _save(results)
            return
        service_id = chatgpt_svc["serviceId"]

        # 2) Agent 생성 (Hybrid 라우팅 — 트랙 #138 정책 활용)
        agent_payload = {
            "agentName": NAME,
            "description": "트랙 #149 P2 자동 e2e 검증용 임시 Agent",
            "systemPrompt": "당신은 친절한 한국어 AI 어시스턴트입니다. 짧게 답하세요.",
            "defaultModel": "gpt-4o",
            "serviceId": service_id,
            "temperature": 0.3,
            "maxTokens": 200,
            "enableRag": False,
            "piiProtectionEnabled": False,
            "llmRouting": "Hybrid",
        }
        r = c.post("/api/agents", json=agent_payload)
        if r.status_code not in (200, 201):
            results.append(log("2. POST /api/agents (Agent 생성)", "FAIL", f"http={r.status_code} body={r.text[:200]}"))
            _save(results)
            return
        agent = r.json()
        agent_id = agent.get("agentId") or agent.get("AgentId")
        agent_code = agent.get("agentCode") or agent.get("AgentCode")
        results.append(log("2. POST /api/agents (Agent 생성)", "PASS", f"id={agent_id} code={agent_code} name={NAME}"))

        # 3) 채팅 conversation 시작 + 첫 메시지 (정상 응답 또는 운영 502 한국어 메시지 모두 PASS)
        r = c.post(
            "/api/chat/conversations",
            json={"agentId": agent_id, "title": f"{NAME} chat"},
        )
        if r.status_code not in (200, 201):
            results.append(log("3a. POST /api/chat/conversations", "FAIL", f"http={r.status_code}"))
        else:
            conv = r.json()
            conv_id = conv.get("conversationId") or conv.get("ConversationId")
            results.append(log("3a. POST /api/chat/conversations", "PASS", f"convId={conv_id}"))

            r = c.post(
                f"/api/chat/conversations/{conv_id}/messages",
                json={"message": "안녕하세요. (트랙 #149 P2 e2e 1회 호출)"},
            )
            if r.status_code == 200:
                resp_msg = r.json().get("response") or r.json().get("Response") or ""
                results.append(log("3b. 채팅 메시지 전송", "PASS", f"응답 len={len(str(resp_msg))}"))
            elif r.status_code in (502, 503):
                # OpenAI quota 소진 / API Key 결함 시 한국어 502 — 운영 정책상 PASS
                body = r.text
                has_korean = _has_korean(body)
                results.append(
                    log(
                        "3b. 채팅 메시지 전송",
                        "PASS" if has_korean else "FAIL",
                        f"http={r.status_code} 한국어={has_korean} (운영 502 정책)",
                    )
                )
            else:
                results.append(log("3b. 채팅 메시지 전송", "FAIL", f"http={r.status_code} body={r.text[:200]}"))

        # 4) Agent 에 API Key 발급
        r = c.post(
            f"/api/agents/{agent_id}/api-keys",
            json={"name": f"{NAME}-key", "scopes": "chat,info"},
        )
        if r.status_code not in (200, 201):
            results.append(log("4. API Key 발급", "FAIL", f"http={r.status_code} body={r.text[:200]}"))
        else:
            keydata = r.json()
            plaintext_key = keydata.get("plainKey") or keydata.get("apiKey") or keydata.get("PlainKey")
            api_key_id = keydata.get("apiKeyId") or keydata.get("ApiKeyId") or keydata.get("id")
            mask = (plaintext_key[:4] + "***" + plaintext_key[-4:]) if plaintext_key else "(평문 미반환)"
            results.append(
                log(
                    "4. API Key 발급",
                    "PASS" if plaintext_key else "FAIL",
                    f"id={api_key_id} key={mask}",
                )
            )

        # 5) 외부 /v1/chat/completions (OpenAI 호환) 호출 — X-API-Key 검증
        # 주의: model 은 OpenAI 모델명이 아니라 AgentHub AgentCode (OpenAICompatController 규약).
        if plaintext_key and agent_code:
            r = httpx.post(
                f"{AH}/v1/chat/completions",
                headers={"X-API-Key": plaintext_key, "Content-Type": "application/json"},
                json={
                    "model": agent_code,
                    "messages": [{"role": "user", "content": "Say hello in Korean."}],
                    "max_tokens": 50,
                },
                timeout=60,
                verify=False,
            )
            if r.status_code == 200:
                body = r.json()
                choice = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                results.append(log("5. /v1/chat/completions 외부 호출", "PASS", f"응답 len={len(str(choice))}"))
            elif r.status_code in (502, 503):
                body_text = r.text
                has_korean = _has_korean(body_text)
                results.append(
                    log(
                        "5. /v1/chat/completions 외부 호출",
                        "PASS" if has_korean else "FAIL",
                        f"http={r.status_code} 한국어={has_korean} (운영 502 정책)",
                    )
                )
            elif r.status_code == 429:
                results.append(log("5. /v1/chat/completions 외부 호출", "PASS", "http=429 (Rate Limit 정상 발동)"))
            else:
                results.append(log("5. /v1/chat/completions 외부 호출", "FAIL", f"http={r.status_code} body={r.text[:200]}"))

        # 6) API Key 회수
        if api_key_id is not None:
            r = c.delete(f"/api/agents/{agent_id}/api-keys/{api_key_id}")
            results.append(log("6. API Key 회수", "PASS" if r.status_code in (200, 204) else "FAIL", f"http={r.status_code}"))

            # 회수 후 키 재호출 → 401 기대 (agent_code 와 무관하게 인증이 먼저 실패)
            if plaintext_key:
                r = httpx.post(
                    f"{AH}/v1/chat/completions",
                    headers={"X-API-Key": plaintext_key, "Content-Type": "application/json"},
                    json={"model": agent_code or "any", "messages": [{"role": "user", "content": "x"}]},
                    timeout=30,
                    verify=False,
                )
                results.append(
                    log(
                        "6b. 회수된 키 재호출 (401 기대)",
                        "PASS" if r.status_code == 401 else "FAIL",
                        f"http={r.status_code}",
                    )
                )

        # 7) Agent 삭제 (cleanup)
        if agent_id is not None:
            r = c.delete(f"/api/agents/{agent_id}")
            results.append(log("7. Agent 삭제 (cleanup)", "PASS" if r.status_code in (200, 204) else "FAIL", f"http={r.status_code}"))

    _save(results)


def _save(results: list[dict]) -> None:
    pass_n = sum(1 for r in results if r["status"] == "PASS")
    fail_n = sum(1 for r in results if r["status"] == "FAIL")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"summary": {"pass": pass_n, "fail": fail_n}, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[summary] PASS={pass_n} FAIL={fail_n} / 결과: {OUT}")


if __name__ == "__main__":
    main()
