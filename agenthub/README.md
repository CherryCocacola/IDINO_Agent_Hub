# AI Agent 통합관리 시스템

ASP.NET Core 8.0, MSSQL, Vue.js 3를 사용하여 구축된 AI Agent 통합관리 시스템입니다.

## 기술 스택

### Backend
- **ASP.NET Core 8.0** - Web API 프레임워크
- **Entity Framework Core 8.0** - ORM
- **Microsoft SQL Server** - 데이터베이스
- **JWT** - 인증 시스템
- **SignalR** - 실시간 통신
- **Redis** - 캐싱 (선택적)
- **Hangfire** - 백그라운드 작업
- **MailKit** - 이메일 발송

### Frontend
- **Vue.js 3** - 프론트엔드 프레임워크
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구
- **Vue Router** - 라우팅
- **Pinia** - 상태 관리
- **Axios** - HTTP 클라이언트
- **Bootstrap 5.3** - UI 프레임워크
- **SignalR Client** - 실시간 통신

## 프로젝트 구조

```
AIAgentManagement/
├── Controllers/          # API Controllers
├── Services/            # Business Logic
├── Models/              # EF Core Models
├── Data/                # DbContext 및 Repository
├── DTOs/                # Data Transfer Objects
├── Middleware/          # Custom Middleware
├── Hubs/                # SignalR Hubs
├── BackgroundJobs/      # Hangfire Jobs
├── ClientApp/           # Vue.js 프로젝트
│   ├── src/
│   │   ├── views/       # Vue 페이지 컴포넌트
│   │   ├── components/  # 재사용 컴포넌트
│   │   ├── services/    # API 서비스
│   │   ├── stores/      # Pinia 스토어
│   │   └── router/      # Vue Router
│   └── package.json
├── wwwroot/             # 정적 파일
└── Program.cs           # 애플리케이션 진입점
```

## 설치 및 실행

### 사전 요구사항

- .NET 8.0 SDK
- Node.js 18+ 및 npm
- SQL Server (LocalDB 또는 SQL Server Express)
- Redis (선택적, 없으면 MemoryCache 사용)

### Backend 설정

1. 데이터베이스 연결 문자열 설정
   - `appsettings.json`에서 `ConnectionStrings:DefaultConnection` 수정

2. JWT Secret Key 설정
   - `appsettings.json`에서 `JwtSettings:SecretKey` 설정 (최소 32자)

3. AI API 키 설정 (선택적)
   - `appsettings.json`에서 `AiApiSettings:OpenAI:ApiKey` 및 `AiApiSettings:Claude:ApiKey` 설정

4. 이메일 설정 (선택적)
   - `appsettings.json`에서 `EmailSettings` 섹션 구성

5. 데이터베이스 마이그레이션
   ```bash
   dotnet ef database update
   ```
   또는 애플리케이션 실행 시 자동 생성 (EnsureCreated)

6. 백엔드 실행
   ```bash
   dotnet run
   ```

### Frontend 설정

1. 의존성 설치
   ```bash
   cd ClientApp
   npm install
   ```

2. 개발 서버 실행
   ```bash
   npm run dev
   ```

3. 프로덕션 빌드
   ```bash
   npm run build
   ```

## 기본 로그인 정보

- **이메일**: admin@example.com
- **비밀번호**: Admin123!

## 주요 기능

- ✅ 사용자 인증 및 권한 관리
- ✅ AI Agent 생성 및 관리
- ✅ 다중 AI 서비스 지원 (OpenAI, Claude 등)
- ✅ 실시간 채팅 인터페이스
- ✅ 할당량 관리 및 모니터링
- ✅ 사용량 통계 및 분석
- ✅ 비용 추적
- ✅ SignalR 실시간 통신
- ✅ 백그라운드 작업 (할당량 리셋, 리포트 생성)
- ✅ 파일 업로드
- ✅ 이메일 알림

## API 엔드포인트

### 인증
- `POST /api/auth/login` - 로그인
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/logout` - 로그아웃
- `POST /api/auth/refresh` - 토큰 갱신

### 사용자
- `GET /api/users` - 사용자 목록 (Admin)
- `GET /api/users/{id}` - 사용자 조회
- `GET /api/users/me` - 현재 사용자 정보
- `POST /api/users` - 사용자 생성 (Admin)
- `PUT /api/users/{id}` - 사용자 수정
- `DELETE /api/users/{id}` - 사용자 삭제 (Admin)

### Agent
- `GET /api/agents` - Agent 목록
- `GET /api/agents/{id}` - Agent 조회
- `POST /api/agents` - Agent 생성
- `PUT /api/agents/{id}` - Agent 수정
- `DELETE /api/agents/{id}` - Agent 삭제

### 채팅
- `GET /api/chat/conversations` - 대화 목록
- `POST /api/chat/conversations` - 대화 생성
- `GET /api/chat/conversations/{id}/messages` - 메시지 목록
- `POST /api/chat/conversations/{id}/messages` - 메시지 전송

### 할당량
- `GET /api/quota` - 할당량 목록 (Admin)
- `GET /api/quota/my-quotas` - 내 할당량 조회
- `POST /api/quota/user/{userId}/service/{serviceId}` - 할당량 설정 (Admin)

### 통계
- `GET /api/analytics/dashboard` - 대시보드 통계
- `GET /api/analytics/usage` - 사용량 통계
- `GET /api/analytics/cost` - 비용 분석

## 개발 가이드

### 새 API 엔드포인트 추가

1. `Services/` 폴더에 서비스 인터페이스 및 구현 추가
2. `DTOs/` 폴더에 DTO 클래스 추가
3. `Controllers/` 폴더에 Controller 추가
4. `Program.cs`에 서비스 등록

### 새 Vue 페이지 추가

1. `ClientApp/src/views/` 폴더에 Vue 컴포넌트 생성
2. `ClientApp/src/router/index.ts`에 라우트 추가
3. 필요시 `ClientApp/src/stores/`에 Pinia 스토어 추가

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
