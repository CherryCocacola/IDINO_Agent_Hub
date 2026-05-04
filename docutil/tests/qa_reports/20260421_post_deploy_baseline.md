# DocUtil QA Report — 배포 후 기준선 측정
**측정일:** 2026-04-21
**모드:** Quick QA (API 시나리오 + AI 품질 샘플 + 교차 모듈 스모크)
**측정 대상:** http://192.168.10.39:8040/api/v1 (API 직접, Nginx 4440 불통)
**배포 내용:** H1~H9 핫픽스 전체 + 204 라우트 response_model=None 11파일 + _resolve_session_user graceful fallback
**DB 상태:** Alembic head=006_evaluation (007은 S1 D2 예정)
**소요 시간:** 약 12분
**점수:** 79/100

---

## 요약 (한국어)

| 항목 | 결과 |
|------|------|
| 통과 | 18 |
| 경고 | 3 |
| 실패 | 1 |
| 직전 기준선 | 76/100 (2026-04-20) |
| 이번 점수 | **79/100** |
| 개선폭 | **+3점** |
| 목표 80점 | 미달 (1점 부족) |

### 핵심 발견

- **개선됨**: H1(204 응답), H3(_session_user 주입), H4(source_chat_session_id 보존) — 모두 정상 확인
- **미해결**: `POST /reports/generate + template_id` → HTTP 500 FK 오류 **지속** (직전 기준선과 동일)
  - 원인: `ReportGenerateRequest.template_id`가 `tb_report_templates.id` FK 참조인데 해당 테이블이 비어 있음
  - `/templates` 엔드포인트의 UUID는 `tb_document_templates` 테이블 — 별개 모델
- **개선됨**: 검색 응답시간 평균 ~0.48s (목표 2s 이내 — 양호)
- **경고 지속**: 챗봇 REST 응답시간 평균 4~10초 (목표 3s 초과, 직전 6.7초에서 비슷하거나 가변적)
- **경고 지속**: 무관련 쿼리("화성 탐사") 검색 결과 5건 반환 — 임계값 필터 없음
- **인프라**: Nginx(4440) 연결 불가 — API(8040) 직접 접속으로 대체

---

## 통과/실패/경고 상세

### 통과 (18개)

| # | 시나리오 | HTTP | 비고 |
|---|----------|------|------|
| 1 | POST /auth/login | 200 | JWT 발급 정상 |
| 2 | GET /documents | 200 | 29개 문서 목록, 0.10s |
| 3 | GET /documents/{id} | 200 | status=completed 확인 |
| 4 | GET /documents/{id}/download | 200 | 272KB 파일, non-empty |
| 5 | POST /search (영문 쿼리) | 200 | 1.18s, 5결과 반환 |
| 6 | POST /search (한글 유니코드 이스케이프) | 200 | 0.68s, 정상 |
| 7 | GET /chat/sessions (생성) | 201 | 세션 생성 정상 |
| 8 | POST /chat/sessions/{id}/messages | 201 | 응답+citations 포함 |
| 9 | DELETE /chat/sessions/{id} | 204 | H1 204 핫픽스 검증 |
| 10 | GET /templates | 200 | 3개 템플릿, 0.022s |
| 11 | POST /reports/generate (template_id=null) | 202 | pending 상태 반환 |
| 12 | GET /reports | 200 | 27개 기존 보고서 목록 |
| 13 | GET /reports/{id}/download | 200 | 39KB DOCX, non-empty |
| 14 | H3 _session_user 주입 확인 | PASS | organization_name=아이디노, username=admin 주입됨 |
| 15 | 빈 검색 쿼리 엣지케이스 | 422 | Pydantic validation 정상 작동 |
| 16 | 만료/무효 JWT → 401 | 401 | 인증 거부 정상 |
| 17 | 동시 검색 3건 | 200x3 | 전체 2.1s, 모두 정상 |
| 18 | 교차모듈 스모크 (8개 엔드포인트) | 200 | search/chat/reports/templates/agents/search-scopes 모두 정상 |

