# AIAgentManagement — GS인증 준비 TODO

> 작성일: 2026-03-17
> 인증 기관: TTA(한국정보통신기술협회) 또는 KTL, KTC 등 5개 지정기관 중 선택
> 인증 근거: 소프트웨어산업 진흥법 / ISO·IEC 25023 기반
> 평균 심사 기간: **약 2개월**

---

## 📋 전체 준비 단계 개요

```
1단계: 사전 상담 (기관 선택 → 상담 신청)
2단계: 제출 문서 작성 (제품설명서 + 사용자 매뉴얼)
3단계: 시험환경 구성
4단계: 자체 사전 점검 (8가지 품질 특성)
5단계: 신청 접수 → 본 심사
6단계: 결함 수정 → 재시험 → 인증서 발급
```

---

## 1단계. 사전 상담 신청

- [ ] 인증 기관 선택 (TTA 권장 — www.tta.or.kr)
- [ ] 상담 요청서 작성 및 제출
  - 제품명, 버전, 주요 기능 목록 요약
  - 운영 환경 정보 (서버 OS, DB, 클라우드 여부)
- [ ] 심사 비용 안내 수령 (기능 수·복잡도 따라 결정)
- [ ] 인증 일정 계획 수립

---

## 2단계. 필수 제출 문서 작성

### 2-A. 제품설명서 (Product Description)

> ✅ 초안 완성 — `DOCS/제품소개서_AIAgentManagement_v1.0.md`

- [x] **제품 개요** 작성
  - 제품명: AIAgentManagement
  - 버전: v1.0
  - 제품 유형: SaaS 웹 서비스 (AI Agent 관리 플랫폼)
  - 지원 환경: Windows Server, SQL Server, IIS
  - 주요 대상 사용자: 기업 내 AI 서비스 운영 담당자

- [x] **핵심 기능 목록** 명세 (아래 기능 전체 문서화 필요)

  | 기능 분류 | 세부 기능 |
  |---|---|
  | 사용자 관리 | 회원가입, 로그인, 비밀번호 재설정, 프로필 관리, 역할(Role) 관리 |
  | Agent 관리 | Agent 생성/수정/삭제, AgentBuilder, 시스템 프롬프트 설정, 아이콘/색상 지정 |
  | 채팅 | 단일 채팅, 멀티 에이전트 채팅, 파일 첨부, 대화 내역 저장/검색 |
  | Knowledge Base | 문서 업로드, 인덱싱(RAG), AI Q&A, 청크 관리 |
  | Workflow | 시각적 워크플로우 편집기, 노드 연결, 테스트 실행 |
  | AI 서비스 연동 | OpenAI, Claude, Gemini, Perplexity, Mistral, Tavily 연동 |
  | 이미지 생성 | AI 이미지 생성 (DALL-E 등) |
  | 프레젠테이션 | AI 기반 PPT/발표자료 생성 |
  | 도구 빌더 | 사용자 정의 Tool 생성·관리 |
  | 팀 관리 | 팀 생성, 팀원 초대, 권한 부여 |
  | API 관리 | API 키 발급, 사용량 조회, 외부 연동 |
  | 관리자 기능 | 사용자 관리, API 서비스 설정, 금지어 관리, 시스템 설정, 활동 로그, 분석 대시보드 |
  | 보안 | JWT 인증, Role 기반 접근 제어, Rate Limiting, PII 탐지 로그 |
  | 파일 업로드 | 이미지/문서/오디오/동영상 업로드, 용량 제한, 확장자 제한 |
  | 도움말 | FAQ, 튜토리얼, 이메일 문의 |
  | 법적 페이지 | 이용약관, 개인정보처리방침 |

- [x] **시스템 아키텍처 다이어그램** 작성
  - Frontend: Vue 3 + TypeScript + Vite
  - Backend: ASP.NET Core 8 Web API
  - DB: SQL Server (메인) + Redis (캐시/세션)
  - 배경 작업: Hangfire (예약 작업) + BackgroundService (ActivityLog Worker)
  - AI 연동: 외부 AI API (HTTP)

- [x] **운영 환경 요구사항** 명세
  - 서버: Windows Server 2019+ / IIS 10+
  - .NET 8 Runtime
  - SQL Server 2019+
  - Redis 7+
  - 권장 RAM: 8GB 이상
  - 클라이언트: Chrome/Edge/Firefox 최신 버전

---

### 2-B. 사용자 취급설명서 (User Manual)

> ✅ 초안 완성 — `DOCS/사용자취급설명서_AIAgentManagement_v1.0.md`

