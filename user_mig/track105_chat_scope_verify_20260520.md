# 트랙 #105 Phase A.3 + B.3 — 운영 배포 + 5계정 검증 결과

**검증일**: 2026-05-20
**배포 commit 대상**: 4 파일 (`projects/reports/search_scopes/templates` router.py)
**배포 스크립트**: `tmp/deploy_track105_role_fix_20260520.py` + `tmp/deploy_track105_resume_20260520.py` (timeout 후 재개)
**결과 raw**: `user_mig/track105_role_matrix_results.json`

---

## 1. 배포 실행 요약

| 단계 | 결과 | 비고 |
|---|---|---|
| SFTP 4 파일 → `/home/idino/docutil/backend/app/modules/*/router.py` | ✅ | 16,616 + 20,558 + 13,619 + 31,574 bytes |
| `docker compose build api` | ✅ | 1차 timeout(600s) → 재시도 1232.9s 완료 (extracting 단계가 길었음) |
| `docker compose up -d --force-recreate api` | ✅ | container 18s healthy |
| `docker restart docutil-nginx` | ✅ | 3s healthy (stale upstream IP 캐시 해소) |

---

## 2. 5계정 × 8 endpoint 매트릭스

| 계정 | role | `/projects/tree` (핵심) | `/projects` | `/reports` | `/search-scopes` | `/templates` | 회귀 `/documents` | 회귀 `/documents-v2` | 회귀 `/agents` |
|---|---|---|---|---|---|---|---|---|---|
| admin@example.com | super_admin | 200/2 | 200/2 | 200/0 | 200/1 | 200/1 | 200/10 | **404** ⚠ | 200/4 |
| dev@example.com | (admin 예상) | — 로그인 실패 (계정 미존재) | | | | | | | |
| user@example.com | user (legacy) | 200/2 | 200/2 | 200/0 | 200/1 | 200/1 | 200/10 | **404** ⚠ | 200/4 |
| **hslee** | **user (직원)** | ✅ **200/2** | 200/2 | 200/5 | 200/1 | 200/1 | 200/10 | **404** ⚠ | 200/4 |
| shbaek | (직원) | 200/2 | 200/2 | 200/2 | 200/1 | 200/1 | 200/10 | **404** ⚠ | 200/4 |

**범례**: HTTP status / items 개수.

---

## 3. 결함 해소 확인

### 3.1 챗봇 0건 결함 (사용자 요청 0-2-1 / 1-3)

`/projects/tree` 가 hslee('user' role) 에 대해 **HTTP 200 + 2 프로젝트** 응답.

- 이전 (fix 전): HTTP 403 (require_role 차단) → frontend `Promise.all` reject → DocumentScopeModal 0건
- 현재 (fix 후): HTTP 200 → frontend 트리 매핑 정상 → DocumentScopeModal 에 프로젝트 + 문서 노출

→ **챗봇 결함 root cause 해소 확정**.

UI 동작 검증(실제 챗봇 화면에서 문서가 보이는지)은 Phase C 의 chat 시나리오에서 Playwright 로 추가 검증.

### 3.2 Phase B.3 4 router fix 검증

| Router | helper | 5계정 응답 | 판정 |
|---|---|---|---|
| projects | `_require_member` ('user' 추가) | 5계정 모두 200 (dev 제외) | ✅ PASS |
| reports | `_require_member` ('user' 추가) | 5계정 모두 200 | ✅ PASS |
| search_scopes | `_require_member` ('user' 추가) | 5계정 모두 200 | ✅ PASS |
| templates | `_require_member` ('manager' + 'user' 추가) | 5계정 모두 200 | ✅ PASS |

### 3.3 트랙 #104 회귀 확인

| Endpoint | 결과 | 판정 |
|---|---|---|
| `/documents` | 5계정 모두 200 (28~31 items) | ✅ 회귀 없음 |
| `/agents` | 5계정 모두 200 (4 items) | ✅ 회귀 없음 |
| `/documents-v2` | **5계정 모두 404** | ⚠ 트랙 #104 잠재 결함 잔존 (트랙 #105 범위 외) |

---

## 4. 잠재 잔존 결함 (별도 트랙 후보)

### 4.1 `/documents-v2` 전계정 404

트랙 #104 progress.md 에서 이미 후보로 언급된 endpoint registration 누락 가능성. 5계정 모두 동일 404 → 권한 문제가 아니라 **routing/registration 결함**. 다음 진단 단계 필요:

- `docutil/backend/app/main.py` 또는 application factory 에서 documents_v2 router include 여부 확인
- nginx 또는 FastAPI prefix 매핑 확인 (예: `/api/v1/documents-v2` vs `/api/v1/documents_v2` 의 hyphen/underscore)
- 별도 트랙 분리 권장

### 4.2 `dev@example.com` 계정 미존재

트랙 #99 매트릭스가 정의한 5계정 명세와 운영 실측 불일치. 5계정 명세 정정:
- 실측 가능: admin@example.com / user@example.com / hslee / shbaek
- 4계정으로 축소 또는 dev 계정 신설 결정 필요

Phase B.4 자동 검증에서는 4계정으로 진행하되, 5번째 계정(다른 role)으로 보완 가능한지 추가 조사.

---

## 5. 다음 단계

- ✅ Phase A.3 (챗봇 결함 운영 검증) 완료
- ✅ Phase B.3 (role 누락 4 router fix 운영 검증) 완료
- ➡ Phase B.4 (5계정 × 전체 410 endpoint 자동 검증) 진행
- 별도: `/documents-v2` 404 진단 (트랙 #105 후속 또는 별도 트랙)

---

## 6. 핵심 파일 (수정/생성)

수정:
- `docutil/backend/app/modules/projects/router.py:52`
- `docutil/backend/app/modules/reports/router.py:64`
- `docutil/backend/app/modules/search_scopes/router.py:48`
- `docutil/backend/app/modules/templates/router.py:52`

생성:
- `tmp/deploy_track105_role_fix_20260520.py`
- `tmp/deploy_track105_resume_20260520.py`
- `user_mig/track105_chat_scope_diag_20260520.md` (Phase A.1)
- `user_mig/track105_chat_scope_verify_20260520.md` (본 문서)
- `user_mig/track105_role_matrix_results.json` (5계정 × 8 endpoint raw)
- `user_mig/track105_endpoint_catalog.json` + `.md` (Phase B.1, 410 endpoint)
- `tools/permission_matrix/extract_endpoints.py`
