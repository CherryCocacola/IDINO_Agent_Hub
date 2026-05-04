# DocUtil — Phase 2 전환계획 (v1.1)

> **작성일**: 2026-04-20 (v1.0), 2026-04-20 S0 후 (v1.1)
> **작성자**: enterprise-architect (Claude Opus 4.7, 1M context)
> **상위 문서**: `docs/phase1_architecture.md` v1.6, `docs/phase1_decisions.md` **v1.2**, `docs/s0_inventory_report.md` v1.0
> **후속 문서**: S3 실행 로드맵(Phase 3), Phase 4 스프린트 착수 문서
> **상태**: Phase 2 전환계획 확정안. **S0 실행 완료 (2026-04-20)**. Phase 3 착수 준비.
>
> **v1.1 변경점** (S0 조사 결과 + `phase1_decisions.md` v1.2 반영):
> - S0 실행 완료: 조직 1건(아이디노), 템플릿 3건, report_templates 0건, MinIO 0 파일
> - S4 기간 **3.5주 → 2.5주 축소** (조직별 배치 변환 불필요)
> - Alembic 008 `organization_type` **스킵** (Phase 1~4 범위 외, 외부 고객사 온보딩 시 별도)
> - 리스크 U4 대폭 완화(중→낮), R12·R13 제거, R14 신규(외부 고객사 온보딩 후속 스프린트)
> - S7 QA 여유분 2주 **원복** (S4 축소분이 S7 원복으로 귀결)
> - **MinIO 템플릿 재업로드**: Phase 1~4 시작 전 운영팀 작업으로 별도 트랙

---

## 1. Executive Summary

Phase 1은 "목표 아키텍처(접근법 C — DocumentSchema SSOT + 22 컴포넌트 라이브러리 + ABC/Registry 빌더)"를 확정했다. Phase 2는 그 아키텍처로 가는 **실행 경로**를 스프린트·데이터·리스크·롤백·QA·팀 배치 여섯 축에서 구체화한다. 코드 변경·DB 실 적용은 Phase 4의 책임이며, 본 문서는 **Phase 4가 첫 날 펼쳐 볼 수 있는 체크리스트 수준**의 전환 계획서다.

핵심 결정 요지 (v1.1):

1. **자산 39항목을 파일/함수 단위로 재분류**했다. 재활용 18, 수정 9, 폐기 12 (세부는 §2).
2. **S0 사전 조사 완료 (2026-04-20)**. 주요 결과: 조직 1건(아이디노), 템플릿 3건, `tb_report_templates` 0 rows, MinIO 0 파일, `organization_type` 필드 부재, Alembic head=006_evaluation. 상세 `docs/s0_inventory_report.md`.
3. **S4가 1.5주 → 2.5주로 축소 확장** (v1.0의 3.5주에서 1주 회수). Q3(Mode 전환 API) 2주 + Mode B Jinja2 UX 0.5주. Q4의 조직별 배치 변환은 S0 결과로 **불필요** 확인 (외부 고객사 데이터 없음). 단 **다조직 설계 구조는 유지** (향후 확장성).
4. **데이터 마이그레이션은 Dual-write 하지 않는다**. 신규 경로(`tb_documents_v2`)는 S1부터 즉시 유일 경로. 기존 `tb_generated_reports`는 S2 시점에 `_archive`로 리네이밍(읽기 전용), S7에서 drop. 병존 기간의 이중 기록·동기화 리스크 회피가 설계 의도.
5. **롤백 트리거는 "QA <78 + P0/P1 미해결"** 두 조건이 동시 충족될 때만. 개별 영역 회귀는 핫픽스 트랙에서 처리, 스프린트 되감기는 최후 수단.
6. **에이전트 역할 분담**: backend-specialist(S1/S2/S4/S5/S6/S7), frontend-specialist(S1/S3/S4/S7), database-architect(S4 보조), research-assistant(S5), sdet-agent(매 스프린트 말 + S7 전체 회귀). S0는 Claude Code가 paramiko로 직접 실행 완료.
7. **외부 고객사 온보딩은 Phase 1~4 이후 별도 스프린트**. Alembic 008(`organization_type`) + 조직별 배치 변환 스크립트 + 고객사 관리 UI는 온보딩 시점에 착수 (R14).
8. **MinIO 템플릿 3건 재업로드**: 운영 DB에 `template_storage_path`는 있으나 MinIO 파일 부재. Phase 4 S1 시작 전 운영팀이 3건 수동 재업로드 필수 (별도 트랙).

상세는 §2~§9.

---

## 2. 자산 재분류 정밀화 (과제 1)

Phase 1 §5.3의 20항목 대략 분류를 파일/함수 단위 39항목으로 확장한다. 출처는 `report_generator.py` 함수 목록(30개), `jinja2_engine.py` 함수 목록(30개+), `modules/templates/service.py`(15개 메서드), 프론트 라우트, DB 테이블, 스크립트, 빌더/통합 전반 직접 스캔.

### 2.1 백엔드 파일·함수 단위 분류 (핵심 21항목)

| # | 자산 경로 | 현재 역할 | 분류 | 신규 위치 | 스프린트 | 이유 |
|---|---|---|---|---|---|---|
| B1 | `backend/app/workers/report_generator.py` (3702줄, 모놀리스) | Celery 보고서 생성 전체 | **분해** | — (함수별 분산) | S1~S7 | 단일 파일이 LLM 호출·템플릿 채움·PPTX 빌드·DOCX 빌드·이미지·차트를 모두 흡수. DocumentBuilder ABC로 분해. |
| B1-a | `report_generator._rag_extract_content` | RAG 컨텍스트 조합 | **재활용(이관)** | `modules/documents_v2/service.py::build_rag_context` | S1 | LLM 호출 전 컨텍스트 주입 로직. 신규 Service에 그대로 이식. |
| B1-b | `report_generator._build_layout_catalog` | 한글 레이아웃 이름 하드코딩 | **폐기** | — | S2 | Phase 0에서 실패 원인으로 확정. `layout_resolver` 런타임 매핑으로 대체. |
| B1-c | `report_generator._build_pptx_from_structured` (~668줄) | 구조화 PPTX 빌드 | **분해·재활용** | `integrations/document_builders/pptx/components.py` | S2 | 컴포넌트별 헬퍼 함수 추출(헤더바/푸터/테이블/차트/이미지). 단일 함수는 폐기, 내부 유틸은 22 컴포넌트 빌더로 재배치. |
| B1-d | `report_generator._build_docx_from_structured` (~220줄) | DOCX 빌드 | **분해·재활용** | `integrations/document_builders/docx/components.py` | S5 | 동일 원칙(컴포넌트별 분해). |
| B1-e | `report_generator._add_table_to_slide`, `_add_table_to_docx`, `_add_chart_to_slide`, `_add_chart_to_docx`, `_add_image_to_slide`, `_set_cell_bg`, `_fetch_stock_image` | PPTX/DOCX 보조 | **재활용** | `integrations/document_builders/{pptx,docx}/components.py` | S2/S3/S5 | 표·차트·이미지 삽입 로직은 포맷 무관 재사용 가치 높음. 인터페이스만 ComponentBase에 맞춰 변환. |
| B1-f | `report_generator` 나머지 17개 함수 (`_generate_docx/_generate_pptx/_generate_jinja2_context/_process_image_variables/_minutes_to_docx_document/_fill_*_template/_call_llm_structured/_extract_*_variables/generate_report` 등) | 모놀리스 경로 진입점 | **폐기(대체)** | — | S4/S7 | LLM 호출은 service로, 빌더는 `document_builders/*`로. `generate_report` 워커는 S7에 제거 후 신규 `export_worker` 대체. |
| B2 | `backend/app/workers/jinja2_engine.py` (2608줄, 30+ 함수) | Jinja2 자동 분석·치환 | **부분 재활용** | 대부분 폐기 | S4/S7 | 변수 치환 3 함수(`render_docx_jinja2`/`render_pptx_jinja2`/`_process_context_images`)만 `document_builders/docx/jinja2_renderer.py`로 이관(B2-a). 나머지 26+ 양식 자동 분석 함수(B2-b, `classify_*`/`extract_*`/`analyze_blank_*`/`auto_generate_*`/`_auto_fill_*`/`_insert_*` 계열)는 DocumentSchema 에디터로 대체되므로 **폐기**. |
| B3 | `backend/app/workers/structured_schemas.py` (394줄) | 보고서 타입별 JSON schema | **대체** | `modules/documents_v2/schemas.py` | S1/S6 | DocumentSchema로 일원화. 회의록 `minutes` 프롬프트 노하우 일부만 서술형으로 이관(§6 회의록 프롬프트). |
| B4 | `backend/app/modules/reports/service.py::ReportTemplateService` (~250줄) | 조직별 PPTX 템플릿 CRUD | **수정** | `modules/documents_v2/service.py::TemplateService` 흡수 | S4 | `tb_report_templates`를 `tb_documents_v2_templates`로 변환한 후 읽기 전용 호환 얇은 레이어만 남김. S7에서 완전 제거. |
| B5 | `backend/app/modules/reports/service.py::ReportGenerationService` (~180줄) | 보고서 생성/조회/다운로드 | **폐기(대체)** | `modules/documents_v2/service.py` | S2~S7 | S2에 신규 `DocumentServiceV2` 가동, S7까지 병존 후 제거. 기존 API(`/reports/*`)는 S7에 301 리다이렉트. |
| B6 | `backend/app/modules/templates/service.py::TemplateService` (~1430줄, 15 메서드) | Jinja2 템플릿 CRUD + 자동분석 + 변수 매핑 | **흡수·재설계** | `modules/documents_v2/service.py` | S4 | CRUD 6 메서드는 `tb_documents_v2_templates` 재배치, 자동 분석 의존 9 메서드(`upload_*`/`_detect_*`/`convert_to_template`/`auto_fill_*` 등)는 **폐기**. |
| B7 | `backend/app/modules/documents_v2/schemas.py` (608줄) | Phase 1 skeleton | **재활용(확장)** | 동일 | S1 | Phase 1에 frontend-specialist/database-architect가 이미 Pydantic discriminated union + 22 컴포넌트 초안 작성. S1에 MVP 6종 완전 구현. |
| B8 | `backend/app/modules/documents_v2/models.py` (286줄) | Phase 1 ORM skeleton | **재활용(확장)** | 동일 | S1 | `DocumentV2` + `DocumentV2Template` skeleton 완비. S1에 Service/Router 작성 후 end-to-end 연결. |
| B9 | `backend/app/modules/search/agentic_search.py` (306줄, `AgenticSearchService`) | Agentic RAG 루프 | **재활용** | 동일 | S1/S6 | Mode A에서 RAG 컨텍스트 조회 시 호출. 챗봇도 동일 서비스 사용(H7 연장). |
| B10 | `backend/app/integrations/rag/agentic_rag.py` (489줄, `AgenticRAGEngine`) | 중복 RAG 엔진 | **폐기** | — | S1 | grep 결과 외부 참조 0건. `modules/search/agentic_search.py`와 기능 중복. S1 착수 시 즉시 삭제(무참조 확인 후). |
| B11 | `backend/app/integrations/rag/graph_rag.py` (200줄, `GraphRAGEngine`) | 그래프 RAG (미사용) | **관망 → 폐기** | — | S6 | 활성 참조 0건. S6 RAG 개선 시점에 최종 판정 후 제거. |
| B12 | `backend/app/integrations/docling/docling_service.py` (181줄) | Granite-Docling VLM 클라이언트 | **재활용** | 동일 | — | 파싱 경로는 원본 문서 인제스트용으로 계속 사용. HWPX 파싱 교체는 별도 PR(S5). |
| B13 | `backend/app/integrations/llm/` (factory + 5 providers) | 멀티 프로바이더 LLM | **수정(확장)** | 동일 | S1 | `generate_structured(schema)` 통일 인터페이스 추가. Claude Tool Use 변환은 Claude 클라이언트 내부. |
| B14 | `backend/app/integrations/image_generation/` (DALL-E 3 + Unsplash) | 이미지 생성 | **재활용** | 동일 | S3 | 선택 알고리즘(§5.5 architecture)을 `documents_v2/service.py`에서 호출. |

