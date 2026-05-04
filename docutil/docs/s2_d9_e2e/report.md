# Phase 4 S2 D9 E2E 시연 결과

- 실행 시각: 2026-04-23 15:39:43 대한민국 표준시
- 대상: http://192.168.10.39:8040
- exit_code: 2
- 생성 PPTX: `mode_a_demo_153940.pptx`

## 호출된 URL 목록 (중복 포함)

```
http://192.168.10.39:8040/api/v1/auth/login
http://192.168.10.39:8040/api/v1/agents
http://192.168.10.39:8040/api/v1/v2/documents
... (총 3건)
```

## 실행 로그

```
[15:39:40] === 1. 로그인 ===
[15:39:40] POST /auth/login → 200
[15:39:40] 
=== 2. 에이전트 조회 ===
[15:39:40] agent_id=e9ff76e1-d0db-4309-81fe-d36d68cd0804
[15:39:40] 
=== 3. POST /v2/documents (Mode A) ===
[15:39:43] POST /v2/documents → 502
[15:39:43] FAIL: {"detail":"LLM 호출에 실패했습니다. 잠시 후 다시 시도해 주세요."}
```