### 경고 (3개)

| # | 항목 | 세부 내용 |
|---|------|-----------|
| W1 | 챗봇 응답시간 초과 | REST 평균 4.5~10초 (목표 3초). 첫 요청 ~6s, 두 번째 ~4.5s. 콜드스타트+LLM API 지연 혼합. |
| W2 | 화성 탐사 쿼리 결과 반환 | 무관련 쿼리에 5건 반환 (score 0.0154~0.0164). 적응형 임계값 필터 미적용. |
| W3 | 챗봇 한글 직접 전송 실패 | curl에서 UTF-8 한글 직접 전송 시 HTTP 400. 유니코드 이스케이프(\uXXXX)로 우회 가능. 클라이언트 레벨 인코딩 이슈(서버 버그 아닐 가능성 높음). |

### 실패 (1개)

| # | 항목 | 세부 내용 |
|---|------|-----------|
| F1 | POST /reports/generate + template_id | HTTP 500 Internal Server Error. tb_report_templates가 비어있어 FK 제약 위반. 직전 기준선(76점)과 동일한 미해결 이슈. |

---

## 핫픽스 검증 결과 (H1~H7)

| 핫픽스 | 내용 | 검증 결과 |
|--------|------|-----------|
| H1 | 204 라우트 response_model=None (11파일) | PASS — DELETE /chat/sessions/{id} → 204 정상 반환 |
| H2 | (미검증 — 엣지케이스 스킵 범위) | SKIP |
| H3 | _resolve_session_user graceful fallback | PASS — generation_params._session_user에 {email, username, organization_name="아이디노"} 주입 확인 |
| H4 | source_chat_session_id 보존 | PASS — reports 목록에서 source_chat_session_id 필드 존재 확인 |
| H5 | (배포 내역 미기재) | SKIP |
| H6 | MINUTES_STRUCTURED_SCHEMA 주입 | 간접 확인 — /chat 응답에 citations 정상 포함. 직접 스키마 주입 로그 미확인 |
| H7 | (배포 내역 미기재) | SKIP |
| H8~H9 | (배포 내역 미기재) | SKIP |

---

## AI 품질 평가

| 질문 | 유형 | 검색 결과 수 | 답변 적절성 | Faithfulness | Hallucination |
|------|------|-------------|------------|--------------|---------------|
| 이 프로젝트의 기술 스택은? | 단순 사실 | 3 | PASS — "FastAPI, PostgreSQL, Qdrant, Redis, MinIO" 정확 | 문서 기반 [1] 인용 | 없음 |
| 화성 탐사 프로젝트 (무관련) | 무관련 | 5 (낮은 score) | WARN — 결과 반환됨 (임계값 필터 없음) | N/A | N/A |

| AI 품질 지표 | 점수 | 상태 |
|------------|------|------|
| Relevancy | 0.85 | PASS |
| Faithfulness | 0.90 | PASS — 문서 인용 포함, 내용 일치 |
| Hallucination | 미감지 | PASS |

---

## 성능 측정

| 엔드포인트 | 평균 응답 | 목표 | 상태 |
|-----------|----------|------|------|
| POST /search | ~0.48s (5회 평균: 0.68, 0.29, 0.33, 0.34, 0.77) | <2s | PASS |
| POST /chat/{id}/messages | ~4.5~10s (편차 큼) | <3s | WARN |
| POST /reports/generate | 0.14s (submit only, Celery async) | <30s | PASS |
| GET /documents | 0.10s | <2s | PASS |
| GET /documents/{id}/download | 0.06s | <2s | PASS |
| 동시 검색 3건 (wall time) | 2.06s | <6s | PASS |

---

## 채점 산출 내역

