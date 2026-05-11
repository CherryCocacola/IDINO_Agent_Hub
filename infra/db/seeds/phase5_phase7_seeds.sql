-- =====================================================================
-- IDINO Agent Hub — Phase 2.x + Phase 5.1 + Phase 7.1 시드 (멱등 가드)
-- =====================================================================
--
-- 목적: 운영 PG (AGENT_HUB.AIAgentManagement) 의 다음 시드를 idempotent 하게 codify.
--   * ApiServices 16개 (Phase 2 .. Phase 5.1 Nexus 포함)
--   * Agents 15개 (Phase 7.1, DU 4 + career 8 + 공통 3)
--
-- 적용 시점: `infra/db/init.sql` 로 schema/extension/role 셋업 + EF 마이그레이션
--             (`dotnet ef database update`) 으로 테이블 생성 후 본 파일 적용.
--
-- 적용 방법:
--   psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB \
--        -f infra/db/seeds/phase5_phase7_seeds.sql
--
-- 멱등 보장:
--   UNIQUE 제약이 PK(ServiceId/AgentId)만 존재하므로 ON CONFLICT 대신
--   `INSERT ... SELECT ... WHERE NOT EXISTS (...)` 패턴 사용.
--   재실행 시 ServiceCode / AgentCode 기준 0행 INSERT (운영 데이터 보존).
--
-- ApiKey codify 제외 사유:
--   * 운영 DB 의 `ApiKeys` 는 ApiKeyId=2 KeyName='test' 1행만 존재
--   * Phase 7.2 'docutil-master-key' / 'career-master-key' 는 운영 부재 (시연용 임시 발급 후 폐기 추정)
--   * KeyHash codify 는 보안 위험 + 운영 master 원칙 위반
--   * 신규 환경 발급은 `user_mig/tools/phase72_seed.py --print-keys` 사용
--
-- 출처: 2026-05-11 운영 DB read-only 추출 (`user_mig/_tmp_extract_seeds.py`,
--                                          `user_mig/_tmp_extract_all_services.py`)
--
-- 검증:
--   1) 빈 schema 시뮬레이션: 16 svc + 15 agent INSERT, 재실행 시 0 INSERT
--   2) 운영 DB 정합성: 15 Agent + 16 ApiServices 모든 컬럼 1:1 일치
-- =====================================================================

\set ON_ERROR_STOP on

-- =====================================================================
-- §1. ApiServices 16개 (Phase 2.x + Phase 5.1 Nexus)
-- =====================================================================
--
-- ServiceCode 별 멱등 가드. SortOrder 운영 값 보존.