- [x] **설치 가이드** 작성 (2.1절 — DB 생성, 환경변수, IIS 배포, 초기 계정 생성)
- [x] **관리자 매뉴얼** 작성 (2.3.11절 — 사용자 관리, AI 서비스 설정, 금지어, PII, Hangfire)
- [x] **사용자 매뉴얼** 작성 (2.3절 전체 — 회원가입~프레젠테이션 생성 12개 기능 단계별 기술)
- [x] **오류 메시지 목록** 작성 (3.4절 — HTTP 코드별 오류 코드·해결 방법)
- [ ] 실제 서비스 화면 스크린샷 추가 (제출 전 보완 권장)

---

### 2-C. 기타 제출 서류

- [ ] 사업자등록증 사본
- [ ] 법인인감증명서 (필요 시)
- [ ] 시험환경 구성 정보서
  - 서버 사양 (CPU, RAM, 디스크)
  - OS 버전 (Windows Server 버전)
  - DBMS 버전 (SQL Server 버전)
  - .NET 버전
  - 브라우저 (Chrome 버전)

---

## 3단계. 시험환경 구성

- [ ] 실 운영환경과 동일한 **별도 시험용 서버** 구성
- [ ] 시험용 DB 및 테스트 데이터 준비
  - 테스트 관리자 계정
  - 테스트 일반 사용자 계정 (복수)
  - 샘플 Agent, 채팅, 문서 데이터
- [ ] HTTPS 인증서 적용 확인
- [ ] 외부 AI API 키 유효성 확인 (시험 중 API 호출 가능 상태)

---

## 4단계. ISO/IEC 25023 품질 특성별 자체 점검

### 4-1. 기능 적합성 (Functional Suitability) ✅ 보완 완료

> **현황 분석 일자**: 2026-03-17
> **보완 완료일**: 2026-03-18
> **전체 평가**: 기능 구현 완성도 높음. 일관성·표준화 보완 완료.

---

#### ✅ 현재 양호한 부분

| 항목 | 상태 | 근거 |
|---|---|---|
| 모든 기능 구현 완료 | ✅ | 28개 Controller, 전 기능 동작 확인 |
| try-catch 예외 처리 | ✅ | 모든 컨트롤러 메서드에 적용 |
| Role 기반 접근 제어 | ✅ | `[Authorize(Roles="Admin")]` 18개 엔드포인트 |
| 사용자 정의 예외 | ✅ | BannedWordException, PiiDetectionException 별도 처리 |
| 에러 로깅 | ✅ | `_logger.LogError(ex, ...)` 패턴 전체 적용 |
| API 키 인증 | ✅ | ApiKeyAuthorizeAttribute (IP화이트리스트, Rate Limit, Scope) |

---

#### ⚠️ 보완 필요 항목 (GS심사 감점 포인트)

---

##### [문제 1] 오류 응답 형식 불통일 — **높은 우선순위**

**현황:**
- `ErrorResponseDto` (표준 형식) 가 정의되어 있으나 BannedWord/PII 케이스에만 사용
- 대부분의 컨트롤러는 익명 객체로 응답:
  ```csharp
  return BadRequest(new { message = "..." })          // 대부분
  return StatusCode(500, new { message = "..." })     // 일부
  return BadRequest(ModelState)                       // KnowledgeBaseController
  ```
- 동일한 오류 상황에 대해 응답 구조가 컨트롤러마다 다름

**보완 완료:**
- [x] `GlobalExceptionHandlerMiddleware` 추가 완료
- [x] 모든 컨트롤러에서 `ErrorResponseDto` 통일 완료 (~217건 교체)
- [x] 에러 코드 카탈로그 적용 (INTERNAL_SERVER_ERROR, NOT_FOUND, FORBIDDEN, BAD_REQUEST, UNAUTHORIZED, BANNED_WORD_DETECTED, PII_DETECTED)

```csharp
// Program.cs에 추가
app.UseExceptionHandler(exceptionHandlerApp => {
    exceptionHandlerApp.Run(async context => {
        context.Response.StatusCode = 500;
        context.Response.ContentType = "application/json";
        var error = context.Features.Get<IExceptionHandlerPathFeature>();
        await context.Response.WriteAsJsonAsync(new ErrorResponseDto {
            Message = "서버 내부 오류가 발생했습니다.",
            ErrorCode = "INTERNAL_SERVER_ERROR",
            Timestamp = DateTime.UtcNow
        });
    });
});
```

---

##### [문제 2] ModelState 유효성 검사 누락 — **높은 우선순위**

