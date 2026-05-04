# DocUtil — Phase 3 실행 로드맵 (v1.0)

> **작성일**: 2026-04-20
> **작성자**: enterprise-architect (Claude Opus 4.7, 1M context)
> **상위 문서**: `docs/phase2_transition_plan.md` v1.1, `docs/phase1_decisions.md` v1.2, `docs/s0_inventory_report.md` v1.0, `docs/phase1_architecture.md` v1.6
> **하위 문서**: `docs/phase4_day1_checklist.md` (선택 발췌본)
> **상태**: Phase 4 착수 전 최종 실행 로드맵. Phase 4 Day 1 아침에 펼쳐 바로 실행 가능한 일 단위 체크리스트.

---

## 1. Executive Summary

Phase 3은 Phase 2 전환계획 v1.1을 **영업일 단위 작업 카드**로 분해하고, 각 스프린트에 QA 수용 기준, 배포·롤백 절차, 모니터링 포인트, 리스크 Watch List를 주입해 Phase 4 착수 당일부터 체크리스트만 소모하며 진행 가능한 상태를 만든다.

S0(조사)는 2026-04-20 완료됐다. Phase 4 실제 코드 변경은 S1부터 시작하며, S1~S7 합계 **68영업일(≈13.6주)** — Phase 2 v1.1의 14.6주 중 S0 0.6주를 소진한 잔여다. 롤백 트리거는 "QA <78 + P0/P1 ≥ 2건 동시 충족"으로 통일하고, 스프린트별 우회 플래그(feature flag)를 우선 사용해 전체 revert는 최후 수단으로 둔다.

핵심 산출:

1. **스프린트별 일 단위 WBS (S1~S7, 68영업일)**. Day 1부터 Day N까지 각 1줄 작업 카드 + 담당 에이전트 + 선행 의존성 + 산출물 명시 (§2).
2. **QA 게이트 상세 기준**. S1~S6 ≥80, S7 ≥90. 스프린트별 특화 회귀 세트(Mode 전환·HWPX 실기·회의록 Relevancy 0.75+). 성능 기준 P95 문서 생성 <30s, JSONB 조회 <100ms (§3).
3. **배포·롤백 전략**. `deploy_to_server.py` → MinIO 이미지 sed → Alembic → qa_quick.sh 고정 절차. 스프린트 말 `docutil-api:sN-stable` 이미지 태그 보관. 롤백은 Alembic downgrade + 이미지 되돌림 + feature flag off 3단 구조 (§4).
4. **모니터링·알림**. 신규 Prometheus 메트릭 **4종**, Grafana 대시보드 **3종**, Loki 로그 집계 4종, 알림 규칙 4종 (§5).
5. **Phase 4 Day 1 체크리스트 (§6, 14항목)**, 스프린트 간 전환 의식 6단계 (§7), 에이전트 조율 가이드 (§8), 리스크 Watch List **7종** + 스프린트별 트리거 지표 (§9).

---

## 2. 스프린트별 일 단위 WBS

### 2.0 공통 약속

- **영업일 기준**: 주말(토·일) 제외. 1주 = 5영업일.
- **담당 표기**: BE = backend-specialist, FE = frontend-specialist, DB = database-architect, RA = research-assistant, SDET = sdet-agent, EA = enterprise-architect.
- **산출물**: 파일 경로 또는 테스트/문서 명시.
- **선행**: 블로킹 의존성. 동일 Day에 병렬 가능한 작업은 선행 없음.

### 2.1 S1 — DocumentSchema MVP + 6 컴포넌트 (10영업일, 2주)

목표: Phase 1 skeleton을 end-to-end 동작 상태로 완성. Mode A 6-컴포넌트 문서 생성 → HTML 프리뷰 → Partial PATCH.

#### Week 1

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 (월) | DocumentSchema Pydantic 모델 최종 검증 + 6종 discriminated union 자동 테스트 | BE | S0 완료 | `tests/test_documents_v2_schemas.py` (10+ 케이스) |
| D1 (월) | `components/document-schema/components/` 6종 skeleton → 실제 렌더 (SlideTitle/Heading/Paragraph) 시작 | FE | S0 완료 | 3종 render props 확정 |
| D2 (화) | Alembic 007 서버 실제 적용 (NOT VALID → VALIDATE 2단계) + `tb_agents` CHECK 검증 | DB | D1 | 007 migration applied, head=007 |
| D2 (화) | BulletList/KPI/DataTable React 렌더 구현 | FE | D1 | 6/6 컴포넌트 렌더 완성 |
| D3 (수) | `DocumentBuilder` ABC + `BuilderRegistry` (B15, B21) | BE | D2 | `integrations/document_builders/base.py` |
| D3 (수) | `preview-pane/` iframe 구조 + postMessage 3종 (element-select, token-update, schema-patch-local) | FE | D2 | `components/document-designer/preview-pane/` |
| D4 (목) | `HtmlRenderer` (B16) + 6 컴포넌트 HTML 템플릿 | BE | D3 | `integrations/document_builders/html/renderer.py` |
| D4 (목) | `edit-sidebar/forms/` 6종 폼 컴포넌트 | FE | D3 | 6 form 파일 |
| D5 (금) | `LLMClient.generate_structured(schema)` 통일 인터페이스 (B13) + 4 프로바이더 교차 단위 테스트 | BE | D4 | `integrations/llm/client.py` 확장 |
| D5 (금) | `design-token-picker/` + `--doc-*` CSS 변수 시스템 | FE | D4 | 토큰 라이브 프리뷰 동작 |

**Week 1 마일스톤**: 6 컴포넌트 React 렌더 + Builder ABC + LLM 인터페이스 + iframe 구조.

#### Week 2

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 (월) | `modules/documents_v2/service.py::DocumentServiceV2.generate` Mode A 구현 + `build_rag_context` (B1-a 이관) | BE | D5 | Mode A 생성 로직 |
| D6 (월) | `prompt-box/` + `generateDocument()` API 호출 훅 | FE | D5 | `useDocumentMutation` |
| D7 (화) | `modules/documents_v2/router.py` POST /v2/documents + GET + PATCH 스텁 | BE | D6 | 3 엔드포인트 |
| D7 (화) | 3-provider(OpenAI/Azure/Gemini) Structured Output 교차 검증 (R1 선제 대응) | BE | D6 | 검증 보고서 (README 갱신) |
| D7 (화) | Claude provider 추가 테스트 (Tool Use 변환 경로) | BE | D7 오전 | 4/4 provider 통과 또는 StrictSchemaFallback 계획 수립 |
| D8 (수) | `PATCH /v2/documents/{id}` Partial DocumentSchema + `jsonb_set` | BE | D7 | PATCH 동작 |
| D8 (수) | `useDocument` / `useComponentRegeneration` 훅 구현 + iframe 메시지 리스너 | FE | D7 | 훅 3종 동작 |
| D9 (목) | `agentic_rag.py` 삭제 (B10) + import 무참조 재확인 | BE | D8 | git diff: 489줄 삭제 |
| D9 (목) | S1 end-to-end 시연: POST → GET → PATCH → HTML 프리뷰 확인 | BE+FE | D8 | 시연 녹화 또는 스크린샷 |
| D10 (금) | `sdet-agent` 테스트 커버리지 확장 (10+ 케이스) + `qa_quick.sh` 실행 80+ | SDET | D9 | `tests/test_documents_v2.py` + QA 리포트 |
| D10 (금) | S1 QA 게이트 통과 확인 + S2 킥오프 준비 | EA | D10 | S1 완료 선언 |