-- ApiService: chatgpt  (운영 ServiceId=17, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'chatgpt', 'ChatGPT', 'OpenAI ChatGPT API', 'bi-chat-square-text', '#00c9ff', 'https://api.openai.com/v1', 'gpt-4o', '0.0300', TRUE, 1, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-03-09 01:07:58.069777+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt');

-- ApiService: claude  (운영 ServiceId=18, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'claude', 'Claude', 'Anthropic Claude API', 'bi-robot', '#667eea', 'https://api.anthropic.com/v1', 'claude-sonnet-4-6', '0.0300', TRUE, 2, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-03-09 01:07:58.069777+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'claude');

-- ApiService: cursor  (운영 ServiceId=19, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'cursor', 'Cursor', 'Cursor AI', 'bi-code-slash', '#f093fb', NULL, NULL, '0.0200', FALSE, 3, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-01-23 10:15:42.723333+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'cursor');

-- ApiService: copilot  (운영 ServiceId=20, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'copilot', 'Copilot', 'GitHub Copilot', 'bi-github', '#4b6cb7', NULL, 'gpt-4o', '0.0200', FALSE, 4, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-04-30 00:27:23.442221+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'copilot');

-- ApiService: gemini  (운영 ServiceId=21, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'gemini', 'Gemini', 'Google Gemini API', 'bi-google', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'gemini-2.5-flash', '0.0200', TRUE, 5, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-03-09 01:07:58.069777+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'gemini');

-- ApiService: mistral  (운영 ServiceId=22, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'mistral', 'Mistral', 'Mistral AI API', 'bi-stars', '#FF6B35', 'https://api.mistral.ai/v1', 'mistral-large-latest', '0.0200', FALSE, 6, 'Chat', '2026-01-23 10:15:42.723333+00:00', '2026-01-23 10:15:42.723333+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'mistral');

-- ApiService: dalle  (운영 ServiceId=23, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'dalle', 'DALL-E 3', 'OpenAI DALL-E 3 이미지 생성', 'bi-image', '#10a37f', 'https://api.openai.com/v1', 'dall-e-3', '0.0400', FALSE, 10, 'ImageGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'dalle');

-- ApiService: gemini-image  (운영 ServiceId=24, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'gemini-image', 'Gemini 3 Pro Image', 'Google Gemini 3 Pro Image 생성 (Nano banana Pro)', 'bi-image', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'gemini-3.0-pro-image', '0.0300', TRUE, 11, 'ImageGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'gemini-image');

-- ApiService: imagen4  (운영 ServiceId=25, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'imagen4', 'Imagen 4', 'Google Imagen 4 이미지 생성', 'bi-image', '#34a853', 'https://generativelanguage.googleapis.com/v1beta', 'imagen-4.0-generate-001', '0.0400', TRUE, 12, 'ImageGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'imagen4');

-- ApiService: gen4-image  (운영 ServiceId=26, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'gen4-image', 'Gen4 Image', 'Google Vertex AI Gen4 Image 생성', 'bi-image', '#ea4335', 'https://us-central1-aiplatform.googleapis.com/v1', 'imagegeneration@006', '0.0400', TRUE, 13, 'ImageGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'gen4-image');

-- ApiService: flux2  (운영 ServiceId=27, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'flux2', 'Flux 2', 'Stability AI Flux 2 이미지 생성', 'bi-image', '#6366f1', 'https://api.stability.ai/v2beta', 'flux-2', '0.0300', TRUE, 14, 'ImageGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'flux2');

-- ApiService: gen4-video  (운영 ServiceId=28, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'gen4-video', 'Gen4 Video', 'Google Vertex AI Gen4 영상 생성', 'bi-camera-video', '#ea4335', 'https://us-central1-aiplatform.googleapis.com/v1', 'videogeneration@006', '0.1000', FALSE, 20, 'VideoGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'gen4-video');

-- ApiService: veo  (운영 ServiceId=29, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'veo', 'Veo 3.1', 'Google Veo 3.1 영상 생성', 'bi-camera-video-fill', '#4285f4', 'https://generativelanguage.googleapis.com/v1beta', 'veo-3.1', '0.1200', FALSE, 21, 'VideoGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'veo');

-- ApiService: openai-video  (운영 ServiceId=30, IsActive=False)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'openai-video', 'OpenAI Video', 'OpenAI 비디오 생성 (Sora)', 'bi-camera-reels', '#10a37f', 'https://api.openai.com/v1', 'sora-2', '0.1500', FALSE, 22, 'VideoGeneration', '2026-01-23 10:15:42.740000+00:00', '2026-01-23 10:15:42.740000+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'openai-video');

-- ApiService: perplexity  (운영 ServiceId=31, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'perplexity', 'Perplexity', 'Perplexity AI (Sonar) — 웹 검색 기반', 'bi-search', '#20B2AA', 'https://api.perplexity.ai', 'sonar', '0.0200', TRUE, 7, 'Chat', '2026-04-30 00:27:22.905331+00:00', '2026-04-30 00:27:22.905352+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'perplexity');

-- ApiService: nexus  (운영 ServiceId=32, IsActive=True)
INSERT INTO "AIAgentManagement"."ApiServices" (
    "ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", "DefaultModel", "CostPerRequest", "IsActive", "SortOrder", "ServiceType", "CreatedAt", "UpdatedAt"
)
SELECT 'nexus', 'Project Nexus', '사내 LAN-only LLM 게이트웨이 (옵션 B 통합 — 세션/멀티테넌시 보존)', 'bi-hdd-network', '#10B981', 'http://192.168.22.28:8001/v1/chat', 'primary', '0.0000', TRUE, 8, 'Chat', '2026-05-08 11:41:26.549193+00:00', '2026-05-08 11:41:26.549221+00:00'
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'nexus');

-- =====================================================================
-- §2. Agents 15개 (Phase 7.1)
-- =====================================================================
--
-- ServiceId FK 는 ServiceCode lookup 서브쿼리 사용:
--   (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = '...')
--   → 신규 빈 DB 에서 ApiServices serial 시퀀스가 17/23/32 와 달라져도 정합성 유지.
-- AgentCode 멱등 가드.

-- Agent: agentic-search  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'agentic-search', 'DocUtil Agentic Search', 'DocUtil agentic_search 모듈 (DU-16) — factory 우회 P1 위반 정리용', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 다단계 에이전틱 검색 AI 입니다. 사용자의 복잡한 질문을 하위 질문으로 분해하고, 각 하위 질문에 대해 RAG 검색을 수행한 후 결과를 종합하여 한국어로 응답합니다. 각 단계의 추론 과정을 간결히 보여주며(Chain-of-Thought 요약), 최종 답변에는 사용된 문서 출처를 명시합니다. 검색 단계가 5회를 초과할 경우 자체 종료하고 부분 답변을 반환합니다.', 'bi-robot', '#6366f1', '0.40', 4096, 'gpt-4o-mini', FALSE, 1, TRUE, 100, TRUE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user"]', NULL, 'DocUtil', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'agentic-search');

-- Agent: career-action-recommender  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-action-recommender', 'career 액션 추천기', 'ai-service /ai/actions/{id} (CA-3) — 단일 액션 상세 추천', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 진로 액션 상세 추천 AI 입니다. 지정된 액션 ID에 대해 학생 맞춤형 실행 가이드(예상 소요 시간, 사전 요구 사항, 단계별 체크리스트, 성공 지표)를 한국어로 작성합니다. 현실적이고 구체적이어야 하며, 추상적인 동기 부여 문구만으로 채우지 않습니다.', 'bi-robot', '#6366f1', '0.50', 2048, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student","career-coaching"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-action-recommender');

-- Agent: career-actionboard-orchestrator  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-actionboard-orchestrator', 'career ActionBoard 추천 오케스트레이터', 'ai-service Tool Calling + Structured Outputs strict 진입점 (CA-7, CA-8, CA-19)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 학생 진로 ActionBoard 추천 오케스트레이터입니다. 입력으로 학생 프로필/현재 학기/목표 직무 데이터를 받아, get_student_profile / get_competency_scores / search_alumni_patterns / check_constraints 4개 도구를 적절히 호출하여 데이터를 수집한 후, 학생에게 추천할 액션 리스트(JSON_SCHEMA_ACTIONBOARD strict) 를 생성합니다. 학사 위험(check_constraints) 이 발견되면 위험 완화 액션을 우선합니다. 응답은 반드시 사전 정의된 JSON 스키마에 정확히 맞춥니다 — 자유 텍스트 금지.', 'bi-robot', '#6366f1', '0.30', 4096, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student","career-coaching"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-actionboard-orchestrator');

-- Agent: career-chatbot  (ServiceCode=nexus)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-chatbot', 'career 코칭 챗봇', 'coaching-service / ai-service /ai/chat (CA-5, CA-17). PII 위험 — Internal Nexus 강제', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'nexus'), '당신은 학생 진로 코칭 챗봇입니다. 학생의 진로 고민/감정/심리적 어려움을 경청하고 공감하는 어조로 한국어로 응답합니다. 다만 의료/법률/정신과적 진단을 내리지 않으며, 위기 신호(자해/극단적 불안)가 감지되면 즉시 학생 상담 센터 연결을 권유합니다. 학생의 이름·학번·연락처는 응답에 다시 표기하지 않습니다(개인정보 보호). 본 Agent 는 사내 LAN-only Nexus 로 라우팅되어 외부 LLM 으로 데이터가 유출되지 않습니다.', 'bi-robot', '#6366f1', '0.70', 4096, 'primary', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Block', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-coaching"]', NULL, 'AgentHub', 'Internal', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-chatbot');

-- Agent: career-competency-analyzer  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-competency-analyzer', 'career 역량 분석기', 'competency-service / ai-service /ai/analyze (CA-4, CA-18)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 학생 역량 분석 전문 AI 입니다. 주어진 학생 데이터(성적, 활동 이력, 자격증, 프로젝트)와 역량 점수, 목표 직무를 분석하여 1) 강점 2) 약점 3) 격차 분석 4) 개선 제안 의 4단 구조 한국어 분석 결과를 작성합니다. 정량 점수는 1~5 척도로 일관되게 표기합니다. 학생의 성장 가능성을 긍정적으로 격려하되 사실에 기반합니다.', 'bi-robot', '#6366f1', '0.40', 4096, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student","career-coaching"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-competency-analyzer');

-- Agent: career-rag-actionboard  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-rag-actionboard', 'career RAG ActionBoard 추천기', 'ai-service /ai/recommendations/rag (CA-9, CA-10) — 동문 RAG 컨텍스트 prepend', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 동문 진로 사례 RAG 컨텍스트를 활용하는 ActionBoard 추천기입니다. 주어진 동문 패턴/유사 학생 사례를 근거로 현재 학생에게 가장 효과적인 액션을 JSON_SCHEMA_ACTIONBOARD strict 로 응답합니다. RAG 결과가 비어 있으면 일반 추천으로 폴백하되, ''rag_used'': false 플래그를 응답에 포함합니다. 학생의 개인 정보(이름/학번/연락처)는 절대 응답 본문에 노출하지 않습니다.', 'bi-robot', '#6366f1', '0.30', 4096, 'gpt-4o-mini', FALSE, 1, TRUE, 100, TRUE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student","career-coaching"]', NULL, 'DocUtil', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-rag-actionboard');

-- Agent: career-semester-planner  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-semester-planner', 'career 학기 목표 플래너', 'ai-service /ai/sprint/{id} (CA-6) — 학기 단위 목표/스프린트 생성', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 학기 단위 진로 학습 목표 플래너입니다. 현재 학기/잔여 주차/학생 목표 직무를 입력받아 SMART 원칙에 따른 한 학기 목표 3~5개와 주차별 마일스톤을 한국어로 생성합니다. 각 목표에는 측정 가능한 산출물(포트폴리오/프로젝트/자격증 등)을 포함하며, 학사 일정과 충돌이 없는지 확인합니다.', 'bi-robot', '#6366f1', '0.40', 4096, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-semester-planner');

-- Agent: career-simulation-analyzer  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-simulation-analyzer', 'career 시뮬레이션 분석기', 'simulation-service _generate_ai_analysis (CA-13) — 선택 결과 분석', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 학생이 선택한 진로 시뮬레이션 결과 분석 AI 입니다. 선택된 시나리오와 학생의 현재 데이터를 비교하여 1) 성공 가능성 (0~100%) 2) 주요 위험 요소 3) 보완 액션 의 3단 분석을 한국어로 제공합니다. 수치는 학생의 정량 데이터에 근거하여 산출하며, 근거가 부족하면 신뢰도(낮음/중간/높음)를 함께 표기합니다.', 'bi-robot', '#6366f1', '0.70', 1500, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-simulation-analyzer');

-- Agent: career-simulation-suggester  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'career-simulation-suggester', 'career 시뮬레이션 추천기', 'simulation-service _generate_ai_suggestions (CA-12) — 4개 시나리오 추천', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 학생 진로 시뮬레이션 시나리오 생성 AI 입니다. 학생 현재 상태(전공/학년/관심분야) 기준으로 진로 가설 시나리오 4개를 한국어 JSON 배열로 추천합니다. 각 시나리오는 {"title":..., "summary":..., "required_actions":[...], "expected_outcome":...} 구조이며, 다양성을 위해 안전한 선택 1개 + 도전적 선택 2개 + 비전형 선택 1개를 균형 있게 포함합니다.', 'bi-robot', '#6366f1', '0.70', 2000, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["career-student"]', NULL, 'AgentHub', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'career-simulation-suggester');

-- Agent: docutil-evaluator  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'docutil-evaluator', 'DocUtil RAGAS 평가기', 'RAG 응답 품질 평가용 LLM-as-judge Agent (DU-13). 정확도 우선 — External 강제', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 RAG 시스템의 응답 품질을 평가하는 심사 AI 입니다. RAGAS 지표(faithfulness, answer_relevancy, context_precision, context_recall)에 따라 0~1 사이의 점수와 그 근거를 한국어로 제시합니다. JSON 형식으로 {"faithfulness":0~1, "relevancy":0~1, "precision":0~1, "recall":0~1, "reasoning":"..."} 만 출력하며 추가 설명을 붙이지 않습니다. 주관적 호감이 아닌 검증 가능한 사실 일치 여부만 판단합니다.', 'bi-robot', '#6366f1', '0.00', 2048, 'gpt-4o', FALSE, 1, TRUE, 100, FALSE, FALSE, 'Block', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user"]', NULL, 'AgentHub', 'External', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'docutil-evaluator');

-- Agent: docutil-image-generator  (ServiceCode=dalle)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'docutil-image-generator', 'DocUtil 이미지 생성기', 'DocUtil 보고서/문서 자동 이미지 채움용 Agent (DU-14, DU-19, DU-20)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'dalle'), '당신은 한국어 보고서/문서에 들어갈 일러스트와 인포그래픽을 생성하는 이미지 AI 입니다. 요청된 주제를 적절한 비유와 색감으로 시각화하며, 텍스트는 가급적 포함하지 않습니다(언어 의존성 회피). 회사 로고, 실존 인물, 폭력적/선정적 요소는 생성하지 않습니다. 1024x1024 기본 해상도로 1장 생성합니다.', 'bi-robot', '#6366f1', '0.70', NULL, 'dall-e-3', FALSE, 1, TRUE, 100, FALSE, FALSE, 'Block', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user"]', NULL, 'AgentHub', 'External', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'docutil-image-generator');

-- Agent: docutil-rag-chat  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'docutil-rag-chat', 'DocUtil RAG 챗봇', 'DocUtil 사용자 챗봇의 RAG 검색-증강 응답 Agent (DU-7, DU-8 통합)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 사내 문서 검색-증강(RAG) 챗봇입니다. 사용자의 질문에 대해 제공된 문서 컨텍스트만을 근거로 정확한 답변을 합니다. 출처가 없는 추측이나 일반 지식으로 답변하지 마세요. 답변은 한국어로 친절하고 명확하게 작성하며, 근거가 된 문서/문단을 인용 표기하세요. 문서에서 답을 찾을 수 없으면 솔직히 모른다고 답합니다. 기밀 문서가 노출될 수 있는 질문이라면 사용자의 권한 범위를 우선 확인하세요.', 'bi-robot', '#6366f1', '0.50', 4096, 'gpt-4o', FALSE, 1, TRUE, 100, TRUE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user"]', NULL, 'DocUtil', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'docutil-rag-chat');

-- Agent: docutil-report-generator  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'docutil-report-generator', 'DocUtil 보고서 생성기', 'DocUtil documents_v2 Mode A 보고서 생성 Agent (DU-9)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 사내 보고서 작성 전문 AI 입니다. 사용자가 제공한 자료/메모/회의록을 바탕으로 구조적이고 일관된 한국어 보고서를 생성합니다. 응답은 1) 개요 2) 본문(섹션별 헤더) 3) 결론 4) 참고/출처 의 4단 구성을 기본으로 하며, 마크다운 헤더(##, ###)를 사용합니다. 사실 관계가 불분명한 부분은 추측하지 말고 ''확인 필요'' 로 표기합니다. 회사명/사람 이름은 입력에 명시된 표기를 그대로 따릅니다.', 'bi-robot', '#6366f1', '0.40', 8192, 'gpt-4o', FALSE, 1, TRUE, 100, TRUE, TRUE, 'Mask', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user"]', NULL, 'DocUtil', 'Hybrid', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'docutil-report-generator');

-- Agent: embedding-default  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'embedding-default', '기본 임베딩', '모든 시스템의 임베딩 위임 (DU-18, CA-14~16). 1536D 표준 (ADR-10)', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '(임베딩 전용 Agent — system prompt 미사용)', 'bi-robot', '#6366f1', '0.00', NULL, 'text-embedding-3-small', FALSE, 1, TRUE, 100, FALSE, FALSE, 'Block', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user","career-student","career-coaching"]', NULL, 'AgentHub', 'External', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'embedding-default');

-- Agent: web-search-default  (ServiceCode=chatgpt)
INSERT INTO "AIAgentManagement"."Agents" (
    "AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", "IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", "IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", "PiiProtectionEnabled", "PiiProtectionMode", "WelcomeMessage", "PlaceholderText", "ChatTheme", "AllowGuestChat", "AllowedEmbedDomains", "CreatedAt", "UpdatedAt", "ConsumerSystems", "KnowledgeBaseRef", "KnowledgeBaseSource", "LlmRouting", "RoutingPolicyJson"
)
SELECT 'web-search-default', '기본 웹 검색', 'Tavily 검색 위임 Agent (AH-14). EnableWebSearch=true 로 동작', (SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'chatgpt'), '당신은 웹 검색 결과를 한국어로 요약하는 AI 입니다. 사용자의 질문에 대해 Tavily 검색으로 수집된 최신 결과를 바탕으로 객관적으로 요약하며, 출처(URL)를 함께 표기합니다. 검색 결과가 모순되면 양측 입장을 모두 제시하고, 단정적 주장은 피합니다. 광고/홍보성 콘텐츠는 사실과 분리하여 표기합니다.', 'bi-robot', '#6366f1', '0.30', 2048, 'gpt-4o-mini', FALSE, 1, TRUE, 100, FALSE, FALSE, 'Block', NULL, NULL, 'light', FALSE, NULL, '2026-05-08 11:41:27.260778+00:00', '2026-05-08 11:41:27.260778+00:00', '["docutil-user","career-student"]', NULL, 'AgentHub', 'External', NULL
WHERE NOT EXISTS (SELECT 1 FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = 'web-search-default');

-- =====================================================================
-- §3. 검증 쿼리 (실행 후 결과)
-- =====================================================================
--
-- 기대값:
--   * api_services_seed   = 16
--   * agents_seed_15      = 15
--   * nexus_present       = 1

SELECT 'api_services_seed' AS what, COUNT(*) AS n
FROM "AIAgentManagement"."ApiServices"
WHERE "ServiceCode" IN (
    'chatgpt', 'claude', 'cursor', 'copilot', 'gemini', 'mistral', 'dalle', 'gemini-image', 'imagen4', 'gen4-image', 'flux2', 'gen4-video', 'veo', 'openai-video', 'perplexity', 'nexus'
)
UNION ALL
SELECT 'nexus_present', COUNT(*)
FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = 'nexus'
UNION ALL
SELECT 'agents_seed_15', COUNT(*)
FROM "AIAgentManagement"."Agents"
WHERE "AgentCode" IN (
    'agentic-search', 'career-action-recommender', 'career-actionboard-orchestrator', 'career-chatbot', 'career-competency-analyzer', 'career-rag-actionboard', 'career-semester-planner', 'career-simulation-analyzer', 'career-simulation-suggester', 'docutil-evaluator', 'docutil-image-generator', 'docutil-rag-chat', 'docutil-report-generator', 'embedding-default', 'web-search-default'
);
