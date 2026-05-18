# 트랙 #99 5단 e2e 매트릭스 — 2026-05-18 19:04:32 시작

- 종료: 2026-05-18 19:18:59
- 계정: SuperAdmin, AdminDev, User, EmployeeHslee, EmployeeShbaek

## 종합 PASS율

- 전체: 398/460 PASS (86%)
- FAIL: 12건
- SKIP: 50건

## Phase별 결과

| Phase | PASS | FAIL | SKIP |
|---|---|---|---|
| AgentHub Phase A (라우트 진입) | 282 | 3 | 0 |
| AgentHub Phase B (인터랙션) | 29 | 6 | 0 |
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

## 발견된 결함 (12건)

1. [phase_a_agenthub] **User** | /quota → 권한차단 미동작 — User 가 admin 페이지 진입
2. [phase_a_agenthub] **User** | /usage-history → 권한차단 미동작 — User 가 admin 페이지 진입
3. [phase_a_agenthub] **User** | /api-keys → 권한차단 미동작 — User 가 admin 페이지 진입
4. [phase_b_agenthub] **AdminDev** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
5. [phase_b_agenthub] **AdminDev** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
6. [phase_b_agenthub] **User** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
7. [phase_b_agenthub] **User** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
8. [phase_b_agenthub] **EmployeeHslee** | /users → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
9. [phase_b_agenthub] **EmployeeHslee** | /admin/docutil-departments → 리다이렉트됨 → / (권한 없음 또는 라우터 문제)
10. [phase_b_docutil] **AdminDev** | DU-B2-Chat → 채팅 input 미발견, path=/chat
11. [phase_b_docutil] **EmployeeHslee** | DU-B2-Chat → 채팅 input 미발견, path=/chat
12. [phase_b_docutil] **EmployeeShbaek** | DU-B2-Chat → 채팅 input 미발견, path=/chat

## 산출물

- 매트릭스: `tools/ui_e2e/full/track99_5step_e2e_results.json`
- 스크린샷: `tools/ui_e2e/screenshots/track99_5step/` (SuperAdmin 만)
- storage_state: `tools/ui_e2e/full/_state_track99_*.json` (gitignore 대상)