**현황:**
- DTO에 `[Required]`, `[EmailAddress]`, `[MinLength(8)]` 어트리뷰트는 정의됨
- 그러나 컨트롤러에서 `ModelState.IsValid` 체크하는 곳이 일부뿐:
  - 체크함: ChatController, KnowledgeBaseController, ImageGenerationController
  - **체크 안 함**: AuthController, AgentsController, UsersController 등 대다수
- 결과: 필수 필드 누락된 요청이 서비스 레이어까지 도달

**보완 완료:**
- [x] 전체 28개 컨트롤러 `[ApiController]` 적용 확인 — 자동 ModelState 검증 동작 중
- [x] `UpdateUserRequestDto` — [MaxLength], [Phone], [MinLength(8)], [RegularExpression] 추가
- [x] `CreateAgentRequestDto` / `UpdateAgentRequestDto` — Temperature [Range(0.0,2.0)], MaxTokens [Range(1,128000)] 추가
- [x] `ImageGenerationRequestDto` — Prompt [MaxLength(4000)], NumberOfImages [Range(1,4)] 추가
- [x] `Program.cs` ApiBehaviorOptions — VALIDATION_ERROR 코드 포함 통일 응답 형식 적용

---

##### [문제 3] HTTP 상태 코드 불통일 — **중간 우선순위**

**현황:**

| 상황 | 현재 사용 | 올바른 방식 |
|---|---|---|
| 권한 없음 (403) | `StatusCode(403)` 또는 `Forbid()` 혼용 | `Forbid()` 통일 |
| 서버 오류 | `StatusCode(500, new {...})` | `Problem()` 사용 권장 |
| 리소스 없음 | `NotFound()` 또는 `NotFound(new {...})` | `NotFound(new {...})` 통일 |

**보완 완료:**
- [x] 403 응답: `StatusCode(403, ErrorResponseDto.Forbidden(...))` 통일
- [x] 500 응답: `StatusCode(500, ErrorResponseDto.InternalError(...))` 통일
- [x] 404 응답: `NotFound(ErrorResponseDto.NotFound(...))` 통일
- [x] 400 응답: `BadRequest(ErrorResponseDto.BadRequest(...))` 통일
- [x] 401 응답: `Unauthorized(ErrorResponseDto.Unauthorized(...))` 통일

---

##### [문제 4] [AllowAnonymous] 표기 불일치 — **낮은 우선순위**

**현황:**
- AgentsController: 공개 에이전트 조회 4개 엔드포인트에 `[AllowAnonymous]` 명시
- 다른 공개 엔드포인트(공개 채팅 등)는 누락

