# DocUtil — Technical Specification (기술 스펙)

> **문서 버전**: v1.0 (2026-04-19 최초 작성)
> **작성 단계**: Phase 0 진단 진행 중 — 일부 섹션은 진단 완료 후 보강 예정
> **담당**: Claude Code + 사용자 합의 기반
> **연관 문서**: `user_mig/project_status.md` (구현 현황), `.claude/rules/` (개발 규약)

---

## 0. Executive Summary

DocUtil은 조직 문서를 업로드·파싱·벡터화하여 RAG 기반 챗봇·검색·보고서 생성을 제공하는 풀스택 시스템이다. 2026년 3월까지 핵심 기능이 대부분 구현되었으나, **문서 생성 엔진에 구조적 결함**이 누적되어 2026-04-19부터 **전면 재설계**를 시작한다.

### 재설계 핵심 방향

1. **두 가지 문서 생성 모드 동시 지원**
   - **Mode A (자유 생성)**: Gamma/Claude Design 방식 — 기본 브랜드 템플릿만 지정 + 프롬프트 → AI가 레이아웃·이미지·디자인을 자동 생성
   - **Mode B (양식 채우기)**: 현재 방식 계승·개선 — 고정 양식에 AI가 내용만 채움
2. **공통 엔진 (접근법 C: 컴포넌트 라이브러리 + DocumentSchema)**: HTML/CSS 라이브 프리뷰 + PPTX/DOCX/HWP/HWPX Export
3. **HWP + HWPX 양쪽 지원**: 기존 HWP 유지하면서 HWPX 추가
4. **RAG·컨텍스트 파이프라인 개선**: 회의록·요약 품질 부실 문제 해결

---

## 1. 구현 현황 (2026-03-30 기준)

### 1.1 기술 스택

| 계층 | 기술 |
|---|---|
| Frontend | Next.js 16 (App Router, Turbopack), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2 async, Pydantic v2, Alembic |
| Database | PostgreSQL 17 |
| Vector DB | Qdrant v1.16 (dense 1536D + sparse BM25) |
| Object Storage | MinIO |
| Message Queue | RabbitMQ 4.0 + Celery |
| Cache | Redis 7 |
| LLM | OpenAI, Azure OpenAI, Gemini, Claude, vLLM/SGLang (멀티 프로바이더) |
| Monitoring | Prometheus + Grafana + Loki |
| Infra | Docker Compose, Nginx, Ubuntu 24.04 운영 서버 (192.168.10.39) |

### 1.2 완료된 기능 (요약)

| 도메인 | 완료 상태 |
|---|---|
| 인증·인가 (JWT + RBAC + 6단계 가시성) | ✅ |
| 조직·부서·프로젝트 관리 | ✅ |
| 문서 업로드·파싱 (PDF, DOCX, PPTX, HWPX, HWP) | ✅ |
| 벡터 임베딩 + 하이브리드 검색 (dense + sparse RRF) | ✅ |
| 챗봇 (WebSocket + REST fallback) | ✅ |
| Agentic RAG 검색 (재검색 루프 최대 3회) | ✅ |
| 템플릿 관리 (Jinja2 + Structured 2가지 모드) | ✅ |
| Jinja2 변수 자동 추출·카테고리 분류 | ✅ |
| 에이전트 시스템 (chatbot/report/proposal/minutes) | ✅ |
| 보고서 생성 (DOCX/PPTX, Celery 비동기) | ✅ |
| IDINO 슬라이드마스터 + Structured Outputs | ✅ |
| DALL-E 3 + Unsplash 이미지 생성 | ✅ |
| 멀티 LLM 프로바이더 (OpenAI/Azure/Gemini/Claude) | ✅ |
| 감사 로그·API 키 관리 | ✅ |
| Ubuntu 서버 배포 + 데이터 이관 | ✅ |

상세 내용은 `user_mig/project_status.md`의 "핵심 기능 구현 상태" 섹션 참조.

### 1.3 기존 해결 이슈