**Week 2 마일스톤 M1**: POST /v2/documents Mode A 6 컴포넌트 생성 → HTML 프리뷰 → PATCH 수정 → agentic_rag.py 삭제. QA ≥80.

**병행 가능**: BE(D1~D10) ∥ FE(D1~D10) — 인터페이스는 Phase 1 `documents-v2.ts` 시그니처로 lock.
**블로커**: S0 완료, 운영팀 MinIO 템플릿 3건 재업로드.
**Watch 리스크**: R1 (Multi-provider Structured Output).

---

### 2.2 S2 — PPTX 빌더 + Mode A PoC + archive 리네이밍 (10영업일, 2주)

목표: PPTX 포맷 end-to-end. IDINO 슬라이드마스터 + `layout_resolver` 런타임 매핑. `tb_generated_reports` → `_archive`.

#### Week 3

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | `PptxBuilder` 골격 (B17) + `_build_pptx_from_structured` 함수별 분해 시작 | BE | S1 완료 | `integrations/document_builders/pptx/builder.py` |
| D1 | `/reports` 상단 배너 "Mode A designer로 이동할까요?" | FE | S1 완료 | `app/(user)/reports/page.tsx` 수정 |
| D2 | `pptx/components.py` SlideTitle/Heading/Paragraph/BulletList 4종 이관 | BE | D1 | 4 컴포넌트 빌더 |
| D2 | `export-menu/` PPTX 다운로드 트리거 + 작업 상태 폴링 | FE | D1 | 다운로드 UX |
| D3 | `pptx/components.py` KPI/DataTable 이관 + 셀 스타일 적용 | BE | D2 | 6/6 PPTX 컴포넌트 |
| D3 | `pptx/layout_resolver.py` IDINO 마스터 실제 이름 ↔ enum 런타임 매핑 (B1-b 대체) | BE | D2 | layout_resolver 동작 |
| D4 | `workers/export_worker.py` 신규 — `BuilderRegistry.get(format).build(schema)` Celery 위임 | BE | D3 | 신규 worker |
| D4 | 진행 상태 폴링 엔드포인트 `GET /v2/documents/{id}/export/status` | BE | D4 오전 | status API |
| D5 | `POST /v2/documents/{id}/export?format=pptx` + MinIO 업로드 | BE | D4 | export 엔드포인트 |
| D5 | PPTX A/B 비교 리뷰 5건 샘플 준비 (기존 vs 신규) | EA | D5 | 5건 비교 파일 |

**Week 3 마일스톤**: PPTX 빌더 6종 + layout_resolver + export worker 완성.

#### Week 4

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 | `tb_generated_reports` → `_archive` 리네이밍 (Alembic 008, write-lock) | DB | D5 | 008 migration |
| D6 | Image 컴포넌트 PPTX 삽입 (`_add_image_to_slide` 재활용) | BE | D5 | Image 빌더 |
| D7 | Chart 컴포넌트 PPTX native (S3 의존 없이 S2에 조기 편입, 기본 바/라인만) | BE | D6 | Chart 기본 빌더 |
| D7 | archive 테이블 읽기 전용 View 생성 + UI "보관된 보고서" 탭 | FE | D6 | read-only UI |
| D8 | PPTX A/B 비교 리뷰 실시 (3명 리뷰어) + 개선점 수집 | EA+BE | D5 샘플 | 리뷰 결과 문서 |
| D8 | 기존 `/reports` 회귀 테스트 (Mode A 미사용 시 경로 생존 확인) | SDET | D7 | 회귀 리포트 |
| D9 | A/B 리뷰 피드백 반영 (IDINO 스타일 세부 튜닝) | BE | D8 | 반영된 builder |
| D9 | `slide_report` 타입 Mode A → PPTX 다운로드 end-to-end 시연 | BE+FE | D8 | 시연 자료 |
| D10 | S2 QA 실행 (qa_quick + Mode A E2E 3건) | SDET | D9 | QA 리포트 ≥80 |
| D10 | `docutil-api:s2-stable` 이미지 태그 + S3 킥오프 | EA | D10 | 태그 push + S3 착수 승인 |

**Week 4 마일스톤 M2 (일부)**: PPTX Mode A end-to-end + archive 리네이밍.

**병행 가능**: BE(빌더) ∥ FE(배너·export-menu·archive UI) ∥ DB(008 migration).
**블로커**: S1 완료.
**Watch 리스크**: R4 (PPTX 품질 체감 저하).

---

### 2.3 S3 — 컴포넌트 확장 + 이미지 자동 (10영업일, 2주)

목표: 7종 추가 컴포넌트(SlideSubtitle/Quote/Callout/Timeline/ImageGrid/IconRow + Chart 완성) + 이미지 자동 선택(DALL-E/Unsplash) + 월 쿼터 UI.

#### Week 5

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | Chart 컴포넌트 PPTX 고도화 + DOCX matplotlib PNG 준비 | BE | S2 완료 | Chart 확장 |
| D1 | SlideSubtitle/Quote React 렌더 + 폼 | FE | S2 완료 | 2 컴포넌트 |
| D2 | Callout/Timeline React 렌더 + 폼 | FE | D1 | 4/7 컴포넌트 |
| D2 | Image/ImageGrid PPTX + HTML 빌더 | BE | D1 | Image 빌더 |
| D3 | ImageGrid/IconRow React 렌더 + 폼 | FE | D2 | 6/7 컴포넌트 |
| D3 | Unsplash 우선 → DALL-E fallback 선택 알고리즘 | BE | D2 | `documents_v2/service.py` 이미지 선택 |
| D4 | Chart React 렌더 (Recharts) + 폼 | FE | D3 | 7/7 컴포넌트 |
| D4 | 조직별 월 DALL-E 쿼터 설정 모델 + `tb_organization_quotas` (Alembic 009) | DB | D3 | 009 migration |
| D5 | 이미지 선택 UI (URL/프롬프트/자동) + 쿼터 초과 시 403 한국어 메시지 | FE+BE | D4 | 이미지 UX 완성 |

#### Week 6

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 | SlideSubtitle/Quote/Callout PPTX 빌더 | BE | D5 | 3 PPTX 빌더 |
| D6 | 관리자 UI: 조직별 월 DALL-E 쿼터 설정 페이지 | FE | D5 | admin 페이지 |
| D7 | Timeline/IconRow PPTX 빌더 | BE | D6 | 2 PPTX 빌더 |
| D7 | 이미지 선택 시각화(자동 선택된 키워드 표시) | FE | D6 | UI 피드백 |
| D8 | 13 컴포넌트 end-to-end 시연 (6 + 7) | BE+FE | D7 | 시연 자료 |
| D8 | Chart + Image 자동 삽입 회귀 테스트 | SDET | D7 | 회귀 리포트 |
| D9 | S3 버그 수정 스프린트 (A/B 리뷰 피드백 반영) | BE+FE | D8 | 버그 수정 PR들 |
| D10 | S3 QA 실행 ≥80 + `docutil-api:s3-stable` 태그 | SDET+EA | D9 | QA 리포트 + 태그 |

