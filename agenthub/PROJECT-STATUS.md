# AIAgentManagement 프로젝트 현재 상태

> 최종 업데이트: 2026-03-16

---

## 개요

**AI 에이전트 관리 플랫폼** — ASP.NET Core 8 + Vue 3 풀스택
조직 내 AI 에이전트를 중앙에서 생성·배포·관리하는 관리자 포털 + 공개 챗봇 페이지

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | ASP.NET Core 8, Entity Framework Core 8, SQL Server |
| 프론트엔드 | Vue 3 (Composition API, TypeScript), Bootstrap 5 |
| 캐싱 | StackExchange.Redis |
| 백그라운드 작업 | Hangfire |
| 인증 | JWT Bearer, BCrypt |
| API 문서 | Swagger (Swashbuckle) |
| Rate Limiting | ASP.NET Core 내장 (`Microsoft.AspNetCore.RateLimiting`) |
| QR 코드 | QRCoder 1.6.0 |
| 문서 처리 | EPPlus, QuestPDF, PdfPig, OpenXML, CsvHelper |

---

## 구현 완료 기능

### 1. 사용자 & 인증
- JWT 로그인 / 로그아웃 / 토큰 갱신
- 사용자 생성 / 수정 / 역할 관리 (Admin / User)
- 팀 관리 (Teams / TeamMembers)

### 2. AI 에이전트 관리
- 에이전트 생성 / 수정 / 삭제 (AgentBuilder — 5단계 위저드)
- 지원 AI 서비스: OpenAI, Claude, Gemini, Mistral, Perplexity, Azure OpenAI, GitHub Copilot
- 에이전트별 설정: 모델, 온도, 최대 토큰, 시스템 프롬프트, 아이콘, 색상
- PII 보호 (masking / block 모드), 금지어 필터
- RAG 연동 (지식 베이스 문서 선택)
- 에이전트 마켓플레이스 / 템플릿

### 3. 공개 채팅 & 임베드
- `GET /chatbot/:code` — 비로그인 챗봇 페이지
- `GET /embed/:code` — 웹페이지 iframe 임베드
- 게스트 채팅 허용 토글 (에이전트별)
- 환영 메시지, 입력창 안내 문구, 테마(밝음/어두움/시스템) 설정
- **임베드 도메인 화이트리스트** — `AllowedEmbedDomains` 컬럼으로 Origin 검증
- **QR 코드 생성** — `GET /api/agents/public/{code}/qr?size=400` PNG 반환

### 4. OpenAI 호환 API (LiteLLM 대안)
- `GET  /v1/models` — 접근 가능한 에이전트 목록 (OpenAI model 형식)
- `POST /v1/chat/completions` — 비스트리밍 + SSE 스트리밍 (`stream: true`)
- `X-API-Key` / `Authorization: Bearer` 인증
- agentCode = OpenAI `model` 필드로 매핑

### 5. Rate Limiting
- `ip-guest` 정책: IP당 분당 20 요청 (공개 엔드포인트)
- `ip-openai` 정책: IP당 분당 30 요청 (OpenAI 호환 API)
- `per-user` 정책: 사용자당 분당 60 요청 (인증 사용자)
- 거절 시 `429 + Retry-After: 60` 헤더 + 한국어 메시지

### 6. Fallback & Load Balancing
- **429 자동 Fallback**: `AiProxyService`에서 429 수신 시 자동으로 다음 모델로 전환
  - 기본 매핑: `gpt-4o → gpt-4o-mini`, `claude-opus → claude-sonnet → claude-haiku`, etc.
  - 요청 시 `FallbackModel` 필드로 수동 지정 가능
- **API 키 풀 (Load Balancing)**: `ApiKeyPoolService`
  - `appsettings.json`의 `ApiKeys[]` 배열로 여러 키 등록
  - 라운드로빈 방식 순환 사용
  - 429/오류 시 해당 키 60초 냉각(Cooldown), 나머지 키로 자동 전환
  - `GET /api/analytics/pool-stats` — 키 상태 조회

### 7. 응답 캐싱
- SHA256 해시 기반 캐시 키 (agentId + model + 메시지 내용)
- TTL: 5분, 백엔드: Redis
- 캐싱 제외 조건: RAG, 웹검색, 멀티모달(이미지 첨부) 요청