### 2.2 빌더 레이어 (신규)

| # | 자산 | 분류 | 위치 | 스프린트 |
|---|---|---|---|---|
| B15 | `integrations/document_builders/base.py::DocumentBuilder` + `BuilderRegistry` | **신규** | 신규 | S1 |
| B16 | `integrations/document_builders/html/renderer.py` | **신규** | 신규 | S1 |
| B17 | `integrations/document_builders/pptx/{builder,components,layout_resolver}.py` | **신규(재활용 이관)** | B1-c/B1-e 이관 | S2 |
| B18 | `integrations/document_builders/docx/{builder,components,jinja2_renderer}.py` | **신규(재활용 이관)** | B1-d/B2-a 이관 | S5 |
| B19 | `integrations/document_builders/hwpx/{builder,components}.py` | **신규** | — | S5 |
| B20 | `integrations/document_builders/pdf/builder.py` | **신규** (Playwright) | — | S7 |
| B21 | `integrations/document_builders/__init__.py` + `BuilderRegistry.register_all()` | **신규** | — | S1 |

### 2.3 프론트엔드 (8항목)

| # | 자산 | 분류 | 신규 위치 | 스프린트 | 이유 |
|---|---|---|---|---|---|
| F1 | `frontend/src/app/(user)/designer/` (skeleton) | **재활용(확장)** | 동일 | S1/S4 | create/fill 라우트 skeleton 존재. S1에 Mode A create 완성, S4에 fill 완성. |
| F2 | `frontend/src/components/document-designer/` (README만) | **신규** | 동일 | S1/S4 | preview-pane/edit-sidebar/prompt-box/export-menu/design-token-picker. |
| F3 | `frontend/src/components/document-schema/components/` (6 컴포넌트 skeleton) | **재활용(완성)** | 동일 | S1 | SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable skeleton → S1에 실제 렌더. |
| F4 | `frontend/src/components/document-schema/components/` (추가 16 컴포넌트) | **신규** | 동일 | S3/S4/S6 | 나머지 16종 단계적 추가. |
| F5 | `frontend/src/app/(user)/reports/` (기존 UI) | **폐기(리다이렉트)** | — | S7 | S2 배너, S4 신규 생성 버튼 리라우트, S7 삭제. |
| F6 | `frontend/src/components/templates/variable-mapping-editor.tsx` | **폐기** | — | S4/S7 | dialog/inline 이중 모드 제거, edit-sidebar/forms로 재설계. S7에 삭제. |
| F7 | `frontend/src/app/(admin)/templates/` | **역할 축소** | 목록 페이지로만 | S4 | 편집은 `(admin)/template-designer/[id]`로 위임. |
| F8 | `frontend/src/app/(admin)/template-designer/` | **신규** | 신규 | S4 | Q9 결정. Shell 재사용 + `mode="template_authoring"` props. |
| F9 | `frontend/src/components/citations/` + `frontend/src/components/chat/Citations` | **승격(재활용)** | `components/citations/` | S6 | 챗봇 구현을 공통 컴포넌트로 승격. |

### 2.4 DB 테이블 (5항목)

| # | 테이블 | 분류 | 운명 | 스프린트 | 이유 |
|---|---|---|---|---|---|
| D1 | `tb_documents_v2` | **신규** | 생성 | S1 | 007 migration에 포함. DocumentSchema JSONB 저장. |
| D2 | `tb_documents_v2_templates` | **신규** | 생성 | S1 | 007 migration. Mode B 양식 저장. |
| D3 | `tb_agents.agent_type` CHECK | **수정** | 5종 enum CHECK 추가 (NOT VALID → VALIDATE 2단계) | S1 직전 | D3(D3 리스크) 대응: `SELECT DISTINCT agent_type FROM tb_agents` 선행. |
| D4 | `tb_generated_reports` | **리네이밍 → polaroid** | S2: `_archive`로 rename(읽기 전용) / S7: drop | S2/S7 | 데이터 손실 없는 가역적 폐기. |
| D5 | `tb_report_templates` | **존치 → S7 drop** | S4: 자동 변환 시도(Q4), 실패분 read-only 아카이브 1년, S7: drop | S4/S7 | 조직별 고객 템플릿 실재. 실패 템플릿 1년 유지. |
| D6 | `tb_document_templates` | **반자동 변환 → S7 drop** | S4: 변환 스크립트(Jinja2 → skeleton_schema), S7: drop | S4/S7 | 16개 상위 5개 우선, 나머지 관리자 수동. |
| D7 | `tb_organizations.organization_type` | **Phase 2 미결** | S0 조사 결과 → Alembic 008 검토 | S0/S4 | Q4 후속. 컬럼 부재 확인됨. 필요 시 008에 `company/university/public/other` 추가. |

### 2.5 스크립트 (5항목)

| # | 스크립트 | 분류 | 스프린트 | 이유 |
|---|---|---|---|---|
| S1-SC | `scripts/create_idino_templates.py` | **보존(참고용)** | — | IDINO 마스터 업로드 1회성 스크립트. 이력 보존. |
| S2-SC | `scripts/create_jinja2_sample_templates.py` | **폐기** | S7 | Jinja2 샘플 템플릿 생성. 신규 경로에서 불필요. |
| S3-SC | `scripts/create_sample_templates.py` | **대체** | S1 | DocumentSchema 샘플 생성기로 재작성(demo 데이터용). |
| S4-SC | **신규**: `scripts/s0_inventory_report.py` | **신규** | S0 | 조직별 템플릿/Agent 타입/LibreOffice 검증 자동 수집. |
| S5-SC | **신규**: `scripts/migrate_templates_to_v2.py` | **신규** | S4 | Jinja2·PPTX 템플릿 → DocumentSchema skeleton 배치 변환기. |

### 2.6 분류 총계

- **재활용(위치 유지 또는 단순 이관)**: 18개 — B1-a, B1-c(분해 후 유지), B1-d, B1-e, B2-a, B7, B8, B9, B12, B13, B14, F1, F3, F9, S1-SC, 그리고 B3 중 회의록 프롬프트, D1/D2(이미 Phase 1에서 생성된 skeleton).
- **수정(확장/재설계)**: 9개 — B4, B6, B13, B15~B18, B21, D3, F7, F8.
- **폐기**: 12개 — B1-b, B1-f, B2-b, B5, B10, B11(관망 후 폐기), D4(S7), D5(S7), D6(S7), F5, F6, S2-SC.
- **S0 선행 확인 필요**: 4개 — D5, D6, D7(organization_type 부재), LibreOffice 사이드카 실현성.
- **신규**: B15~B21, D1, D2, F8, S4-SC, S5-SC = 11항목.