**Week 6 마일스톤 M2 (완)**: 13 컴포넌트 end-to-end.

**병행 가능**: BE(PPTX 빌더) ∥ FE(React) ∥ DB(쿼터 migration). S4 초반(BE 다른 개발자)과 중복 가능.
**블로커**: S2 완료.
**Watch 리스크**: R9 (DALL-E 비용 — 쿼터로 1차 대응).

---

### 2.4 S4 — Mode B + Mode 전환 (12영업일, 2.5주)

목표 (v1.2 축소본): Mode B slot-fill + `POST /v2/documents/{id}/switch-mode` + `(admin)/template-designer/`. **조직별 배치 변환 스크립트 불요(S0 결과 반영)**. IDINO 활성 3건(Jinja2)만 skeleton 변환.

#### Week 7

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | `DocumentServiceV2.generate` Mode B (slot-fill 프롬프트, `locked=true` 영역 고정) | BE | S1+S2 완료 | Mode B 로직 |
| D1 | `(admin)/template-designer/create/page.tsx` 라우트 skeleton | FE | S1 완료 | admin 라우트 |
| D1 | `tb_documents_v2_templates` 초기 데이터 3건 수동 변환 설계 | DB | S0 | 변환 매핑 문서 |
| D2 | `LockedRegionError(422)` + 한국어 메시지 | BE | D1 | 에러 처리 |
| D2 | Shell 재사용 — `mode="template_authoring"` + `allow_lock_toggle=true` props | FE | D1 | Shell 확장 |
| D2 | IDINO 보고서_양식 수동 skeleton 변환 (Jinja2 → DocumentSchema) | DB | D1 | 1/3 변환 |
| D3 | `docx/jinja2_renderer.py` (B2-a 이관) Mode B docx 경로 | BE | D2 | jinja2_renderer |
| D3 | `edit-sidebar/forms/LockToggleForm.tsx` + `AnchorNameForm.tsx` | FE | D2 | 관리자 폼 2종 |
| D3 | IDINO 회의록_양식 + ppt_제안서_가로양식 수동 변환 | DB | D2 | 3/3 변환 |
| D4 | `POST /v2/documents/{id}/switch-mode` 엔드포인트 (Q3) | BE | D3 | switch-mode API |
| D4 | `(admin)/template-designer/[templateId]/page.tsx` 편집 라우트 | FE | D3 | 편집 라우트 |
| D5 | `ModeTransitionValidator` — 자유→템플릿 AI slot 매핑 (기존 Jinja2 slot 매칭 재활용) | BE | D4 | validator |
| D5 | `audit_logs`에 `mode_transition` 이벤트 타입 + 전/후 snapshot | BE | D4 | audit 확장 |

**Week 7 마일스톤**: Mode B 기본 + switch-mode API + admin 라우트.

#### Week 8

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 | `(user)/designer/`에 "Mode 전환" 드롭다운 + conflict_policy 선택 UI | FE | D5 | Mode 전환 UX |
| D6 | Mode B locked 컴포넌트 시각 구분 (자물쇠 + dim + aria-disabled) | FE | D5 | locked UX |
| D7 | TwoColumn/ThreeColumn React 레이아웃 컴포넌트 | FE | D6 | 2 레이아웃 |
| D7 | Hero/Comparison React 레이아웃 컴포넌트 | FE | D6 | 4/4 레이아웃 |
| D8 | TwoColumn/ThreeColumn PPTX 빌더 | BE | D7 | 2 PPTX 레이아웃 |
| D8 | Mode 전환 회귀 테스트 세트 초기 버전 (SDET 주도) | SDET | D7 | `test_mode_transition.py` 6+ 케이스 |
| D9 | Hero/Comparison PPTX 빌더 | BE | D8 | 4/4 PPTX 레이아웃 |
| D9 | Mode 전환 자동 매핑 실측 (IDINO 3건 대상) → 목표 85% 자동 + 15% 사용자 선택 | BE+SDET | D8 | 매핑 성공률 리포트 |

#### Week 9 (반주)

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D10 | Jinja2 양식 업로드 API read-only 전환 (B2-b 단계적 폐기) | BE | D9 | API 403 변경 |
| D10 | Mode 전환 회귀 세트 완성 (§3.2 기준 6항목 모두) | SDET | D9 | 회귀 테스트 통과 |
| D11 | S4 end-to-end 시연 (Mode A→B→A 전환) + `conflict_policy` 양쪽 확인 | BE+FE | D10 | 시연 자료 |
| D12 | S4 QA ≥80 + `docutil-api:s4-stable` 태그 + 리스크 재평가 | SDET+EA | D11 | QA + 태그 + Watch 갱신 |

**Week 9 마일스톤 M3**: Mode B + 전환 API + admin 라우트 + 17 컴포넌트/레이아웃 완성.

**병행 가능**: BE(Mode B/switch-mode) ∥ DB(template 변환) ∥ FE(admin 라우트/Mode 전환 UX). 3인 병렬 필수.
**블로커**: S1 + S2 완료. S0 완료. IDINO 3건 MinIO 재업로드.
**Watch 리스크**: U3 (Mode 전환 매핑), R6 (병존 유지보수).

---

### 2.5 S5 — HWPX 빌더 + hwp-extract + DOCX 완성 (10영업일, 2주)

목표: HwpxDocumentBuilder 12종 + 스타일·폰트까지(Q7, 색상 배제) + hwp-extract 통합 + DOCX 빌더 22/22.

#### Week 9~10 (S4 말 병렬 / 뒤이어)

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | `integrations/document_builders/hwpx/builder.py` 골격 (B19) + `_to_bytes()` 임시파일 경유(방법 A) | RA+BE | S2 완료 | HwpxBuilder skeleton |
| D1 | IDINO_제목1/2/3 스타일 등록 테스트 (빈 문서 한컴 2020 열기) | RA | D1 오전 | 한컴 열기 확인 |
| D2 | `hwpx/components.py` SlideTitle/Heading/Paragraph 빌더 | RA | D1 | 3 빌더 |
| D2 | BulletList/DataTable 빌더 | RA | D2 오전 | 5/12 빌더 |
| D3 | Image `<hp:pic>` lxml 수동 wrapper | RA | D2 | Image 빌더 |
| D3 | Quote/TwoColumn/ThreeColumn 빌더 | RA | D2 | 9/12 빌더 |
| D4 | Hero/Comparison/ImageGrid 빌더 (degraded_components 기록 포함) | RA | D3 | 12/12 빌더 |
| D4 | hwp-extract 통합 (`integrations/docling/hwp_extract_adapter.py`) A/B 테스트 시작 | RA | D3 | 어댑터 동작 |
| D5 | `python-hwpx` A/B BytesIO(방법 B) 실측 → 임시파일 유지/교체 결정 | RA | D4 | ADR 추가 |