현재까지 34개 이슈 해결 완료 (PPT 슬라이드마스터 관련 #19~#21·#32, 한글 파일명 #4·#23·#30 등). 상세 목록은 `project_status.md` 9절 참조.

---

## 2. 재설계 대상 이슈 (2026-04-19 식별)

사용자 보고 + 진단 결과를 기반으로 **5개 핵심 이슈**를 식별. 해결 방식은 단편적 수정이 아니라 **문서 생성 엔진 전면 재설계**로 접근.

### 2.1 이슈 목록

| # | 이슈 | 심각도 | 재설계 그룹 |
|---|---|---|---|
| 1 | Jinja2 양식 매핑은 동작하지만 **사용성 개선 필요** | 중간 | A (생성 엔진) |
| 2 | PPT 슬라이드마스터가 등록된 양식으로 **PPT 생성 실패** | **높음** | A (생성 엔진) |
| 3 | **HWP 양식 업로드·생성 실패**, HWPX 지원 확장 필요 | 높음 | B (한국 포맷) |
| 4 | 기준 문서·Chat 로드 불안정 → **회의록·요약 내용 부실** | 높음 | C (RAG 파이프라인) |
| 5 | Claude Design/Gamma식 **"제약된 자동 문서 생성"** 신규 기능 필요 | 신규 | A (생성 엔진) |

### 2.2 이슈 그룹화

```
그룹 A: 문서 생성 엔진 재설계 (#1, #2, #5)
  ↓
  통합 엔진: 컴포넌트 라이브러리 + DocumentSchema
  ├─ Mode A: 자유 생성 (Gamma/Claude Design식)
  └─ Mode B: 양식 채우기 (Jinja2 UX 개선)

그룹 B: 한국 문서 포맷 (#3)
  ↓
  HWP (기존 유지) + HWPX (신규 추가)
  파싱·생성 라이브러리 재정비

그룹 C: RAG·컨텍스트 파이프라인 (#4)
  ↓
  회의록·요약 품질 개선
  기준 문서·Chat 로드 디버깅
```

---

## 3. 목표 아키텍처

### 3.1 문서 생성 엔진 (그룹 A)

**접근법 C — 컴포넌트 라이브러리 + DocumentSchema 기반 이중 렌더러**

```
[LLM: Opus 4.7 / GPT-4o / Claude / Gemini]
      ↓ Structured Outputs (화이트리스트 컴포넌트만 허용)
[DocumentSchema JSON]
      ↓
 ┌────┴────────────────────────┐
 ↓                             ↓
[HTML Renderer]          [파일 빌더들]
 (Next.js iframe)          ├─ PPTX (python-pptx)
     ↓                     ├─ DOCX (docxtpl)
 라이브 프리뷰              ├─ PDF  (Playwright HTML→PDF)
 인라인 편집                ├─ HWP  (pyhwp/hwp5 + 템플릿 치환)
     ↓                     └─ HWPX (lxml 기반 XML 조작)
 사용자 편집이 Schema로 환원
```

#### 3.1.1 DocumentSchema (개념)

```json
{
  "documentId": "uuid",
  "type": "slide_report | docx_report | minutes | proposal | one_pager",
  "mode": "free_generation | template_fill",
  "templateId": "optional-uuid (Mode B에서 사용)",
  "designTokens": {
    "primary": "#0A4FC2",
    "accent": "#FF6B35",
    "font": "Pretendard",
    "spacing": "compact | normal | relaxed"
  },
  "slides": [
    {
      "id": "s1",
      "layout": "title | kpi_dashboard | two_column | ...",
      "locked": false,
      "components": [
        { "type": "SlideTitle", "text": "..." },
        { "type": "KPI", "label": "...", "value": "...", "delta": "..." },
        { "type": "Chart", "chartType": "bar", "data": {...} }
      ]
    }
  ]
}
```

#### 3.1.2 컴포넌트 라이브러리 (1차 MVP 20~25개)

| 카테고리 | 컴포넌트 |
|---|---|
| 텍스트 | `SlideTitle`, `SlideSubtitle`, `Heading`, `Paragraph`, `BulletList`, `Quote`, `Callout` |
| 데이터 | `KPI`, `DataTable`, `Chart(bar/line/pie)`, `Timeline` |
| 미디어 | `Image`, `ImageGrid`, `IconRow` |
| 레이아웃 | `TwoColumn`, `ThreeColumn`, `Hero`, `Comparison` |
| 보고서 특화 | `ExecutiveSummary`, `RiskMatrix`, `ActionItemList` |

**각 컴포넌트는 세 가지 구현을 동시에 갖는다**:
1. React 렌더러 (프리뷰용, Tailwind CSS)
2. PPTX 빌더 (python-pptx, IDINO 마스터 placeholder 매핑)
3. DOCX 빌더 (docxtpl 또는 python-docx)

HWP·HWPX·PDF는 별도 파이프라인:
- PDF: HTML 프리뷰를 Playwright로 변환
- HWP: 템플릿 치환 방식 (아래 3.2절)
- HWPX: XML 조작 (아래 3.2절)

#### 3.1.3 Mode A vs Mode B 통합

| | Mode A (자유 생성) | Mode B (양식 채우기) |
|---|---|---|
| 입력 | 프롬프트 + 디자인 토큰만 | 템플릿 ID + 슬롯별 입력 |
| LLM 역할 | Schema 전체 생성 | 빈 슬롯만 채움 |
| 자유도 | 슬라이드 개수·레이아웃·이미지 자동 | 레이아웃·개수 고정 |
| 수정 가능 | 모든 컴포넌트 | 잠금 영역 외만 |
| 사용 시나리오 | "Q1 매출 보고서 만들어줘" | "이 분기보고서 양식에 채워줘" |

### 3.2 HWP + HWPX 전략 (그룹 B)

> 상세 기술 선택은 Phase 0-C (research-assistant) 조사 결과를 기다린 뒤 확정.

**방향**:
- **HWP 파싱**: 기존 `olefile` 기반 유지 + 품질 개선 (표·이미지 추출 강화)
- **HWP 생성**: 템플릿 치환 방식 권장 (사용자가 HWP 양식 업로드 → LLM이 변수값 생성 → 기존 HWP 파일의 해당 부분만 교체)
- **HWPX 파싱**: 기존 ZIP/XML 파싱 유지
- **HWPX 생성**: `lxml` 기반 XML 조작 (표준 스펙 존재)
- **공통**: DocumentSchema → HWP/HWPX 변환 레이어 신규 작성 (기존 컴포넌트 재활용)

### 3.3 RAG·컨텍스트 파이프라인 개선 (그룹 C)

> Phase 0-B 진단 결과에 따라 확정. 현재 추정되는 개선 포인트:

1. **기준 문서 주입 표준화**: 보고서 생성 시 사용자 지정 문서가 확실히 컨텍스트에 포함되도록 파이프라인 통일
2. **Chat 히스토리 요약 개선**: 토큰 한계 고려한 계층적 요약 전략
3. **회의록·요약 프롬프트 재작성**: 현재 프롬프트의 구체적 약점 개선
4. **Agentic RAG 확장 적용**: 현재 챗봇·검색에만 적용된 Agentic 루프를 회의록·요약에도 적용 검토
5. **Citations 필수화**: 회의록·요약 모든 문단에 근거 청크 인용

---

## 4. 전환 로드맵

### Phase 0 — 현황 진단 (진행 중, 3~4일)

| 하위 작업 | 담당 | 상태 |
|---|---|---|
| 문서 생성 엔진 코드 분석 (그룹 A) | code-analysis-specialist | 진행 중 |
| RAG 파이프라인 코드 분석 (그룹 C) | code-analysis-specialist | 진행 중 |
| HWP/HWPX 기술 옵션 조사 (그룹 B) | research-assistant | 진행 중 |
| 진단 결과 종합 → Phase 1 입력 | Claude Code | 대기 |

### Phase 1 — 목표 아키텍처 확정 (5~6일)

| 하위 작업 | 담당 |
|---|---|
| DocumentSchema 최종 스펙 | enterprise-architect |
| 컴포넌트 라이브러리 카탈로그 (20~25개 props·제약 명세) | enterprise-architect + frontend-specialist |
| HWP/HWPX 기술 선택 확정 | enterprise-architect (Phase 0-C 결과 기반) |
| 데이터베이스 스키마 변경안 (Alembic) | database-architect |
| RAG 파이프라인 리디자인 | backend-specialist |

### Phase 2 — 전환 계획 (3일)

- 기존 자산 분류 (재활용·수정·폐기)
- 마이그레이션 순서 (기존 기능 유지하며 점진 교체)
- 데이터·파일 이전 계획
- 리스크 매트릭스

### Phase 3 — 실행 로드맵 (1~2일)

- 스프린트 단위 구현 계획 (주차별)
- QA 기준 (QA 점수 80+ 유지)
- 배포·롤백 전략

### Phase 4 — 구현 (10~12주)

| 스프린트 | 내용 | 소요 |
|---|---|---|
| S1 | DocumentSchema + React 컴포넌트 5개 MVP + HTML 렌더러 | 2주 |
| S2 | PPTX 빌더 연동 + Mode A PoC (1개 보고서 유형) | 2주 |
| S3 | 컴포넌트 15개 추가 + 이미지 자동 삽입 | 2주 |
| S4 | Mode B 통합 + 슬롯 시스템 + Jinja2 UX 개선 | 1.5주 |
| S5 | HWP 생성 (템플릿 치환) + HWPX 생성 (XML) | 2주 |
| S6 | RAG 파이프라인 개선 (회의록·요약 품질) | 1.5주 |
| S7 | 인라인 편집 + 부분 재생성 + QA | 2주 |

**전체 예상**: 계획 2~2.5주 + 구현 10~12주 = **약 13~14주**

---

## 5. Claude Design 대비 목표 달성도

| 기능 | 목표 달성도 | 비고 |
|---|---|---|
| 자연어 → 슬라이드 생성 (Mode A) | 85~90% | Opus 4.7 + 컴포넌트 제약 |
| 라이브 HTML 프리뷰 | 95% | iframe 렌더링 동등 |
| 인라인 편집 | 80% | 컴포넌트 단위 |
| 실시간 슬라이더 미세조정 | 60% | 디자인 토큰만 허용 |
| 디자인 시스템 자동 적용 | 75% | IDINO 토큰 강제 |
| PPTX Export (IDINO 규정) | **100%** (Claude Design보다 우수) | 기존 자산 활용 |
| HWP/HWPX Export | Claude Design에 없음 (DocUtil 고유) | — |
| 양식 채우기 모드 (Mode B) | Claude Design에 없음 (DocUtil 고유) | — |
| **종합** | **약 75~80%** Claude Design UX + DocUtil 고유 강점 | |

---

## 6. 개발 원칙 (재강조)

재설계 중에도 다음 규약을 **반드시** 준수:

- `.claude/rules/architecture.md` P1~P6
  - 단일 구현 (LLMClient, MinIOService, settings)
  - 고정 모듈 구조 (router/service/schemas/models/utils/constants/exceptions)
  - 절대 import만
  - Router → Service → Integration 단방향 흐름
  - Structured Outputs 우선
- `.claude/rules/anti-patterns.md` 금지 패턴
- `.claude/rules/domain-model.md` 용어 통일
- 커밋 메시지: `[module] 한글 설명`
- 모든 변경 후: ruff + pytest + `scripts/lint_structure.py` + QA 80점 이상

---

## 7. Phase 0 진단 결과 (2026-04-19 완료)

병렬 에이전트 3개 진행 완료. 다음 세 섹션에 요약. 전체 상세 진단 로그는 각 에이전트 출력 파일 참조.

---

### 7.1 문서 생성 엔진 진단 (그룹 A)

#### 7.1.1 PPT 슬라이드마스터 실패 근본원인 ⭐

**위치**: `backend/app/workers/report_generator.py:1250-1344` 의 `_build_layout_catalog()`

**원인**: 함수가 **IDINO 조직 전용 한글 레이아웃 이름을 하드코딩으로 매칭**한다.

```
매칭 대상 (하드코딩): "1_표지", "Ⅰ. 본문", "본문 - Ⅰ", ...
```

- 다른 조직이 업로드한 마스터 → catalog가 **빈 딕셔너리**가 됨
- 모든 슬라이드가 `slide_layouts[0]`으로 fallback
- 플레이스홀더 idx(0/1/10/11/16)도 IDINO 마스터에 고정되어 일반 PPT에선 매칭 실패

**해결 방향**: 하드코딩 레이아웃 이름 제거 → 업로드된 마스터의 레이아웃을 동적으로 파싱하고, LLM Structured Output에 "이 마스터의 사용 가능한 레이아웃 목록"을 주입해 LLM이 선택하게 한다. 이는 접근법 C의 **컴포넌트 라이브러리**가 해결해야 할 핵심 기능.

#### 7.1.2 추가 Critical 버그 4개 (즉시 핫픽스 가능)

| # | 위치 | 증상 | 해결 방향 |
|---|---|---|---|
| B1 | `GeneratedReport` ORM 모델 | `rendering_mode`, `jinja2_context` 컬럼 누락 (Alembic 004는 DB에 추가했지만 모델이 모름) | ORM 모델에 컬럼 추가 |
| B2 | `backend/app/modules/reports/service.py` | MinIO 호출 잘못된 import → ReportTemplate 업로드/삭제 시 AttributeError | `MinIOService` 인스턴스 사용 (P1 규칙 위반) |
| B3 | 보고서 생성 흐름 | `_session_user`가 `generation_params`에 주입 안 됨 → Jinja2 session_auto 항상 빈 문자열 | 라우터에서 주입 추가 |
| B4 | 템플릿 시스템 이중화 | `tb_report_templates` + `tb_document_templates` 동시 존재, 3개 생성 분기 로직 중복 | 단일 테이블로 통합 (`tb_document_templates` 일원화) |

#### 7.1.3 Jinja2 UX 개선 포인트

- 빈 양식 자동 분석이 **표 기반만 지원** (가로 교차 패턴), 일반 문서 헤딩·번호 패턴은 별도 경로
- 변수 카테고리 자동 분류(`session_auto/user_input/ai_generated`)는 휴리스틱 + LLM fallback인데 LLM 경로가 불안정
- 매핑 에디터는 dialog/inline 2가지 모드가 분기돼 있어 코드 중복

---

### 7.2 RAG·컨텍스트 파이프라인 진단 (그룹 C)

#### 7.2.1 회의록·요약 부실의 근본원인 Top 5

| # | 위치 | 증상 | 검증 방법 |
|---|---|---|---|
| R1 | `backend/app/modules/reports/service.py:312-326` | ⭐ **`source_chat_session_id`가 서버에서 증발** — 요청의 chat session 필드를 ORM row에 저장 안 함. 어떤 Chat을 지정해도 워커는 NULL을 봄 | `SELECT source_chat_session_id FROM tb_generated_reports ORDER BY created_at DESC LIMIT 10` → 전부 NULL이면 확정 |
| R2 | `report_generator.py` 전반 | Chat → 보고서 경로 코드 부재 — `tb_chat_messages` 조회 로직 자체가 없음. R1을 고쳐도 Chat transcript가 LLM 컨텍스트에 들어갈 출구 없음 | 코드 grep: `tb_chat_messages` 참조 없음 확인 |
| R3 | `report_generator.py:571` `_load_source_chunks` | LIMIT 100 + `(document_id UUID, chunk_index)` 정렬 → 다중 문서 지정 시 UUID 순서로 뒤쪽 문서 통째로 누락. 삼중 컷(100 → 50 → 25000자) 누적 | 워커 로그에서 "소스 청크 로드 완료: 100개"가 고정으로 나오는지 |
| R4 | 회의록 생성 프롬프트 (line 3016-3022) | 회의록 전용 프롬프트·Structured 스키마 **부재** — "보고서/제안서 AI" 프롬프트로 고정. 참석자/안건/결정사항/액션아이템 구조 유도 안 됨 → LLM이 자유형 문단을 뱉어 "부실"로 체감 | 프롬프트 audit |
| R5 | `AgenticRAGEngine` | 완전한 **dead code**. 유일하게 동작하는 `AgenticSearchService`는 WebSocket `deep_search=true`일 때만, REST 챗봇은 옵션 미전달로 영구 비활성 | 코드 리뷰 |

#### 7.2.2 즉시 가능한 개선

1. `reports/service.py`에서 `source_chat_session_id` 저장 누락 fix (R1)
2. `_load_source_chunks` LIMIT 100 → 문서별 분할 로딩 (R3)
3. 회의록 전용 Structured Schema + 프롬프트 추가 (R4)
4. Chat 메시지 조회 코드 추가 (R2)
5. `AgenticRAGEngine` dead code 제거 또는 활성화 (R5)

상세 감사 기록은 **메모리 `rag_context_audit_2026_0419.md`** 에 저장됨.

---

### 7.3 HWP/HWPX 기술 조사 (그룹 B)

#### 7.3.1 핵심 발견

- **HWP(이진) 생성은 Linux/Docker 환경에서 사실상 불가능** — 한컴 SDK는 Windows 전용, pyhwpx는 win32com 래퍼, LibreOffice+H2Orestart는 읽기 전용
- **HWPX 생성만 현실적 경로** — ZIP+XML 구조라 순수 Python 가능
- 2026년 현재 HWP와 HWPX 공존, 신규 문서는 HWPX 비중 증가
- pyhwp는 **AGPL 라이선스** → 상용 서비스에 법적 위험 (사용 금지 권장)

#### 7.3.2 권장 조합 (시나리오 B 균형형)

| 작업 | 도구 | 라이선스 | 비고 |
|---|---|---|---|
| HWP 파싱 | `olefile` (현행) + `hwp-extract` (Volexity) | BSD + Apache 2.0 | 텍스트 + 표/이미지 추출 보강 |
| HWPX 파싱 | `python-hwpx` (airmang) | MIT | 단락/표 구조 보존, 현재 수동 zipfile 파싱 교체 |
| HWP 생성 | **포기** | — | UI에서 "HWPX로 다운로드" 안내 |
| HWPX 생성 | `python-hwpx` (airmang) | MIT | `_build_hwpx_from_structured()` 신규 구현 |
| PDF 변환 | LibreOffice + H2Orestart 사이드카 (옵션, Phase 2) | MPL + LGPL | 컨테이너 +1GB, JRE 필요 |

**예상 공수**: 5~8일 (신규 아키텍처 Phase 4 S5에 편입)

**리스크 및 대응**:
- `python-hwpx` 신생 라이브러리 → lxml fallback 유지
- 사용자가 HWP 이진 고집 → UI 안내 ("HWPX는 한컴 2020+에서 열림")
- pyhwp 혼입 금지 → requirements.txt 검증

#### 7.3.3 주요 라이브러리 링크

- [airmang/python-hwpx](https://github.com/airmang/python-hwpx) — HWPX 읽기/쓰기/생성 (MIT)
- [volexity/hwp-extract](https://github.com/volexity/hwp-extract) — HWP 추출 (Apache 2.0, 2024-11)
- [ebandal/H2Orestart](https://github.com/ebandal/H2Orestart) — LibreOffice HWP 확장 (MPL, 2025-10)
- [한컴테크 — Python HWPX 파싱](https://tech.hancom.com/python-hwpx-parsing-1/)

---

## 8. 즉시 핫픽스 트랙 (Phase 1과 병행 가능)

재설계가 진행되는 동안 운영 영향이 큰 버그는 **핫픽스 트랙**으로 먼저 수정한다. 각 건의 난이도가 낮아 재설계 의사결정과 독립적으로 처리 가능.

| # | 항목 | 난이도 | 담당 |
|---|---|---|---|
| H1 | `GeneratedReport` ORM에 `rendering_mode`/`jinja2_context` 컬럼 추가 (B1) | 낮음 | backend-specialist |
| H2 | `reports/service.py` MinIO 직접 import 제거, `MinIOService` 사용 (B2) | 낮음 | backend-specialist |
| H3 | `_session_user`를 `generation_params`에 주입 (B3) | 낮음 | backend-specialist |
| H4 | `source_chat_session_id` 저장 누락 fix (R1) | 낮음 | backend-specialist |
| H5 | `_load_source_chunks` 문서별 분할 로딩 (R3) | 중간 | backend-specialist |
| H6 | 회의록 전용 Structured Schema + 프롬프트 (R4) | 중간 | backend-specialist |
| H7 | Chat 메시지 조회 코드 추가 (R2) | 중간 | backend-specialist |

**핫픽스 효과**: QA 점수 73 → 80+ 복귀 예상, 사용자가 체감하는 회의록·요약 부실 및 PPT 생성 실패 즉시 개선.

---

## 9. Phase 1 아키텍처 기준선 (2026-04-19 완료)

Phase 1 목표 아키텍처가 확정되었다. 상세 스펙은 **`docs/phase1_architecture.md`** 참조. 아래는 핵심 결정사항 요약.

### 9.1 핵심 결정

1. **DocumentSchema를 SSOT로 채택** — LLM Structured Output의 유일한 형태. HTML 프리뷰/PPTX/DOCX/HWPX/PDF 모두 이 스키마만 소비.
2. **Mode A/B는 동일 스키마의 두 생성 경로** — 렌더러·빌더는 분기하지 않고 `mode` 필드와 `locked` 플래그만으로 표현.
3. **22개 컴포넌트 MVP 카탈로그** — Pydantic v2 Discriminated Union 기반. MVP 5종(S1), 전체 22종은 S1~S6에 분산 도입.
4. **신규 모듈 `documents_v2/` + 빌더 레이어 `integrations/document_builders/`** — 기존 `modules/reports`, `modules/templates`, `workers/report_generator.py`는 S2~S7에 걸쳐 단계적 폐기.
5. **`DocumentBuilder` ABC + Registry(P7 신설)** — 모든 파일 포맷 빌더는 `build(schema) -> bytes` 시그니처 준수. 신규 포맷은 ABC 구현 + 레지스트리 등록만으로 완성.

### 9.2 DocumentType 확정 (7종)

`slide_report` / `docx_report` / `proposal` / `minutes` / `one_pager` / `weekly_status` / `freeform_doc`

### 9.3 기술 선택 확정

- HWPX: `python-hwpx` (airmang, MIT) — 파싱/생성 양쪽
- HWP: 생성 불가(UI 안내), 파싱은 `olefile` + `hwp-extract`(Apache 2.0)
- PDF: Playwright HTML→PDF (Celery `pdf-worker` 전용)
- LLM Structured Output: OpenAI/Azure strict → 기본 / Gemini·Claude → `LLMClient.generate_structured` 내부에서 평탄화·Tool Use 변환

### 9.4 스프린트 DoD 요약

- **S1**(2주): Schema + 5 MVP 컴포넌트 + React 렌더러 (의존성 잠금 지점)
- **S2**(2주): PPTX 빌더 + layout_resolver + `_build_layout_catalog` 제거
- **S3**(2주): 컴포넌트 13종 누적 + 이미지 생성 통합
- **S4**(1.5주): Mode B + locked 페이지 + 템플릿 에디터
- **S5**(2주): HWPX 빌더(14 컴포넌트) + DOCX 22 컴포넌트 완성
- **S6**(1.5주): 회의록 전용 프롬프트 + Agentic RAG/Mode A 결합 + 특화 컴포넌트 4종
- **S7**(2주): 인라인 편집 + 부분 재생성 + 기존 모듈 완전 제거 + QA 90+

**총 13주** (Phase 2~3 계획 2~2.5주 + 구현 10.5주 + 버퍼). techspec §4 로드맵(13~14주)과 일치.

### 9.5 Top 3 리스크

1. **R1** — Gemini/Claude Discriminated Union 호환. `StrictSchemaFallback` 준비 + S1 DoD에 멀티프로바이더 테스트 포함.
2. **R6** — `modules/reports` 병존 기간 이중 유지보수. S4부터 read-only, S7 완전 제거.
3. **R2** — `python-hwpx` 신생 라이브러리. PoC 우선 + lxml fallback + 한컴 뷰어 호환 매트릭스.

### 9.6 후속 에이전트 인계

- **database-architect**: `tb_documents_v2` 신설, `tb_document_templates` 통합, Alembic 006 작성, 기존 테이블 아카이브 마이그레이션. 입력은 `phase1_architecture.md` 부록 E.1.
- **frontend-specialist**: 22개 React 컴포넌트, `designer` UX, Mode A/B 라우팅. 입력은 부록 E.2.
- **research-assistant**: `python-hwpx` API 탐색, 컴포넌트 14종 PoC, LibreOffice+H2Orestart 사이드카 설계. 입력은 부록 E.3.

---

## 10. Phase 1 — DB 설계 (2026-04-19 완료)

상세는 [`phase1_database_design.md`](phase1_database_design.md). 아래는 핵심 결정 요약.

### 10.1 신규 테이블

- **`tb_documents_v2`** — 생성된 모든 문서의 단일 엔티티. `document_schema` JSONB 에 DocumentSchema v1 전체 저장. 목록 API 필터 축 (`document_type`, `mode`, `organization_id`, `status`, `generated_by_user_id`) 은 비정규화 컬럼으로 병행 보관. `schema_version INT` 로 JSONB 스키마 메이저 버전 관리.
- **`tb_documents_v2_templates`** — Mode B 양식 채우기 템플릿. `skeleton_schema` JSONB + `slot_definitions` JSONB (`session_auto / user_input / ai_generated` 카테고리).

### 10.2 인덱스

- B-tree: `(organization_id, ins_dt DESC)`, `(generated_by_user_id, ins_dt DESC)`, `(document_type)`, `(mode)`, `(status)`, `(agent_id)`, `(template_id)`.
- GIN `jsonb_path_ops`: `document_schema`, `skeleton_schema` — `@>` 컨테인먼트 쿼리 (컴포넌트 타입 포함 문서 검색 등).
- 함수 기반 인덱스 후보 (Phase 4 관찰 후 활성화): `citations` 보유·`degraded_components` 보유 부분 인덱스.

### 10.3 기존 테이블 변경 최소화

- **`tb_agents.agent_type`**: CHECK 제약 **최초 도입** (003 migration 시 누락 확인). 값 5 종 — `chatbot / report / proposal / minutes / freeform_doc`. 운영 적용 시 `NOT VALID` + `VALIDATE CONSTRAINT` 2 단계 권장.
- **`tb_generated_reports`** → `tb_generated_reports_archive` 소프트 리네이밍. 읽기 전용으로 1 년 유지 후 S7 에 완전 drop.
- `tb_report_templates`, `tb_document_templates` 는 본 migration 에서 수정하지 않음. 데이터 변환은 Phase 4 S4 에 별도 스크립트로 수행.

### 10.4 Alembic 파일 번호

- 사용자 요청 원문은 "006 draft" 였으나 기존 저장소에 이미 `006_evaluation_module` 이 존재 → **`007_documents_v2_and_template_consolidation.py`** 로 승격 (`down_revision='006_evaluation'`). 범위는 부록 E.1 과 동일.

### 10.5 Top 3 리스크

1. **D3** — `tb_agents` 기존 레코드가 5종 밖의 값을 가질 경우 CHECK 추가 실패. Phase 4 S0 `SELECT DISTINCT agent_type` 점검 선행.
2. **D5** — 16 개 Jinja2 템플릿 자동 변환 실패율 높음. 상위 5 개 수동 재작성 우선 + 나머지 관리자 요청.
3. **D1** — `document_schema` JSONB TOAST 오버헤드. ORM 레이어 `defer()` 기본화, 목록 API 는 JSONB 컬럼 조회 금지.

### 10.6 선행 조건 / 미해결 질문 (enterprise-architect 재확인 필요)

- `freeform_doc` 이 DocumentType enum 과 agent_type enum 에 동일 값으로 중복 존재 — 의도 여부 확인.
- `source_document_ids UUID[]` 유지 vs 조인 테이블 정규화 — 역방향 조회 빈도에 따라 결정.
- `tb_report_templates` 의 PPTX 자산이 IDINO 마스터 외 **조직별 템플릿** 인지 확인 — phase1_architecture.md §5.3 항목 5 에는 언급 누락.

---

## 11. Phase 1 — 프론트엔드 설계 (2026-04-19 완료)

상세는 [`phase1_frontend_design.md`](phase1_frontend_design.md)와 동반 문서 [`phase1_frontend_wireframes.md`](phase1_frontend_wireframes.md). 핵심 결정 요약은 아래와 같다. 실제 React 구현은 Phase 4 S1에서 착수한다.

### 11.1 폴더 구조

- `frontend/src/app/(user)/designer/{create,fill/[templateId]}/` — Mode A/B 라우트 placeholder 2건 + `[documentId]/`은 Phase 4 S1 추가.
- `frontend/src/components/document-designer/{preview-pane,edit-sidebar,prompt-box,export-menu,design-token-picker}/` — 3분할 shell의 5개 패널. 디렉토리 단위로 확장 여지 확보.
- `frontend/src/components/document-schema/{components,layouts,renderer}/` — Schema → React 순수 렌더 레이어 (iframe·PDF 서버렌더 공용).
- `frontend/src/components/citations/` — 챗봇에서 승격될 공통 Citations(S6).
- `frontend/src/lib/document-schema/use-document.ts` — `useDocument` / `useDocumentMutation` / `useComponentRegeneration` 3종 훅 시그니처.
- `frontend/src/lib/api/documents-v2.ts` — 8개 함수 시그니처 (`generateDocument`, `fillTemplate`, `fetchDocument`, `updatePage`, `regenerateComponent`, `regeneratePage`, `deleteDocument`, `exportDocument`) + `EXPORT_FORMATS` 상수.
- `frontend/src/types/document-schema.ts` — 22개 컴포넌트 discriminated union 수동 draft. Phase 4 S1에 `openapi-typescript` 자동 생성으로 교체.
- `frontend/src/styles/document-tokens.css` — `--doc-*` CSS 변수 스펙 (`--color-*` 셸 토큰과 네임스페이스 분리).

### 11.2 핵심 결정 3가지

1. **`--doc-*` 토큰 네임스페이스 분리** — 앱 셸(globals.css `--color-*`)과 프리뷰(`--doc-*`)를 분리해 조직별 브랜드(custom 프리셋) 적용 시 셸 UI 오염 방지.
2. **좌측 30% Tab(편집 | 프롬프트) 공유** — 동시 노출 대신 탭 전환. 선택 대상 변화 시 편집 탭을 자동 활성화.
3. **iframe 프리뷰 고수** — Tailwind/shadcn 토큰이 `--doc-*`를 덮지 못하게 하는 확실한 경계. postMessage 프로토콜(element-select, token-update, schema-patch)은 S1에서 확정.

### 11.3 MVP 컴포넌트 스켈레톤 (6건)

- `SlideTitle`, `Heading`, `Paragraph`, `BulletList`, `KPI` + `DataTable` — Phase 1 시그니처 + placeholder + 한글 TODO 주석만. 실제 렌더는 S1.
- 합집합 6건 이유: `phase1_architecture.md` §3.2 MVP 5종(Heading 포함)과 본 에이전트 과제 입력의 MVP 5종(DataTable 포함)이 불일치 → 양쪽 커버.

### 11.4 UX 와이어프레임

- 3분할 (30 / 55 / 15): 좌 편집·프롬프트 Tab / 중 iframe 프리뷰 / 우 Export + 디자인 토큰.
- 5가지 인터랙션 흐름: (1) 프롬프트 생성, (2) 컴포넌트 클릭 편집, (3) Mode B locked 시각 구분, (4) Export 드롭다운, (5) 부분 재생성.
- 1023px 이하 점진적 붕괴. S1은 ≥ 1280px만 지원, RWD 완성은 S7.

### 11.5 기존 UI 이관 계획

| 경로 | Phase 4 시점 | 조치 |
|---|---|---|
| `/reports` | S2 | "designer로 이동" 배너 |
| `/reports` | S4 | 신규 생성 버튼 `/designer/create` 라우팅 |
| `/reports` | S7 | 301 리다이렉트 후 파일 삭제 |
| `/templates` | S4 | Schema 에디터 탭 추가, Jinja2 탭 병존 |
| `/templates` | S7 | Jinja2 탭 제거, Schema 전용 |
| `/search` Jinja2 변수 입력 | S4 | "이 결과로 문서 만들기" 딥링크로 대체 |
| `components/chat/` Citations | S6 | `components/citations/`로 승격 |
| `components/templates/variable-mapping-editor.tsx` | S7 | 파일 삭제, `edit-sidebar/forms/*`로 재설계 |

### 11.6 미해결 질문 (enterprise-architect 재확인 요망)

- **Q1** MVP 5종 정의 불일치(Heading vs DataTable): S1 DoD의 "5-컴포넌트 end-to-end 문서" 기준 확정 필요.
- **Q2** `/designer`의 라우트 그룹 — `(user)`만? admin 템플릿 편집 재사용 경로 결정 필요.
- **Q3** iframe postMessage 프로토콜 + 서버 PATCH 단위(전체 교체 vs JSON Patch) — backend-specialist와 공동 결정 필요.

---

## 12. 변경 이력

| 날짜 | 버전 | 내용 | 담당 |
|---|---|---|---|
| 2026-04-19 | v1.0 | 최초 작성 (Phase 0 진단 개시 기준) | Claude Code + 사용자 |
| 2026-04-19 | v1.1 | §7 Phase 0 진단 결과 · §8 핫픽스 트랙 추가 | Claude Code |
| 2026-04-19 | v1.2 | §9 Phase 1 아키텍처 기준선 추가 (`phase1_architecture.md` 연계) | enterprise-architect |
| 2026-04-19 | v1.3 | §10 Phase 1 DB 설계 추가 (`phase1_database_design.md` 연계) | database-architect |
| 2026-04-19 | v1.4 | §13 Phase 1 HWPX 어댑터 설계 추가 (`phase1_hwpx_adapter.md` 연계) | research-assistant |
| 2026-04-19 | v1.5 | §11 Phase 1 프론트엔드 설계 추가 (`phase1_frontend_design.md`·`phase1_frontend_wireframes.md` 연계) | frontend-specialist |
| 2026-04-19 | v1.6 | §14 Phase 1 후속 의사결정 10건 요약 추가 (`phase1_decisions.md` 연계, Q1~Q10 확정) | enterprise-architect |

---

## 13. Phase 1 — HWPX 어댑터 설계 (2026-04-19 완료)

상세는 [`docs/phase1_hwpx_adapter.md`](phase1_hwpx_adapter.md). 아래는 핵심 결정 요약.

### 12.1 python-hwpx 채택 확정

- **버전**: `python-hwpx` v2.9.0 (MIT, airmang)
- **채택 조건부**: S5 PoC에서 한컴 2020/2022 실기 열기 테스트 통과 필요
- **`to_bytes()` 미확인**: `save_to_path()` 후 임시 파일 읽기 방법 사용 (방법 A)
- **이미지 API 미성숙**: `<hp:pic>` 수동 lxml 조작 wrapper 자체 구현 필요
- **lxml fallback 유지**: PoC 실패 시 OWPML XML 직접 빌드로 전환
- **pyhwp 혼입 방지**: `requirements.txt` 명시 + `lint_structure.py` 금지 패키지 검사

### 12.2 HWPX 지원 컴포넌트 14종 확정

`phase1_architecture.md §7.3` 일치. 완전 지원 14(+1)종:

| 그룹 | 컴포넌트 | HWPX 구현 |
|---|---|---|
| 텍스트 | SlideTitle, Heading, Paragraph, BulletList, Quote | `add_paragraph()` + 스타일 |
| 데이터 | DataTable | `add_table()` + `set_cell_text()` |
| 미디어 | Image, ImageGrid | lxml `<hp:pic>` 수동 삽입 |
| 레이아웃 | TwoColumn, ThreeColumn, Hero, Comparison | `add_table(1,N)` 내 컴포넌트 |
| 보고서 특화 | ExecutiveSummary, ActionItemList, AttendeeList | 조합 또는 `add_table(N,M)` |

### 12.3 미지원 8종 Degradation

| 미지원 | 대체 | 기록 위치 |
|---|---|---|
| KPI | DataTable 2×1 | `metadata.degraded_components` |
| Chart | matplotlib PNG → Image | 동일 |
| Callout | Quote 단락 | 동일 |
| Timeline | BulletList | 동일 |
| IconRow | BulletList | 동일 |
| RiskMatrix | DataTable 4열 | 동일 |
| SlideSubtitle | Heading(level=3) | 동일 |
| Hero 배경이미지 | 인라인 Image 1장 | 동일 |

### 12.4 hwp-extract 통합

- Apache 2.0 라이선스, Volexity 개발 (2024-11)
- HWP 파싱 보강: 텍스트 + 표 + 이미지 + 메타데이터 + **비밀번호 HWP** 지원
- `integrations/docling/` 내 `HwpExtractAdapter` 신설 (Phase 4 S5)
- 기존 olefile 파싱과 A/B 테스트 후 교체

### 12.5 LibreOffice 사이드카 설계 (S5 옵션)

- 이미지: Ubuntu 22.04 + LibreOffice + H2Orestart (`apt install libreoffice-h2orestart`)
- 크기: ~1.0~1.2GB / 메모리: 유휴 ~200MB, 변환 중 최대 ~1GB
- 백엔드 통신: HTTP 멀티파트 (`POST /convert`)
- **채택 조건**: 서버 메모리 여유 1.5GB 이상 + x86-64-v1 LibreOffice 구동 확인 + 변환 성공률 ≥95%
- **스킵 조건**: 서버 메모리 부족 또는 x86-64-v1 호환 실패 → Playwright HTML→PDF만 사용

### 12.6 기술 리스크 Top 3

1. **python-hwpx 이미지 API 미성숙** (중/중): lxml 직접 조작 fallback 준비
2. **python-hwpx 생성 HWPX 한컴 2020 미열림** (중/높음): S5 PoC 1주차 단계적 테스트, 실패 시 lxml 직접 OWPML 빌드 전환
3. **LibreOffice 사이드카 x86-64-v1 호환 불안** (중/중): S5 착수 전 서버 사전 검증

---

## 14. Phase 1 — 후속 의사결정 (2026-04-19 완료)

상세는 [`docs/phase1_decisions.md`](phase1_decisions.md). 10건 결정 1줄 요약:

- **Q1** `freeform_doc` 이름 중복: **동일 문자열 유지**. DocumentType 7종 ↔ agent_type 5종 의미상 1:1 대응.
- **Q2** `source_document_ids` ARRAY vs 조인: **Phase 1 ARRAY 유지**. S6에서 역방향 질의 실측 후 정규화 여부 결정.
- **Q3** Mode 전환 CHECK: **엄격 CHECK 유지**. Mode 전환 기능은 Phase 1 범위 외 (ADR로 승격 시점 별도 결정). **[정책 승인]**
- **Q4** 조직별 PPTX 템플릿: **S4 자동 변환 스크립트 입력 소스 확장**으로 처리. 신규 경로 신설 안 함. **[정책 승인]**
- **Q5** `HwpxBuilder.build()` 반환 타입: **`-> bytes` 유지**. 임시파일은 빌더 내부 구현 세부로 은닉 (P7 일관성).
- **Q6** AttendeeList HWPX 포함 시점: **S5에는 스텁(degrade 경로), 완전 구현은 S6**. §7.3은 포맷 표현 가능성 선언, §3.2가 구현 시점.
- **Q7** HWPX 색상 주입 S5 DoD: **스타일 이름·폰트까지**가 S5 DoD. 색상(표 헤더 배경 등 lxml 직접 조작)은 S6 이연.
- **Q8** MVP 5종 정의 불일치: **6종으로 확장** (SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable). S1 DoD "6-컴포넌트 end-to-end". **[정책 승인]**
- **Q9** `/designer` 라우트 그룹: **(user)/designer/ 유지 + (admin)/template-designer/ 신설**. 동일 Shell을 props로 재사용.
- **Q10** iframe postMessage + 서버 PATCH 단위: **RFC 6902 JSON Patch 미도입**. `PATCH /v2/documents/{id}` Partial DocumentSchema로 통일.

전체 영향 문서 업데이트 현황 (Phase 2 병합 대상):

| 문서 | 변경 유형 | 반영 상태 |
|---|---|---|
| `phase1_architecture.md` | 본문 수정 + 변경이력 v1.6 | **완료** (본 작업) |
| `phase1_database_design.md` | 변경이력 v1.1 (본문은 Phase 2) | **완료** (본 작업) |
| `phase1_frontend_design.md` | 변경이력 신설 v1.1 (본문은 Phase 2) | **완료** (본 작업) |
| `phase1_hwpx_adapter.md` | 변경이력 신설 v1.1 (본문은 Phase 2) | **완료** (본 작업) |
| `phase1_frontend_wireframes.md` | 변경 불필요 | — |
| `phase1_decisions.md` | 신규 | **완료** (본 작업) |

> **v1.1 반영 주석 (2026-04-20)**: 위 Q3·Q4 1줄 요약은 `phase1_decisions.md` v1.0 초안 기준이다. **v1.1에서 두 항목이 뒤집혔다**. 정답은:
> - **Q3 뒤집힘**: Mode 전환 기능 **Phase 1 범위 포함**. CHECK 소프트 체크 전환, `POST /v2/documents/{id}/switch-mode` 신설. S4 기간 1.5주 → 2주 확장.
> - **Q4 확정**: 조직별 PPTX 템플릿 **실재 확인** (회사·대학). S0 전수 조사 필수. S4 기간 2주 → 2.5주 재확장 (Q3 누적 시 S4 총 3.5주).
> 상세는 `phase1_decisions.md` v1.1 본문과 `phase2_transition_plan.md` §3.6·§4.2 참조.

---

## 15. Phase 2 — 전환계획 (2026-04-20 완료)

상세는 [`docs/phase2_transition_plan.md`](phase2_transition_plan.md) v1.0. 핵심 결정 5건 요약:

1. **자산 재분류 39+11항목**: 재활용 18 / 수정 9 / 폐기 12 / 신규 11. `report_generator.py`(3702줄) 함수 단위 분해, `jinja2_engine.py`(2608줄) 대부분 폐기(변수 치환 로직만 S4 이관), `agentic_rag.py` 즉시 폐기(외부 참조 0건 확인), `graph_rag.py` S6 관망 후 폐기. 상세는 전환계획 §2.
2. **S0 사전 조사 스프린트 신설 (3~5일)**: Q4(조직별 PPTX 템플릿 실재)로 전수 조사 필수. `tb_report_templates`·`tb_document_templates`·`tb_agents.agent_type`·`tb_organizations.organization_type` 부재·LibreOffice Ubuntu 구동·복잡도 샘플링 총 13건 점검. 산출: `docs/s0_inventory_report.md`.
3. **S0~S7 스프린트 기간 확정**: 0.6 + 2 + 2 + 2 + 3.5 + 2 + 1.5 + 1 = **14.6주**. S4는 Q3+Q4 누적으로 3.5주 확장, S7은 1주 축소로 보전. 상세는 §3.
4. **데이터 마이그레이션 — Dual-write 금지**: S1부터 `tb_documents_v2`가 유일 쓰기 경로. `tb_generated_reports`는 S2에 `_archive` rename(읽기 전용), S7 drop. `tb_document_templates`/`tb_report_templates`는 S4 배치 변환(성공률 ≥50% 목표), 실패분은 read-only 아카이브 1년. 신규 `tb_documents_v2_templates`는 S4에 채움. 상세는 §4.
5. **리스크 Top 5 + 롤백 트리거**: R1(Multi-provider Structured Output), R6(병존 유지보수), U3(Mode 전환 매핑), U4(조직별 PPTX 변환), H2(HWPX 한컴 호환), O1(서버 메모리) 동률 6점. 롤백은 QA <78 + P0/P1 ≥2건 동시 충족 시만. Feature flag 우선, 전체 revert 최후 수단. 상세는 §5, §7.

### 15.1 Phase 2 완료 체크

- [x] 자산 재분류 정밀화 (§2)
- [x] S0~S7 스프린트 DoD + 의존성 (§3)
- [x] 데이터 마이그레이션 전략 (§4)
- [x] 리스크 매트릭스 v2 통합 (§5)
- [x] S0 실행 체크리스트 (§6) + 최초 5개 명령 복사 가능 형태
- [x] 롤백 전략 (§7)
- [x] QA 게이트 (§8) + Mode 전환 회귀 세트 + HWPX 실기 테스트
- [x] 팀 역량 배치 (§9)
- [ ] S0 실행 (Phase 2 승인 후 즉시)
- [ ] Phase 3 실행 로드맵 (S0 결과 반영)

### 15.2 Phase 3 진입 조건

- [x] 본 §15 + `phase2_transition_plan.md` v1.0 완료
- [x] S0 실행 완료 → `docs/s0_inventory_report.md`
- [x] 사용자 Phase 3 착수 승인

---

## 16. Phase 3 — 실행 로드맵 (2026-04-20 완료)

상세는 [`docs/phase3_execution_roadmap.md`](phase3_execution_roadmap.md) v1.0 + [`docs/phase4_day1_checklist.md`](phase4_day1_checklist.md). 핵심 결정 6건 요약:

1. **S1~S7 일 단위 WBS 확정 (68영업일)**: Phase 2 v1.1의 14.6주 중 S0 0.6주 소진 후 잔여 13.6주. 각 스프린트별 D1~D10(S6·S7은 D8) 영업일 카드 + 담당 에이전트(BE/FE/DB/RA/SDET/EA) + 선행 의존성 + 산출물 명시. Week 단위 마일스톤 M1~M5 정의. 상세는 §2.
2. **QA 게이트 특화 기준**: S1~S6 ≥80, S7 ≥90. 스프린트별 특화 회귀 세트 — S1(6종 JSON 반환 4 provider 100%), S2(PPTX 빌드 성공률 ≥95%), S4(Mode 전환 자동 매핑 ≥85%), S5(HWPX 한컴 2020/2022 실기 열기 100%), S6(회의록 Relevancy ≥0.75), S7(전체 회귀 + 병존 제거 후 48h 스테이지 P0/P1 0건). 상세는 §3.
3. **배포·롤백 전략 표준화**: `deploy_to_server.py` → MinIO 이미지 `sed` → Alembic → `qa_quick.sh` 6단 고정 절차. 스프린트 말 `docutil-api:sN-stable` 이미지 태그 보관 + `pg_dump` DB 스냅샷. 롤백은 QA <78 + P0/P1 ≥2건 동시 충족 시만. Feature flag 우선, 전체 revert는 최후 수단. 상세는 §4.
4. **모니터링·알림 신설**: Prometheus 메트릭 4종 (`documents_v2_generated_total`, `builder_duration_seconds`, `llm_tokens_used_total`, `mode_transition_count`), Grafana 대시보드 3종 (DocumentSchema Pipeline, Mode A vs B 사용률, 조직별 문서 생성 현황), Loki 로그 집계 4종, 알림 규칙 4종. 도입 순서 — S1 말 1호 대시보드, S4 말 2호, S6 말 3호. 상세는 §5.
5. **Phase 4 Day 1 체크리스트 14항목**: 문서 최신 버전 확인, 개발 환경·Ubuntu 서버 구동, MinIO 템플릿 3건 재업로드 (운영팀 별도 트랙), 에이전트 분담, Q1~Q10 숙지, Alembic head=006 확인, QA 기준선 기록, S1 착수 승인. 별도 파일 `docs/phase4_day1_checklist.md` 제공. 상세는 §6.
6. **스프린트별 Watch List 7종 (누적 리스크 13건 커버)**: S1 (R1 Multi-provider, D3 agent_type), S2 (R4 PPTX 품질, R6 병존), S3 (R9 DALL-E 비용), S4 (U3 Mode 전환 매핑, R6), S5 (H2 HWPX 한컴 호환, H3 LibreOffice, O1 서버 메모리), S6 (R5 RAG 회귀), S7 (R6 사용자 혼란, R7 PDF 메모리), 공통 (D1 JSONB TOAST, R10 schema migration). 각 Watch에 트리거 감지 지표 + 즉시 대응 플레이북. 상세는 §9.

### 16.1 Phase 3 완료 체크

- [x] 스프린트별 일 단위 WBS (§2)
- [x] QA 게이트 상세 기준 (§3)
- [x] 배포·롤백 전략 (§4)
- [x] 모니터링·알림 설정 (§5)
- [x] Phase 4 Day 1 체크리스트 (§6) — 별도 파일 `phase4_day1_checklist.md` 제공
- [x] 스프린트 간 전환 의식 (§7)
- [x] 에이전트 조율 가이드 (§8)
- [x] 리스크 최종 통제 (§9)

### 16.2 Phase 4 착수 준비 상태

- [x] Phase 1~3 문서 모두 확정 (v1.6 / v1.2 / v1.1 / v1.0)
- [x] S0 조사 완료 (`s0_inventory_report.md` v1.0)
- [x] 실행 로드맵 + Day 1 체크리스트 산출
- [ ] 운영팀 MinIO 템플릿 3건 재업로드 (Day 1 체크 5번)
- [ ] 사용자 Phase 4 착수 승인 (Day 1 체크 14번)

Phase 4 S1 D1 실제 착수는 운영팀 재업로드 완료 + 사용자 승인 시점. 본 로드맵은 해당 시점에 즉시 실행 가능.

---