합계 39개 + 신규 11개 = **50 항목**(지표 기준 39 자산 + 11 신규 생성).

---

## 3. 마이그레이션 순서 S0~S7 (과제 2)

### 3.1 의존성 그래프 (v1.1 반영)

```
S0 사전 조사 (3~5일)
   │ ├─ tb_report_templates 전수 조사
   │ ├─ tb_agents.agent_type DISTINCT
   │ ├─ tb_organizations.organization_type 부재 확인 → 008 계획
   │ ├─ LibreOffice 사이드카 Xeon E5-2620 v4 구동 검증
   │ └─ 조직별 템플릿 복잡도 샘플링
   ▼
S1 DocumentSchema MVP + 6 컴포넌트 (2주)
   │ 선행: S0 완료, 007 migration 리뷰 확정
   │ └─ agentic_rag.py 삭제(B10)
   ▼
S2 PPTX 빌더 + Mode A PoC + tb_generated_reports_archive (2주)
   │
   ├─────────┬─────────────────────────┐
   ▼         ▼                         ▼
S3          S4 Mode B + Mode 전환 +    S5 HWPX (2주)
컴포넌트    조직별 PPTX 변환 (3.5주)    선행: S2 + S3 완료
확장        선행: S1 + S2 + S0 조사
(2주)       └─ Mode 전환 API 신설
   │                                    │
   └────────────┬───────────────────────┘
                ▼
        S6 RAG·보고서 품질 + HWPX 색상 + 특화 컴포넌트 (1.5주)
                선행: S3 + S5 완료
                ▼
        S7 인라인 편집 + 부분 재생성 + QA + 병존 제거 (1주 축소)
                선행: S4 + S6 완료, QA 80+
```

- **S0**: 신규, 3~5일.
- **S1**: 모든 후속 스프린트의 스키마 lock. S1 완료 전 S2/S4/S5 착수 금지.
- **S3/S4**: 병렬 가능(frontend-specialist / backend-specialist 별도 배정).
- **S4**: Q3·Q4 누적으로 3.5주.
- **S7**: 2주 → 1주 축소(S4 확장 흡수).

총 기간: 0.6 + 2 + 2 + 2 + 3.5 + 2 + 1.5 + 1 = **14.6주** (Phase 1 당초 계획 13~14주 대비 0.6~1.6주 여유분).

### 3.2 S0 사전 조사 (신규, 3~5일)

**목적**: 전수 조사로 S4 스크립트 스펙 확정 + R13(도메인 모델 파급) 경량 스파이크 + R3 LibreOffice 사전 검증.

**작업 목록**:

| # | 작업 | 출력 | 소요 |
|---|---|---|---|
| S0-1 | `tb_report_templates` 조직별 COUNT + 파일 크기 + 슬라이드 수 샘플링 | `s0_inventory_report.md` §1 | 0.5일 |
| S0-2 | `tb_document_templates` (16개 예상) 상세 리스트 + Jinja2 변수 수 | `s0_inventory_report.md` §2 | 0.5일 |
| S0-3 | `tb_agents.agent_type` DISTINCT + 5종 외 값 정제 필요성 | `s0_inventory_report.md` §3 | 0.25일 |
| S0-4 | `tb_organizations.organization_type` 부재 확정 + 필요성 사용자 컨펌 | `s0_inventory_report.md` §4 | 0.5일 |
| S0-5 | Ubuntu 서버(192.168.10.39)에서 LibreOffice + H2Orestart 구동 테스트 | `s0_inventory_report.md` §5 | 1일 |
| S0-6 | 조직별 상위 1개 템플릿 수동 검사(복잡도 분류: 단순/중간/극복잡) | `s0_inventory_report.md` §6 | 1일 |
| S0-7 | 007 migration 리뷰 + NOT VALID/VALIDATE 2단계 변경 적용 | Alembic 007 draft 수정 (실적용은 S1) | 0.5일 |

**DoD**:
- [ ] `docs/s0_inventory_report.md` 작성 완료
- [ ] 조직별 템플릿 총량 N (조직 수) × M (평균 템플릿 수) 확정
- [ ] LibreOffice 사이드카 채택/스킵 판정
- [ ] `organization_type` 008 migration 필요 여부 확정
- [ ] 007 draft 2단계 CHECK 적용 확정(NOT VALID → VALIDATE)

**블로커**: 없음 (Phase 2 승인 즉시 착수 가능).

**폐기 대상**: 없음 (조사만).

**병행 가능 작업**: S0-1~S0-4(database-architect) + S0-5(research-assistant) + S0-6(database-architect or user 협업) 병렬 실행.

**QA 게이트**: S0에는 QA 불필요. 조사 결과가 S1 이후 모든 결정의 입력.

### 3.3 S1 DocumentSchema MVP + 6 컴포넌트 (2주)

**목적**: Phase 1 skeleton(`modules/documents_v2/schemas.py` + `models.py`)을 end-to-end 실행 가능한 상태로 완성. Mode A 6-컴포넌트 문서를 JSON으로 생성 + HTML 프리뷰 확인 + Partial PATCH 동작.

**작업 목록**:

- S1-B1: `DocumentBuilder` ABC + `BuilderRegistry` 구현 (B15)
- S1-B2: `HtmlRenderer` (B16, 프리뷰 서버 렌더 fallback)
- S1-B3: `modules/documents_v2/router.py` (POST /v2/documents, GET, PATCH)
- S1-B4: `modules/documents_v2/service.py` (`DocumentServiceV2.generate` Mode A + `build_rag_context` from B1-a)
- S1-B5: `LLMClient.generate_structured(schema)` 통일 인터페이스 (B13)
- S1-B6: `agentic_rag.py` 삭제 (B10, 무참조 재확인 후)
- S1-B7: `PATCH /v2/documents/{id}` Partial DocumentSchema 처리 (jsonb_set)
- S1-B8: `tb_agents` CHECK 추가 (NOT VALID → VALIDATE 2단계, D3)
- S1-F1: 6 React 컴포넌트 실제 렌더 완성 (F3)
- S1-F2: `preview-pane/` iframe + postMessage 3종 (element-select, token-update, schema-patch-local)
- S1-F3: `edit-sidebar/` 6종 폼 (SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable)
- S1-F4: `prompt-box/` + `generateDocument()` API 호출
- S1-F5: `design-token-picker/` + `--doc-*` CSS 변수 시스템
- S1-F6: `useDocument/useDocumentMutation/useComponentRegeneration` 훅 실제 구현 (generate/fetchDocument/updatePage만 S1, 나머지는 후속)

**DoD**:
- [ ] `POST /v2/documents` Mode A로 6 컴포넌트 포함 문서 생성 성공
- [ ] HTML 프리뷰에서 6 컴포넌트 정상 렌더(data-component-id 셀렉터로 확인)
- [ ] `PATCH /v2/documents/{id}` Partial DocumentSchema로 컴포넌트 수정 동작
- [ ] `agentic_rag.py` 삭제, import 오류 없음
- [ ] 007 migration (신규 테이블 2개 + archive rename + agent CHECK) Phase 4 적용 완료
- [ ] QA 80+ 유지 (기존 기능 회귀 없음, 신규 경로 단위 테스트 커버)
- [ ] `sdet-agent`: `tests/test_documents_v2.py` 최소 10 케이스

**블로커**: S0 완료 (tb_agents DISTINCT 결과 확인).

**폐기 대상 (S1 말)**: `integrations/rag/agentic_rag.py` (B10).

**병행 가능**: S1-B1~B8 (backend-specialist) ∥ S1-F1~F6 (frontend-specialist). 인터페이스는 Phase 1 `documents-v2.ts` 시그니처로 lock.

**QA 게이트**: 80+ 필수. 하락 시 S2 착수 지연.

**리스크**: R1(Gemini/Claude Structured Output Discriminated Union 호환) → S1 말에 3 프로바이더 교차 테스트 필수. 실패 시 `StrictSchemaFallback` 평탄화 버전 추가(+2일).

### 3.4 S2 PPTX 빌더 + Mode A PoC + archive 리네이밍 (2주)

**목적**: PPTX 포맷 end-to-end. IDINO 슬라이드마스터 16종과 신규 `layout_resolver` 매핑. `tb_generated_reports` → `_archive` 리네이밍(읽기 전용).

**작업 목록**:
- S2-B1: `PptxBuilder` (B17) — Phase 0 `_build_pptx_from_structured` 분해 이관
- S2-B2: `pptx/components.py` (B1-c/B1-e 재배치: KPI/DataTable/BulletList/SlideTitle/Heading/Paragraph 6종 + Chart/Image 추가)
- S2-B3: `pptx/layout_resolver.py` — IDINO 마스터 실제 이름 ↔ layout enum 런타임 매핑 (B1-b 폐기 대체)
- S2-B4: `POST /v2/documents/{id}/export?format=pptx` Celery 비동기 + MinIO 업로드
- S2-B5: `workers/export_worker.py` 신규 — `BuilderRegistry.get(format).build(schema)` 위임
- S2-B6: `tb_generated_reports` → `_archive` 리네이밍(읽기 전용, D4)
- S2-F1: `/reports` 페이지 상단 배너 ("Mode A designer로 이동할까요?")
- S2-F2: `export-menu/` PPTX 다운로드 동작 + 작업 상태 폴링