#### Week 10~11

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 | DOCX 빌더 22/22 컴포넌트 (B18, B1-d 이관) | BE | S3 완료 | `docx/builder.py` + `components.py` |
| D6 | 한컴 2020 + 한컴 2022 + Polaris Office 실기 열기 테스트 | RA+user | D5 | 열기 성공률 리포트 |
| D7 | HWPX `degraded_components` 메타데이터 API 반영 | BE | D6 | metadata 처리 |
| D7 | hwp-extract vs olefile A/B 비교 완료 → olefile 제거 여부 결정 | RA | D5 | ADR |
| D8 | DOCX 회귀 테스트 (22 컴포넌트 전수) | SDET | D7 | 회귀 리포트 |
| D8 | LibreOffice + H2Orestart 사이드카 컨테이너 추가 (S0 결과 반영) | BE | D7 | docker-compose 사이드카 |
| D9 | HWPX + DOCX end-to-end 시연 | BE+RA | D8 | 시연 자료 |
| D10 | S5 QA ≥80 + HWPX 실기 열기 **필수 통과** + `docutil-api:s5-stable` 태그 | SDET+EA | D9 | QA + 태그 |

**Week 11 마일스톤**: HWPX 12 빌더 + DOCX 22 빌더 + hwp-extract 통합.

**병행 가능**: RA(HWPX 빌더) ∥ BE(DOCX 빌더) ∥ BE(사이드카). S6 초반과 1일 중복 허용.
**블로커**: S2 + S3 완료. 한컴 정품 테스트 PC 확보(또는 Polaris Office 대체).
**Watch 리스크**: H2 (HWPX 한컴 호환), H3 (LibreOffice 사이드카), O1 (서버 메모리).

---

### 2.6 S6 — RAG·보고서 품질 + HWPX 색상 + 특화 컴포넌트 (8영업일, 1.5주)

목표: 회의록 전용 프롬프트 + Agentic RAG ↔ Mode A Citations + HWPX 표 헤더 색상(Q7) + 특화 4종.

#### Week 12

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | `minutes` 타입 프롬프트 — 참석자/결정사항/액션아이템 구조 필수 | BE | S5 완료 | minutes 프롬프트 |
| D1 | Citations 공통 컴포넌트 승격 (F9, `components/citations/`) | FE | S5 완료 | 공통 컴포넌트 |
| D2 | Agentic RAG citations `metadata.citations` 주입 | BE | D1 | citations 주입 |
| D2 | 컴포넌트 본문 `[cite: id]` 마커 렌더 | FE | D1 | 마커 렌더 |
| D3 | HWPX 표 헤더 primary_color 배경 lxml 직접 조작 (Q7 완전 구현) | RA | S5 완료 | 색상 주입 |
| D3 | ExecutiveSummary/ActionItemList React + 폼 | FE | D2 | 2 특화 컴포넌트 |
| D4 | RiskMatrix/AttendeeList React + 폼 | FE | D3 | 4/4 특화 컴포넌트 |
| D4 | ExecutiveSummary/ActionItemList/AttendeeList HTML/PPTX/DOCX/HWPX 빌더 | BE+RA | D3 | 3×4=12 빌더 |
| D5 | RiskMatrix HTML/PPTX/DOCX 빌더 (HWPX degradation 기록) | BE | D4 | 3 빌더 + degradation |

#### Week 13 (반주)

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D6 | `structured_schemas.py` 폐기 (B3, 회의록 프롬프트 이관 후) | BE | D5 | 파일 삭제 |
| D6 | `graph_rag.py` 활성 참조 재확인 후 제거 (B11) | BE | D5 | 파일 삭제 |
| D7 | `source_document_ids` 역방향 질의 실측 (Q2) → 정규화 의사결정 ADR | DB | D6 | ADR |
| D7 | 회의록 품질 AI 평가 (Relevancy, Faithfulness) — 목표 Relevancy 0.75+ | SDET | D6 | 평가 리포트 |
| D8 | S6 QA ≥80 + 회의록 E2E 통과 + `docutil-api:s6-stable` 태그 | SDET+EA | D7 | QA + 태그 |

**Week 13 마일스톤 M4**: 21~22 컴포넌트 완성 + 회의록 Relevancy 0.75+ + HWPX 색상 주입 + 정리 완료.

**병행 가능**: BE(프롬프트·빌더) ∥ RA(HWPX 색상) ∥ FE(Citations·특화 컴포넌트) ∥ DB(ADR).
**블로커**: S5 완료.
**Watch 리스크**: R5 (RAG 회귀).

---

### 2.7 S7 — 인라인 편집 + 부분 재생성 + QA + 병존 제거 (8영업일, 1.5~2주 — 버퍼 포함)

목표: regenerate API + 인라인 편집 + PDF export + `modules/reports`·`modules/templates` 완전 제거 + QA ≥90.

#### Week 13~14

| Day | 작업 | 담당 | 선행 | 산출물 |
|---|---|---|---|---|
| D1 | `POST /v2/documents/{id}/regenerate-component` + `/regenerate-page` | BE | S4+S6 완료 | 2 엔드포인트 |
| D1 | 인라인 편집 텍스트박스 within iframe (direct edit) | FE | S4+S6 완료 | 인라인 편집 |
| D2 | `integrations/document_builders/pdf/builder.py` (Playwright HTML→PDF) + 전용 pdf-worker 큐 | BE | D1 | PDF 빌더 |
| D2 | 부분 재생성 UI (컴포넌트 선택 + "재생성" 버튼) | FE | D1 | 재생성 UX |
| D3 | 모바일 반응형 대응 (1023px 이하) | FE | D2 | 반응형 확인 |
| D3 | 48시간 스테이지 관찰 시작 (S7-B7 drop 이전 안정성 확인) | SDET+EA | D2 | 관찰 로그 |
| D4 | 인라인 편집 500ms debounce + PATCH 저장 | FE | D3 | debounce 저장 |
| D4 | `(user)/reports/*` → `/designer/*` 301 리다이렉트 적용 (F5) | FE+BE | D3 | 리다이렉트 동작 |
| D5 | 스테이지 48h 관찰 완료 → P0/P1 0건 확인 | EA | D3+48h | 관찰 보고서 |
| D5 | `workers/report_generator.py` 삭제 (B1 전체) + `workers/jinja2_engine.py` 삭제 (B2) | BE | D5 오전 | 2 파일 삭제 |
| D6 | `modules/reports/` 삭제 (B5) + `modules/templates/` 삭제 (B6) | BE | D5 | 2 모듈 삭제 |
| D6 | `components/templates/variable-mapping-editor.tsx` 삭제 (F6) | FE | D5 | 파일 삭제 |
| D7 | Alembic 010 — `tb_report_templates`, `tb_document_templates`, `tb_generated_reports_archive` drop + `source_document_ids` 정규화 (Q2 결정 시) | DB | D6 | 010 migration |
| D7 | S7 전체 회귀 + 성능 테스트 (10 시나리오 §3.5) | SDET | D6 | 회귀 + 성능 리포트 |
| D8 | S7 최종 QA ≥90 + `docutil-api:s7-stable` + Phase 4 완료 선언 | SDET+EA | D7 | QA + 완료 보고 |