### 8. 대화 관리
- 대화 생성 / 조회 / 삭제
- 메시지 이력 저장 (ChatConversation, ChatMessage)
- 스트리밍 응답 (SSE)

### 9. 지식 베이스 (RAG)
- 문서 업로드 (PDF, Word, Excel, CSV, TXT)
- 벡터 임베딩 + 유사도 검색
- 에이전트별 문서 연결

### 10. 워크플로우 엔진
- 노드 기반 시각적 워크플로우 빌더
- 트리거 / 조건 / 액션 노드
- 실행 이력 모니터링

### 11. 도구 (Tools)
- 커스텀 도구 생성 (API 호출 / 스크립트 / C# 코드)
- 버전 관리, 실행 이력

### 12. 이미지 / 비디오 생성
- DALL-E, Imagen 등 이미지 생성 API 연동
- 비디오 생성 (준비 중 표시)

### 13. 프레젠테이션 생성
- AI 기반 슬라이드 자동 생성
- 템플릿 관리, PPTX 내보내기

### 14. 분석 & 모니터링
- 통합 Analytics 대시보드 (사용자 / API 호출 / 비용 / 토큰)
- **에이전트별 통계**: 대화수, 총 요청, 토큰, 비용, 응답시간, 성공률 (일/주/월/년)
- 비용 분석 (`CostAnalysis`)
- 사용 이력 (`UsageHistory`)
- 감사 로그 (`AuditLog`)

### 15. 보안 & 관리
- API 키 관리 (외부 서비스 키)
- 금지어 관리
- PII 검출 로그
- 할당량(Quota) 관리

### 16. 시스템
- 시스템 상태 (`SystemHealth`)
- DB 백업 (`DatabaseBackup`)
- 시스템 설정

---

## 라우트 목록

### 공개 (인증 불필요)
| 경로 | 컴포넌트 | 설명 |
|------|----------|------|
| `/login` | Login.vue | 로그인 |
| `/chatbot/:code` | AgentPublicChat.vue | 공개 챗봇 |
| `/embed/:code` | AgentEmbed.vue | 임베드 채팅 |
| `/agent-test/:code` | AgentTestPage.vue | 에이전트 테스트 |

### 내부 (인증 필요)
| 경로 | 컴포넌트 |
|------|----------|
| `/` | Dashboard |
| `/agents` | AgentSelect |
| `/agents/chat/:id?` | AgentChat |
| `/agents/multi-chat` | AgentMultiChat |
| `/agents/builder` | AgentBuilder |
| `/agents/marketplace` | AgentMarketplace |
| `/agents/templates` | AgentTemplates |
| `/analytics` | Analytics |
| `/cost-analysis` | CostAnalysis |
| `/usage-history` | UsageHistory |
| `/audit-log` | AuditLog |
| `/quota` | Quota |
| `/api-keys` | ApiKeys |
| `/users` | Users |
| `/team` | Team |
| `/knowledge-base` | KnowledgeBase |
| `/tools` | ToolList |
| `/tools/builder` | ToolBuilder |
| `/workflows` | WorkflowList |
| `/workflows/builder` | WorkflowBuilder |
| `/workflows/executions/:id?` | WorkflowExecutionMonitor |
| `/image-generation` | ImageGeneration |
| `/quick-image` | QuickImageGeneration |
| `/video-generation` | VideoGeneration |
| `/presentation-builder` | PresentationBuilder |
| `/presentation-templates` | PresentationTemplateManagement |
| `/banned-words` | BannedWords |
| `/pii-protection` | PiiProtection |
| `/system-health` | SystemHealth |
| `/database-backup` | DatabaseBackup |
| `/playground` | Playground |
| `/settings` | Settings |
| `/help` | Help |
| `/reports` | Reports |

---

## 주요 API 엔드포인트

### 에이전트
```
GET    /api/agents                          # 목록
POST   /api/agents                          # 생성
GET    /api/agents/{id}                     # 상세
PUT    /api/agents/{id}                     # 수정
DELETE /api/agents/{id}                     # 삭제
GET    /api/agents/bycode/{code}            # 코드로 조회
GET    /api/agents/public/{code}/info       # 공개 정보 (Rate Limited)
POST   /api/agents/public/{code}/chat       # 공개 채팅 (Rate Limited)
POST   /api/agents/public/{code}/stream     # 공개 스트리밍 (Rate Limited)
GET    /api/agents/public/{code}/qr         # QR 코드 PNG (?size=400)
```

### OpenAI 호환
```
GET    /v1/models                           # 에이전트 목록
GET    /v1/models/{model}                   # 에이전트 상세
POST   /v1/chat/completions                 # 채팅 (스트리밍 지원)
```

### 분석
```
GET    /api/analytics/dashboard             # 전체 대시보드
GET    /api/analytics/usage                 # 사용량 통계
GET    /api/analytics/cost                  # 비용 분석
GET    /api/analytics/top-users             # 상위 사용자
GET    /api/analytics/agents/{id}/stats     # 에이전트별 통계 (?period=day|week|month|year)
GET    /api/analytics/pool-stats            # API 키 풀 상태
```

---

## DB 변경사항 (수동 실행 필요)

이전에 이미 실행된 컬럼과 아직 실행이 필요한 컬럼:

```sql
-- ✅ 이미 실행 완료 (사용자 직접 실행)
ALTER TABLE Agents ADD WelcomeMessage   NVARCHAR(1000) NULL;
ALTER TABLE Agents ADD PlaceholderText  NVARCHAR(500)  NULL;
ALTER TABLE Agents ADD ChatTheme        NVARCHAR(20)   NULL DEFAULT 'light';
ALTER TABLE Agents ADD AllowGuestChat   BIT            NOT NULL DEFAULT 0;

-- ⚠️ 아직 실행 필요
ALTER TABLE Agents ADD AllowedEmbedDomains NVARCHAR(2000) NULL;
```

---

## 설정 파일 구조 (appsettings.json)

```json
{
  "AiApiSettings": {
    "OpenAI": {
      "ApiKey": "sk-...",
      "ApiKeys": ["sk-key1", "sk-key2"]   // 로드밸런싱용 복수 키
    },
    "Claude":      { "ApiKey": "..." },
    "Gemini":      { "ApiKey": "..." },
    "Mistral":     { "ApiKey": "..." },
    "Perplexity":  { "ApiKey": "..." },
    "AzureOpenAI": { "ApiKey": "...", "Endpoint": "..." }
  },
  "ConnectionStrings": {
    "DefaultConnection": "..."
  },
  "Redis": {
    "ConnectionString": "localhost:6379"
  }
}
```

---

## 파일 구조 요약

```
AIAgentManagement/
├── Controllers/          # 28개 컨트롤러
│   ├── AgentsController.cs        (에이전트 + QR + 공개 채팅)
│   ├── OpenAICompatController.cs  (OpenAI 호환 /v1/* API)
│   ├── AnalyticsController.cs     (통계 + 에이전트별 통계)
│   └── ...
├── Services/             # 30+ 서비스
│   ├── AiProxyService.cs          (AI 호출 + 429 Fallback + 키 풀)
│   ├── ApiKeyPoolService.cs       (라운드로빈 로드밸런싱)
│   ├── ChatService.cs             (대화 + 캐싱 + Fallback 로직)
│   └── ...
├── DTOs/                 # 79개 DTO
├── Models/               # 36개 모델
├── ClientApp/src/
│   ├── views/
│   │   ├── agent/
│   │   │   ├── AgentBuilder.vue   (5단계 위저드 + QR + 도메인설정)
│   │   │   ├── AgentTestPage.vue  (테스트 + QR 코드 표시)
│   │   │   └── ...
│   │   ├── Analytics.vue          (대시보드 + 에이전트별 통계)
│   │   └── ...
│   └── router/index.ts            (33개 라우트)
└── AIAgentManagement.csproj
```

---

## 알려진 제한 / 향후 과제

| 항목 | 상태 | 비고 |
|------|------|------|
| 랜딩 페이지 | HTML 시안만 존재 | Vue 컴포넌트 미구현 |
| 이용약관 / 개인정보처리방침 | 초안만 존재 | Vue 페이지 미구현 |
| 비디오 생성 | 준비 중 표시 | 실제 API 미연결 |
| 에이전트 편집 (기존 에이전트 수정) | AgentBuilder가 신규 생성만 지원 | 수정 모드 미구현 |
| `AllowedEmbedDomains` DB 컬럼 | 코드 완료, DB 실행 대기 | 위 SQL 실행 필요 |
