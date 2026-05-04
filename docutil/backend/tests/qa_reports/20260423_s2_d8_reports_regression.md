# Phase 4 S2 D8 — /reports 회귀 테스트 리포트

> **작성일**: 2026-04-23
> **작성자**: sdet-agent
> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.2 S2 D8 (line 111),
> `docs/phase4_s2_d6_alembic_008_skip_rationale.md`
> **대상**: `backend/app/modules/reports/router.py` — S2 D6 이후 archive 읽기
> 전용 전환이 후속 기능(FE 변경, /v2/documents 활성 경로) 과 충돌 없이
> 유지되는지 백엔드 레벨에서 검증

---

## 0. 요약

- **테스트 케이스**: 기존 9건 → **26건** (+17건 신규 추가)
- **실행 결과**: **26 passed / 0 failed** (5.5 초)
- **광역 회귀**: `test_reports.py` + `test_documents_v2*.py` + `test_document_builders_*.py`
  합본 **190 passed / 0 failed** (13.5 초)
- **Ruff**: `All checks passed!` (I001 Auto-fix 후 깨끗)
- **발견 이슈**: 없음 (410/헤더/401/독립성 모두 설계대로 동작)

---

## 1. 테스트 파일 변경 사항

| 파일 | 변경 유형 | 라인 수 (대략) |
|---|---|---|
| `backend/tests/test_reports.py` | 확장 (append only) | +493 lines (기존 293 → 786) |

D8 신규 케이스는 "Phase 4 S2 D8 — SDET 회귀 테스트 확장" 블록 (`# =======` 헤더
기준 test_reports.py 라인 296~786) 에 집중 배치해 기존 D6 테스트와 명확히 분리
했다. 공용 헬퍼 `_assert_gone()` / `_assert_deprecated_header()` 두 개를 추가해
동일 조건 반복 검증을 DRY 하게 처리했다.

---

## 2. 카테고리별 신규 케이스 (17건)

### 2.1 410 Gone 쓰기 경로 — 변형 입력 (6건)

| # | 테스트 | 의도 |
|---|---|---|
| D8-1 | `test_delete_report_with_nonexistent_id_returns_410_gone` | 존재하지 않는 id DELETE → 404 대신 410 선행 |
| D8-2 | `test_create_template_with_minimal_form_returns_410_gone` | 파일 없이 form 만 보내도 422 대신 410 |
| D8-3 | `test_generate_report_with_empty_body_returns_410_gone` | 최소 body 로도 410 (Pydantic 422 보다 우선) |
| D8-4 | `test_update_template_with_empty_payload_returns_410_gone` | 빈 JSON 도 410 |
| D8-5 | `test_delete_template_with_nonexistent_id_returns_410_gone` | 존재하지 않는 template id → 410 선행 |
| D8-6 | `test_generate_report_410_response_detail_is_korean` | detail 한국어 키워드 3종 검증 (`/v2/documents`, `디자이너`, `/designer/create`) |

모든 케이스에서 서비스 메서드(`generate_report`/`create_template`/`update_template`/`delete_template`/`delete_report`/`get_report`/`get_template`) 가 호출되지 않음을 `assert_not_called()` 로 확인.

### 2.2 archive 읽기 경로 생존 (5건)

| # | 테스트 | 의도 |
|---|---|---|
| D8-7 | `test_get_template_by_id_returns_deprecated_header` | GET /reports/templates/{id} 200 + X-Deprecated-API |
| D8-8 | `test_get_template_by_id_returns_404_when_missing` | 없는 template id → 404 매핑 정상 |
| D8-9 | `test_get_report_returns_404_when_missing` | 없는 report id → 404 매핑 정상 |
| D8-10 | `test_list_reports_with_pagination_returns_deprecated_header` | page/size 파라미터와 함께 조회해도 헤더 유지 |
| D8-11 | `test_download_report_returns_rfc5987_encoded_filename` | 한글 파일명 RFC 5987 인코딩 + deprecated 헤더 + 본문 바이트 |

한글 파일명 검증은 CLAUDE.md Critical Rules("Korean filenames: always use RFC 5987 encoding") 와 직결되는 회귀 방어선.

### 2.3 /reports ↔ /v2/documents 독립성 (3건)

| # | 테스트 | 의도 |
|---|---|---|
| D8-12 | `test_v2_documents_post_still_works_when_reports_is_deprecated` | Mode A POST 202 + deprecated 헤더 **없음** 확인 |
| D8-13 | `test_v2_documents_get_still_works_when_reports_is_deprecated` | GET /v2/documents/{id} 200 + deprecated 헤더 **없음** |
| D8-14 | `test_reports_write_block_does_not_block_v2_documents_post` | 동일 세션에서 순차 호출 시 상호 독립 (410 → 202 흐름 정상) |

`/v2/documents` 응답에 `X-Deprecated-API` 가 들어가지 않음을 명시적으로 검증해
"잘못된 헤더 오염" 회귀를 잡는다.

### 2.4 인증/권한 교차 확인 (3건)

| # | 테스트 | 의도 |
|---|---|---|
| D8-15 | `test_unauthenticated_generate_report_returns_401_before_410` | 미인증 POST → 410 이 아니라 401 이 먼저 |
| D8-16 | `test_unauthenticated_delete_report_returns_401_before_410` | 미인증 DELETE → 401 선행 |
| D8-17 | `test_unauthenticated_list_reports_returns_401` | 미인증 읽기 경로도 archive 데이터 노출 차단 |

`unauth_client` fixture (JWT 없이 앱에 직접 연결) 를 재사용해 의존성 순서를 검증.
이는 "readonly archive 가 무인증 노출" 같은 잠재 regression 을 사전에 차단한다.