**Week 14 마일스톤 M5**: 병존 제거 + 인라인 편집 + PDF + QA ≥90. Phase 4 종료.

**병행 가능**: BE(regenerate·worker 삭제) ∥ FE(인라인·리다이렉트). **D5의 삭제 작업은 D3 스테이지 관찰 통과 후 수행**.
**블로커**: S4 + S6 완료. QA ≥80 유지 확인.
**Watch 리스크**: R6 (병존 제거 사용자 혼란), R7 (PDF 메모리).

---

### 2.8 전체 타임라인 요약

| 주 | 영업일 | 스프린트 | 마일스톤 |
|---|---|---|---|
| W1~W2 | D1~D10 | S1 | M1 (Mode A 6컴포 + PATCH) |
| W3~W4 | D11~D20 | S2 | M2 일부 (PPTX + archive) |
| W5~W6 | D21~D30 | S3 | M2 완 (13 컴포넌트) |
| W7~W9a | D31~D42 | S4 | M3 (Mode B + 전환) |
| W9b~W11 | D43~D52 | S5 | HWPX + DOCX 완성 |
| W12~W13a | D53~D60 | S6 | M4 (RAG + 특화) |
| W13b~W14 | D61~D68 | S7 | M5 (Phase 4 종료) |

**총 영업일**: 68일 ≈ 13.6주. Phase 2 v1.1 14.6주에서 S0 0.6주 소진 후 잔여. S7 뒤 2~5영업일 버퍼 별도(롤백 발동 시 사용).

---

## 3. QA 게이트 상세 기준

### 3.1 기본 QA 수용 기준

| 스프린트 | QA 목표 | 특화 영역 100% | 성능 기준 | AI 품질 기준 |
|---|---|---|---|---|
| S1 | ≥80 | DocumentSchema 6종 생성 100% JSON 반환 (4 provider) | POST P95 < 10s | — |
| S2 | ≥80 | PPTX 빌드 성공률 ≥95% | Export P95 < 15s | — |
| S3 | ≥80 | 13 컴포넌트 렌더 100% | 이미지 자동 선택 < 5s | DALL-E 쿼터 초과 403 정상 |
| S4 | ≥80 | Mode 전환 자동 매핑 ≥85% | switch-mode P95 < 3s | 매핑 실패 컴포넌트 자유 페이지 보존 100% |
| S5 | ≥80 + HWPX 실기 열기 필수 | 한컴 2020/2022 열기 100% | HWPX 빌드 P95 < 20s | — |
| S6 | ≥80 | 회의록 구조 일치 100% | HWPX 색상 주입 P95 < 25s | **Relevancy ≥0.75** (이전 0.68 대비), Faithfulness ≥0.80, Hallucination ≤0.10 |
| S7 | **≥90** | 병존 제거 후 P0/P1 0건 | JSONB 조회 P95 < 100ms, PDF P95 < 30s, 메모리 peak < 2GB worker | 전 영역 회귀 |

### 3.2 S4 Mode 전환 회귀 테스트 필수 세트 (6항목)

1. 자유 생성 문서 → 템플릿 끼워맞추기 (자유→템플릿) — 매핑 성공률 ≥85% 컴포넌트
2. 매핑 실패 컴포넌트 "자유 페이지" 보존 (default policy) 100% 동작
3. 템플릿 채우기 문서 → 자유 편집 (템플릿→자유) — `locked=true` 해제 정상
4. `conflict_policy=discard_unmapped` vs `keep_all` 양쪽 동작 확인
5. Mode 전환 중 네트워크 실패 시 원상 복구 (트랜잭션 롤백 + snapshot 복원)
6. 감사 로그 전/후 snapshot JSONB 저장 + `mode_transition` 이벤트 타입 확인

### 3.3 S5 HWPX 실기 열기 테스트 (환경 확보 시)

1. python-hwpx 2.9.0 생성 → 한컴 2020 열기
2. 동일 파일 → 한컴 2022 열기
3. 동일 파일 → Polaris Office 열기 (무료 대체)
4. 표 5×4 렌더 정상
5. 한글 UTF-8 표시
6. 스타일 이름(IDINO_제목1/2/3, IDINO_본문) 반영
7. 이미지 삽입 후 표시
8. LibreOffice + H2Orestart 컨테이너에서 ODT 변환 성공

**환경 확보 대안**: 한컴 정품 PC 확보 불가 시 Polaris Office + LibreOffice+H2Orestart만으로 70% 수준 통과 허용 (사용자 명시 승인 시).

### 3.4 S6 AI 품질 기준

RAGAS 또는 동등 평가 프레임워크로:
- **Relevancy ≥0.75** (이전 Phase 0 0.68 대비 +10% 향상)
- **Faithfulness ≥0.80** (원본 인용 정확도)
- **Hallucination ≤0.10** (허위 생성 비율)
- 평가 샘플: 회의록 생성 10건 + 챗봇 응답 20건

### 3.5 S7 전체 회귀 + 성능 테스트 시나리오 10건

1. 신규 사용자 회원가입 → 로그인
2. 문서 업로드(Docling 파싱) → 검색(Agentic RAG)
3. 챗봇 세션 시작 → Citations 확인
4. Mode A 슬라이드 보고서 생성 (5페이지)
5. Mode B 회의록 양식 채우기
6. Mode 전환 (자유 → 템플릿)
7. 컴포넌트 부분 재생성
8. PDF export (10페이지 문서)
9. HWPX export + 한컴 열기
10. 관리자 IDINO 템플릿 3건 관리 (업로드/수정/삭제)
11. (+ 성능) `tb_documents_v2` JSONB 조회 P95 < 100ms (100만 행 더미 데이터)

### 3.6 QA 78~79 예외 통과 기준

1. 하락 원인이 본 스프린트 회귀가 아닌 기존 기능 P2 버그
2. 해당 P2는 다음 스프린트 초반 핫픽스 일정 확보
3. 본 스프린트 고유 DoD 전부 충족
4. 사용자 또는 EA의 명시적 승인

### 3.7 QA 실패 시 조치

| 조건 | 조치 |
|---|---|
| QA 70~77, 본 스프린트 P1 원인 | **핫픽스 트랙** (별도 브랜치), 2일 이내 재QA. 통과 시 다음 스프린트 착수. |
| QA <70, P0 ≥1건 | **스프린트 연장** 최대 3영업일. 소유자: 본 스프린트 주 담당. |
| QA <78 + P0/P1 ≥2건 48시간 초과 | **롤백** (§4.3). 이전 `sN-stable` 이미지로 복귀 + Alembic downgrade. |

---

## 4. 배포·롤백 전략

### 4.1 Ubuntu 서버 배포 절차 (표준)

