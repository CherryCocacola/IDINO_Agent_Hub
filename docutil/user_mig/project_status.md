# DocUtil 프로젝트 개발 현황 (2026-04-23)

> **최근 변경**: 2026-04-23 Phase 4 **S1/S2/S3 전체 완주** (하루 집중 실행). M2 마일스톤 (13~14 컴포넌트 E2E) 달성.
> **진행 단계**: Phase 4 **S4 착수 대기** (Mode B + 전환 + admin template-designer, 12영업일 2.5주).
> **전체 진척**: **37/68 영업일 완료 (≈54%)**, 남은 31일 ≈ 6.2주.
> **최신 QA**: S3 80점 / S2 86점 / S1 84점 (모두 Green Light).
> **s3-stable 이미지**: `docutil-api:s3-stable be731e1c6d1f` 등 3종 태그 + DB 스냅샷 `post_s3_20260423_1543.sql`.
> **외부 블로커**: OpenAI API 쿼터 초과 — 신규 Mode A 생성 일시 차단, 결제/계정 갱신 필요.

## 1. 프로젝트 개요

통합 문서 활용 시스템(Document Utilization System) — 조직 내 문서를 업로드, 파싱, 벡터화하여 RAG 기반 챗봇 및 검색 기능을 제공하는 풀스택 시스템.

## 2. 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | Next.js 16 (App Router, Turbopack), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2 (async), Pydantic v2, Alembic |
| Database | PostgreSQL 17 |
| Vector DB | Qdrant v1.16 (named vectors: dense 1536D + sparse BM25) |
| Object Storage | MinIO |
| Message Queue | RabbitMQ 4.0 + Celery |
| Cache | Redis 7 (임베딩 캐시 + Rate Limiter) |
| LLM | 멀티 프로바이더 (OpenAI GPT-4o, Azure OpenAI, Gemini, Claude), text-embedding-3-small (embedding) |
| Monitoring | Prometheus + Grafana + Loki |
| Reverse Proxy | Nginx (WebSocket 프록시 포함) |
| Container | Docker Compose |

## 3. 운영 환경

### 개발 환경 (Windows)
- Windows 11 Pro, Docker Desktop
- 경로: `D:\workspace\document_utilization`

### 운영 서버 (Ubuntu) — 2026-03-25 데이터 이관 완료
- Ubuntu 24.04.3 LTS, Docker CE 29.3.0
- 서버: 192.168.10.39 (ai-ubuntu), Xeon E5-2620 v4, 32GB RAM, **600GB SSD (LVM 확장 완료)**
- 경로: `/home/idino/docutil/`
- 접속: ssh idino@192.168.10.39

### 서비스 포트 맵 (양쪽 동일)

| 서비스 | 포트 | 용도 |
|--------|------|------|
| Frontend (Next.js) | 3040 | 웹 UI |
| API (FastAPI) | 8040 | REST API |
| Nginx | 8041 / 4440 | 리버스 프록시 (WebSocket 포함) |
| PostgreSQL | 5440 | DB |
| Redis | 6340 | 캐시/세션/임베딩캐시 |
| RabbitMQ | 5640 / 15640 | 메시지큐 / 관리UI |
| Qdrant | 6341 / 6342 | 벡터DB (HTTP/gRPC) |
| MinIO | 9040 / 9041 | 오브젝트 스토리지 / 콘솔 |
| Flower | 5540 | Celery 모니터링 |
| Prometheus | 9042 | 메트릭 |
| Grafana | 3041 | 대시보드 |
| Loki | 3042 | 로그 수집 |

## 4. 조직/사용자 현황

### 부서 구조
```
대표이사
├── 사업지원팀
├── 미래기술연구소
│   ├── SW기술팀
│   └── AI기술팀
└── U-이노베이션본부
    ├── 울산대1팀
    ├── 플랫폼사업팀
    └── 교육사업팀
TestDept (독립)
```

### 사용자 계정

| 이름 | 로그인ID | 비밀번호 | 역할 | 부서 |
|------|----------|----------|------|------|
| 관리자 | admin | admin123! | super_admin | - |
| 변동언 | dongun | idino!@#$ | admin | 대표이사 |
| 김용휴 | yhkim | idino!@#$ | admin | 미래기술연구소 |
| 백성현 | shbaek | idino!@#$ | admin | 교육사업팀 |
| 이현수 | hslee | idino!@#$ | member | AI기술팀 |
| 일반유저 | user | admin123! | member | - |

## 5. 핵심 기능 구현 상태

### 완료된 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| 인증/인가 | ✅ | JWT, email 로컬파트 로그인, RBAC |
| 사용자 관리 | ✅ | CRUD, 역할/부서 지정, 비밀번호/이름 수정 |
| 부서 관리 | ✅ | 계층형 트리, materialized path, 부서장, 멤버 조회 |
| 프로젝트 관리 | ✅ | CRUD, 참여부서 캐스케이드, 멤버 관리 |
| 문서 업로드 | ✅ | 부서/프로젝트 대상, 공개범위, Nginx 경유 업로드 |
| 문서 파싱 | ✅ | PDF(pypdfium2), HWPX(ZIP/XML), HWP(olefile), DOCX, PPTX |
| 벡터 임베딩 | ✅ | OpenAI embedding + BM25 sparse → Qdrant |
| 하이브리드 검색 | ✅ | Dense+Sparse+RRF, Redis 캐시, 병렬 검색 |
| 검색 품질 | ✅ | 적응형 임계값(0.35), BM25 미매칭 패널티, 키워드 미포함 패널티 |
| 검색 필터 | ✅ | 날짜, 형식, 태그 필터 (프론트→백엔드 연동) |
| 검색 결과 다운로드 | ✅ | 검색 결과 카드에서 원본 문서 다운로드 (apiClient.getBlob) |
| 챗봇 | ✅ | GPT-4o 스트리밍, WebSocket(Nginx) + REST fallback |
| 챗봇 Fallback | ✅ | 벡터 검색 실패 시 MinIO 원문 직접 추출 |
| 문서 가시성 | ✅ | 6단계 공개범위, materialized path 기반 |
| 문서 삭제 권한 | ✅ | admin/org_admin/manager/사용자별 |
| 보고서/제안서 생성 | ✅ | Celery 비동기, DOCX/PPTX 출력, Structured Outputs |
| 보고서 다운로드 | ✅ | Blob 다운로드, 한글 파일명 RFC 5987 |
| 보고서 삭제 | ✅ | DELETE 엔드포인트 + MinIO 파일 삭제 |
| 검색범위 관리 | ✅ | CRUD, 검색/챗봇/QA에서 사용 |
| 감사 로그 | ✅ | 로그인, 사용자/문서 변경 기록 |
| Orphan 벡터 정리 | ✅ | Settings > Maintenance (super_admin) |