**DoD**:
- [ ] `slide_report` 타입으로 Mode A 생성 → PPTX 다운로드 → IDINO 마스터 적용 확인(수동 열기)
- [ ] 구 `_build_layout_catalog()` 완전 미사용 (grep 확인)
- [ ] PPTX 6 컴포넌트 + Chart/Image 렌더
- [ ] `_archive` 테이블로 이관, 신규 쓰기 차단
- [ ] 현행 `/reports` 플로우 생존 (회귀 없음)
- [ ] QA 80+

**블로커**: S1 완료 (DocumentSchema + HTML 프리뷰).

**폐기 대상 (S2 말)**: `_build_layout_catalog()` 경로 (B1-b).

**병행 가능**: S2-F1~F2 (frontend) ∥ S2-B1~B6 (backend).

**QA 게이트**: 80+. PPTX A/B 비교 리뷰(현행 vs 신규) 5건 샘플.

**리스크**: R4(품질 체감 저하). PoC 단계 A/B 비교 필수. 실패 시 IDINO 마스터 추가 스타일 튜닝 +3일.

### 3.5 S3 컴포넌트 확장 + 이미지 자동 (2주)

**목적**: MVP 6종 외 S3 도입 컴포넌트 7종(SlideSubtitle/Quote/Callout/Timeline/ImageGrid/IconRow + Chart) + 이미지 자동 삽입 알고리즘(DALL-E 3 / Unsplash 키워드 분기) + 월별 쿼터 관리 UI.

**작업 목록**:
- S3-B1: Chart 컴포넌트 PPTX 네이티브 + DOCX matplotlib PNG
- S3-B2: Image/ImageGrid 컴포넌트 (Unsplash 우선 → DALL-E fallback)
- S3-B3: SlideSubtitle/Quote/Callout/Timeline/IconRow PPTX 빌더
- S3-B4: 관리자 UI: 조직별 월 DALL-E 쿼터 설정
- S3-F1: 7 React 컴포넌트 실제 렌더
- S3-F2: `edit-sidebar/forms/` 7 폼 추가
- S3-F3: 이미지 선택 UI (URL 입력 / 프롬프트 생성 / 자동 선택)

**DoD**:
- [ ] 13 컴포넌트 end-to-end (6 MVP + 7 신규)
- [ ] 한 문서에 Chart + Image 자동 삽입 성공
- [ ] DALL-E 쿼터 초과 시 403 반환 + 한국어 메시지
- [ ] QA 80+

**블로커**: S2 완료.

**폐기 대상**: 없음.

**병행 가능**: S3-B (backend) ∥ S3-F (frontend) ∥ S4 초반 (backend-specialist 분할).

**QA 게이트**: 80+.

**리스크**: R7(Playwright 메모리) — S3는 PDF 미포함이므로 해당 없음. R9(이미지 비용) — 쿼터로 1차 대응.

### 3.6 S4 Mode B + Mode 전환 + 조직별 PPTX 변환 (3.5주, 확장)

**목적**: Q3(Mode 전환)·Q4(조직별 PPTX) 반영. `tb_documents_v2_templates` 데이터 채움. `(admin)/template-designer/` 신설. TwoColumn/ThreeColumn/Hero/Comparison 레이아웃 컴포넌트 4종.

**작업 목록 (Mode B 기반)**:
- S4-B1: `DocumentServiceV2.generate` Mode B (slot-fill 프롬프트, `locked=true` 영역 고정)
- S4-B2: `LockedRegionError(422)` — Mode B에서 locked 편집 차단
- S4-B3: `integrations/document_builders/docx/jinja2_renderer.py` — B2-a 이관 (Mode B docx 경로)
- S4-B4: `POST /v2/documents/{id}/switch-mode` 엔드포인트 (Q3)
- S4-B5: `ModeTransitionValidator` — 자유→템플릿 전환 시 AI slot 매핑 로직(기존 Jinja2 slot 매칭 재활용)
- S4-B6: `audit_logs`에 `mode_transition` 이벤트 타입 추가 + 전/후 snapshot

**작업 목록 (Q4 조직별 PPTX 변환)**:
- S4-B7: `scripts/migrate_templates_to_v2.py` (S5-SC) — `tb_document_templates` + `tb_report_templates` 배치 변환
- S4-B8: 조직별 실행 + 실패 리포트 분리 (변환 실패 템플릿 read-only 아카이브)
- S4-B9: 조직 관리자에게 "템플릿 변환 결과 검토" 이메일/알림
- S4-B10: `tb_documents_v2_templates` 채움 + 샘플 검증(조직별 1개씩 수동 열기)

**작업 목록 (Q4 Organization 도메인 모델)**:
- S4-B11: S0 조사 결과에 따라 `tb_organizations.organization_type` Alembic 008 작성·적용 (옵셔널)

**작업 목록 (Frontend)**:
- S4-F1: `(admin)/template-designer/create/page.tsx` + `[templateId]/page.tsx` 신설
- S4-F2: Shell 재사용 — `components/document-designer/` props `mode="template_authoring"` + `allow_lock_toggle=true`
- S4-F3: `edit-sidebar/forms/LockToggleForm.tsx` + `AnchorNameForm.tsx` 관리자 전용 폼
- S4-F4: `(user)/designer/`에 "Mode 전환" 메뉴 (Export 메뉴 옆 드롭다운)
- S4-F5: TwoColumn/ThreeColumn/Hero/Comparison 레이아웃 4종 React 컴포넌트
- S4-F6: Mode B locked 컴포넌트 시각 구분 (자물쇠 아이콘 + dim overlay + `aria-disabled`)

**DoD**:
- [ ] Mode B 양식 채우기로 `weekly_status` 타입 문서 생성 성공
- [ ] `POST /v2/documents/{id}/switch-mode` 동작 (자유→템플릿 + 템플릿→자유 양방향)
- [ ] 조직별 PPTX 템플릿 자동 변환 성공률 ≥50% (S0 조사로 목표 재조정)
- [ ] `(admin)/template-designer/` 양쪽 라우트 동작
- [ ] 16 컴포넌트 + 4 레이아웃 (S1 6 + S3 7 + S4 4 + 레이아웃 ≈ 17)
- [ ] QA 80+ (Mode 전환 회귀 테스트 세트 추가)

**블로커**: S1 완료 + S2 완료 + S0 조사 완료.

**폐기 대상 (S4 말)**: Jinja2 양식 업로드 API read-only 전환 (B2-b), 관리자 UI에서 신규 업로드 불가.

**병행 가능**: S4-B1~B6 (backend-specialist) ∥ S4-B7~B10 (database-architect) ∥ S4-F1~F6 (frontend-specialist). 3인 병렬 필수.

**QA 게이트**: 80+ + **Mode 전환 회귀 테스트 세트** (§8 세부).

**리스크**:
- R11 (Mode 전환 자동 매핑 정확도): 매핑 실패 컴포넌트는 "자유 페이지로 보존" default policy. `conflict_policy=keep_all` 기본값.
- R12 (조직별 극복잡 템플릿 변환 실패): 실패 템플릿 read-only 아카이브 1년 + 관리자 수동 재작성 요청 접수.
- R13 (대학·회사 도메인 파급): S4에서 경량 스파이크 (권한 모델 파급 여부). Phase 1 범위 외지만 S4 DoD에 "도메인 파급 효과 정리" 한 줄 포함.

### 3.7 S5 HWPX 빌더 + hwp-extract (2주)

**목적**: `HwpxDocumentBuilder` 12종 구현(Q6) + 스타일/폰트까지(Q7) + hwp-extract 통합. 색상 주입은 S6 이연.

**작업 목록**:
- S5-B1: `integrations/document_builders/hwpx/builder.py` (B19)
- S5-B2: `hwpx/components.py` — 12종 빌더(SlideTitle/Heading/Paragraph/BulletList/DataTable/Image/Quote/TwoColumn/ThreeColumn/Hero/Comparison/ImageGrid)
- S5-B3: `_to_bytes()` 임시파일 경유(방법 A) 구현(Q5) + BytesIO 경로(방법 B) 시도
- S5-B4: IDINO_제목1/2/3, IDINO_본문, 목록 글머리표, 인용문 커스텀 스타일 등록
- S5-B5: 한컴 2020/2022 실기 열기 테스트(테스트 환경 확보 후)
- S5-B6: `<hp:pic>` 수동 XML 이미지 wrapper
- S5-B7: `integrations/docling/hwp_extract_adapter.py` — Volexity hwp-extract 통합 (B12 후속)
- S5-B8: 기존 olefile 파싱과 A/B 비교 → olefile 제거 여부 결정
- S5-B9: DOCX 빌더 구현 (B18) — B1-d 이관 + 22/22 컴포넌트 커버
- S5-B10: `jinja2_renderer.py` docxtpl 경로 Mode B docx 지원

**DoD**:
- [ ] HWPX 다운로드 한컴 2020/2022에서 열림 확인
- [ ] 한글 UTF-8 정상 표시
- [ ] `degraded_components`에 미지원 8종 기록
- [ ] 스타일 이름·폰트 반영 확인 (색상은 배제)
- [ ] DOCX 빌더 22 컴포넌트 커버
- [ ] hwp-extract로 HWP 업로드 파싱 A/B 승리
- [ ] QA 80+

**블로커**: S2 완료 (PptxBuilder 선행) + S3 완료 (Chart/Image 경로).