```bash
# 1. 로컬 빌드·테스트
cd D:\workspace\document_utilization
docker compose up -d --build api celery-worker
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend nginx
docker exec docutil-api alembic upgrade head
scripts\qa_quick.bat   # 로컬 QA ≥80 확인

# 2. 서버 파일 전송
python scripts/deploy_to_server.py

# 3. 서버 SSH + 재빌드
ssh idino@192.168.10.39
cd ~/docutil

# ⚠️ MinIO 이미지 sed 필수 (docker-compose 덮어쓰기 방지)
sed -i 's|image: minio/minio:latest|image: quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z|' docker-compose.yml

docker compose up -d --build api celery-worker
docker builder prune -af
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend nginx

# 4. DB 마이그레이션
docker exec docutil-api alembic upgrade head
# 출력 head 번호가 예상 migration(007/008/009/010)과 일치하는지 확인

# 5. 서버 QA 실행
bash scripts/qa_quick.sh
# 점수 확인 → ≥80 필수

# 6. 외부 접속 확인
curl -I https://navi.inje.ac.kr/api/v1/health   # 또는 지정 엔드포인트
```

### 4.2 스프린트 말 이미지 태그 관리

각 스프린트 QA 통과 직후:

```bash
docker tag docutil-api:latest docutil-api:s1-stable   # 또는 s2, s3, ..., s7
docker tag docutil-frontend:latest docutil-frontend:s1-stable
# 원격 레지스트리 사용 시 push
```

롤백 시 다음 순서로 복귀: `docker compose down api frontend` → `image:` 필드 `sN-stable` 지정 → `docker compose up -d api frontend`.

### 4.3 스프린트별 롤백 트리거 + 절차

| 스프린트 | 롤백 트리거 | 절차 | 소요 |
|---|---|---|---|
| S1 | DocumentSchema 생성 실패 ≥50% (4 provider 평균) | Alembic 007 downgrade + `s0-stable` 복귀 (pre-S1 상태) | 0.5일 |
| S2 | PPTX 빌드 에러 rate ≥10% 또는 A/B 리뷰 3인 중 2인 이상 품질 저하 판정 | feature flag `DOC_V2_PPTX_EXPORT=false` + `s1-stable` 복귀. archive rename 유지 | 0.5일 |
| S3 | 신규 컴포넌트 렌더 P0 | 해당 컴포넌트 React 렌더 placeholder 복귀 (삭제 아님) | 0.25일 |
| S4 | Mode 전환 자동 매핑 <50% 또는 데이터 손실 보고 | `switch-mode` API 403 + 수동 재작성 | 1일 |
| S5 | 한컴 2020 미열림 또는 HWPX 파일 손상 보고 | HWPX export 비활성 + UI "준비 중" 안내. DOCX 대체 | 0.5일 |
| S6 | 회의록 Relevancy < 0.70 (이전 대비 저하) | H1~H7 핫픽스 상태 복귀. HWPX 색상 주입 feature flag off | 1일 |
| S7 | 병존 제거 후 핵심 기능 P0 | S7-B5~B7 delete 연기 1주, `modules/reports` 복구 | 1주 연기 |

### 4.4 Alembic 롤백

각 migration별:
- **007**: `alembic downgrade 006` — `tb_documents_v2*` drop + archive rename 복구 + `tb_agents` CHECK drop. **가역적**.
- **008**: `alembic downgrade 007` — archive 테이블 drop은 비가역. S2 시점에는 archive rename만 있어 가역.
- **009**: `alembic downgrade 008` — `tb_organization_quotas` drop. 가역.
- **010 (S7)**: **비가역**. drop은 downgrade 불가. S7 DoD에 "모든 archive 1년 보관 완료 확인" 명시적 포함.

### 4.5 DB 스냅샷 / pg_dump 타이밍

각 스프린트 말 QA 직후(이미지 태그와 동시):

```bash
ssh idino@192.168.10.39 "docker exec docutil-postgres pg_dump -U docutil -d docutil -F c -f /backup/pre_sN+1_$(date +%Y%m%d).dump"
```

MinIO 백업:

```bash
ssh idino@192.168.10.39 "docker exec docutil-minio mc mirror /data /backup/minio_pre_sN+1_$(date +%Y%m%d)"
```

### 4.6 MinIO 파일 복구

- 현재 `documents` 버킷 0 파일 (S0 확인).
- Phase 4 S1 시작 전 운영팀이 IDINO 템플릿 3건 재업로드 (별도 트랙).
- 스프린트 중 MinIO 파일 손실 보고 시: 백업(`/backup/minio_pre_sN_*`)에서 `mc mirror` 복원.

### 4.7 배포 시 주의사항 (기존 §10 보강)

- **MinIO 이미지**: 매 배포마다 `sed` 재실행 (덮어쓰기 발생)
- **Nginx 재시작**: API 컨테이너 재시작 후 업스트림 끊김 가능성 → Nginx도 함께 재시작
- **프론트 캐시**: `docker builder prune -af` → `--no-cache` 빌드
- **브라우저 캐시**: 배포 후 Ctrl+Shift+R 또는 시크릿 모드 안내
- **Alembic 실행**: 반드시 컨테이너 내부(`docker exec docutil-api alembic upgrade head`). 호스트에서 직접 실행 금지 (`.env` 경로 차이)

---

## 5. 모니터링·알림 설정

### 5.1 신규 Prometheus 메트릭 (4종)

1. **`documents_v2_generated_total{mode, document_type, status}`** — 생성 요청 카운터. mode ∈ {free_form, template_fill}, status ∈ {success, failed, timeout}
2. **`builder_duration_seconds{target}`** — 포맷별 빌더 소요 시간 Histogram. target ∈ {html, pptx, docx, hwpx, pdf}
3. **`llm_tokens_used_total{provider, task}`** — 프로바이더·작업별 토큰 사용량. task ∈ {mode_a, mode_b, regenerate, citations, mode_transition}
4. **`mode_transition_count{direction, policy}`** — Mode 전환 이벤트. direction ∈ {free_to_template, template_to_free}, policy ∈ {discard_unmapped, keep_all}

**기존 메트릭 보강**:
- `api_request_duration_seconds` 를 `{route}` 레이블로 세분 (특히 `/v2/documents/*`)
- `celery_task_duration_seconds` 에 `export_worker`·`pdf_worker` 레이블 추가

### 5.2 Grafana 대시보드 (3종)

1. **"DocumentSchema Pipeline"** — 생성 요청 → Schema → 빌더 → Export 흐름 시각화
   - 패널: 초당 요청률, mode별 성공률, 빌더별 P50/P95/P99, LLM 토큰 사용량
2. **"Mode A vs Mode B 사용률"** — 시간대별 mode 비율, 전환 방향별 빈도, 매핑 성공률
3. **"조직별 문서 생성 현황"** — 외부 고객사 온보딩 대비 사전 구축. 현재는 IDINO 단일 조직 + 템플릿 3건 trend

### 5.3 Loki 로그 집계 (4종)

1. **`modules.documents_v2.*`** INFO 이상 — 생성·PATCH·switch-mode 요청 추적
2. **LLM 실패·재시도 로그** — provider별 finish_reason=length, rate_limit, validation_error
3. **빌더 예외 트래픽** — HwpxBuilder degraded_components, PDF 메모리 warning
4. **Mode 전환 audit 로그** — 전/후 snapshot 크기, 매핑 실패 컴포넌트 수

