# AI Agent 통합관리 시스템 - 데이터베이스 설계서

## 📋 목차
1. [개요](#개요)
2. [테이블 리스트](#테이블-리스트)
3. [테이블 명세서](#테이블-명세서)
4. [ERD](#erd)
5. [인덱스 설계](#인덱스-설계)
6. [DDL 스크립트](#ddl-스크립트)
7. [샘플 데이터](#샘플-데이터)

---

## 개요

### 데이터베이스 정보
- **DBMS**: Microsoft SQL Server 2019+
- **문자셋**: UTF-8 (SQL_Latin1_General_CP1_CI_AS)
- **테이블 수**: 14개
- **FK 제약조건**: 미사용 (애플리케이션 레벨에서 관리)

### 설계 원칙
- 정규화: 3NF (Third Normal Form) 준수
- 명명 규칙: PascalCase (예: Users, ApiQuotas)
- 기본키: 각 테이블마다 ID 컬럼 (IDENTITY)
- 외래키: 물리적 FK 제약조건 없음 (인덱스만 설정)
- 감사: CreatedAt, UpdatedAt 컬럼 포함
- 소프트 삭제: IsDeleted 플래그 사용

---

## 테이블 리스트

| No | 테이블명 | 설명 | 주요 용도 |
|----|---------|------|----------|
| 1 | Users | 사용자 | 사용자 계정 정보 관리 |
| 2 | UserSessions | 사용자 세션 | 로그인 세션 관리 |
| 3 | Roles | 역할 | 사용자 역할 정의 |
| 4 | UserRoles | 사용자-역할 매핑 | 사용자와 역할 연결 |
| 5 | ApiServices | API 서비스 | ChatGPT, Claude 등 서비스 정의 |
| 6 | ApiQuotas | API 할당량 | 사용자별 서비스 할당량 |
| 7 | ApiUsages | API 사용 내역 | API 호출 기록 |
| 8 | Agents | AI Agent | 커스텀 Agent 정의 |
| 9 | ChatConversations | 채팅 대화 | 채팅 세션 관리 |
| 10 | ChatMessages | 채팅 메시지 | 개별 메시지 저장 |
| 11 | ActivityLogs | 활동 로그 | 사용자 활동 추적 |
| 12 | SystemSettings | 시스템 설정 | 전역 설정값 저장 |
| 13 | KnowledgeBaseDocuments | 지식 베이스 문서 | RAG용 문서 저장 |
| 14 | DocumentChunks | 문서 청크 | RAG용 문서 청크 및 임베딩 저장 |

---

## 테이블 명세서

### 1. Users (사용자)

사용자 계정 정보를 관리하는 핵심 테이블입니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| UserId | INT | NOT NULL | IDENTITY(1,1) | 사용자 ID (PK) |
| Email | NVARCHAR(100) | NOT NULL | - | 이메일 (로그인 ID) |
| PasswordHash | NVARCHAR(255) | NOT NULL | - | 암호화된 비밀번호 |
| FullName | NVARCHAR(100) | NOT NULL | - | 전체 이름 |
| PhoneNumber | NVARCHAR(20) | NULL | - | 전화번호 |
| Department | NVARCHAR(100) | NULL | - | 부서 |
| Bio | NVARCHAR(500) | NULL | - | 자기소개 |
| ProfileImageUrl | NVARCHAR(500) | NULL | - | 프로필 이미지 URL |
| Status | NVARCHAR(20) | NOT NULL | 'Active' | 상태 (Active/Pending/Inactive) |
| IsEmailVerified | BIT | NOT NULL | 0 | 이메일 인증 여부 |
| LastLoginAt | DATETIME2 | NULL | - | 마지막 로그인 시간 |
| IsDeleted | BIT | NOT NULL | 0 | 삭제 여부 (소프트 삭제) |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

**제약조건**:
- PRIMARY KEY: UserId
- UNIQUE: Email (WHERE IsDeleted = 0)
- CHECK: Status IN ('Active', 'Pending', 'Inactive')

**인덱스**:
- IDX_Users_Email (Email) - 로그인 조회
- IDX_Users_Status (Status, IsDeleted) - 상태별 조회

---

### 2. UserSessions (사용자 세션)

로그인 세션 및 활성 세션을 관리합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| SessionId | INT | NOT NULL | IDENTITY(1,1) | 세션 ID (PK) |
| UserId | INT | NOT NULL | - | 사용자 ID |
| SessionToken | NVARCHAR(255) | NOT NULL | - | 세션 토큰 (UUID) |
| DeviceInfo | NVARCHAR(500) | NULL | - | 디바이스 정보 |
| IpAddress | NVARCHAR(50) | NULL | - | IP 주소 |
| UserAgent | NVARCHAR(500) | NULL | - | User Agent |
| LoginAt | DATETIME2 | NOT NULL | GETDATE() | 로그인 시간 |
| LastActivityAt | DATETIME2 | NOT NULL | GETDATE() | 마지막 활동 시간 |
| LogoutAt | DATETIME2 | NULL | - | 로그아웃 시간 |
| IsActive | BIT | NOT NULL | 1 | 활성 여부 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |

**제약조건**:
- PRIMARY KEY: SessionId
- UNIQUE: SessionToken

**인덱스**:
- IDX_UserSessions_UserId (UserId, IsActive)
- IDX_UserSessions_Token (SessionToken)

---

### 3. Roles (역할)

사용자 역할을 정의합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| RoleId | INT | NOT NULL | IDENTITY(1,1) | 역할 ID (PK) |
| RoleName | NVARCHAR(50) | NOT NULL | - | 역할 이름 (Admin/Developer/User) |
| DisplayName | NVARCHAR(100) | NOT NULL | - | 표시 이름 |
| Description | NVARCHAR(500) | NULL | - | 설명 |
| Permissions | NVARCHAR(MAX) | NULL | - | 권한 (JSON 형식) |
| IsActive | BIT | NOT NULL | 1 | 활성 여부 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

**기본 데이터**:
- Admin: 관리자
- Developer: 개발자
- User: 일반 사용자

---

### 4. UserRoles (사용자-역할 매핑)

사용자와 역할 간의 다대다 관계를 관리합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| UserRoleId | INT | NOT NULL | IDENTITY(1,1) | 매핑 ID (PK) |
| UserId | INT | NOT NULL | - | 사용자 ID |
| RoleId | INT | NOT NULL | - | 역할 ID |
| AssignedAt | DATETIME2 | NOT NULL | GETDATE() | 할당 일시 |
| AssignedBy | INT | NULL | - | 할당한 사용자 ID |

**제약조건**:
- PRIMARY KEY: UserRoleId
- UNIQUE: (UserId, RoleId)

---

### 5. ApiServices (API 서비스)

ChatGPT, Claude 등 AI 서비스를 정의합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| ServiceId | INT | NOT NULL | IDENTITY(1,1) | 서비스 ID (PK) |
| ServiceCode | NVARCHAR(50) | NOT NULL | - | 서비스 코드 (chatgpt/claude 등) |
| ServiceName | NVARCHAR(100) | NOT NULL | - | 서비스 이름 |
| Description | NVARCHAR(500) | NULL | - | 설명 |
| IconClass | NVARCHAR(100) | NULL | - | 아이콘 CSS 클래스 |
| ColorCode | NVARCHAR(20) | NULL | - | 색상 코드 (HEX) |
| ApiEndpoint | NVARCHAR(500) | NULL | - | API 엔드포인트 URL |
| DefaultModel | NVARCHAR(100) | NULL | - | 기본 모델 |
| CostPerRequest | DECIMAL(10,4) | NOT NULL | 0 | 요청당 비용 ($) |
| IsActive | BIT | NOT NULL | 1 | 활성 여부 |
| SortOrder | INT | NOT NULL | 0 | 정렬 순서 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

**기본 데이터**:
1. ChatGPT - $0.10
2. Claude - $0.15
3. Cursor - $0.15
4. GitHub Copilot - $0.10

---

### 6. ApiQuotas (API 할당량)

사용자별 서비스 할당량을 관리합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| QuotaId | INT | NOT NULL | IDENTITY(1,1) | 할당량 ID (PK) |
| UserId | INT | NOT NULL | - | 사용자 ID |
| ServiceId | INT | NOT NULL | - | 서비스 ID |
| MonthlyLimit | INT | NOT NULL | 1000 | 월간 한도 (요청 수) |
| DailyLimit | INT | NOT NULL | 100 | 일일 한도 (요청 수) |
| CostLimit | DECIMAL(10,2) | NOT NULL | 100.00 | 비용 한도 ($) |
| CurrentUsage | INT | NOT NULL | 0 | 현재 사용량 |
| CurrentCost | DECIMAL(10,2) | NOT NULL | 0.00 | 현재 비용 ($) |
| AlertThreshold | INT | NOT NULL | 80 | 알림 임계값 (%) |
| IsAlertEnabled | BIT | NOT NULL | 1 | 알림 활성화 여부 |
| LastResetAt | DATETIME2 | NULL | - | 마지막 초기화 일시 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

**제약조건**:
- UNIQUE: (UserId, ServiceId) - 사용자당 서비스별 1개 할당량

---

### 7. ApiUsages (API 사용 내역)

API 호출 기록 및 비용을 추적합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| UsageId | BIGINT | NOT NULL | IDENTITY(1,1) | 사용 내역 ID (PK) |
| UserId | INT | NOT NULL | - | 사용자 ID |
| ServiceId | INT | NOT NULL | - | 서비스 ID |
| ConversationId | INT | NULL | - | 대화 ID |
| Model | NVARCHAR(100) | NULL | - | 사용 모델 |
| TokensUsed | INT | NULL | - | 사용 토큰 수 |
| RequestCost | DECIMAL(10,4) | NOT NULL | 0 | 요청 비용 ($) |
| RequestTime | DATETIME2 | NOT NULL | GETDATE() | 요청 시간 |
| ResponseTime | INT | NULL | - | 응답 시간 (ms) |
| StatusCode | INT | NULL | - | HTTP 상태 코드 |
| ErrorMessage | NVARCHAR(MAX) | NULL | - | 오류 메시지 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |

**인덱스**:
- IDX_ApiUsages_UserId_RequestTime
- IDX_ApiUsages_ServiceId_RequestTime
- IDX_ApiUsages_ConversationId

**파티셔닝 권장**: 월별 파티셔닝으로 대용량 데이터 관리

---

### 8. Agents (AI Agent)

커스텀 AI Agent를 정의합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| AgentId | INT | NOT NULL | IDENTITY(1,1) | Agent ID (PK) |
| AgentCode | NVARCHAR(50) | NOT NULL | - | Agent 코드 |
| AgentName | NVARCHAR(100) | NOT NULL | - | Agent 이름 |
| Description | NVARCHAR(500) | NULL | - | 설명 |
| ServiceId | INT | NOT NULL | - | 기본 서비스 ID |
| SystemPrompt | NVARCHAR(MAX) | NULL | - | 시스템 프롬프트 |
| IconClass | NVARCHAR(100) | NULL | - | 아이콘 CSS 클래스 |
| ColorCode | NVARCHAR(20) | NULL | - | 색상 코드 (HEX) |
| Temperature | DECIMAL(3,2) | NULL | 0.7 | Temperature 설정 |
| MaxTokens | INT | NULL | 2000 | 최대 토큰 수 |
| IsPublic | BIT | NOT NULL | 1 | 공개 여부 |
| CreatedBy | INT | NOT NULL | - | 생성자 ID |
| IsActive | BIT | NOT NULL | 1 | 활성 여부 |
| SortOrder | INT | NOT NULL | 0 | 정렬 순서 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

**기본 Agent**:
1. 코드 리뷰 Agent
2. 문서 작성 Agent
3. 데이터 분석 Agent
4. 고객 지원 Agent
5. 번역 Agent

---

### 9. ChatConversations (채팅 대화)

채팅 세션(대화방)을 관리합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| ConversationId | INT | NOT NULL | IDENTITY(1,1) | 대화 ID (PK) |
| UserId | INT | NOT NULL | - | 사용자 ID |
| AgentId | INT | NULL | - | Agent ID (NULL이면 기본 모드) |
| ServiceId | INT | NOT NULL | - | 사용 서비스 ID |
| Title | NVARCHAR(200) | NULL | - | 대화 제목 |
| Model | NVARCHAR(100) | NULL | - | 사용 모델 |
| Temperature | DECIMAL(3,2) | NULL | - | Temperature 설정 |
| MaxTokens | INT | NULL | - | 최대 토큰 수 |
| MessageCount | INT | NOT NULL | 0 | 메시지 개수 |
| TotalTokens | INT | NOT NULL | 0 | 총 토큰 사용량 |
| TotalCost | DECIMAL(10,4) | NOT NULL | 0 | 총 비용 ($) |
| LastMessageAt | DATETIME2 | NULL | - | 마지막 메시지 시간 |
| IsArchived | BIT | NOT NULL | 0 | 보관 여부 |
| IsPinned | BIT | NOT NULL | 0 | 고정 여부 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

---

### 10. ChatMessages (채팅 메시지)

개별 채팅 메시지를 저장합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| MessageId | BIGINT | NOT NULL | IDENTITY(1,1) | 메시지 ID (PK) |
| ConversationId | INT | NOT NULL | - | 대화 ID |
| Role | NVARCHAR(20) | NOT NULL | - | 역할 (user/assistant/system) |
| Content | NVARCHAR(MAX) | NOT NULL | - | 메시지 내용 |
| TokensUsed | INT | NULL | - | 사용 토큰 수 |
| Model | NVARCHAR(100) | NULL | - | 사용 모델 |
| FinishReason | NVARCHAR(50) | NULL | - | 종료 이유 |
| Attachments | NVARCHAR(MAX) | NULL | - | 첨부파일 (JSON) |
| Metadata | NVARCHAR(MAX) | NULL | - | 메타데이터 (JSON) |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |

**제약조건**:
- CHECK: Role IN ('user', 'assistant', 'system')

---

### 11. ActivityLogs (활동 로그)

사용자 활동을 추적하고 감사합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| LogId | BIGINT | NOT NULL | IDENTITY(1,1) | 로그 ID (PK) |
| UserId | INT | NULL | - | 사용자 ID |
| ActivityType | NVARCHAR(50) | NOT NULL | - | 활동 유형 |
| EntityType | NVARCHAR(50) | NULL | - | 대상 엔티티 |
| EntityId | INT | NULL | - | 대상 엔티티 ID |
| Description | NVARCHAR(500) | NULL | - | 설명 |
| IpAddress | NVARCHAR(50) | NULL | - | IP 주소 |
| UserAgent | NVARCHAR(500) | NULL | - | User Agent |
| Details | NVARCHAR(MAX) | NULL | - | 상세 정보 (JSON) |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |

**활동 유형 예시**:
- Login/Logout
- Create/Update/Delete
- View/Export

---

### 12. SystemSettings (시스템 설정)

전역 시스템 설정값을 저장합니다.

| 컬럼명 | 데이터타입 | Null | 기본값 | 설명 |
|--------|-----------|------|--------|------|
| SettingId | INT | NOT NULL | IDENTITY(1,1) | 설정 ID (PK) |
| SettingKey | NVARCHAR(100) | NOT NULL | - | 설정 키 |
| SettingValue | NVARCHAR(MAX) | NULL | - | 설정 값 |
| DataType | NVARCHAR(20) | NOT NULL | 'String' | 데이터 타입 |
| Category | NVARCHAR(50) | NULL | - | 카테고리 |
| Description | NVARCHAR(500) | NULL | - | 설명 |
| IsEncrypted | BIT | NOT NULL | 0 | 암호화 여부 |
| CreatedAt | DATETIME2 | NOT NULL | GETDATE() | 생성 일시 |
| UpdatedAt | DATETIME2 | NOT NULL | GETDATE() | 수정 일시 |

---

## ERD

### Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│     Users       │────────<│   UserSessions   │         │      Roles      │
│─────────────────│         │──────────────────│         │─────────────────│
│ UserId (PK)     │         │ SessionId (PK)   │         │ RoleId (PK)     │
│ Email           │         │ UserId           │         │ RoleName        │
│ PasswordHash    │         │ SessionToken     │         │ DisplayName     │
│ FullName        │         │ LoginAt          │         └─────────────────┘
│ Status          │         └──────────────────┘                 │
└─────────────────┘                                              │
         │                                                       │
         └───────────<│   UserRoles      │>─────────────────────┘
                      │──────────────────│
                      │ UserRoleId (PK)  │
                      │ UserId           │
                      │ RoleId           │
                      └──────────────────┘


┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   ApiServices   │────────<│   ApiQuotas      │>────────│     Users       │
│─────────────────│         │──────────────────│         └─────────────────┘
│ ServiceId (PK)  │         │ QuotaId (PK)     │
│ ServiceCode     │         │ UserId           │
│ ServiceName     │         │ ServiceId        │
│ CostPerRequest  │         │ MonthlyLimit     │
└─────────────────┘         │ CurrentUsage     │
         │                  └──────────────────┘
         │                           │
         └───────────<│   ApiUsages      │
                      │──────────────────│
                      │ UsageId (PK)     │
                      │ UserId           │
                      │ ServiceId        │
                      │ RequestCost      │
                      └──────────────────┘


┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│     Agents      │────────<│ChatConversations │>────────│     Users       │
│─────────────────│         │──────────────────│         └─────────────────┘
│ AgentId (PK)    │         │ ConversationId   │
│ AgentCode       │         │ UserId           │
│ SystemPrompt    │         │ AgentId          │
└─────────────────┘         │ ServiceId        │
                            └──────────────────┘
                                     │
                            ┌──────────────────┐
                            │  ChatMessages    │
                            │──────────────────│
                            │ MessageId (PK)   │
                            │ ConversationId   │
                            │ Role             │
                            │ Content          │
                            └──────────────────┘
```

### 관계 요약

| 부모 테이블 | 자식 테이블 | 관계 | 설명 |
|------------|-----------|------|------|
| Users | UserSessions | 1:N | 한 사용자는 여러 세션 가질 수 있음 |
| Users | UserRoles | 1:N | 한 사용자는 여러 역할 가질 수 있음 |
| Roles | UserRoles | 1:N | 한 역할은 여러 사용자에게 할당됨 |
| Users | ApiQuotas | 1:N | 한 사용자는 여러 서비스 할당량 가짐 |
| ApiServices | ApiQuotas | 1:N | 한 서비스는 여러 사용자 할당량 가짐 |
| Users | ApiUsages | 1:N | 한 사용자는 여러 사용 내역 가짐 |
| Users | ChatConversations | 1:N | 한 사용자는 여러 대화 가짐 |
| ChatConversations | ChatMessages | 1:N | 한 대화는 여러 메시지 포함 |

**주의**: 물리적 FK는 없으며, 인덱스로만 관리됩니다.

---

## 인덱스 설계

### 인덱스 전략

1. **PK 인덱스**: 자동 생성 (Clustered Index)
2. **조회 성능**: 자주 조회되는 컬럼에 Non-Clustered Index
3. **조인 성능**: FK 역할 컬럼에 인덱스
4. **복합 인덱스**: WHERE + ORDER BY 조건에 맞춰 설계

### 주요 인덱스

```sql
-- Users
CREATE UNIQUE NONCLUSTERED INDEX IDX_Users_Email 
    ON Users(Email) WHERE IsDeleted = 0;

-- ApiQuotas
CREATE UNIQUE NONCLUSTERED INDEX IDX_ApiQuotas_Unique 
    ON ApiQuotas(UserId, ServiceId);

-- ApiUsages (대용량 예상)
CREATE NONCLUSTERED INDEX IDX_ApiUsages_UserId 
    ON ApiUsages(UserId, RequestTime DESC);

-- ChatMessages (대용량 예상)
CREATE NONCLUSTERED INDEX IDX_ChatMessages_ConversationId 
    ON ChatMessages(ConversationId, CreatedAt ASC);
```

---

## DDL 스크립트

### 데이터베이스 생성

```sql
-- 데이터베이스 생성
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'AIAgentManagement')
BEGIN
    CREATE DATABASE [AIAgentManagement]
    COLLATE SQL_Latin1_General_CP1_CI_AS;
END
GO

USE [AIAgentManagement];
GO
```

### 전체 테이블 생성 스크립트

전체 DDL 스크립트는 별도 파일로 제공됩니다.
- 파일명: `create_tables.sql`
- 포함 내용: 12개 테이블 생성 + 인덱스 + 제약조건

---

## 샘플 데이터

### 기본 데이터 삽입

```sql
-- 1. Roles (역할)
INSERT INTO Roles (RoleName, DisplayName, Description) VALUES
('Admin', '관리자', '시스템 전체 관리 권한'),
('Developer', '개발자', 'Agent 생성 및 관리 권한'),
('User', '일반 사용자', '기본 사용 권한');

-- 2. ApiServices (API 서비스)
INSERT INTO ApiServices (ServiceCode, ServiceName, ColorCode, CostPerRequest, SortOrder) VALUES
('chatgpt', 'ChatGPT', '#10A37F', 0.10, 1),
('claude', 'Claude', '#6366F1', 0.15, 2),
('cursor', 'Cursor', '#F59E0B', 0.15, 3),
('copilot', 'GitHub Copilot', '#000000', 0.10, 4);

-- 3. Users (사용자)
-- 비밀번호: password (bcrypt 해시)
INSERT INTO Users (Email, PasswordHash, FullName, Department, Status) VALUES
('admin@example.com', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '관리자', 'IT팀', 'Active'),
('developer@example.com', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '개발자', '개발팀', 'Active'),
('user@example.com', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '김사용자', '마케팅팀', 'Active');

-- 4. Agents (AI Agent)
INSERT INTO Agents (AgentCode, AgentName, Description, ServiceId, SystemPrompt, IconClass, ColorCode, CreatedBy, SortOrder) VALUES
('code-review', '코드 리뷰 Agent', '코드의 품질, 성능, 보안을 분석', 2, '당신은 전문 코드 리뷰어입니다...', 'bi-code-square', '#0EA5E9', 1, 1),
('document-writer', '문서 작성 Agent', '기술 문서, 보고서 작성', 1, '당신은 전문 기술 작가입니다...', 'bi-file-earmark-text', '#10B981', 1, 2),
('data-analyst', '데이터 분석 Agent', '데이터 분석 및 시각화', 2, '당신은 데이터 분석 전문가입니다...', 'bi-graph-up', '#F59E0B', 1, 3);
```

---

## 데이터베이스 관리

### 정기 유지보수

```sql
-- 1. 통계 업데이트 (매일)
UPDATE STATISTICS Users;
UPDATE STATISTICS ApiUsages;
UPDATE STATISTICS ChatMessages;

-- 2. 인덱스 재구성 (주간)
ALTER INDEX ALL ON Users REORGANIZE;
ALTER INDEX ALL ON ApiUsages REORGANIZE;

-- 3. 오래된 세션 삭제 (월간)
DELETE FROM UserSessions 
WHERE IsActive = 0 
  AND LogoutAt < DATEADD(DAY, -90, GETDATE());

-- 4. 백업 (일일)
BACKUP DATABASE AIAgentManagement 
TO DISK = 'C:\Backup\AIAgentManagement.bak';
```

---

## 부록

### A. 명명 규칙

- **테이블**: PascalCase (Users, ApiServices)
- **컬럼**: PascalCase (UserId, FullName)
- **인덱스**: IDX_TableName_ColumnName
- **제약조건**: 
  - PK: PK_TableName
  - CK: CK_TableName_ColumnName
  - DF: DF_TableName_ColumnName

### B. 확장성 고려사항

1. **대용량 테이블**
   - ApiUsages, ChatMessages, ActivityLogs
   - 월별 파티셔닝 적용 권장

2. **성능 최적화**
   - 자주 조회되는 컬럼에 INCLUDE 인덱스
   - 복합 인덱스 활용

3. **아카이빙**
   - 오래된 데이터 별도 테이블로 이동
   - 읽기 전용 파일그룹 사용

---

**문서 버전**: 1.0  
**최종 수정일**: 2024-12-26  
**작성자**: AI Agent 통합관리 시스템 개발팀
