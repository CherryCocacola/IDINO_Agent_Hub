# Phase 4 S1 D9-B — End-to-end 시연 결과

- 실행 시각: 2026-04-23 01:19:48 대한민국 표준시
- 대상 서버: `http://192.168.10.39:8040`
- 스크립트 exit_code: 0

## 실행 로그

```
[01:19:21] === 1. 로그인 ===
[01:19:22] POST /auth/login → 200
[01:19:22] access_token 획득
[01:19:22] 
=== 2. 에이전트 목록 조회 ===
[01:19:22] GET /agents → 200
[01:19:22] agent_id=e9ff76e1-d0db-4309-81fe-d36d68cd0804 (type=report)
[01:19:22] 
=== 3. POST /v2/documents (Mode A) ===
[01:19:45] POST /v2/documents → 202
[01:19:45] document_id=d460e261-b661-40bf-a2f6-ecfc8c80c9ac, status=completed
[01:19:45] 
=== 4. 상태 폴링 (최대 90초) ===
[01:19:48] [01] status=completed
[01:19:48] 생성 완료. 페이지 3개
[01:19:48] 첫 페이지 id=p1, 컴포넌트 2개
[01:19:48] 첫 SlideTitle: {"id": "c1", "text": "2026년 1분기 사업 실적 요약", "type": "SlideTitle", "anchor": null, "locked": false}
[01:19:48] 
=== 5. PATCH /v2/documents/{id} (component 교체) ===
[01:19:48] PATCH → 200
[01:19:48] 
=== 6. GET 재조회 + 반영 검증 ===
[01:19:48] 재조회 text/value: [D9 시연으로 수정된 제목] 2026 1분기 실적
[01:19:48] ✅ PATCH 반영 확인
[01:19:48] schema_version: before=1.0 → after=1.0
[01:19:48] 
=== 7. 프리뷰 URL 접근성 ===
[01:19:48] GET http://192.168.10.39:3040/designer/d460e261-b661-40bf-a2f6-ecfc8c80c9ac → 404
[01:19:48] WARN: 예상치 못한 status 404
[01:19:48] 
=== 시연 완료 요약 ===
[01:19:48] - document_id: d460e261-b661-40bf-a2f6-ecfc8c80c9ac
[01:19:48] - 최종 페이지 수: 3
[01:19:48] - PATCH 반영: OK
[01:19:48] - schema_version: 1.0 → 1.0
[01:19:48] - 프리뷰 URL: http://192.168.10.39:3040/designer/d460e261-b661-40bf-a2f6-ecfc8c80c9ac
```