**폐기 대상 (S5 말)**: HWP 생성 UI 버튼(F5의 일부) → UI에서 "HWPX로 받기" 안내.

**병행 가능**: S5-B (backend+research-assistant 공동) ∥ S3 말미 / S6 초반과 부분 중복.

**QA 게이트**: 80+. **HWPX 실기 열기 테스트 통과 필수**.

**리스크**: R2(python-hwpx 품질). 1주차 빈 문서 → 단락 → 표 단계적 테스트. 실패 시 lxml 직접 OWPML 빌드 전환(+3일).

### 3.8 S6 RAG·보고서 품질 + HWPX 색상 + 특화 컴포넌트 (1.5주)

**목적**: 회의록 전용 프롬프트 + Agentic RAG ↔ Mode A 결합 + HWPX 색상 주입(Q7) + 특화 컴포넌트 4종 (ExecutiveSummary/RiskMatrix/ActionItemList/AttendeeList).

**작업 목록**:
- S6-B1: `minutes` 타입 프롬프트 — 참석자/결정사항/액션아이템 구조 필수
- S6-B2: Agentic RAG citations `metadata.citations` 주입
- S6-B3: 컴포넌트 본문 `[cite: id]` 마커 렌더
- S6-B4: HWPX 표 헤더 primary_color 배경 lxml 직접 조작(Q7)
- S6-B5: ExecutiveSummary/RiskMatrix/ActionItemList/AttendeeList 4종 빌더(HTML/PPTX/DOCX + HWPX 3종: Executive/ActionItem/Attendee, RiskMatrix는 HWPX degradation)
- S6-B6: `structured_schemas.py` 폐기 (B3 회의록 프롬프트 이관 후)
- S6-B7: `graph_rag.py` 활성 참조 재확인 후 제거 (B11)
- S6-B8: `source_document_ids` 역방향 질의 실측 (Q2) → 정규화 의사결정
- S6-F1: Citations 공통 컴포넌트 승격 (F9, components/citations/)
- S6-F2: 4 특화 컴포넌트 React + 폼

**DoD**:
- [ ] 회의록 생성 시 참석자/결정사항/액션아이템 구조화 확인
- [ ] Mode A에서 RAG 근거 문서 선택 시 `metadata.citations` 자동 삽입
- [ ] HWPX 표 헤더 배경 primary_color 적용 확인
- [ ] `structured_schemas.py` 제거
- [ ] `graph_rag.py` 제거 또는 활성화 결정 문서화
- [ ] `source_document_ids` 정규화 008 migration 스펙 초안 또는 ARRAY 유지 확정
- [ ] 20/22 컴포넌트 (S1 6 + S3 7 + S4 4 + 레이아웃 + S6 특화 4 ≈ 21~22)
- [ ] QA 80+

**블로커**: S5 완료 (HWPX 빌더 기본) + S3 완료 (Chart).

**폐기 대상 (S6 말)**: `structured_schemas.py`, `graph_rag.py`.

**병행 가능**: S6-B ∥ S6-F ∥ S7 초반과 부분 중복.

**QA 게이트**: 80+. 회의록 end-to-end 시나리오 테스트 추가.

### 3.9 S7 인라인 편집 + 부분 재생성 + QA + 병존 제거 (1주 축소)

**목적**: `regenerate-component/regenerate-page` API + 클라이언트 인라인 편집 + PDF export + 병존 시스템 완전 제거.

**작업 목록**:
- S7-B1: `POST /v2/documents/{id}/regenerate-component` + `/regenerate-page`
- S7-B2: `integrations/document_builders/pdf/builder.py` (Playwright HTML→PDF)
- S7-B3: `workers/report_generator.py` 삭제 (B1 전체)
- S7-B4: `workers/jinja2_engine.py` 삭제 (B2 나머지)
- S7-B5: `modules/reports/` 삭제 (B5)
- S7-B6: `modules/templates/` 삭제 (B6)
- S7-B7: `tb_report_templates`, `tb_document_templates`, `tb_generated_reports_archive` drop (Alembic 008+ 추가)
- S7-B8: `source_document_ids` 정규화 008 migration 적용 (Q2 결정에 따라)
- S7-F1: `(user)/reports/*` → `/designer/*` 301 리다이렉트 + 파일 삭제 (F5)
- S7-F2: `components/templates/variable-mapping-editor.tsx` 삭제 (F6)
- S7-F3: 인라인 편집 텍스트박스 within iframe (direct edit)
- S7-F4: 부분 재생성 UI (컴포넌트 선택 상태에서 "재생성" 버튼)
- S7-F5: 모바일 반응형 대응 (1023px 이하)

**DoD**:
- [ ] `modules/reports/` + `modules/templates/` 완전 제거 (grep 확인)
- [ ] `tb_*_archive` + `tb_document_templates` + `tb_report_templates` drop
- [ ] PDF export 동작 (10페이지 문서 기준)
- [ ] 부분 재생성 동작 (컴포넌트/페이지 단위)
- [ ] 인라인 편집 저장 (500ms debounce)
- [ ] QA 90+ (전체 회귀 + 성능 테스트)
- [ ] JSONB P95 < 100ms 실측 확인

**블로커**: S4 완료 + S6 완료 + QA 80+ 유지 확인.

**폐기 대상 (S7 말)**: B1, B2, B5, B6, D4, D5, D6, F5, F6, S2-SC.

**병행 가능**: S7-B1~B4 (backend) ∥ S7-F1~F5 (frontend). S7-B7은 반드시 마지막(모든 신규 경로 안정화 확인 후).

**QA 게이트**: **90+** (유일하게 상향). 전체 회귀 + 성능 테스트 + 사용자 시나리오 E2E 10건.

**리스크**: R6(이중 유지보수 종결). 제거 실패 시 1주 연기.

---

## 4. 데이터 마이그레이션 전략 (과제 3)

### 4.1 Dual-write 금지 원칙

S1부터 신규 경로는 **유일한 쓰기 경로**다. 이중 기록은 동기화 오류 원인이므로 채택하지 않는다. 대신 다음을 보장한다:

1. **신규 쓰기 = `tb_documents_v2`로만**. `tb_generated_reports`는 S2에 `_archive`로 rename + write-lock.
2. **읽기는 양쪽 허용** (S7까지). 기존 `/reports`는 `tb_generated_reports_archive`에서 읽기, `/designer`는 `tb_documents_v2`에서 읽기.
3. **데이터 이관은 오직 `tb_document_templates` + `tb_report_templates` → `tb_documents_v2_templates` 단방향**(S4).
4. **`tb_generated_reports`는 이관하지 않는다**. 과거 생성물은 archive에서만 조회, 새 구조로 변환 불필요(제품 가치 없음).

### 4.2 기존 테이블의 운명

#### 4.2.1 `tb_report_templates` (Q4 확장 반영)

- **S0**: 전수 조사.
  - `SELECT organization_id, COUNT(*) FROM tb_report_templates GROUP BY organization_id` — 조직별 건수
  - `SELECT id, name, LENGTH(schema::text), pg_size_pretty(octet_length(template_storage_path)) FROM tb_report_templates` — 파일 크기 추정
  - 상위 조직별 1개 템플릿을 MinIO에서 다운로드해 복잡도 분류(단순/중간/극복잡)
- **S2**: 쓰기 차단(신규 업로드 API disable, 읽기만).
- **S4**: 조직별 배치 자동 변환 (`scripts/migrate_templates_to_v2.py`).
  - 단순: 자동 변환 성공률 목표 ≥80%
  - 중간: 자동 변환 성공률 목표 ≥50% + 관리자 검토
  - 극복잡: 자동 변환 스킵 + 관리자 수동 재작성 요청
- **변환 실패 처리**: `tb_report_templates_failed`(읽기 전용) 뷰로 원본 보관 1년.
- **S7**: drop.

#### 4.2.2 `tb_document_templates` (Jinja2)

- **S0**: 16개 상세 조사 + Jinja2 변수 수 카운트.
- **S4**: 수동 재작성 상위 5개 우선 + 자동 변환 시도 나머지 11개.
  - `DocumentSchema skeleton + locked=true + slot_definitions` 구조로 변환
  - Jinja2 변수 → `slot_definitions[].anchor` + `category`(session_auto/user_input/ai_generated 유지)
- **S7**: drop.

#### 4.2.3 `tb_generated_reports`

- **S2**: `tb_generated_reports_archive`로 rename + FK 이름 유지(drop 시 단순 테이블 drop).
- **S2~S7**: 읽기 전용. UI에서 "보관된 보고서" 탭으로만 노출.
- **S7**: drop. **신규 경로로 이관하지 않음** (제품 가치 없음, 과거 생성물은 재생성 가능).

#### 4.2.4 `tb_agents`

- **S0**: `SELECT DISTINCT agent_type FROM tb_agents` — 5종 외 값 존재 여부 확인.
- **S1 직전**: `ALTER TABLE tb_agents ADD CONSTRAINT ck_tb_agents_agent_type CHECK (...) NOT VALID` → `VALIDATE CONSTRAINT ck_tb_agents_agent_type` 2단계 (downtime-free).
- **S4**: Mode 전환 대응 에이전트 추가 (선택). 기존 5종으로 충분하면 스킵.

#### 4.2.5 `tb_organizations` (Q4 후속)

