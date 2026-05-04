# Phase 4 S1 D7 완료 보고서

- 작성일: 2026-04-19
- 범위: router.py 구축 + 실 LLM API 교차 검증 (Full C 옵션)

## Part 1 — router.py 구축

### 신규/수정 파일

| 경로 | 상태 | 요약 |
|------|------|------|
| `backend/app/modules/documents_v2/router.py` | 신규 | FastAPI 라우터 4 엔드포인트 |
| `backend/app/modules/documents_v2/schemas.py` | 확장 | `GenerateDocumentRequest`, `DocumentV2Response`, `PaginatedDocumentListResponse`, `PartialDocumentPatch` 추가 |
| `backend/app/main.py` | 수정 | `documents_v2_router` 등록 + `documents_v2.models` import |
| `backend/pyproject.toml` | 수정 | `live_api` 마커 등록 |
| `backend/tests/test_documents_v2_router.py` | 신규 | 13건 테스트 (mock 기반) |

### 엔드포인트 계약

| 메서드 | 경로 | Status | 설명 |
|--------|------|--------|------|
| POST | `/api/v1/v2/documents` | 202 | Mode A 자유 생성 |
| GET | `/api/v1/v2/documents` | 200 | 조직 범위 목록 조회 (limit/offset/document_type/mode) |
| GET | `/api/v1/v2/documents/{id}` | 200 | 단건 조회 (404/403) |
| PATCH | `/api/v1/v2/documents/{id}` | 501 | D7 스텁 (D8 본구현) |

### 예외 → HTTP 매핑

| 예외 | HTTP | 사유 |
|------|------|------|
| `RAGContextError` | 503 | Qdrant/DB 외부 실패 (재시도 가능) |
| `DocumentSchemaValidationError` | 422 | LLM 응답 검증 실패 |
| `DocumentGenerationError` (에이전트 찾을 수 없음) | 404 | agent_id 미존재 |
| `DocumentGenerationError` (타 조직 에이전트) | 403 | 권한 위반 |
| `DocumentGenerationError` (지원하지 않는 타입) | 400 | 입력 검증 |
| `DocumentGenerationError` (LLM 호출 실패) | 502 | 외부 LLM 실패 |

### 테스트 결과

```
tests/test_documents_v2_router.py        13 passed
tests/test_documents_v2_service.py       (기존)
tests/test_documents_v2_schemas.py       (기존)
tests/test_html_renderer.py              (기존)
tests/test_document_builders_base.py     (기존)
tests/test_llm_structured_cross_provider.py (기존 30)
-----------------------------------------------------
총                                       106 passed
```

목표 105+ 대비 **106 PASS** 달성.

### 린트

```
ruff check app/modules/documents_v2/router.py
ruff check tests/test_documents_v2_router.py
ruff check tests/test_llm_live_providers.py
→ All checks passed
```

`schemas.py` 의 사전 존재 TC003/UP037 경고는 Phase 1 원본 디자인 영역으로 본 D7 범위 외. Phase 1 설계 수정 금지 원칙에 따라 그대로 유지.

### 사전 존재 실패 (D7 범위 밖)

```
test_projects.py  3 fail — ProjectDepartmentService attribute 누락
test_users.py     5 fail — /api/v1/users 경로 404
```

이전 커밋 시점에 이미 실패하던 테스트로, documents_v2 변경과 무관함. 별도 이슈로 기록.

## Part 2 — 실 API 교차 검증 결과 (요약)

상세 내용은 `docs/r1_live_provider_verification.md` 참조.

### 실 호출 현황

| provider | 실행 | 비용 |
|----------|------|------|
| openai (gpt-4o) | 8 회 | $0.15 |
| azure_openai | 0 회 | - |
| gemini | 0 회 | - |
| anthropic | 0 회 | - |
| **Total** | **8 회** | **$0.15** |

**제약 사항**: 서버 환경에 `OPENAI_API_KEY` 만 설정되어 있고 Azure / Gemini / Anthropic 은 env / DB 모두에서 누락. 4-provider 교차 검증은 **환경 한계로 OpenAI 로 한정**.

### 주요 발견 요약

1. **D5 `pydantic_to_openai_schema` strict=true 모드 결함** — OpenAI strict 요구사항 (`required` 에 모든 properties 키) 미충족으로 400 Bad Request. 실 API 에서만 재현 (mock 30 PASS 가 이 결함을 놓침).
2. **LLM document_id UUID 실패** — `doc_001` 같은 비 UUID 응답. 서비스 `_apply_metadata_overrides` 가 덮어쓰므로 production 영향 없음.
3. **D6 프롬프트 ISO-8601 규정 부재** — `ActionItem.due` 에 `"2023년 10월 27일"` 생성.
4. **페이지 수 가이드 미준수** — minutes 가 4~6 페이지 생성 (안건별 분리 경향).
5. **조건부 필수 컴포넌트 누락** — proposal 에서 RiskMatrix 대신 BulletList.
6. **OpenAI TPM 30,000 레이트 리밋** — 연속 호출 시 429.

### R1 최종 판정

**PARTIAL PASS (openai only)**

- OpenAI: strict 모드 결함 수정 + 프롬프트 개선 후 production 사용 가능.
- Azure / Gemini / Anthropic: live 검증 **BLOCKED** (API 키 필요). 기존 D5 mock 30 PASS 는 유효.

## D8 선행조건 충족 여부

| 항목 | 상태 | 비고 |
|------|------|------|
| POST/GET/LIST 엔드포인트 | ✅ | 13건 테스트 PASS |
| PATCH 스키마 (`PartialDocumentPatch`) | ✅ | D8 본구현 대기 |
| 예외 매핑 체계 | ✅ | 401/403/404/422/502/503 매핑 완료 |
| 조직 스코프 보호 | ✅ | SQL 레벨 `WHERE organization_id` |
| 실 LLM API 기반 품질 보증 | ⚠️ | OpenAI 부분 검증. strict 결함 수정 필요 |

**D8 진행 권고**: 아래 선결 조건 후 착수.

1. **[Blocker]** `pydantic_to_openai_schema` strict 결함 수정 (D5 영역 수정 불가피).
2. **[Required]** `constants.py` § 4·5 프롬프트 권고 반영.
3. **[Recommended]** Azure / Gemini / Anthropic API 키 확보 후 교차 재검증.

## 산출물

- `backend/app/modules/documents_v2/router.py` (신규)
- `backend/app/modules/documents_v2/schemas.py` (확장)
- `backend/tests/test_documents_v2_router.py` (신규, 13건 PASS)
- `backend/tests/test_llm_live_providers.py` (신규, live_api 마커)
- `scripts/run_s1_d7_live_api.py` (서버 실행 자동화)
- `backend/tests/qa_reports/20260421_s1_d7_live_api_metrics.json` (raw 데이터)
- `backend/tests/qa_reports/20260421_s1_d7_live_api_report.md` (메트릭 요약)
- `docs/r1_live_provider_verification.md` (상세 분석)
- `docs/phase4_s1_d7_completion_report.md` (본 문서)