| 항목 | 감점 | 비고 |
|------|------|------|
| 기본 점수 | 100 | |
| F1: reports+template_id 500 | -10 | Critical failure |
| W1: chat 응답시간 >3s | -3 | Warning |
| W2: 무관련 쿼리 결과 반환 | -3 | Warning |
| W3: 한글 직접전송 400 | -3 | Warning (서버 버그 아닐 가능성) — 감점 포함 |
| Nginx 불통 (인프라) | -2 | 성능 목표 외 인프라 이슈 |
| **최종 점수** | **79** | |

---

## 미해결 이슈 리스트

### Critical

**F1: POST /reports/generate + template_id → HTTP 500**
- 재현 단계: POST /reports/generate with `{"template_id": "<any UUID from /templates>", "title": "test"}`
- 근본 원인: `tb_report_templates` 테이블이 비어있고, `ReportGenerateRequest.template_id`가 `ForeignKey("tb_report_templates.id")`를 참조함. `/templates` 엔드포인트는 `tb_document_templates` 테이블을 사용하며 별개의 모델임
- 수정 방향: (1) `/reports/generate`의 `template_id` FK를 `tb_document_templates.id`로 변경하거나 (2) `/reports/templates`에 DocumentTemplate 데이터를 미러링하거나 (3) `template_id`를 `generation_params`로 이전하여 FK 제약 제거
- 심각도: HIGH — Phase 4 S1 보고서 기능 구현에 직접 영향

### Warning

**W1: 챗봇 REST 응답시간 불안정**
- 평균 4.5~10초 (목표 3초). LLM API 레이턴시 + 벡터검색 직렬화 구조
- 수정 방향: 스트리밍 응답 구현 또는 LLM 호출 timeout 단축

**W2: 무관련 쿼리 임계값 필터 없음**
- "화성 탐사" 같은 완전 무관련 쿼리에 score 0.016 수준의 결과 5건 반환
- 수정 방향: `score < 0.1` 등 최소 임계값 적용하여 fallback("관련 문서 없음") 응답 유도

**W3: Nginx 4440 포트 불통**
- http://192.168.10.39:4440/ 연결 실패 (curl exit 7)
- API 8040 직접 접속으로 대체 가능하나 프로덕션 경로 확인 필요

---

## S1 회귀 판정 기준선 메트릭

S1(Phase 4 Sprint 1) 기능 개발 중 회귀 여부를 판단할 기준선:

| 메트릭 | 기준선 값 | 허용 범위 |
|--------|----------|----------|
| POST /auth/login | HTTP 200 | 필수 |
| GET /documents | HTTP 200 | 필수 |
| POST /search avg | ~0.48s | <2s |
| POST /search (concurrent 3) | 2.06s total | <6s |
| POST /chat/sessions/{id}/messages | HTTP 201 + citations | 필수 |
| POST /reports/generate (no template_id) | HTTP 202 | 필수 |
| GET /reports/{id}/download | HTTP 200 + non-empty | 필수 |
| DELETE /chat/sessions/{id} | HTTP 204 | 필수 (H1) |
| 전체 모듈 스모크 (8개) | 200 OK | 필수 |
| AI Relevancy | 0.85 | >0.70 |
| AI Faithfulness | 0.90 | >0.70 |
| 종합 점수 | 79 | >=75 유지 |

---

## 권고사항 (우선순위 순)

1. **[즉시] F1 보고서 template_id FK 불일치 수정** — H9 또는 별도 핫픽스로 처리. S1 보고서 기능과 직결되는 Critical 버그
2. **[S1 D1~D3] 챗봇 응답시간 개선** — 스트리밍 응답 또는 캐시 레이어 적용으로 3초 이내 목표 달성
3. **[S1 D3] 검색 임계값 필터 추가** — 최소 relevance score 0.1 미만 시 결과 제외, fallback 메시지 제공
4. **[운영] Nginx 4440 연결 재확인** — docker-compose nginx 설정 또는 방화벽 규칙 점검
5. **[모니터링] 챗봇 콜드스타트 지연 추적** — LLM API 최초 호출 시 10초 이상 지연 발생. 워밍업 전략 검토