- **S0**: `\d tb_organizations` — `organization_type` 컬럼 부재 확인.
  - 현재 상태(2026-04-20): `name`, `slug`, `description`, `settings` 4개 필드만 존재. `organization_type` 없음.
- **S0 사용자 컨펌**: "대학/회사/공공" 구분이 권한·템플릿·UI에 실제 영향을 주는가?
- **영향 있음 판정 시 S4**: Alembic 008 `organization_type VARCHAR(20) NOT NULL DEFAULT 'company' CHECK IN ('company','university','public','other')` + `tb_organizations` 관리 UI에 타입 선택 추가.
- **영향 없음 판정 시**: 008 생략, `settings->'organization_type'` JSONB에 기록하는 경량 경로만.

### 4.3 신규 테이블 채우기 순서

| 테이블 | 생성 | 최초 데이터 | 정상 쓰기 경로 |
|---|---|---|---|
| `tb_documents_v2` | S1 (007 migration) | S1 이후 사용자 생성 | Mode A/B `DocumentServiceV2.generate` |
| `tb_documents_v2_templates` | S1 (007 migration) | S4 (변환 스크립트) | `(admin)/template-designer/` 저장 |

### 4.4 롤백 안전성

- 007 downgrade: 신규 테이블 drop + archive rename 복구 + CHECK drop. 데이터 손실 없음.
- 008 downgrade (conditional): `organization_type` drop (기본값 적용이므로 역변환 단순).
- S7 drop migrations (008~): **downgrade 불가** (테이블 drop은 비가역). 따라서 S7 DoD는 "모든 archive 1년 보관 완료 확인"을 포함.

---

## 5. 리스크 매트릭스 v2 (과제 4)

표기 통일: D=DB, F=FE, H=HWPX, R=아키텍처, U=사용자 결정 파생, O=운영.

점수 = 심각도(1~3) × 확률(1~3). 최대 9.

### 5.1 통합 리스크 표

| ID | 리스크 | 심각도 | 확률 | 점수 | 영향 스프린트 | 대응 (사전 + 발생 시) | 모니터링 지표 | 소유자 |
|---|---|---|---|---|---|---|---|---|
| **R1** | Gemini/Claude Discriminated Union Structured Output 불완전 지원 | 3 | 2 | **6** | S1 | 사전: S1 말 3-provider 교차 테스트. 발생: `StrictSchemaFallback` 평탄화 스키마(+2일). | provider별 Structured validation 실패율 | backend-specialist |
| **R6** | `modules/reports` 병존 기간 이중 유지보수 비용 | 2 | 3 | **6** | S2~S7 | 사전: S4 read-only 전환, S7 제거. 공유 유틸 선이관. 발생: 핫픽스 대응 우선순위 매트릭스. | `modules/reports` 변경 PR 수 | backend-specialist |
| **U3** | Mode 전환 시 자동 매핑 정확도 낮음 → 사용자 불만 (R11, Q3 파생) | 2 | 3 | **6** | S4 | 사전: 매핑 실패 시 "자유 페이지로 보존" default. 발생: `conflict_policy` 명시 UI + 롤백 버튼. | Mode 전환 이벤트별 매핑 실패율 | backend-specialist |
| **U4** | 조직별 극복잡 PPTX 템플릿 자동 변환 실패 (R12, Q4 파생) | 3 | 2 | **6** | S4 | 사전: S0 복잡도 분류 → 극복잡은 스크립트 대상에서 제외. 발생: read-only 아카이브 1년 + 관리자 재작성 요청. | 조직별 변환 성공률 | database-architect |
| **H2** | python-hwpx 생성 HWPX 한컴 2020 미열림 (비표준 XML) | 3 | 2 | **6** | S5 | 사전: S5 1주차 빈 문서 → 단락 → 표 단계적 테스트. 발생: lxml 직접 OWPML 빌드(+3일). | 한컴 열기 성공률 | research-assistant |
| **D5** | Jinja2 템플릿 자동 변환 실패율 > 50% | 2 | 2 | **4** | S4 | 사전: S4 PoC 5개로 실측. 발생: 상위 5개 수동 재작성 + 자동 변환 포기. | 16개 중 변환 성공 건수 | database-architect |
| **H1** | python-hwpx 이미지 API 미성숙 (Image/ImageGrid 구현 불가) | 2 | 2 | **4** | S5 | 사전: lxml `<hp:pic>` wrapper 자체 구현. 발생: HWPX 이미지 미지원 `degraded_components` 기록. | Image 컴포넌트 HWPX degradation 빈도 | research-assistant |
| **H3** | LibreOffice 사이드카 Ubuntu 서버(Xeon E5-2620 v4, x86-64-v1) 실행 불가 | 2 | 2 | **4** | S0/S5 | 사전: S0-5 사전 구동 검증. 실패 시 사이드카 스킵, PDF는 Playwright만. | `soffice --headless --version` 결과 | research-assistant |
| **R2** | `python-hwpx` 신생 라이브러리 유지보수 리스크 | 2 | 2 | **4** | S5/S7 | 사전: MIT 라이선스 확보, lxml fallback 경로 준비. 발생: fork 유지 전략. | GitHub 커밋 주기 | research-assistant |
| **R3** | 기존 16 IDINO 템플릿 자동 변환 실패율 높음 (= D5 일부) | 2 | 2 | **4** | S4 | 중복. D5와 단일 관리. | — | — |
| **R4** | 하드코딩 제거 후 기존 PPTX 품질 체감 저하 | 3 | 1 | **3** | S2 | 사전: S2 PoC A/B 비교 5건. 발생: IDINO 마스터 추가 스타일 튜닝(+3일). | PPTX 사용자 만족도 (스프린트 말 설문) | backend-specialist |
| **R7** | Playwright PDF 메모리 폭주 | 2 | 2 | **4** | S7 | 사전: 전용 `pdf-worker` 분리, 동시 2건 제한. 발생: 큐 백오프 + 사용자 대기. | PDF 워커 OOM 카운트 | backend-specialist |
| **R8** | Mode A/B 동시 지원으로 UX 혼란 | 2 | 2 | **4** | S1/S4 | 사전: 2-카드 진입 페이지 + onboarding tour. 발생: UX 리디자인(S7). | `/designer/create` 이탈률 | frontend-specialist |
| **R10** | DocumentSchema v1.0 → v1.1 migration 복잡 | 3 | 1 | **3** | S1~S6 | 사전: `schema_version` 필수 + 버전별 loader. 새 필드는 Optional만. 발생: dual-loader 유지. | schema_version distinct values | backend-specialist |
| **D1** | `document_schema` JSONB TOAST 임계 초과 → SELECT * 저하 | 2 | 2 | **4** | S1~S7 | 사전: ORM `defer("document_schema")` 기본. 목록 API `document_schema` 미조회 강제. | `SELECT * FROM tb_documents_v2` 호출 검출 (pg_stat_statements) | database-architect |
| **D2** | GIN 인덱스 쓰기 비용 (Mode A batch 지연) | 2 | 1 | **2** | S1~S7 | 사전: jsonb_path_ops 선택. 발생: batch 크기 제한 + 백그라운드 재인덱싱. | tb_documents_v2 insert P95 | database-architect |
| **D3** | `tb_agents.agent_type` CHECK 추가 실패 (5종 외 값 존재) | 2 | 2 | **4** | S0/S1 | 사전: S0-3 선행 DISTINCT + 정제. NOT VALID → VALIDATE 2단계. | S0-3 결과 | database-architect |
| **D6** | `source_document_ids UUID[]` orphan 참조 | 1 | 2 | **2** | S1~S6 | 사전: UI에 "원본 삭제됨" 표시. 발생: S6에서 조인 테이블 정규화(Q2). | orphan 비율 (S6 실측) | database-architect |
| **U1** | 대학/회사/공공 도메인 파급 효과 예측 불가 (R13, Q4 파생) | 2 | 2 | **4** | S0/S4 | 사전: S0 사용자 컨펌. 발생: 경량 스파이크 + ADR 작성(S4). | 도메인 이슈 발생 건수 | enterprise-architect |
| **R9** | DALL-E 3 비용 예산 초과 | 1 | 2 | **2** | S3 | 사전: 조직별 월 쿼터. Unsplash 우선. 발생: 403 + 수동 요청 승인 UI. | 월간 DALL-E API 호출 건수 | backend-specialist |
| **R5** | Schema JSON 토큰 한계 (LLM 응답 잘림) | 2 | 1 | **2** | S1~S7 | 사전: 페이지 상한 20, 컴포넌트 상한 10/페이지. 발생: 부분 재생성. | LLM 응답 `finish_reason=length` 빈도 | backend-specialist |
| **O1** | Ubuntu 서버 메모리 부족 (x86-64-v1 + LibreOffice + Playwright 동시) | 3 | 2 | **6** | S5/S7 | 사전: S0-5 free -h 확인. 발생: LibreOffice 스킵 + Playwright만 + worker 재기동 정책. | 메모리 피크 (Prometheus) | research-assistant |
| **O2** | S0 조사 일정 지연 (데이터 접근 권한 / 서버 접속 문제) | 1 | 2 | **2** | S0 | 사전: Phase 2 승인 시점 서버 접속 계정·권한 동반 확인. 발생: 조사 축소(상위 5조직만). | S0 경과일 | enterprise-architect |

### 5.2 정량 Top 5 (점수순)

