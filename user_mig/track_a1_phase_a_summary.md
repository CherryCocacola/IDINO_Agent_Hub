# 트랙 A1 Phase A — AgentHub 13 admin/docutil-* 회귀 spot check

- 실행일시: 2026-05-25T23:37:55
- base: http://192.168.10.39:64005
- 매트릭스: 4 계정 × 13 화면 = **52 cell**
- 결과: **PASS 52 / FAIL 0 / SKIP 0**

## 계정별 요약

| 계정 | role | expected | PASS | FAIL | SKIP |
|---|---|---|---:|---:|---:|
| SuperAdmin | Admin,SuperAdmin | 200 | 13 | 0 | 0 |
| UserLegacy | User | 401/403 | 13 | 0 | 0 |
| EmployeeHslee | User | 401/403 | 13 | 0 | 0 |
| EmployeeShbaek | Admin | 200 | 13 | 0 | 0 |

## FAIL 없음 — 전 매트릭스 PASS