### 2026-03-21~23 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **검색 속도 최적화** | ✅ | Redis 임베딩 캐시(24h TTL), httpx 커넥션 풀링, asyncio.gather 병렬 검색 → **53% 속도 향상** |
| **LLM API 키 연동** | ✅ | DB 저장 키 우선 사용, .env fallback (`core/llm_keys.py`) |
| **에이전트 시스템** | ✅ | `tb_agents` 테이블, CRUD API + 관리자 페이지, 챗봇/보고서 연동 |
| **템플릿 관리** | ✅ | `tb_document_templates` 테이블, CRUD API + 관리자 페이지, 16개 IDINO 템플릿 |
| **AI 지시사항 반영** | ✅ | 페이지 수 감지 → 동적 max_tokens, 강화된 프롬프트 |
| **보고서 생성 흐름** | ✅ | 유형 → 문서형식 → 템플릿(형식별 필터) → 소스 → 에이전트 → AI지시사항 → 생성 |

### 2026-03-24 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **세션 Cross-tab 동기화** | ✅ | `storage` 이벤트 리스너로 탭 간 로그인/로그아웃/토큰 갱신 동기화 |
| **루트 페이지 인증 수정** | ✅ | `localStorage("user")` 잘못된 키 → `useAuth()` 훅으로 교체 |
| **토큰 갱신 Zustand 동기화** | ✅ | `refreshAccessToken()` 후 인메모리 상태도 동기화 |
| **업로드 401 처리** | ✅ | `upload()` 메서드에 토큰 갱신→재시도 로직 추가 |
| **GPT-4o Structured Outputs** | ✅ | JSON 스키마 기반 슬라이드/문서 구조 생성 (마크다운 파싱 대체) |
| **PPTX IDINO 디자인** | ✅ | 슬라이드마스터 없이도 IDINO 스타일 자동 적용 (헤더바/푸터/강조선/색상) |
| **DOCX IDINO 디자인** | ✅ | 커버페이지, 헤더/푸터, 섹션 헤딩 스타일, 콘텐츠 박스 |
| **차트 삽입 (PPTX)** | ✅ | bar/pie/line 차트 (python-pptx 네이티브) |
| **차트 삽입 (DOCX)** | ✅ | matplotlib → PNG 이미지로 삽입 |
| **표 삽입** | ✅ | PPTX/DOCX 모두 IDINO 스타일 헤더(#34495E) 적용 |
| **이미지 검색/삽입** | ✅ | Unsplash API 연동 (unsplash_access_key 설정 시) |
| **Agent 실제 연결** | ✅ | worker에서 agent의 system_prompt/temperature/max_tokens 적용 |
| **발표자 노트** | ✅ | Structured Output에서 speaker_notes 자동 생성 |
| **부서 멤버 조회 API** | ✅ | `GET /organizations/{org_id}/departments/{dept_id}/members` 추가 |
| **문서 다운로드 한글 수정** | ✅ | storage_path 없을 때 패턴 경로 생성 + RFC 5987 인코딩 |
| **Ubuntu 서버 배포** | ✅ | 192.168.10.39에 14개 컨테이너 전체 배포 완료 |

### 2026-03-25~26 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **서버 데이터 이관** | ✅ | PostgreSQL pg_dump + MinIO API 전송 + Qdrant 볼륨 복사 완료 |
| **서버 디스크 확장** | ✅ | LVM 100GB → 600GB (488GB 여유) |
| **Jinja2 템플릿 엔진** | ✅ | `jinja2_engine.py` — 변수 추출/렌더링/빈양식 분석/자동변환 |
| **docxtpl DOCX 렌더링** | ✅ | Jinja2 for/if/필터 + InlineImage + 표 행 반복 지원 |
| **PPTX 커스텀 Jinja2** | ✅ | paragraph 단위 렌더링, 서식 보존 |
| **DALL-E 3 이미지 생성** | ✅ | `image_generation/service.py` — OpenAI DALL-E 3 + Unsplash fallback |
| **템플릿 파일 업로드** | ✅ | 3가지: 양식 업로드 / 예제→AI변환 / 빈양식→자동변환 |
| **빈 양식 자동 분석** | ✅ | 표 기반 양식 지원 — 가로 교차 패턴, 라벨/값 구분, 줄바꿈 라벨 합치기 |
| **변수 카테고리 자동 분류** | ✅ | session_auto(소속/성명) / user_input(보고서명/참석자) / ai_generated(보고내용/문제점) |
| **세션 자동 채움** | ✅ | 로그인 응답에 department_name, organization_name 추가 → 소속 = "회사명 부서명" |
| **AI 자동 채우기 API** | ✅ | `POST /templates/{id}/auto-fill` — 소스 문서 기반 변수값 생성 |
| **에이전트 3종** | ✅ | 보고서(report)/제안서(proposal)/회의록(minutes) 전용 에이전트 |
| **챗봇 Citations 수정** | ✅ | snake→camelCase 매핑, 한국어 UI, 유사도 색상, 클릭 펼침 |
| **날짜 캘린더 picker** | ✅ | 날짜 변수 자동 감지 → `<input type="date">` |
| **미리보기 한글 수정** | ✅ | RFC 5987 인코딩 (`filename*=UTF-8''`) |
| **검색 페이지 보고서** | ✅ | 템플릿 선택 + 컨텐츠 옵션 추가 |
| **세션 타이머** | ✅ | JWT 30분 + 헤더 MM:SS 카운트다운 + API 활동 시 자동 갱신 |
| **부서 트리 회사 노드** | ✅ | 최상단에 조직명 표시, 인라인 수정 가능 |
| **관리자/사용자 전환 수정** | ✅ | isAdminPage에 /templates, /agents 등 추가 |
| **템플릿 중복 방지** | ✅ | 같은 이름+조직이면 upsert + 버튼 중복 클릭 방지 |
| **파일 업로드 Nginx 경유** | ✅ | Next.js 30초 타임아웃 → Nginx(8041) 직접 + CORS FastAPI 위임 |
| **PPTX 슬라이드마스터 연동** | ✅ | document_template의 PPTX를 Structured 빌드의 슬라이드마스터로 사용 |
| **Jinja2 context 객체 배열** | ✅ | task.업무명 등 점 표기 변수 → AI가 객체 배열로 생성 |
| **CLAUDE.md 보강** | ✅ | 코드 작성 체크리스트 + 개발 프로세스 5단계 + 보고서 시스템 문서화 |
| **샘플 Jinja2 템플릿 5종** | ✅ | 주간업무보고서/사업제안서/회의록/기술검토보고서/프로젝트현황보고 |
| **사용 가이드 패널** | ✅ | 관리자 템플릿 페이지에 접이식 Jinja2 문법 안내 |

### 2026-03-26 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **회의록 양식 매핑 수정** | ✅ | vMerge 행 건너뛰기, long 필드 판단 개선, 변수 삽입 위치 수정 |
| **AI 기반 양식 분석** | ✅ | GPT-4o Structured Outputs로 빈 양식 변수 자동 추출 (휴리스틱 fallback) |
| **변수 매핑 에디터** | ✅ | 풀스크린 에디터 (문서 구조 시각화 + 셀 클릭 변수 지정), dialog/inline 모드 |
| **스마트 업로드 API** | ✅ | `POST /templates/upload-smart` — Jinja2/Structured 자동 판별, 유형 자동 추측 |
| **템플릿 UX 전면 리디자인** | ✅ | 4단계 스텝(파일→기본정보→변수매핑→저장), 렌더링모드 자동감지, 고급설정 접이식 |
| **템플릿 수정 모드 개선** | ✅ | 파일 교체, 변수 매핑 에디터 접근, 변수 배지 요약, 고급설정 접이식 |
| **하드코딩 템플릿 제거** | ✅ | REPORT_TEMPLATES/PROPOSAL_TEMPLATES 빈 배열, tmpl- 분기 코드 정리 |
| **회의록 유형 추가** | ✅ | DocumentType에 "minutes" 추가, 에이전트 필터 매핑, 에이전트 관리 UI 반영 |
| **DatePicker 달력** | ✅ | react-day-picker v9 + 한국어 로케일, Popover 팝업 달력 (기존 input[date] 교체) |
| **검색 페이지 Jinja2** | ✅ | 검색 보고서 생성에 Jinja2 변수 입력 UI 추가, custom_context/template_name 전달 |
| **custom_context 병합** | ✅ | reports/router.py에서 custom_context → generation_params 자동 병합 |
| **삭제 즉시 반영** | ✅ | 템플릿 삭제 시 setTemplates로 즉시 UI 제거 + fetchTemplates 동기화 |
| **제목 변수 수정** | ✅ | 제목 변수를 "문서제목"으로 고정 + category="user_input" (AI 내용 생성 방지) |
| **변수 required 개선** | ✅ | user_input만 필수, ai_generated/session_auto는 선택적 |
| **에디터 변수 위치 수정** | ✅ | 라벨 셀에 변수 매핑 방지, 옆 빈 값 셀에만 자동 배치 |

### 2026-03-27 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **멀티 AI 프로바이더** | ✅ | LLMClient ABC 확장, OpenAICompatibleClient 공통 베이스 추출 |
| **Azure OpenAI 클라이언트** | ✅ | `azure_client.py` — OpenAICompatibleClient 상속, 헤더/URL 오버라이드 |
| **Gemini 클라이언트** | ✅ | `gemini_client.py` — OpenAI 호환 엔드포인트, Structured Outputs 응답 검증 |
| **Claude 클라이언트** | ✅ | `claude_client.py` — anthropic SDK, Tool Use 패턴 Structured Outputs |
| **클라이언트 팩토리** | ✅ | `factory.py` — `create_llm_client(provider, api_key, model)` 중앙 팩토리 |
| **기능별 프로바이더 분리** | ✅ | `chat_llm_provider`, `report_llm_provider`, `template_llm_provider` 설정 |
| **직접 호출 5곳 통합** | ✅ | chat/service, report_generator(2), jinja2_engine, templates/service → 팩토리 경유 |
| **Agent 프로바이더 선택** | ✅ | `tb_agents.llm_provider` 컬럼 추가, 에이전트별 프로바이더/모델 지정 가능 |
| **프론트 프로바이더 UI** | ✅ | API키 페이지: 5개 프로바이더 옵션, 에이전트 페이지: 프로바이더별 모델 드롭다운 |

### 2026-03-30 신규 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| **Agentic RAG 검색** | ✅ | `agentic_search.py` — LLM 쿼리 분석 → 검색 → 품질 판정 → 재검색 루프 (최대 3회, 15초 타임아웃) |
| **검색 API agentic 모드** | ✅ | `SearchRequest.agentic=True`로 활성화, 기존 엔드포인트 하위호환 유지 |
| **챗봇 심층 검색** | ✅ | WebSocket `options.deep_search=True` → `AgenticSearchService` 사용, 프론트 토글 |
| **Agentic 결과 캐싱** | ✅ | Redis 5분 TTL, SHA256 기반 캐시 키 |
| **.claude/ 디렉토리 구조화** | ✅ | `rules/` 5개 + `agents/qa-tester.md` + `commands/` 7개 + CLAUDE.md 경량화 |
| **QA 테스트 자동화** | ✅ | `qa-tester` 에이전트 (Sonnet) + `scripts/qa.sh`, `qa_quick.sh` (Linux/Windows) |

### 진행 중 / 미완료

| 항목 | 상태 | 설명 |
|------|------|------|
| **에이전트 유형 확장** | 📋 | agent_type을 하드코딩(4종)에서 자유 텍스트/DB 관리로 변경 |
| **보고서 템플릿 시스템 통합** | 🔧 | Jinja2 DocumentTemplate ↔ ReportTemplate 불일치 → 500 에러. 단일 시스템으로 통합 필요 |
| PPTX 양식 기반 보고서 | 🔧 | 슬라이드마스터 PPTX 업로드 → Structured 빌드 연동 검증 필요 |
| 보고서 이미지/차트 삽입 | 🔧 | Jinja2 경로에서 DALL-E 3 이미지 + 표/차트 삽입 동작 검증 |
| **QA 점수 80+ 안정화** | 🔧 | 현재 73점 — 보고서 500 수정, 검색 Relevancy 0.68→0.70 개선 필요 |
| Kubernetes 전환 | 📋 | k3s 기반 전환 계획 수립 완료 (`docs/migration-plan.md`) |
| GPU 서비스 활성화 | 📋 | vLLM, TEI, reranker 컨테이너 활성화 시 검색 200ms 이내 가능 |
| SSL/TLS 인증서 | 📋 | Let's Encrypt + certbot 설정 예정 |
| CI/CD 파이프라인 | 📋 | GitHub Actions → SSH 배포 구성 예정 |

### 2026-04-19 재설계 개시 (문서 생성 엔진 + RAG 파이프라인)

#### 식별된 5대 이슈

| # | 이슈 | 그룹 | 심각도 |
|---|------|------|--------|
| 1 | Jinja2 양식 매핑 UX 개선 필요 (동작하지만 불편) | A (엔진) | 중간 |
| 2 | PPT 슬라이드마스터 등록된 양식으로 PPT 생성 실패 | A (엔진) | **높음** |
| 3 | HWP 양식 업로드·생성 문제 + HWPX 지원 확장 필요 | B (한국포맷) | 높음 |
| 4 | 기준 문서·Chat 로드 불안정 → 회의록·요약 부실 | C (RAG) | 높음 |
| 5 | Claude Design/Gamma식 자동 생성 신규 기능 | A (엔진) | 신규 |

#### Phase 0 현황 진단 결과 (2026-04-19 완료)

**그룹 A — 문서 생성 엔진 (PPT 마스터 실패 근본원인)**
- `report_generator.py:1250-1344` `_build_layout_catalog()`가 IDINO 한글 레이아웃 이름(`"1_표지"`, `"Ⅰ. 본문"` 등) 하드코딩 매칭 → 다른 마스터 업로드 시 빈 딕셔너리 → 모든 슬라이드 `slide_layouts[0]` fallback
- 추가 Critical 버그: `GeneratedReport` ORM 컬럼 누락(`rendering_mode`, `jinja2_context`), MinIO 직접 import(P1 위반), `_session_user` 주입 누락, 이중 템플릿 테이블

**그룹 B — HWP/HWPX 기술 선택 (시나리오 B 권장)**
- HWP(이진) 생성은 Linux Docker에서 불가 → HWPX 생성으로 전환 권장
- HWP 파싱: `olefile`(현행) + `hwp-extract`(Apache 2.0, Volexity, 2024-11) 표·이미지 보강
- HWPX 파싱: `python-hwpx`(airmang, MIT) 전면 교체
- HWPX 생성: `python-hwpx` 신규 구현 (`_build_hwpx_from_structured()`)
- pyhwp(AGPL)는 상용 법적 위험으로 사용 금지
- 예상 공수: 5~8일

**그룹 C — RAG·컨텍스트 파이프라인 (회의록 부실 근본원인)**
- `reports/service.py:312-326`이 `source_chat_session_id` 저장 누락 → 어떤 Chat 지정해도 워커는 NULL
- `report_generator.py`에 `tb_chat_messages` 조회 코드 자체가 없음
- `_load_source_chunks`(report_generator.py:571) LIMIT 100 + UUID 정렬 → 다중 문서 시 뒤쪽 문서 누락
- 회의록 전용 프롬프트·Structured Schema 부재 (보고서 프롬프트로 고정)
- `AgenticRAGEngine` dead code, `AgenticSearchService`는 WebSocket deep_search만 동작

#### 재설계 방향 (접근법 C — 컴포넌트 라이브러리 + DocumentSchema)

- **Mode A**: Gamma/Claude Design식 자유 생성 (브랜드 토큰 + 프롬프트 → AI가 전체 구성)
- **Mode B**: 양식 채우기 (템플릿 슬롯만 AI가 채움, Jinja2 UX 개선)
- **공통 엔진**: DocumentSchema(JSON) → React 렌더러(iframe 프리뷰) + PPTX/DOCX/HWPX 빌더
- **핫픽스 트랙 (H1~H7)**: 재설계와 병행하여 즉시 Critical 버그 수정 → QA 73→80+ 복귀

#### 로드맵 진척 (2026-04-23 기준)

| Phase | 내용 | 상태 | QA |
|---|---|---|---|
| 0 | 현황 진단 | ✅ (2026-04-19) | - |
| 1 | 목표 아키텍처 + 핫픽스 H1~H10 | ✅ (2026-04-20~21) | - |
| 2 | 전환 계획 v1.1 | ✅ (2026-04-20) | - |
| 3 | 실행 로드맵 v1.2 | ✅ (2026-04-20) | - |
| 4-S1 | DocumentSchema MVP (6 컴포넌트 + PATCH + agentic_rag 삭제) | ✅ (2026-04-23) | 84 |
| 4-S2 | PPTX Mode A + archive 리네이밍 + W4 API 프록시 | ✅ (2026-04-23) | 86 |
| 4-S3 | 컴포넌트 확장 (14종) + 이미지 자동 (Unsplash/DALL-E) + 쿼터 | ✅ (2026-04-23) | **80** |
| 4-S4 | Mode B + 전환 + admin template-designer (12영업일) | 🟡 **착수 대기** | - |
| 4-S5 | HWPX + DOCX 완성 + LibreOffice 사이드카 | ⏳ | - |
| 4-S6 | RAG 품질 + HWPX 색상 + 특화 4종 | ⏳ | - |
| 4-S7 | 인라인 편집 + 부분 재생성 + 병존 제거 + PDF | ⏳ | - |

**Phase 4 전체 68영업일 중 37일 완료 (≈54%)**. 남은 31일 ≈ 6.2주.

### M2 마일스톤 달성 (2026-04-23)

- **PPTX 14 컴포넌트 end-to-end**:
  - 텍스트 5종: SlideTitle / SlideSubtitle / Heading / Paragraph / BulletList
  - 데이터 3종: KPI / DataTable / Chart (pie native + bar/line)
  - 미디어 2종: Image / ImageGrid (자동 2/3/4 레이아웃)
  - 강조 2종: Quote / Callout (variant 4색)
  - 구조 2종: Timeline / IconRow
- **HTML 렌더러 9종** (동일 컴포넌트)
- **DocxBuilder 골격** (S5 완성 예정)
- **이미지 자동 선택** (Unsplash 우선 → DALL-E fallback → MinIO 업로드 → `minio://` 스킴)
- **조직별 DALL-E 쿼터** (Alembic 009 `tb_organization_quotas` + 관리자 UI `/quotas`)
- **E2E 파이프라인**: `/designer/create` 프롬프트 → LLM 생성 → PptxBuilder → MinIO → **API 프록시 다운로드** `/v2/documents/exports/{job_id}/download`

상세 스펙은 `docs/techspec.md`, S1/S2/S3 완료 선언 리포트는 `docs/phase4_s{1,2,3}_completion_report.md` 참조.

### Phase 1 완료 산출물 (2026-04-20)

- `docs/phase1_architecture.md` — 목표 아키텍처 전체 (enterprise-architect, 1055줄)
- `docs/phase1_database_design.md` — DB 스키마 + `modules/documents_v2/` + Alembic 007 draft
- `docs/phase1_frontend_design.md` + `phase1_frontend_wireframes.md` — 22 TS 타입 + MVP 6종 React 스켈레톤
- `docs/phase1_hwpx_adapter.md` — python-hwpx v2.9.0 MIT 조건부 채택
- `docs/phase1_decisions.md` v1.2 — Q1~Q10 확정 (Q3 Mode 전환 포함, Q4 외부 고객사 방향)
- `docs/s0_inventory_report.md` — 운영서버 현황 조사

### 핫픽스 완료 목록 (H1~H10, 2026-04-20~21)

| # | 내용 | 파일 |
|---|------|------|
| H1 | `GeneratedReport` ORM `rendering_mode`/`jinja2_context` 컬럼 추가 | Alembic 006 |
| H2 | `reports/service.py` MinIO 직접 import → `MinIOService` | reports/service.py |
| H3 | `_session_user` → `generation_params` 주입 | report_generator.py |
| H4 | `source_chat_session_id` 저장 누락 fix | reports/service.py |
| H5 | `_load_source_chunks` 문서별 분할 로딩 | report_generator.py |
| H6 | 회의록 전용 Structured Schema + 프롬프트 추가 | structured_schemas.py, prompts.py |
| H7 | Chat 메시지 조회 코드 추가 | report_generator.py |
| H8 | 204 라우트 `response_model=None` 일괄 적용 (11파일) | 다수 router.py |
| H9 | 경로 문서 수정 (누락 엔드포인트 추가) | docs/api-spec.json |
| H10 | `POST /reports/generate` + `template_id` FK 위반 fix | reports/service.py |

### S1~S3 완료 현황 (2026-04-23, 하루 집중 실행)

#### S1 (10영업일, QA 84)
- DocumentSchema + 6 MVP 컴포넌트 (SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable)
- `documents_v2/` 신규 모듈 + PATCH 엔드포인트 + iframe 프리뷰 + 동적 라우트 `/designer/[id]`
- `agentic_rag.py` dead code 489줄 삭제
- SDET 통합 테스트 89건 PASS

#### S2 (10영업일, QA 86) — M2 일부
- PptxBuilder ABC + `layout_resolver` (Phase 0 하드코딩 14종 해소)
- PPTX 컴포넌트 8 + 2 = **9종** 렌더
- `export_worker` Celery 태스크 + MinIO 업로드 + **W4 API 프록시** `GET /v2/documents/exports/{job_id}/download`
- reports 410 Gone + archive 읽기 유지 (ISSUE-D2-1 해소)
- E2E 성공률 3/3, 평균 2.8초

#### S3 (10영업일, QA 80) — M2 완성
- PPTX **14 컴포넌트 완성** + HTML 렌더러 9종 + Chart pie native
- **이미지 자동 선택 파이프라인**: `auto_select.py` (Unsplash → DALL-E fallback → MinIO)
- **Alembic 009** `tb_organization_quotas` + `QuotaService` (FOR UPDATE) + `GET/PUT /organizations/{id}/quotas/*`
- FE 7 신규 컴포넌트 (Recharts 활용 Chart 포함) + `ImageForm` 3-Radio + `AutoSelectedBadge`
- 관리자 쿼터 설정 페이지 `/quotas`

### 운영 중 해결한 Critical 정리 (S1~S3)

| ID | 이슈 | 해결 |
|---|---|---|
| F1 (S2) | Celery worker가 `document_export` queue 미구독 | docker-compose.yml `-Q` 확장 |
| F2 (S2) | BuilderRegistry에 pptx 빌더 미등록 (501) | `document_builders/__init__.py` side-effect import |
| F3 (S2) | MinIO presigned URL Docker hostname 외부 resolve 불가 (W4) | API 프록시 엔드포인트 + StreamingResponse |
| C1 (S3) | S3 배포 시 F1 regression (docker-compose.yml 덮어쓰기) | 로컬에 영구 반영 (`document_export,evaluation`) |

### S4 이관 Watch List

| ID | 내용 | 심각도 |
|---|---|---|
| **C2** | **OpenAI API 쿼터 초과 — Mode A 생성 차단** | **P0 외부** |
| W3 | `DELETE /v2/documents/{id}` 405 미구현 | 중 (S4 D1 보강) |
| W5 | 컴포넌트 한국어 비율 0.56~0.66 (목표 0.7) | 중 (S6) |
| W6 | OpenAI TPM 30k 초과 시 502 재시도/백오프 없음 | 중 (S6) |
| W7 | 신규 4종(Quote/Timeline/IconRow/ImageGrid) LLM 활용도 낮음 | 낮 (프롬프트 예시 보강) |
| W1/W2 | Nginx 4440 / 챗봇 5.7s | 낮 (기존) |

## 6. DB 마이그레이션 이력

| 버전 | 파일 | 내용 |
|------|------|------|
| 001 | `001_initial_schema.py` | 초기 스키마 (모든 기본 테이블) |
| 002 | `002_department_project_restructure.py` | 부서/프로젝트 구조개편, 문서 가시성 |
| 003 | `003_templates_and_agents.py` | `tb_document_templates`, `tb_agents`, chat/report에 `agent_id` 추가 |
| 004 | `004_jinja2_template_system.py` | template_storage_path, jinja2_variables, rendering_mode, image_generation_config 추가 |
| 005 | `005_multi_provider.py` | `tb_agents.llm_provider` 컬럼 추가 (VARCHAR(50), nullable) |
| 006 | `006_evaluation.py` | evaluation 관련 테이블 + `tb_generated_reports.rendering_mode`/`jinja2_context` 추가 (H1) |
| 007 | `007_documents_v2_and_template_consolidation.py` | ✅ **운영 적용 완료** (S1 D2). `tb_documents_v2` + `tb_documents_v2_templates` 생성, `tb_generated_reports` → `_archive` 리네이밍, `tb_agents.agent_type` CHECK 제약 추가 |
| 008 | **skip** | `docs/phase4_s2_d6_alembic_008_skip_rationale.md` 참조 — 007에서 이미 archive 리네이밍 완료. 008은 `organization_type` 용으로 예약 |
| 009 | `009_organization_quotas.py` | ✅ **운영 적용 완료** (S3 D10, 2026-04-23). `tb_organization_quotas` — 조직별 월 DALL-E/Unsplash 쿼터 + FOR UPDATE 동시성 |

## 7. 주요 파일 경로

```
backend/
├── app/main.py                          # FastAPI 앱, 라우터 등록, lifespan
├── app/core/config.py                   # 설정 (CORS, LLM, Redis, embedding, unsplash 등)
├── app/core/cache.py                    # Redis 임베딩 캐시
├── app/core/llm_keys.py                 # DB→런타임 API 키 해석
├── app/core/dependencies.py             # 인증/인가 (require_role)
├── app/modules/auth/                    # JWT 로그인/리프레시
├── app/modules/users/                   # 사용자 CRUD
├── app/modules/organizations/           # 조직/부서 (materialized path, 멤버 조회)
├── app/modules/projects/                # 프로젝트/보드/폴더/멤버
├── app/modules/documents/               # 문서 업로드/조회/삭제/가시성/다운로드
├── app/modules/search/                  # Hybrid search + Agentic RAG (agentic_search.py)
├── app/modules/chat/                    # 챗봇 (WS+REST, 에이전트 프롬프트)
├── app/modules/reports/                 # 보고서 생성/다운로드/삭제
├── app/modules/templates/               # 문서 템플릿 CRUD
├── app/modules/agents/                  # AI 에이전트 CRUD
├── app/modules/api_keys/               # LLM API 키 관리
├── app/modules/admin/                   # 대시보드, 유지보수
├── app/workers/document_processor.py    # Celery: 문서 파싱
├── app/workers/embedding_generator.py   # Celery: 임베딩 + Qdrant upsert
├── app/workers/report_generator.py      # Celery: 보고서 생성 (Structured Outputs + IDINO 디자인)
├── app/workers/structured_schemas.py    # PPTX/DOCX Structured Outputs JSON 스키마
├── app/integrations/llm/client.py       # LLM 클라이언트 ABC + OpenAI/vLLM/SGLang
├── app/integrations/llm/azure_client.py # Azure OpenAI 클라이언트
├── app/integrations/llm/gemini_client.py # Gemini 클라이언트
├── app/integrations/llm/claude_client.py # Claude (Anthropic) 클라이언트
├── app/integrations/llm/factory.py      # 프로바이더별 클라이언트 팩토리
├── app/integrations/llm/prompts.py      # 프롬프트 템플릿 (Structured Output + Agentic RAG)
├── app/integrations/vector_store/       # Qdrant 클라이언트
├── app/integrations/image_generation/   # DALL-E 3 + Unsplash 이미지 생성
└── app/integrations/object_storage/     # MinIO 클라이언트

frontend/
├── src/app/(auth)/login/                # 로그인
├── src/app/(admin)/
│   ├── admin-accounts/                  # 사용자 관리
│   ├── departments/                     # 부서 관리 (멤버 조회 포함)
│   ├── projects/                        # 프로젝트 관리
│   ├── documents/                       # 문서 관리
│   ├── search-scopes/                   # 검색범위 관리
│   ├── search-test/                     # 검색 테스트
│   ├── templates/                       # 템플릿 관리
│   ├── agents/                          # 에이전트 관리
│   ├── api-keys/                        # API 키 관리
│   └── settings/                        # 설정 + Maintenance
├── src/app/(user)/
│   ├── search/                          # 통합 검색 (필터 연동, 원본 다운로드)
│   ├── chat/                            # 챗봇 (WS+REST, 에이전트 선택)
│   ├── reports/                         # 보고서/제안서 (차트/표/이미지 옵션)
│   └── my-documents/                    # 내 문서
├── src/components/search/search-result-card.tsx  # 검색 결과 카드 (다운로드 버튼)
├── src/lib/api/client.ts                # API 클라이언트 (getBlob, Zustand 동기화)
├── src/lib/hooks/use-auth.ts            # Zustand 인증 스토어 (cross-tab sync)
├── next.config.ts                       # rewrites 프록시
└── Dockerfile                           # 멀티스테이지 빌드

scripts/
├── create_idino_templates.py            # IDINO 스타일 템플릿 생성 (16종, IDINO 디자인)
├── create_jinja2_sample_templates.py    # Jinja2 샘플 템플릿 5종 생성 + API 등록
├── create_default_agents.py             # 보고서/제안서/회의록 기본 에이전트 3종 생성
├── deploy_to_server.py                  # Ubuntu 서버 배포 스크립트

docs/
└── migration-plan.md                    # Ubuntu/K8s 마이그레이션 계획서
```

## 8. 기동 방법

### 개발 환경 (Windows)
```bash
cd D:\workspace\document_utilization
docker compose up -d --build
docker exec docutil-api alembic upgrade head

# 프론트엔드 리빌드 (NEXT_PUBLIC_* 빌드 타임 변수)
docker compose build --no-cache frontend && docker compose up -d frontend

# Celery worker만 리빌드
docker compose up -d --build celery-worker
```

### 운영 서버 (Ubuntu)
```bash
ssh idino@192.168.10.39
cd ~/docutil
docker compose up -d --build
docker exec docutil-api alembic upgrade head
```

## 9. 해결한 주요 이슈 (2026-03-20~26)

| # | 이슈 | 원인 | 해결 |
|---|------|------|------|
| 1 | 검색 무관한 결과 | 코사인 유사도 노이즈 (0.25~0.44) | ABS_MIN_SCORE=0.35, BM25 패널티, 키워드 패널티 |
| 2 | 검색 필터 미작동 | 프론트에서 filters를 API에 미전달 | requestBody에 filters 추가 + `_apply_filters()` 구현 |
| 3 | 보고서 다운로드 실패 | `minio_client` 모듈 직접 import | `MinIOService()` 인스턴스 사용 |
| 4 | 보고서 다운로드 한글 깨짐 | Content-Disposition latin-1 인코딩 | RFC 5987 `filename*=UTF-8''` |
| 5 | 보고서 삭제 405 | DELETE 엔드포인트 없음 | `DELETE /reports/{id}` 추가 |
| 6 | 보고서 생성 500 (FK) | `tb_document_templates` ID를 `template_id`로 전송 | `generation_params.document_template_id`로 변경 |
| 7 | 검색범위 422 | 파라미터명 `type` vs `location_type` 불일치 | 프론트 수정 |
| 8 | AI 지시사항 무시 | max_tokens=4096, 컨텍스트 15K 제한 | 동적 토큰(최대 16384), 컨텍스트 30K |
| 9 | PPTX 형식 미허용 | 스키마+라우터에서 pptx 누락 | 허용 목록 추가 |
| 10 | MinIO 템플릿 업로드 실패 | `schema` vs `schema_` ORM 속성명 | `schema_=` 수정 |
| 11 | 보고서 목록 에러 | `getStatusBadge`에 `processing` 없음 | `processing` + `default` 추가 |
| 12 | 보고서 다운로드 인증 실패 | `window.open()` 토큰 미전송 | `apiClient.getBlob()` + 토큰 갱신 |
| 13 | 외부 접속 타임아웃 | Windows 방화벽 + WSL2 네트워크 | 방화벽 규칙 + portproxy |
| 14 | DB 한글 이름 깨짐 | curl UTF-8 인코딩 문제 | psql UPDATE로 수정 |
| 15 | report_template 검색 실패 | ILIKE 중복 result 변수 | `result2` 분리 + 중복 라인 제거 |
| 16 | `prs.presentation` 에러 | python-pptx API 차이 | `prs.part._element` 사용 |
| 17 | 새 탭 로그인 풀림 | `localStorage("user")` 잘못된 키 참조 | `useAuth()` 훅 + `_hasHydrated` 체크 |
| 18 | 토큰 갱신 시 UI stale | localStorage만 업데이트, Zustand 미동기화 | `useAuth.getState().setAccessToken()` 추가 |
| 19 | PPT 디자인 없음 | 슬라이드마스터 미매칭 → 빈 Presentation() | IDINO 디자인 자동 적용 (도형+텍스트박스) |
| 20 | PPT 0슬라이드 | 구 템플릿(v1) 레이아웃명 불일치 | MinIO+DB 구 템플릿 42개 삭제, 새 16개 생성 |
| 21 | `SlidePlaceholders.get()` | python-pptx에 `.get()` 없음 | `in` 연산자로 변경 |
| 22 | 부서 멤버 404 | GET departments/members 엔드포인트 없음 | `organizations/router.py`에 GET 추가 |
| 23 | 문서 다운로드 502 | storage_path=None + 한글 파일명 latin-1 | 패턴 경로 생성 + RFC 5987 인코딩 |
| 24 | Ubuntu MinIO 시작 실패 | CPU(Xeon E5)가 x86-64-v2 미지원 | MinIO RELEASE.2023-09-04 (v1 호환) |
| 25 | Ubuntu NumPy 에러 | NumPy 2.x가 x86-64-v2 요구 | `numpy<2.0.0` 고정 |
| 26 | Citations 빈칸 | 백엔드 snake_case ↔ 프론트 camelCase 불일치 | 매핑 코드 추가 (document_id→id, snippet→chunkText) |
| 27 | settings.openai_model 없음 | config.py에 해당 속성 없음 | `settings.llm_model` 사용 |
| 28 | Jinja2 변수 파싱 실패 | `variables_schema.items()` 구조 불일치 | `.get("variables", [])` 배열 추출 |
| 29 | 표 기반 양식 미인식 | heading/번호 패턴만 감지 | 가로 교차 패턴 + 라벨/값 구분 로직 추가 |
| 30 | 미리보기 500 한글 | Content-Disposition latin-1 에러 | RFC 5987 `filename*=UTF-8''` |
| 31 | 업로드 30초 타임아웃 | Next.js rewrite 프록시 30초 제한 | Nginx(8041) 직접 경유 |
| 32 | PPTX 변수 0개 에러 | 슬라이드마스터 양식은 텍스트 없음 | 변수 0개면 structured 모드 자동 전환 |
| 33 | Nginx CORS 중복 헤더 | Nginx + FastAPI 양쪽에서 CORS 헤더 추가 | Nginx CORS 제거, FastAPI에만 위임 |
| 34 | 업로드 시 파일 미저장 | 저장 버튼이 파일 없이 JSON만 전송 | 파일 있으면 자동 업로드 + 저장 한 번에 처리 |

## 10. 배포 필수 체크리스트

### 로컬 + 서버 동시 배포 (매 수정 시 반드시 양쪽 모두)
```bash
# 1. 로컬 빌드
docker compose up -d --build api celery-worker
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend nginx

# 2. 서버 배포 (deploy_to_server.py 사용)
python scripts/deploy_to_server.py

# 3. 서버 빌드 (SSH 또는 paramiko)
# ⚠️ 주의: docker-compose.yml이 덮어써지므로 MinIO 이미지 수정 필수
cd /home/idino/docutil
sed -i 's|image: minio/minio:latest|image: quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z|' docker-compose.yml
docker compose up -d --build api celery-worker
docker builder prune -af
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend nginx
```

### 배포 시 주의사항
- **MinIO 이미지**: 배포 시 docker-compose.yml이 로컬 버전으로 덮어써지므로, 서버에서 반드시 `sed` 명령으로 MinIO 이미지를 `RELEASE.2023-09-04` 버전으로 수정
- **Nginx 재시작**: API 컨테이너 재시작 후 Nginx 업스트림이 끊어질 수 있으므로 Nginx도 함께 재시작
- **프론트 캐시**: `docker builder prune -af` 실행하여 BuildKit 캐시 완전 삭제 후 `--no-cache` 빌드
- **브라우저 캐시**: 배포 후 사용자에게 Ctrl+Shift+R 또는 시크릿 모드 안내

## 11. 멀티 AI 프로바이더 (2026-03-27 구현 완료)

### 구현 완료 구조
- `LLMClient` ABC → `OpenAICompatibleClient` 공통 베이스 → 6개 클라이언트 구현
- `factory.py` 중앙 팩토리: `create_llm_client(provider, api_key, model)`
- `get_provider_for_task(task_type)`: 기능별 프로바이더 자동 해석
- 직접 호출 5곳 모두 팩토리 경유로 통합 완료

### 프로바이더 현황

| 프로바이더 | 상태 | Structured Outputs | 비고 |
|-----------|:----:|:------------------:|------|
| OpenAI | ✅ 구현 | 완전 지원 (strict) | 기본 프로바이더 |
| Azure OpenAI | ✅ 구현 | 완전 지원 (strict) | 헤더/URL 오버라이드 |
| Gemini | ✅ 구현 | 부분 지원 | OpenAI 호환 엔드포인트 |
| Claude | ✅ 구현 | Tool Use 패턴 | anthropic SDK |
| vLLM/SGLang | ✅ 구현 | 모델 의존 | GPU 필요 |

### 에이전트 유형 확장 계획
- **현재**: `agent_type` Pydantic `pattern=r"^(chatbot|report|proposal|minutes)$"` 제한
- **DB**: VARCHAR(20) (데이터베이스 레벨 제약 없음)
- **변경**: pattern 제거 또는 확장, 프론트 하드코딩 제거 → DB 기반 동적 유형 관리
- **영향 파일**: `agents/schemas.py`, `agents/page.tsx`, `reports/page.tsx`

## 12. Claude Code 개발 환경

### .claude/ 디렉토리 구조 (2026-03-30 구성)
```
.claude/
├── rules/                    # 자동 로드 규칙 (CLAUDE.md와 동일 우선순위)
│   ├── architecture.md       # P1~P6 아키텍처 원칙
│   ├── anti-patterns.md      # 금지 패턴 (직접 SDK import 등)
│   ├── domain-model.md       # 도메인 용어 정의
│   ├── testing.md            # 테스트 전략
│   └── agent-collaboration.md # AI 코딩 협업 규칙
├── agents/
│   └── qa-tester.md          # QA 테스트 에이전트 (Sonnet 모델)
├── commands/                 # 슬래시 커맨드 정의 (7개)
└── settings.local.json       # 로컬 설정 (git 제외)
```

### QA 테스트 시스템
- **에이전트**: `qa-tester` (Claude Sonnet) — 4계층 테스트 자동 실행
  - Layer 1: 시나리오 API 테스트 (문서 라이프사이클, 챗봇, 보고서, 접근 제어)
  - Layer 2: 엣지 케이스 (빈 쿼리, 특수문자, 만료 JWT, 동시 요청)
  - Layer 3: AI 품질 평가 (Relevancy, Faithfulness, Hallucination)
  - Layer 4: 교차 모듈 영향 분석
- **실행**: `scripts/qa.bat` (전체 ~5분) / `scripts/qa_quick.bat` (빠른 ~2분)
- **리포트**: `tests/qa_reports/{date}_report.md` — 100점 만점, 80점 이상 시 커밋 허용
- **채점**: Critical -10, Warning -3, AI 품질 미달 -5, 성능 초과 -2

## 13. 서버 호환성 참고사항

### Ubuntu 서버 (Xeon E5-2620 v4) x86-64-v2 비호환
- **MinIO**: `minio/minio:latest` 사용 불가 → `quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z` 사용
- **NumPy**: `numpy>=2.0.0` 사용 불가 → `numpy<2.0.0` 고정
- docker-compose.yml에서 MinIO 이미지 버전 주의 필요
