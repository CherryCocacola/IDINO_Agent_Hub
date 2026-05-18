# 트랙 #99 5단 e2e 매트릭스 — 2026-05-18 17:13:34 시작

- 종료: 2026-05-18 17:28:11
- 계정: SuperAdmin, AdminDev, User, EmployeeHslee, EmployeeShbaek

## 종합 PASS율

- 전체: 376/460 PASS (81%)
- FAIL: 34건
- SKIP: 50건

## Phase별 결과

| Phase | PASS | FAIL | SKIP |
|---|---|---|---|
| AgentHub Phase A (라우트 진입) | 268 | 17 | 0 |
| AgentHub Phase B (인터랙션) | 21 | 14 | 0 |
| DocUtil Phase A (라우트 진입) | 75 | 0 | 50 |
| DocUtil Phase B (인터랙션) | 12 | 3 | 0 |

## storage_state 생성 결과

- **SuperAdmin_ah**: ok=True verify=PASS note=localStorage already has token (ls=OK)
- **SuperAdmin_du**: ok=False verify=- note=SKIP — 4단 결함
- **AdminDev_ah**: ok=True verify=PASS note=localStorage already has token (ls=OK)
- **AdminDev_du**: ok=True verify=- note=ok
- **User_ah**: ok=True verify=PASS note=localStorage already has token (ls=OK)
- **User_du**: ok=False verify=- note=SKIP — 4단 결함
- **EmployeeHslee_ah**: ok=True verify=PASS note=localStorage already has token (ls=OK)
- **EmployeeHslee_du**: ok=True verify=- note=ok
- **EmployeeShbaek_ah**: ok=True verify=PASS note=localStorage already has token (ls=OK)
- **EmployeeShbaek_du**: ok=True verify=- note=ok

## 발견된 결함 (34건)

1. [phase_a_agenthub] **SuperAdmin** | /admin/knowledge-base → 5xx 발생
2. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-users → 5xx 발생
3. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-departments → 5xx 발생
4. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-projects → 5xx 발생
5. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-dashboard → 5xx 발생
6. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-audit → 5xx 발생
7. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-search-scopes → 5xx 발생
8. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-evaluation → 5xx 발생
9. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-faq → 5xx 발생
10. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-reports → 5xx 발생
11. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-templates → 5xx 발생
12. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-api-keys → 5xx 발생
13. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-doc-agents → 5xx 발생
14. [phase_a_agenthub] **SuperAdmin** | /admin/docutil-documents-v2 → 5xx 발생
15. [phase_a_agenthub] **User** | /quota → 권한차단 미동작 — User 가 admin 페이지 진입
16. [phase_a_agenthub] **User** | /usage-history → 권한차단 미동작 — User 가 admin 페이지 진입
17. [phase_a_agenthub] **User** | /api-keys → 권한차단 미동작 — User 가 admin 페이지 진입
18. [phase_b_agenthub] **SuperAdmin** | B3-Settings-DeptTree → 부서 트리 키워드 발견=False, readonly_input=있음
19. [phase_b_agenthub] **SuperAdmin** | /admin/docutil-departments → 콘텐츠 키워드 미발견 (path=/admin/docutil-departments)
20. [phase_b_agenthub] **AdminDev** | B3-Settings-DeptTree → 부서 트리 키워드 발견=False, readonly_input=있음
21. [phase_b_agenthub] **AdminDev** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
22. [phase_b_agenthub] **AdminDev** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
23. [phase_b_agenthub] **User** | B3-Settings-DeptTree → 부서 트리 키워드 발견=False, readonly_input=있음
24. [phase_b_agenthub] **User** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
25. [phase_b_agenthub] **User** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
26. [phase_b_agenthub] **EmployeeHslee** | B3-Settings-DeptTree → 부서 트리 키워드 발견=False, readonly_input=있음
27. [phase_b_agenthub] **EmployeeHslee** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
28. [phase_b_agenthub] **EmployeeHslee** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
29. [phase_b_agenthub] **EmployeeShbaek** | B3-Settings-DeptTree → 부서 트리 키워드 발견=False, readonly_input=있음
30. [phase_b_agenthub] **EmployeeShbaek** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
31. [phase_b_agenthub] **EmployeeShbaek** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
32. [phase_b_docutil] **AdminDev** | DU-B2-Chat → 채팅 input 미발견, path=/chat
33. [phase_b_docutil] **EmployeeHslee** | DU-B2-Chat → 채팅 input 미발견, path=/chat
34. [phase_b_docutil] **EmployeeShbaek** | DU-B2-Chat → 채팅 input 미발견, path=/chat

## 산출물

- 매트릭스: `tools/ui_e2e/full/track99_5step_e2e_results.json`
- 스크린샷: `tools/ui_e2e/screenshots/track99_5step/` (SuperAdmin 만)
- storage_state: `tools/ui_e2e/full/_state_track99_*.json` (gitignore 대상)