### 5.4 알림 규칙 (Grafana Alert, 4종)

| 이름 | 조건 | 채널 | 우선순위 |
|---|---|---|---|
| **doc-gen-p95-high** | `histogram_quantile(0.95, documents_v2_generated_total) > 30s` for 5m | Slack (또는 이메일) | P2 |
| **mode-transition-failure-spike** | `rate(mode_transition_count{status="failed"}[5m]) > 0.1` | 즉시 (P1) | P1 |
| **builder-error-spike** | `rate(builder_duration_seconds_count{status="error"}[5m]) > 0.05` (PPTX·HWPX) | 즉시 (P1) | P1 |
| **celery-queue-depth** | `celery_queue_length > 50` | Slack | P2 |

### 5.5 대시보드·알림 도입 순서

- **S1 말**: "DocumentSchema Pipeline" 1호 대시보드 구축 + doc-gen-p95-high 알림.
- **S4 말**: "Mode A vs Mode B 사용률" + mode-transition-failure-spike 알림.
- **S6 말**: "조직별 문서 생성 현황" + builder-error-spike·celery-queue-depth 알림.
- **S7**: 전체 알림 운영 상태 검증 + 필요 시 Grafana Silence 정책 (심야 알림 축소).

---

## 6. Phase 4 Day 1 체크리스트

Phase 4 S1 D1 아침에 사용자 + Claude Code 에이전트 팀이 아래 항목 **모두** 확인한 뒤 착수한다.

- [ ] **S0 조사 결과 이해**: `docs/s0_inventory_report.md` §0 핵심 발견 8건 숙지 (조직 1·템플릿 3·report_templates 0·MinIO 0파일·Alembic head=006)
- [ ] **Phase 1~3 문서 최신 버전 확인**: `phase1_decisions.md` **v1.2**, `phase2_transition_plan.md` **v1.1**, `phase1_architecture.md` **v1.6**, `phase3_execution_roadmap.md` **v1.0**
- [ ] **개발 환경 정상 구동 (Windows)**: `docker compose up -d --build` → 14 컨테이너 정상, `curl localhost:8040/api/v1/health` 200
- [ ] **Ubuntu 서버 접속 확인**: `ssh idino@192.168.10.39 "docker ps --format 'table {{.Names}}\t{{.Status}}'"` 14개 정상
- [ ] **MinIO 템플릿 3건 재업로드**: 운영팀 별도 트랙 완료 여부 확인 (보고서_양식.docx, 회의록_양식.docx, ppt_제안서_가로양식.pptx)
- [ ] **에이전트 분담 확정**: BE(S1/S2/S4/S5/S6/S7), FE(S1/S3/S4/S7), DB(S1/S4), RA(S5), SDET(전 스프린트 말), EA(전체 조율)
- [ ] **Q1~Q10 결정 + v1.2 조정 요지 숙지**: 특히 Q3(Mode 전환 포함), Q4(조직별 로드맵 성격), Q8(MVP 6종)
- [ ] **S1 D1 작업 즉시 착수 준비**: DocumentSchema Pydantic 검증(BE) + 6 컴포넌트 React 렌더 시작(FE)
- [ ] **Alembic head 확인**: `docker exec docutil-api alembic current` → `006_evaluation` 확인
- [ ] **Alembic 007 draft 파일 존재 확인**: `backend/alembic/versions/007_*.py` + NOT VALID/VALIDATE 2단계 적용 여부
- [ ] **linting·QA 기준선**: `scripts\qa_quick.bat` 실행 → 현재 기준 점수 기록 (S1 회귀 판정 기준)
- [ ] **리스크 Watch List S1용 확인**: R1 (Multi-provider Structured Output) 우선 대응 계획
- [ ] **Prometheus/Grafana 접근 확인**: 기존 대시보드 로그인 + S1 말 "DocumentSchema Pipeline" 신규 대시보드 구축 예정
- [ ] **사용자 S1 착수 승인**: Phase 3 로드맵 리뷰 완료 + S1 DoD 합의

**통과 기준**: 14/14 체크 완료 시 S1 D1 작업 시작 가능. 누락 1건이라도 있으면 해당 항목 해소 후 재검토.

---

## 7. 스프린트 간 전환 의식 (Sprint Handover)

각 스프린트 종료 → 다음 스프린트 시작 사이의 공식 인수 절차. 누락 없이 실행해야 다음 스프린트의 블로커가 생기지 않는다.

### 7.1 6단계 절차

1. **QA 보고서 작성** — SDET가 `tests/qa_reports/sN_YYYY-MM-DD.md` 생성. 점수, 커버리지, 실패 테스트 목록, P0/P1/P2 버그, 성능 지표 포함.
2. **완료 자산 체크리스트 검증** — 본 문서 §2 해당 스프린트 DoD 체크 항목 전부 확인. 누락 시 다음 스프린트 D1 전에 완료.
3. **다음 스프린트 입력 인계** — 본 스프린트에서 발견된 설계 영향 사항을 다음 스프린트 담당에게 전달. 예: S1 Week 2에 R1 Multi-provider 이슈 발견 시 S2 D1에 영향.
4. **리스크 재평가** — §9 Watch List를 리뷰하여 신규 리스크를 `phase2_transition_plan.md` §5에 추가 또는 점수 조정. EA 소유.
5. **techspec.md / project_status.md 업데이트** — §16에 스프린트 완료 요약 1~2문단, `project_status.md` 기능 상태 갱신.
6. **사용자 대면 데모** (선택, 스프린트 따라) — M1/M3/M5에 데모 권장. S1 (Mode A 6컴포), S4 (Mode B + 전환), S7 (최종 end-to-end).

### 7.2 이미지 태그 + DB 스냅샷

전환 의식 실행 시점에 동시 수행:

```bash
docker tag docutil-api:latest docutil-api:sN-stable
docker tag docutil-frontend:latest docutil-frontend:sN-stable
ssh idino@192.168.10.39 "docker exec docutil-postgres pg_dump -U docutil -d docutil -F c -f /backup/post_sN_$(date +%Y%m%d).dump"
```

### 7.3 스프린트 회고 템플릿

각 전환 의식 말미에 5분 회고:
- 잘 된 점 1~2가지
- 개선할 점 1~2가지
- 다음 스프린트에 가져갈 학습 1가지
- 기록 위치: `docs/sprint_retrospectives.md` (신규, 스프린트별 append)

---

## 8. 에이전트 조율 가이드

`.claude/rules/agent-collaboration.md` 연장선.

### 8.1 병렬 작업 시 충돌 방지

- **공유 파일 락**: `documents_v2/schemas.py`, `phase1_architecture.md`, `docker-compose.yml` 등은 한 번에 한 에이전트만 수정. 수정 전 `git status` + `git log -5 <파일>` 확인. 동시 수정 필요 시 EA가 병합 PR 생성.
- **인터페이스 lock 우선**: S1 D1에 확정된 Pydantic schema + TS `documents-v2.ts` 타입은 S1 중 변경 금지. 필요 시 S2 이상에서 minor 버전.
- **branch 분리**: 각 스프린트 내 작업은 `feature/sN-<topic>` 브랜치. 스프린트 말에 `develop`으로 병합 후 `main`.