**보완 완료:**
- [x] AuthController — login, register, refresh, forgot-password, reset-password `[AllowAnonymous]` 명시
- [x] ExamplePromptsController — GET, GET/{id} `[AllowAnonymous]` 추가
- [x] FaqsController, TutorialsController — 기존 적용 유지
- [x] AgentsController — public/* 엔드포인트 4개 기존 적용 유지
- [x] 접근 정책 일람표 — 사용자취급설명서 2.2 기능목록에 권한 컬럼 포함

---

#### 📋 기능 적합성 보완 작업 목록

| 우선순위 | 작업 | 예상 공수 | 담당 파일 |
|---|---|---|---|
| ✅ 완료 | GlobalExceptionHandlerMiddleware 구현 | — | Program.cs |
| ✅ 완료 | [ApiController] 전체 적용 확인 + DTO 유효성 보완 | — | DTOs/ |
| ✅ 완료 | HTTP 상태 코드 통일 (400/401/403/404/500) | — | 전체 Controllers |
| ✅ 완료 | ErrorResponseDto 통일 사용 (~217건) | — | 전체 Controllers |
| ✅ 완료 | [AllowAnonymous] 표기 정리 | — | 공개 Controllers |
| ✅ 완료 | 에러 코드 카탈로그 적용 | — | ErrorResponseDto.cs |

---

#### 전수 테스트 체크리스트 (GS심사 대비)

- [ ] 제품설명서에 기재된 모든 기능 동작 확인 (전수 테스트)
- [ ] 각 기능의 입력→처리→출력 결과 일치 여부 검증
- [x] 예외 처리 및 오류 메시지 출력 확인 ← ErrorResponseDto 통일 완료
- [x] 권한 없는 기능 접근 시 차단 확인 (Role 기반) ← 양호
- [x] 필수 입력 누락 시 400 오류 반환 확인 ← [ApiController] + DTO 유효성 보완 완료
- [x] 존재하지 않는 리소스 조회 시 404 반환 확인 ← NotFound(ErrorResponseDto.NotFound()) 통일 완료

### 4-2. 성능 효율성 (Performance Efficiency) ⚠️ 코드 최적화 완료 / 실측 필요

- [ ] **응답 시간 측정** — `performance-tests/01-auth.test.js`, `02-agents.test.js`, `03-chat.test.js` 실행
  - 목표: 일반 API p(95) < 2,000ms (AI 응답 제외)
- [ ] **동시 사용자 부하 테스트** — `performance-tests/04-concurrent-users.test.js` 실행
  - 10명 동시 접속, p(95) < 2,000ms, 오류율 < 1%
  - 결과 리포트: `performance-tests/results/concurrent-users-summary.txt` 자동 생성
- [ ] **파일 업로드 성능** — `performance-tests/05-file-upload.test.js` 실행
  - p(95) < 5,000ms
- [x] AI API 타임아웃 설정 (DefaultTimeout: 120초)
- [x] DB 인덱스 6개 OnModelCreating 반영 완료 (운영 DB SQL 직접 적용 필요)
- [x] ChatService AsNoTracking 4곳 적용 완료
- [x] ActivityLogging 비동기 Channel 처리 완료 (ActivityLogWorker)
- [x] Named HttpClient 등록 완료 (openai, claude, gemini, perplexity, mistral)

> **k6 설치**: `winget install k6`
> **실행**: `k6 run -e BASE_URL=https://agenthub.idino.co.kr performance-tests/04-concurrent-users.test.js`
> 상세 가이드: [performance-tests/README.md](performance-tests/README.md)

### 4-3. 호환성 (Compatibility)

- [ ] **브라우저 호환성 테스트**
  - [ ] Chrome 최신 버전 ✓
  - [ ] Microsoft Edge 최신 버전
  - [ ] Firefox 최신 버전
  - [ ] Safari (Mac/iOS) — 부분 지원 여부 명시
- [ ] 모바일 반응형 동작 확인 (1280px / 768px / 375px)
- [ ] 한글 데이터 입출력 정상 확인

### 4-4. 사용성 (Usability)

- [ ] 주요 기능 접근 단계 확인 (3클릭 이내 도달 권장)
- [ ] 오류 발생 시 사용자 안내 메시지 표시 확인
- [ ] 필수 입력 항목 미입력 시 안내 확인
- [ ] 로딩 상태 표시 (스피너/스켈레톤) 확인
- [ ] 빈 상태(데이터 없음) 화면 안내 문구 확인
- [ ] **접근성 (Accessibility) 기본 점검**
  - input 요소에 label 또는 placeholder 존재
  - 이미지에 alt 텍스트 존재
  - 키보드 탭 이동 가능 여부

### 4-5. 신뢰성 (Reliability)

- [ ] 서버 재시작 후 정상 동작 확인
- [ ] DB 연결 끊김 후 재연결 동작 확인
- [ ] Redis 연결 실패 시 Fallback 동작 확인
- [ ] ActivityLogWorker 백그라운드 서비스 재시작 후 동작 확인
- [ ] 장시간(4시간+) 연속 운영 테스트
- [ ] AI API 타임아웃/오류 발생 시 사용자 안내 확인

### 4-6. 보안성 (Security) ✅ 코드 보강 완료 / 운영 점검 필요

- [x] **HTTPS 전용 운영** — RequireHttpsForDomainMiddleware 적용 완료
- [ ] **JWT 토큰** 만료 및 갱신 동작 확인
- [x] **비인가 접근 차단** — [Authorize] / [Authorize(Roles="Admin")] 전체 적용
- [x] **SQL Injection 방어** — EF Core 파라미터화 쿼리 사용
- [x] **XSS 방어** — Help.vue v-html에 DOMPurify.sanitize() 적용 완료
- [x] **보안 헤더** — SecurityHeadersMiddleware 추가 완료
  - X-Frame-Options: SAMEORIGIN
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: camera=(), microphone=(), geolocation=()
  - Strict-Transport-Security (HTTPS 접속 시 자동 적용)
  - Content-Security-Policy (Vue SPA 호환 설정)
- [x] **CORS** — 프로덕션 도메인 `https://agenthub.idino.co.kr` 추가 완료
- [ ] **파일 업로드 보안** 확인
  - 허용 확장자 외 차단 (appsettings AllowedExtensions 설정)
  - 저장 경로 외부 노출 방지
- [ ] **Rate Limiting** 설정 운영 값 조정
- [ ] **개인정보** 처리 최소화 확인 (불필요한 PII 미저장)
- [x] **비밀번호 정책** — 최소 8자, BCrypt 해시 저장 확인
- [x] **관리자 기능 접근 제어** — Hangfire Admin role 체크 구현 완료
- [ ] **보안 취약점 진단 도구** 실행
  - OWASP ZAP (무료) 스캔 후 리포트 첨부 권장

### 4-7. 유지보수성 (Maintainability)

- [ ] 로그 레벨 설정 확인 (Production: Warning 이상)
- [ ] 오류 발생 시 로그 기록 확인 (ILogger 사용)
- [ ] Hangfire 작업 실패 시 재시도 동작 확인
- [ ] 설정 변경(appsettings) 시 재시작 없이 반영되는 항목 문서화

### 4-8. 이식성 (Portability)

- [ ] 설치 절차 문서화 완성도 확인
- [ ] 신규 서버 환경 설치 테스트 (처음부터 재현 가능한지)
- [ ] DB 백업/복원 절차 확인 (DatabaseBackupController 동작)
- [ ] Docker 컨테이너화 고려 (선택 — 이식성 점수 향상)

---

## 5단계. 보안성 보강 항목 (신청 전 필수)

> GS인증에서 보안성은 감점 포인트가 가장 많은 영역

### 5-1. XSS 취약점 점검

- [x] `Help.vue` — FAQ 답변 `v-html`에 `DOMPurify.sanitize()` 적용 완료
  - `dompurify ^3.0.6` 이미 설치됨, `sanitize(faq.answer)` 함수로 래핑

### 5-2. 보안 헤더 추가

- [x] `Middleware/SecurityHeadersMiddleware.cs` 신규 생성 및 Program.cs 등록 완료
  - X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
  - Referrer-Policy, Permissions-Policy
  - Strict-Transport-Security (HTTPS 환경 자동)
  - Content-Security-Policy (Vue SPA 호환)

### 5-3. 개인정보처리방침 연동

- [ ] 이용약관/개인정보처리방침 페이지에 실제 내용 기재 (법무 검토)
- [ ] 회원가입 시 약관 동의 체크박스 확인

---

## 6단계. 신청 접수 및 심사 대응

- [ ] 신청서 및 문서 일체 제출
- [ ] 시험환경 접속 정보 제공 (심사관용 계정)
- [ ] 심사 중 결함 발견 시 수정 기간 내 패치 적용
- [ ] 재시험 통과 → 인증서 발급 (약 2개월 소요)

---

## 🔵 추가 권장 사항 (점수 향상)

| 항목 | 설명 | 난이도 |
|---|---|---|
| ~~보안 헤더 추가~~ | ✅ SecurityHeadersMiddleware 완료 | ~~낮음~~ |
| ~~XSS 방어 강화~~ | ✅ DOMPurify.sanitize() 완료 | ~~낮음~~ |
| ~~성능 테스트 리포트~~ | ✅ k6 스크립트 완성 (실행 후 결과 첨부) | ~~중간~~ |
| ~~에러 응답 통일~~ | ✅ ErrorResponseDto 전 컨트롤러 적용 완료 | ~~중간~~ |
| ~~라이선스 교체~~ | ✅ EPPlus/QuestPDF → ClosedXML/DocumentFormat.OpenXml | ~~낮음~~ |
| ~~사용자 취급설명서~~ | ✅ `DOCS/사용자취급설명서_AIAgentManagement_v1.0.md` 완성 | ~~높음~~ |
| OWASP ZAP 스캔 리포트 | 취약점 진단 결과 첨부 | 중간 |
| 접근성 개선 | WCAG 2.1 AA 기준 일부 적용 | 중간 |
| Docker 컨테이너화 | 이식성 점수 향상 | 높음 |
| API 문서 (Swagger) | ✅ `/swagger` 이미 적용됨 | ~~낮음~~ |

---

## 📂 GS인증 제출 문서 패키지 구성 (최종)

```
GS인증_제출패키지/
├── 01_신청서.pdf
├── 02_사업자등록증.pdf
├── 03_제품설명서_AIAgentManagement_v1.0.pdf
├── 04_사용자취급설명서_AIAgentManagement_v1.0.pdf
├── 05_시험환경정보.pdf
├── 06_보안취약점진단결과(OWASP_ZAP).pdf  ← 권장
└── 07_성능테스트결과(JMeter).pdf          ← 권장
```

---

## 🏢 인증 기관 연락처

| 기관 | 웹사이트 | 비고 |
|---|---|---|
| **TTA 한국정보통신기술협회** | www.tta.or.kr | 가장 일반적 |
| KTL 한국산업기술시험원 | customer.ktl.re.kr | |
| KTC 한국기계전기전자시험연구원 | www.ktc.re.kr | |

> 사전 상담 후 비용 및 일정 확정 → 2개월 내 인증 완료 목표

---

*이 파일은 GS인증 준비 진행에 따라 업데이트하세요.*
