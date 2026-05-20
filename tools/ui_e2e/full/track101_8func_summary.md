# 트랙 #101 — DocUtil 운영자 8 기능 × 5계정 e2e 매트릭스

- 시작: 2026-05-19 12:49:51
- 종료: 2026-05-19 12:52:29
- e2e prefix: `e2e-t101-202605191249`
- 계정: SuperAdmin, AdminDev, User, EmployeeHslee, EmployeeShbaek

## 종합 결과

- 전체: 40/40 PASS (100%)
- SuperAdmin 8 기능: PASS=8 / FAIL=0 / SKIP=0
- Redirect Guards (4계정 × 8): PASS=32 / FAIL=0 / SKIP=0
- Cleanup 잔여: 0건

## storage_state

- **SuperAdmin**: ok=True, verify=RECREATED, source=재생성, note=localStorage already has token (ls=OK)
- **AdminDev**: ok=True, verify=RECREATED, source=재생성, note=localStorage already has token (ls=OK)
- **User**: ok=True, verify=RECREATED, source=재생성, note=localStorage already has token (ls=OK)
- **EmployeeHslee**: ok=True, verify=RECREATED, source=재생성, note=localStorage already has token (ls=OK)
- **EmployeeShbaek**: ok=True, verify=RECREATED, source=재생성, note=localStorage already has token (ls=OK)

## SuperAdmin 8 기능 결과

| 시나리오 | 결과 | Cleanup | Note |
|---|---|---|---|
| F1-DeptList | PASS | - | 발견 부서=['대표이사', '사업지원팀', '미래기술연구소', 'U-이노베이션본부', 'AI기술팀'], .list-group-item=10개 |
| F2-DeptCreate | PASS | done (DELETE by_id status=204, attempt=1) | 부서 생성 OK (post=[201], in_list=False) |
| F3-UserDeptAssign | PASS | done (restored deptId=None, status=200) | 부서 할당 OK (put=[200], user_id=ef5aa277-2ca0-4ab1-bd8f-41ef5e2540a5, orig_dept=None) |
| F4-UserProjectAssign | PASS | done (DELETE status=204) | 프로젝트 멤버 추가 OK (UI post=[201], target=admin@example.com, pid=c6955ce6-de61-4611-8eff-213c8101d82f) |
| F5-DeptMembersView | PASS | - | dept='대표이사', 멤버 키워드=True, 멤버 추가 버튼=True, 멤버/empty 영역=True |
| F6-ProjectMembersView | PASS | - | project='연구과제', 멤버 키워드=True, 멤버 추가 버튼=True, 멤버/empty 영역=True |
| F7-DocumentsFilterUI | PASS | - | pending=True, dept_label=True, proj_label=True, selects=3 |
| F8-ApiKeyCreateVerify | PASS | done (BFF DELETE status=204) | 키 발급+verify OK (post=[201], verify=[200]) |

## 4계정 × /admin/* Redirect 차단

| 시나리오 | 계정 | 결과 | Final URL | Note |
|---|---|---|---|---|
| F1-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F2-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F3-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F5-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F4-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F6-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F7-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F8-RedirectGuard | AdminDev | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F1-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F2-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F3-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F5-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F4-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F6-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F7-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F8-RedirectGuard | User | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F1-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F2-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F3-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F5-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F4-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F6-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F7-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F8-RedirectGuard | EmployeeHslee | PASS | http://192.168.10.39:64005/ | 비Admin 권한차단 OK → / |
| F1-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-departments | Admin 진입 OK (path 유지) |
| F2-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-departments | Admin 진입 OK (path 유지) |
| F3-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-departments | Admin 진입 OK (path 유지) |
| F5-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-departments | Admin 진입 OK (path 유지) |
| F4-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-projects | Admin 진입 OK (path 유지) |
| F6-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-projects | Admin 진입 OK (path 유지) |
| F7-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-documents-v2 | Admin 진입 OK (path 유지) |
| F8-RedirectGuard | EmployeeShbaek | PASS | http://192.168.10.39:64005/admin/docutil-api-keys | Admin 진입 OK (path 유지) |

## Cleanup 잔여 (운영자 회수 필요)

- 잔여 없음. 모든 mutation 회수 완료.

## 산출물

- 매트릭스: `tools/ui_e2e/full/track101_8func_e2e_results.json`
- 스크린샷: `tools/ui_e2e/screenshots/track101_8func/` (SuperAdmin 만)
- storage_state: `tools/ui_e2e/full/_state_track101_*.json` (gitignore 차단)