### 8.2 중간 점검 포인트

- **스프린트 중간 (5영업일째)**: EA가 15분 점검. DoD 진행도 50%+ 여부, 신규 리스크 발견 여부.
- **3일마다 상시 모니터링**: SDET가 `scripts/qa_quick.sh` 1회 실행 → 점수 저하 감지.

### 8.3 우선순위 매트릭스

여러 에이전트가 동시에 수정 대기 중일 때:

1. **P0 버그 핫픽스**: 모든 작업 중단, 해당 에이전트만 작업
2. **블로킹 의존성**: 선행 작업(예: Alembic 007)이 후행(예: Service 구현)을 블록하는 경우
3. **스프린트 DoD 진행**: 본 스프린트 DoD 작업
4. **스트레치 / 다음 스프린트 선행**

### 8.4 롤백 판단 주체

- **SDET**: QA 점수 + P0/P1 건수 일 1회 보고
- **EA**: 롤백 트리거 판정 (§4.3)
- **사용자**: 최종 롤백 승인 (특히 S4·S7)

### 8.5 Claude Code 세션 분배

- **BE 세션**: `backend/app/modules/documents_v2/`, `backend/app/integrations/document_builders/` 집중
- **FE 세션**: `frontend/src/app/(user)/designer/`, `frontend/src/components/document-designer/` 집중
- **DB 세션**: `backend/alembic/versions/`, 관련 models.py 집중
- **RA 세션**: `backend/app/integrations/document_builders/hwpx/`, hwp-extract 연구
- **SDET 세션**: `backend/tests/`, `scripts/qa*.sh` 집중
- **EA 세션**: `docs/*.md`, ADR 생성, 리스크 매트릭스 갱신

중복 세션 방지: EA가 주간 플래닝 시 각 세션이 만질 파일 범위 확정.

---

## 9. 리스크 최종 통제 (스프린트별 Watch List)

Phase 2 §5 리스크 매트릭스 v2를 스프린트별 Watch List로 분해. 각 Watch 리스크는 (1) 트리거 감지 지표, (2) 즉시 대응 플레이북을 포함한다. 총 **7개 Watch List 세트, 누적 리스크 항목 11건 (중복 제외 실질 8종)**.

### 9.1 S1 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **R1** Multi-provider Discriminated Union 불완전 지원 | 4 provider 중 1개 이상 Structured validation 실패율 ≥20% (S1 D7 테스트) | `StrictSchemaFallback` 평탄화 스키마 추가 (2일 소요). S2 D1 착수 전 통과 필수. |
| **D3** `tb_agents.agent_type` CHECK 실패 | S0-4 DISTINCT 결과 외 값 발견 | `UPDATE tb_agents SET agent_type='chatbot' WHERE agent_type NOT IN (...)` 사전 정제 후 VALIDATE. |

### 9.2 S2 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **R4** 하드코딩 제거 후 PPTX 품질 체감 저하 | A/B 리뷰 3인 중 2인 이상 신규 품질 < 기존 | IDINO 마스터 추가 스타일 튜닝 3일. feature flag 유지하여 기존 경로 생존. |
| **R6** 병존 기간 이중 유지보수 비용 | `modules/reports` PR 수 ≥3건/주 지속 | 핫픽스는 신규 경로에서만. 기존 경로는 "read-only maintenance mode" 선언 + 코드 주석 표시. |

### 9.3 S3 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **R9** DALL-E 3 비용 예산 초과 | 월간 호출 건수 > 계획 150% | Unsplash 우선 정책 강화 + 조직별 쿼터 축소 + 수동 승인 UI. |

### 9.4 S4 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **U3** Mode 전환 자동 매핑 정확도 | 매핑 성공률 < 70% (D9 실측) | `conflict_policy=keep_all` 기본값 + 사용자 명시 선택 UI 강조. 매핑 실패 컴포넌트 자유 페이지 보존. |
| **R6** 병존 유지보수 | 신규 `/designer` 도달률 < 30% (S4 D10 기준) | `/reports` 배너 강화 + onboarding tour 재설계. |

### 9.5 S5 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **H2** python-hwpx 생성 HWPX 한컴 2020 미열림 | D1~D5 중 한컴 실기 열기 실패 2회 이상 | lxml 직접 OWPML 빌드 전환 (+3일). 스프린트 연장 또는 S6 일부 작업 선 이관. |
| **H3** LibreOffice 사이드카 x86-64-v1 호환 불안 | 사이드카 컨테이너 기동 실패 또는 soffice 크래시 | LibreOffice 스킵, PDF는 Playwright 전담 (S7에서 확인). |
| **O1** 서버 메모리 부족 (x86-64-v1 + LibreOffice + Playwright 동시) | 메모리 피크 > 1.5GB × 2 worker | worker 동시성 축소 (concurrency=1) + Celery queue 백오프. |

### 9.6 S6 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **R5** RAG 개선 회귀 (챗봇 품질 저하) | 회의록 Relevancy < 0.70 또는 챗봇 이전 대비 저하 | H1~H7 핫픽스 상태로 회귀. Agentic RAG 튜닝 롤백 commit revert. |

### 9.7 S7 Watch List

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **R6** 병존 제거 후 사용자 혼란 | `/reports` 301 리다이렉트 후 404 또는 이탈률 ≥ 15% 급증 | D5 삭제 작업 1주 연기. archive rename 유지, drop만 뒤로. |
| **R7** Playwright PDF 메모리 폭주 | pdf-worker OOM 카운트 ≥1/일 | 동시 2건 제한 → 1건. 큐 백오프 + 사용자 대기 UX. |

### 9.8 전 스프린트 공통 Watch

| 리스크 | 트리거 지표 | 즉시 대응 |
|---|---|---|
| **D1** `document_schema` JSONB TOAST 임계 초과 | `SELECT *` 호출 pg_stat_statements에서 검출 | ORM `defer("document_schema")` 강제. 목록 API 재작성. |
| **R10** DocumentSchema v1.0→v1.1 migration 복잡 | schema_version distinct values > 1 시 오류 발생 | dual-loader 경로 유지 + 새 필드 Optional 고수. |

### 9.9 Watch List 운영

- EA가 매 스프린트 말 Watch 지표 리뷰 → `tests/qa_reports/sN_*.md` 말미에 기록
- 신규 리스크 발견 시 `phase2_transition_plan.md` §5 매트릭스 버전 up + Watch List 추가

---

## 10. 변경이력

| 날짜 | 버전 | 변경 | 담당 |
|---|---|---|---|
| 2026-04-20 | v1.0 | 최초 작성. S1~S7 68영업일 WBS + QA 게이트 + 배포·롤백 + 모니터링 4 메트릭/3 대시보드 + Day 1 체크리스트 14항목 + 전환 의식 6단계 + Watch List 7종 (R1/R4/R5/R6/R7/R9/U3/H2/H3/O1/D1/D3/R10 총 13건 커버) | enterprise-architect |

---

**(문서 끝)**