1. **R1** (6) — Multi-provider Structured Output 호환. 일정 +2일 리스크.
2. **R6** (6) — 병존 유지보수. S2~S7 내내 누적.
3. **U3** (6) — Mode 전환 자동 매핑 정확도. 사용자 만족 직결.
4. **U4** (6) — 조직별 PPTX 변환 실패. Q4 파생 직접 리스크.
5. **H2** (6) — HWPX 한컴 호환. S5 완료 자체가 흔들림.
6. **O1** (6) — 서버 메모리. 운영 환경 제약(동률).

### 5.3 정책 의사결정 필요 리스크

- **U1** (조직 도메인 파급) — S0 사용자 컨펌 필수. "대학"이 권한/템플릿/UI 어디까지 영향 주는가?
- **H3** / **O1** — LibreOffice 사이드카 채택/스킵. S0 결과에 따라 S5 DoD 일부 조정.
- **D6** / **Q2** — `source_document_ids` 조인 테이블 정규화. S6 실측 후 결정.

---

## 6. S0 실행 계획 (과제 5)

Phase 2 승인 후 즉시 실행 가능. 3~5일. 산출물: `docs/s0_inventory_report.md`.

### 6.1 실행 체크리스트

| # | 작업 | 실행 명령 (복사-붙여넣기) | 판단 기준 | 실패 시 대응 |
|---|---|---|---|---|
| **S0-1** | `tb_report_templates` 전수 조사 | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT organization_id, COUNT(*) AS tmpl_count FROM tb_report_templates GROUP BY organization_id ORDER BY tmpl_count DESC;"` | 10건 이상이면 S4 배치 변환 스크립트 필수. 0건이면 Q4 영향 제거 가능. | 쿼리 실패 시 Postgres 컨테이너 상태 확인 (`docker logs docutil-postgres`). |
| **S0-2** | `tb_report_templates` 파일 크기·형식 분포 | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT format, COUNT(*), AVG(LENGTH(template_storage_path)) FROM tb_report_templates GROUP BY format;"` | pptx 다수 확인. hwp/hwpx 포함 여부 확인. | — |
| **S0-3** | `tb_document_templates` (Jinja2) 상세 | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT id, name, template_type, jsonb_array_length(jinja2_variables) AS var_count FROM tb_document_templates ORDER BY var_count DESC;"` | 변수 50+ 템플릿은 극복잡으로 분류. | — |
| **S0-4** | `tb_agents.agent_type` DISTINCT | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT agent_type, COUNT(*) FROM tb_agents GROUP BY agent_type ORDER BY COUNT(*) DESC;"` | 5종(chatbot/report/proposal/minutes/freeform_doc) 외 값 존재 시 → 데이터 정제 선행 (`UPDATE tb_agents SET agent_type='chatbot' WHERE agent_type=...`). | 정제 필요 시 D3 리스크 활성화. |
| **S0-5** | `tb_organizations` 구조 확인 | `docker exec docutil-postgres psql -U docutil -d docutil -c "\d+ tb_organizations"` | `organization_type` 부재 확인 (예상). 존재 시 Q4 파생 질문 일부 해소. | 추가 조직 확장 시 008 migration 필요. |
| **S0-6** | `tb_organizations` 데이터 | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT id, name, slug, settings FROM tb_organizations;"` | 조직 수·이름 확인. "대학" 관련 조직 파악. | — |
| **S0-7** | LibreOffice Xeon E5-2620 v4 구동 테스트 (Ubuntu 서버) | `ssh idino@192.168.10.39 "soffice --headless --version"` → 버전 출력 확인 | 버전 출력 성공 = x86-64-v1 호환. 실패 시 사이드카 스킵. | 실패 시 H3/O1 리스크 활성화, PDF는 Playwright 전담. |
| **S0-8** | 서버 메모리 여유 | `ssh idino@192.168.10.39 "free -h && docker stats --no-stream"` | 여유 1.5GB 이상 = LibreOffice 사이드카 수용. | 부족 시 O1 활성화. |
| **S0-9** | 조직별 상위 1 템플릿 복잡도 샘플링 | 별도 python 스크립트 (S0에 작성): `python scripts/s0_inventory_report.py --sample=1` | 슬라이드 20+ + 플레이스홀더 30+ = 극복잡 분류. | 샘플 분석 실패 시 S4 착수 전까지 보완. |
| **S0-10** | `tb_generated_reports` 용량 | `docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('tb_generated_reports')) FROM tb_generated_reports;"` | 1GB 이상이면 S2 archive rename 시 일시 lock 주의 (`SET lock_timeout='5s'`). | — |
| **S0-11** | `agentic_rag.py` 외부 참조 재확인 | `grep -rn "from app.integrations.rag.agentic_rag\|AgenticRAGEngine\|RAGStrategy" backend/app --include="*.py"` | 외부 참조 0건 = S1 즉시 삭제 가능. | 참조 발견 시 제거 경로 수립. |
| **S0-12** | `graph_rag.py` 외부 참조 재확인 | `grep -rn "from app.integrations.rag.graph_rag\|GraphRAGEngine" backend/app --include="*.py"` | 외부 참조 0건 = S6에 즉시 삭제 가능. | 참조 발견 시 S6 경로 수립. |
| **S0-13** | 007 migration 2단계 CHECK 적용 편집 | `backend/alembic/versions/007_documents_v2_and_template_consolidation.py` 편집: `op.create_check_constraint(..., postgresql_not_valid=True)` + 별도 `op.execute("ALTER TABLE tb_agents VALIDATE CONSTRAINT ck_tb_agents_agent_type")` 2단계 분리 | 파일 변경 + git diff 확인 | — |

### 6.2 최초 5개 실행 명령 (Phase 2 승인 후 즉시 복사 실행 가능)

```bash
# 1. tb_report_templates 조직별 건수 + 포맷 분포
docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT organization_id, format, COUNT(*) AS cnt FROM tb_report_templates GROUP BY organization_id, format ORDER BY cnt DESC;"

# 2. tb_document_templates (Jinja2) 상세
docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT id, name, template_type, jsonb_array_length(jinja2_variables) AS var_count FROM tb_document_templates ORDER BY var_count DESC LIMIT 20;"

# 3. tb_agents.agent_type DISTINCT (D3 선행)
docker exec docutil-postgres psql -U docutil -d docutil -c "SELECT agent_type, COUNT(*) FROM tb_agents GROUP BY agent_type;"

# 4. tb_organizations.organization_type 부재 확인 (Q4 파생)
docker exec docutil-postgres psql -U docutil -d docutil -c "\d+ tb_organizations"

# 5. LibreOffice Ubuntu 서버 구동 + 메모리 여유 (H3/O1)
ssh idino@192.168.10.39 "soffice --headless --version && free -h && docker stats --no-stream | head -5"
```

### 6.3 S0 산출물 (`docs/s0_inventory_report.md`)

구조 초안:
- §1 tb_report_templates 인벤토리 (조직별, 포맷별, 복잡도별)
- §2 tb_document_templates 인벤토리 (Jinja2 변수 수, template_type)
- §3 tb_agents.agent_type 정제 필요성
- §4 tb_organizations.organization_type 결정 (008 migration 필요/불필요)
- §5 LibreOffice 사이드카 채택/스킵 판정
- §6 조직별 복잡도 샘플링 결과
- §7 007 migration 2단계 CHECK 적용 diff
- §8 S4 배치 변환 스크립트 스펙 초안
- §9 R11/U3/U4 리스크 점수 업데이트

### 6.4 S0 DoD

- [ ] `docs/s0_inventory_report.md` 작성 완료
- [ ] S4 작업량 확정 (조직 수·템플릿 수)
- [ ] LibreOffice 사이드카 채택/스킵 판정 기록
- [ ] `organization_type` 008 migration 필요 여부 사용자 컨펌
- [ ] 007 draft 2단계 CHECK 편집 완료
- [ ] U1/U3/U4 리스크 점수 재조정

---

## 7. 롤백 전략 (과제 6)

### 7.1 스프린트별 롤백 가능성

| 스프린트 | 롤백 트리거 | 롤백 액션 | 소요 |
|---|---|---|---|
| **S0** | 없음 (조사만) | — | — |
| **S1** | QA <78 + 신규 경로 P0/P1 ≥2건 | 007 migration downgrade + `modules/documents_v2/` 코드 PR revert + frontend designer 라우트 비활성 | 0.5일 |
| **S2** | PPTX 품질 체감 저하 + QA <78 | 기존 `/reports` 유지(실질 상태), 신규 `/v2/documents/export?format=pptx` feature flag off | 0.5일 |
| **S3** | 신규 컴포넌트 렌더 오류 P0 | 해당 컴포넌트 React 렌더를 placeholder로 복귀(컴포넌트 제거 아님) | 0.25일 |
| **S4** | Mode B 전환 부분 실패 | **Mode 전환 API 비활성** (switch-mode 403) + 자동 변환 실패 템플릿은 기존 경로 read-only 유지. 조직별 템플릿 변환 50% 미만 성공 시 수동 재작성으로 선회. | 1일 |
| **S5** | HWPX 열기 실패 (한컴 2020) | **HWPX export 비활성** + UI에서 "HWPX 지원 준비 중" + DOCX 대체 제공 | 0.5일 |
| **S6** | RAG 개선 회귀 (챗봇 품질 저하) | H1~H7 핫픽스 상태로 복귀 (agentic_search commit revert). HWPX 색상 주입 비활성. | 1일 |
| **S7** | 병존 시스템 제거가 사용자 혼란 유발 | **S7-B7 / F1 연기 1주** — archive rename 유지하되 drop 연기. `/reports` 리다이렉트 비활성. | 1주 연기 |

