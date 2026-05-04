# IDINO Agent Hub — AI 코딩 협업 규칙

Claude Code 또는 다른 AI 코딩 도구가 이 monorepo에서 작업할 때 따라야 하는 절차.

## 작업 시작 전

1. **어느 서브프로젝트인지 명시** — `agenthub`/`docutil`/`career`/`nexus`/`docs`/`infra` 중 하나
2. **해당 서브프로젝트의 `CLAUDE.md`와 `.claude/rules/`도 함께 확인** — 이 monorepo 루트 규칙은 통합 차원, 서브프로젝트별 규칙도 적용
3. **수정할 파일을 반드시 먼저 `Read`** — 기존 패턴 파악
4. **3개 이상 파일 수정 시 → 한글 계획서 제시 + 사용자 승인**
5. **서브프로젝트 경계를 넘는 변경**(예: agenthub와 docutil 동시 수정) → 반드시 계획 모드

## 작업 중

1. **R1 서브프로젝트 경계** — `from career.xxx import` 같은 cross-import 금지
2. **R2 AI 호출 진입점** — docutil/career에서 LLM SDK 직접 사용 금지, AgentHub API 호출
3. **R3 스키마 격리** — Cross-schema 조인 금지
4. **R4 시크릿 비커밋** — `.env`, `appsettings.*.json`에 평문 시크릿 추가 금지
5. **R5 한국어 우선** — 사용자 메시지/주석은 한국어, 변수/함수/커밋은 영어
6. **각 서브프로젝트의 라이프타임/수명주기 규칙 준수**:
   - .NET: Singleton/Scoped 구분, DI 등록 누락 금지
   - FastAPI: dependency injection, 비동기 흐름
   - Next.js: Server/Client Component 구분
   - Nexus: 4-Tier AsyncGenerator 체인 우회 금지

## 작업 완료 후

1. **빌드 검증**:
   - `agenthub`: `dotnet build` (워닝 0건 목표)
   - `docutil/backend`: `ruff check . && ruff format .`
   - `career`: 각 MS별 lint 도구
   - `nexus`: `ruff check .`
2. **타입 검증**:
   - `agenthub/ClientApp`: `npm run build:check`
   - `docutil/frontend`: `npx tsc --noEmit && npx eslint .`
   - `career/frontend`: `npx tsc --noEmit && npx eslint .`
3. **서브프로젝트별 테스트** (가능한 경우):
   - `dotnet test`, `pytest`, `npm test`
4. **변경 요약을 한국어로** 작성
5. **`user_mig/progress.md` 갱신 (필수)**:
   - 작업 로그 추가 (날짜 역순)
   - Phase 상태표 변경 (해당 시)
   - ADR / 위험 / Open Question 갱신 (해당 시)
   - 마지막 commit 해시 갱신 (commit 후)
   - **갱신 없이 작업 종료 금지** — progress.md는 차기 세션의 컨텍스트 진입점

## 커밋 메시지 형식

```
[scope/모듈] 한글 설명

scope 종류: agenthub | docutil | career | nexus | docs | infra | shared

예시:
[agenthub/aiproxy] Nexus provider 추가 — CallNexusAsync 구현
[docutil/llm] AgentHub /v1/chat 호출로 전환
[career/coaching] 학생 코칭 Agent ID 매핑 추가
[nexus/web] tenant_id 헤더 검증 강화
[docs] AI_INVENTORY.md 작성
[infra/db] AGENT_HUB DB + 3개 스키마 생성 SQL
[shared] 공통 디자인 토큰 정의
```

## 위험 작업 — 사용자 확인 필요

다음 작업은 **반드시 사용자 확인을 받은 후** 실행:

- DB 스키마 변경 / 데이터 마이그레이션 (특히 운영 데이터 영향)
- `git push`, `git rebase`, `git reset --hard`, `git push --force`
- 서브프로젝트 디렉토리 삭제 또는 대규모 리팩토링
- 외부 LLM API 키 신규 발급/회전
- IIS / Docker 프로덕션 배포
- AGENT_HUB DB 스키마/사용자 변경
- `.gitignore` 패턴 약화 (시크릿 노출 위험)

## 통합 작업 패턴

서브프로젝트 간 통합 작업 시 표준 절차:

### 패턴 A: 인터페이스 정의 → 양쪽 구현
1. `docs/`에 인터페이스 명세 작성 (OpenAPI / Pydantic schema)
2. AgentHub 측 엔드포인트 구현 + 테스트
3. End-User 앱(docutil/career) 측 클라이언트 작성 + 테스트
4. 통합 테스트 (양 시스템이 동시에 살아있는 상태)

### 패턴 B: AgentHub Agent 정의 → 사용처 교체
1. AgentHub UI에서 Agent 정의 (모델/프롬프트/라우팅)
2. API Key 발급 (스코프 설정)
3. 사용처(docutil/career)의 LLM 호출 코드 → AgentHub Agent API 호출로 교체
4. 통합 테스트 — Agent의 라우팅(External/Internal)이 올바르게 동작하는지

### 패턴 C: DB 마이그레이션
1. `infra/db/`에 변경 SQL 작성
2. 개발 환경에서 시험 실행
3. 영향받는 모든 서브프로젝트 검증
4. 운영 적용 (사용자 확인 후)
5. 변경 내역을 `docs/DB_MIGRATION.md`에 기록

## 변경 시 함께 점검할 항목

| 변경 | 함께 점검 |
|---|---|
| AgentHub Agent 엔티티 변경 | DTO, Service, Migration, Frontend AgentBuilder, ApiKey 스코프 |
| 새 LLM 프로바이더 추가 | `appsettings.json`, Named HttpClient, AiProxyService 분기, ApiServices 시드 |
| Nexus API 변경 | AgentHub의 `CallNexusAsync` 클라이언트, 옵션 B 호환성 |
| DocUtil RAG API 변경 | AgentHub의 RagService BFF 클라이언트 |
| career 신규 AI 기능 | AgentHub Agent 정의, AI_INVENTORY.md 갱신 |
| DB 스키마 변경 | 영향받는 서브프로젝트의 ORM 모델, 마이그레이션 |

## Sub-agent 위임 규칙

이 monorepo는 다국어 스택이므로 작업의 도메인에 맞는 전문 에이전트로 위임:

| 도메인 | 위임 대상 |
|---|---|
| .NET 백엔드 (agenthub) | backend-specialist |
| Python FastAPI (docutil, career) | backend-specialist |
| Next.js / Vue Frontend | frontend-specialist |
| DB 스키마 / 마이그레이션 | database-architect |
| 통합 아키텍처 결정 | enterprise-architect |
| 코드 분석 / 보안 리뷰 | code-analysis-specialist |
| 테스트 작성 | sdet-agent |
| 기술 조사 | research-assistant |

복수 도메인에 걸치는 작업은 병렬 위임.