---

## 3. 실행 결과

### 3.1 test_reports.py 단독

```
collected 26 items

tests/test_reports.py ..........................            [100%]
======================= 26 passed, 3 warnings in 5.53s =======================
```

PASS/FAIL 분포:
- 410 Gone (쓰기 5+6=11): **11 PASS**
- archive 읽기 (GET/LIST/DOWNLOAD 4+5=9): **9 PASS**
- 독립성 (v2/documents 교차 3): **3 PASS**
- 인증 (401 우선 3): **3 PASS**
- **합계: 26 PASS / 0 FAIL** (기존 9건 + 신규 17건)

### 3.2 광역 회귀 (reports + documents_v2 + document_builders)

```
tests/test_reports.py                    26 ... [ 13%]
tests/test_documents_v2.py               25 ... [ 26%]
tests/test_documents_v2_router.py        13 ... [ 33%]
tests/test_documents_v2_service.py       20 ... [ 44%]
tests/test_documents_v2_schemas.py       19 ... [ 54%]
tests/test_documents_v2_patch.py         23 ... [ 66%]
tests/test_documents_v2_export.py        14 ... [ 73%]
tests/test_document_builders_base.py     10 ... [ 78%]
tests/test_document_builders_pptx.py     40 ... [100%]

====================== 190 passed, 3 warnings in 13.46s =======================
```

**/reports 변경이 인접 모듈 (documents_v2 + builders) 어느 테스트도 파괴하지
않음을 확인.** 190건 모두 녹색.

### 3.3 Ruff

```
cd backend && python -m ruff check tests/test_reports.py
All checks passed!
```

신규 추가분에서 I001 (import 정렬) 3건이 있었으나 `ruff --fix` 자동 수정으로
정리 완료.

---

## 4. 회귀 리포트 요약

1. S2 D6 의 410 Gone 차단 설계가 **비정상 id, 빈 payload, 파일 없음, 인증 없음**
   같은 변형 입력에서도 일관되게 동작함을 17 건 신규 케이스로 확증.
2. archive 읽기 4종 (`GET /reports`, `GET /reports/{id}`, `GET /reports/templates`,
   `GET /reports/templates/{id}`, `GET /reports/{id}/download`) 은 모두 200 + `X-Deprecated-API: true`
   헤더를 정확히 내려보낸다.
3. `/v2/documents` 활성 경로는 `/reports` 전환 영향을 받지 않음 (202 + 헤더 비포함).
4. 미인증 요청은 410 보다 401 이 우선 반환되어 FE 로그인 리디렉션 UX 가 보존
   된다. 이는 readonly archive 가 무인증 노출되지 않도록 추가 방어선 역할도 한다.
5. 광역 회귀(190건) 전량 PASS — D6 BE · D7 FE · D8 SDET 조합으로 이관 설계가
   프로덕션 품질 기준을 충족함을 보인다.

---

## 5. S2 D9/D10 QA 권고

1. **D9 `slide_report` E2E**: Mode A 프롬프트 → PPTX 다운로드 시연 시,
   `/reports` 레거시 경로가 혹시 호출되는지 네트워크 로그로 **절대 호출되지 않음**
   을 확인. 호출되면 즉시 410 에 걸려 시연이 멈추므로 조기 탐지 효과.
2. **D10 qa_quick 임계값**: `test_reports.py` 9 → 26 건으로 확장된 만큼,
   qa_quick 소요 시간 상승분(약 +1.5 초) 은 무시 가능. 그러나 qa.sh 전체 합산 시
   `test_reports.py` 가 핵심 모듈로 승격되었으므로 리포트 카테고리 가중치 조정 검토.
3. **파일 다운로드 경로 실사용 검증 (D10)**: `test_download_report_returns_rfc5987_encoded_filename`
   은 라우터 mock 수준 검증. 실제 MinIO 에서 한글 파일명으로 저장된 archive 보고서
   한 건을 대상으로 Playwright 등을 통한 브라우저 다운로드 테스트를 D10 E2E 에
   1건만 포함하면 RFC 5987 계약이 엔드투엔드로 보장된다.
4. **헤더 회귀 테스트 확대 (S3 이후)**: `X-Deprecated-API` 는 본 리포트 범위
   내 5 개 읽기 경로에서 검증됐지만, S3 에서 새 읽기 엔드포인트 추가 시
   `_assert_deprecated_header` 헬퍼를 재사용한 새 케이스 추가를 체크리스트화.

---

## 6. 블로커 / 미해결

- **블로커**: 없음.
- **미해결**: 없음.
- **주의 (향후)**: S7 에서 `/reports` 모듈 전체 삭제 시, 본 파일 (`test_reports.py`) 도
  동반 삭제되어야 하며, 그 전까지는 본 테스트 스위트가 "archive 읽기 전용이 유지
  되는지" 를 지속 감시한다. S7 착수 PR 에 삭제 체크리스트로 반영 권장.

---

## 7. 근거 파일 경로 (상대)

- 테스트 파일: `backend/tests/test_reports.py` (확장)
- 회귀 대상 라우터: `backend/app/modules/reports/router.py`
- 회귀 대상 ORM: `backend/app/modules/reports/models.py` (`tb_generated_reports_archive`)
- 교차 검증 대상: `backend/app/modules/documents_v2/router.py`
- 프로젝트 규약: `CLAUDE.md`, `.claude/rules/testing.md`, `.claude/rules/architecture.md`
- 설계 문서: `docs/phase3_execution_roadmap.md` §2.2 S2 D8,
  `docs/phase4_s2_d6_alembic_008_skip_rationale.md` §2