### 7.2 롤백 트리거 상세 조건

**QA 하락 트리거**:
- QA <78 이틀 연속 + 원인이 본 스프린트 변경으로 귀결
- P0 버그 2건 이상 미해결 48시간 초과

**품질 체감 트리거**:
- 사용자 만족도 설문(스프린트 말 5점 척도) 평균 <3.5
- A/B 비교 리뷰에서 신규 경로 품질이 기존 대비 현저히 낮음 (리뷰어 3명 중 2명 이상)

**성능 트리거**:
- JSONB P95 >150ms (목표 <100ms 대비 50% 초과)
- PPTX 생성 P95 >30초 (목표 <15초)

### 7.3 롤백 회피 원칙

1. **작은 변경 우선**: 각 스프린트는 feature flag로 경로 전환 가능하게 설계. 완전 revert보다 flag off 우선.
2. **하이브리드 기간**: S2~S6는 신규/기존 병존. 기존 경로는 S7까지 생존.
3. **핫픽스 트랙 활용**: 스프린트 중 P0는 핫픽스 트랙으로 처리(별도 브랜치). 스프린트 롤백과 분리.
4. **QA 게이트를 80+로 유지**: 70점대 통과는 예외 조건(§8.4) 충족 시만.

---

## 8. QA 게이트 (과제 7)

### 8.1 스프린트별 QA 목표

| 스프린트 | QA 목표 | 게이트 성격 |
|---|---|---|
| S0 | QA 불필요 (조사만) | — |
| S1 | **80+** | 신규 경로 단위 테스트 + 기존 회귀 없음 |
| S2 | **80+** | + PPTX 품질 A/B 비교 통과 |
| S3 | **80+** | + 이미지 자동 삽입 시나리오 |
| S4 | **80+** | + **Mode 전환 회귀 테스트 세트** (§8.2) |
| S5 | **80+** | + **HWPX 실기 열기 필수** (§8.3) |
| S6 | **80+** | + 회의록 end-to-end + Citations 자동 삽입 |
| S7 | **90+** | 전체 회귀 + 성능 테스트 + E2E 10건 (§8.5) |

### 8.2 S4 Mode 전환 회귀 테스트 필수 세트

- [ ] 자유 생성 문서 → 템플릿 끼워맞추기 (자유→템플릿)
  - 매핑 성공률 ≥70% 컴포넌트
  - 매핑 실패 컴포넌트는 "자유 페이지"로 보존 (default policy)
  - audit_logs에 mode_transition 이벤트 기록
- [ ] 템플릿 채우기 문서 → 자유 편집 (템플릿→자유)
  - `locked=true` 해제 정상 동작
  - 전환 후 편집 가능 확인
- [ ] `conflict_policy=discard_unmapped` 동작 확인
- [ ] Mode 전환 중 네트워크 실패 시 원상 복구
- [ ] 감사 로그 전/후 snapshot JSONB 저장 확인
- [ ] Mode 전환 후 `template_id` 일관성(소프트 체크) 위반 시 한국어 메시지 422

### 8.3 S5 HWPX 실기 테스트 (환경 확보 시)

- [ ] python-hwpx 2.9.0 생성 → 한컴 2020 열기
- [ ] 동일 파일 → 한컴 2022 열기
- [ ] 동일 파일 → Polaris Office 열기
- [ ] 표 5×4 렌더 정상
- [ ] 한글 텍스트 UTF-8 표시
- [ ] 스타일 이름(IDINO_제목1/2/3, IDINO_본문) 반영
- [ ] 이미지 삽입 후 표시
- [ ] LibreOffice + H2Orestart 열기 + ODT 변환

**환경 확보 방법**: Phase 3 실행 로드맵 수립 시 테스트 PC(한컴 정품)를 사내 기존 자산에서 확보. 불가 시 Polaris Office(무료) + LibreOffice+H2Orestart만으로 대체 확인 가능(품질 기준 80% 낮춤).

### 8.4 QA 78~79 예외 통과 기준

기본은 80+이지만 78~79에서 다음 조건 **모두** 충족 시 통과 가능:
1. 하락 원인이 기존 기능(비본 스프린트)에서 발생한 P2 버그 (본 스프린트 회귀 아님)
2. 해당 P2는 다음 스프린트 초반 핫픽스 일정 확보
3. 본 스프린트 고유 DoD는 전부 충족
4. 사용자 또는 enterprise-architect의 명시적 승인

### 8.5 S7 전체 회귀 + 성능 테스트 시나리오 10건

1. 신규 사용자 회원가입 → 로그인
2. 문서 업로드 (Docling 파싱) → 검색 (Agentic RAG)
3. 챗봇 세션 시작 → Citations 확인
4. Mode A 슬라이드 보고서 생성 (5 페이지)
5. Mode B 회의록 양식 채우기
6. Mode 전환 (자유 → 템플릿)
7. 컴포넌트 부분 재생성
8. PDF export (10 페이지 문서)
9. HWPX export + 한컴 열기
10. 관리자 조직별 템플릿 변환 결과 검토
11. (+ 성능) `tb_documents_v2` JSONB 조회 P95 <100ms (100만 행 더미 데이터)

---

## 9. 팀 역량 배치 (과제 8)

DocUtil은 사용자 1인 + Claude Code 협업 구조. 각 스프린트별 주 담당 에이전트:

### 9.1 에이전트별 주 스프린트 매핑

| 에이전트 | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 |
|---|---|---|---|---|---|---|---|---|
| **backend-specialist** | | ★ | ★ | | ★ | ★ | ★ | ★ |
| **frontend-specialist** | | ★ | ○ | ★ | ★ | | ○ | ★ |
| **database-architect** | ★ | ○ | ○ | | ★ | | ○ | ○ |
| **research-assistant** | ★ | | | | | ★ | | |
| **sdet-agent** | | ○ | ○ | ○ | ★ | ○ | ○ | ★ |
| **enterprise-architect** | ○ | ○ | | | ○ | | ○ | ○ |

★ = 주담당, ○ = 보조

### 9.2 병렬 가능/순차 필수 구분

**병렬 가능**:
- **S1**: backend (`modules/documents_v2/*`, B10 제거) ∥ frontend (6 컴포넌트 + designer shell)
- **S3/S4**: 같은 기간 backend/frontend 분리 가능
- **S4**: backend (Mode B API) ∥ database-architect (조직별 변환) ∥ frontend (template-designer + Mode 전환 UI)
- **S5**: backend (HWPX 빌더) ∥ research-assistant (hwp-extract A/B)

**순차 필수**:
- **S0 → S1**: 007 migration 2단계 CHECK 적용은 S0 결과 입력 후만 가능
- **S1 → S2/S4/S5**: 스키마 lock 선행
- **S2 → S3**: PptxBuilder 선행 (S3 Chart는 PPTX 네이티브)
- **S5 → S6**: HWPX 기본 빌더 선행 (S6 색상 주입은 빌더 위에)
- **S4/S6 → S7**: 모든 신규 경로 안정화 후 병존 제거

### 9.3 sdet-agent 운영 방식

- 각 스프린트 말 3일: 해당 스프린트 테스트 커버리지 작성 + QA 실행
- S4 + S7은 주담당 (Mode 전환 회귀 + 전체 회귀)
- 지속적 실행: `scripts/qa_quick.sh` 일 1회 자동 (Ubuntu 서버 cron)

### 9.4 enterprise-architect 운영 방식

- S0 시작 시점 검토 + 결과 승인
- S1/S4/S7 착수 전 DoD 리뷰
- 각 스프린트 말 리스크 매트릭스 업데이트
- Q3·Q4 외 신규 정책성 의사결정 발생 시 ADR 승격

---

## 10. Phase 3 인계

Phase 3 실행 로드맵은 본 전환계획을 기반으로 다음을 산출한다:

1. **주차별 간트 차트** — S0 3~5일 + S1~S7 14.6주 포함, 에이전트별 병렬 타임라인
2. **GitHub 이슈 분해** — 스프린트별 ~10개 이슈 + DoD 체크박스
3. **마일스톤 정의** — M1(S1 완료), M2(S2+S3 완료), M3(S4 완료), M4(S5+S6 완료), M5(S7 완료 = Phase 4 종료)
4. **리스크 재평가** — S0 결과 반영한 점수 조정
5. **팀 커뮤니케이션 계획** — Claude Code 세션 단위 작업 분배, 스프린트 말 회고 템플릿

Phase 3 진입 조건:
- [x] Phase 1 기준선(v1.6) + 의사결정(v1.1) 확정
- [x] Phase 2 전환계획(본 문서) 작성
- [ ] S0 실행 완료 및 `s0_inventory_report.md` 산출
- [ ] 사용자가 Phase 3 착수를 승인

---

## 11. 변경이력

| 날짜 | 버전 | 변경 | 담당 |
|---|---|---|---|
| 2026-04-20 | v1.0 | 최초 작성. Phase 1(v1.6) + phase1_decisions(v1.1) 반영. Q3·Q4 뒤집힘 흡수. 자산 39+11항목 분류. S0 신설. 리스크 매트릭스 v2 통합. | enterprise-architect |

---

**(문서 끝)**
