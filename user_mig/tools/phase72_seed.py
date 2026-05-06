"""
Phase 7.2 — 운영 PG 시드 + ApiKey 발급 스크립트
====================================================

목적:
  Phase 7.1 코드(`agenthub/Data/DatabaseInitializer.cs`)에 등록된 15개 Agent 카탈로그가
  현재 운영 PG(192.168.10.39:5440 / AGENT_HUB DB) 에 *미적용* 상태이므로 본 스크립트가
  멱등적으로 적용한다. 동시에 Phase 7.2 의 핵심 산출물인 시연용 master ApiKey 2개
  (docutil-master-key, career-master-key)를 발급한다.

DatabaseInitializer.SeedAsync 의 절차를 그대로 모방:
  1) Roles 3개 (Admin / Developer / User) — 멱등
  2) admin@example.com / Admin123! / BCrypt 11 라운드 — 멱등
  3) ApiServices 핵심 3개 (chatgpt / dalle / nexus) — 멱등
  4) Agents 15개 (AI_INVENTORY §6) — AgentCode 멱등 가드
  5) ApiKeys 2개 — KeyName 멱등 가드 (이미 존재하면 발급된 평문 출력 불가 — 경고)

암호화 정책 (AgentHub ApiKeyService 와 정확히 일치해야 함, Phase 3.3c):
  - AES key = SHA-256(JwtSettings:SecretKey) (Encryption:ApiKeyAesKey 미설정 폴백)
  - AES-GCM 12바이트 random IV + 16바이트 Tag (분리 저장)
  - EncryptedKey = base64(ciphertext)
  - KeyHash = SHA-256(plaintext) HEX 대문자 64자
  - Scopes = "chat,stream,info,usage" 전체 권한 (시연용)
  - AgentId = NULL (모든 Agent 호출 가능)

운영 보안 주의:
  - 본 스크립트는 *시연용 monorepo COPY 환경* 에서만 실행한다.
  - 출력된 평문 ApiKey 는 .env 파일에만 저장하고 git 커밋 금지.
  - 운영 환경에서는 AgentHub UI 의 정식 API Key 발급 절차 사용.

사용법:
  python user_mig/tools/phase72_seed.py [--dry-run] [--print-keys]
  --dry-run:   변경하지 않고 어떤 작업이 일어날지 출력
  --print-keys: 발급된 ApiKey 평문을 stdout 으로 출력 (.env 적용용)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any

import asyncpg
import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── 설정 ───────────────────────────────────────────────────────────────────
DSN = "postgresql://AGENT_HUB:idino%21%40%23%24@192.168.10.39:5440/AGENT_HUB"

# AgentHub appsettings.Development.json 의 JwtSettings:SecretKey 와 동일해야 한다.
# Encryption:ApiKeyAesKey 가 비어 있어 JWT key 폴백 분기를 사용 (ApiKeyService.LoadAesKey).
JWT_SECRET_KEY = "YourSuperSecretKeyForJWTTokenGenerationThatShouldBeAtLeast32CharactersLong!"

# 시연용 master 키 정의 — 두 개를 발급
MASTER_KEYS = [
    {
        "key_name": "docutil-master-key",
        "service_code": "agent-api",  # ApiKeyService.GenerateAgentApiKeyAsync 와 동일
        "agent_id": None,             # 모든 Agent 호출 허용
        "description": "DocUtil 시스템용 시연 master API Key (Phase 7.2). 모든 docutil-* Agent 호출 가능",
        "scopes": "chat,stream,info,usage",
        "consumer_system": "docutil-user",
    },
    {
        "key_name": "career-master-key",
        "service_code": "agent-api",
        "agent_id": None,
        "description": "career 시스템용 시연 master API Key (Phase 7.2). 모든 career-* Agent 호출 가능",
        "scopes": "chat,stream,info,usage",
        "consumer_system": "career-coaching",
    },
]

# ── Phase 7.1 시드 카탈로그 (DatabaseInitializer.cs SEED_AGENTS 와 1:1 일치) ──
# 각 row: (agent_code, agent_name, description, service_code, default_model,
#         temperature, max_tokens(0=NULL), system_prompt, enable_rag,
#         pii_enabled, pii_mode, llm_routing, consumer_systems_json)
AGENT_SEEDS: list[tuple[str, str, str, str, str, float, int, str, bool, bool, str, str, str]] = [
    # DocUtil 4개
    (
        "docutil-rag-chat",
        "DocUtil RAG 챗봇",
        "DocUtil 사용자 챗봇의 RAG 검색-증강 응답 Agent (DU-7, DU-8 통합)",
        "chatgpt", "gpt-4o", 0.5, 4096,
        "당신은 사내 문서 검색-증강(RAG) 챗봇입니다. 사용자의 질문에 대해 제공된 문서 컨텍스트만을 근거로 정확한 답변을 합니다. "
        "출처가 없는 추측이나 일반 지식으로 답변하지 마세요. 답변은 한국어로 친절하고 명확하게 작성하며, "
        "근거가 된 문서/문단을 인용 표기하세요. 문서에서 답을 찾을 수 없으면 솔직히 모른다고 답합니다. "
        "기밀 문서가 노출될 수 있는 질문이라면 사용자의 권한 범위를 우선 확인하세요.",
        True, True, "Mask", "Hybrid",
        '["docutil-user"]',
    ),
    (
        "docutil-report-generator",
        "DocUtil 보고서 생성기",
        "DocUtil documents_v2 Mode A 보고서 생성 Agent (DU-9)",
        "chatgpt", "gpt-4o", 0.4, 8192,
        "당신은 사내 보고서 작성 전문 AI 입니다. 사용자가 제공한 자료/메모/회의록을 바탕으로 구조적이고 일관된 한국어 보고서를 생성합니다. "
        "응답은 1) 개요 2) 본문(섹션별 헤더) 3) 결론 4) 참고/출처 의 4단 구성을 기본으로 하며, 마크다운 헤더(##, ###)를 사용합니다. "
        "사실 관계가 불분명한 부분은 추측하지 말고 '확인 필요' 로 표기합니다. 회사명/사람 이름은 입력에 명시된 표기를 그대로 따릅니다.",
        True, True, "Mask", "Hybrid",
        '["docutil-user"]',
    ),
    (
        "docutil-evaluator",
        "DocUtil RAGAS 평가기",
        "RAG 응답 품질 평가용 LLM-as-judge Agent (DU-13). 정확도 우선 — External 강제",
        "chatgpt", "gpt-4o", 0.0, 2048,
        "당신은 RAG 시스템의 응답 품질을 평가하는 심사 AI 입니다. "
        "RAGAS 지표(faithfulness, answer_relevancy, context_precision, context_recall)에 따라 0~1 사이의 점수와 그 근거를 한국어로 제시합니다. "
        'JSON 형식으로 {"faithfulness":0~1, "relevancy":0~1, "precision":0~1, "recall":0~1, "reasoning":"..."} 만 출력하며 추가 설명을 붙이지 않습니다. '
        "주관적 호감이 아닌 검증 가능한 사실 일치 여부만 판단합니다.",
        False, False, "Block", "External",
        '["docutil-user"]',
    ),
    (
        "docutil-image-generator",
        "DocUtil 이미지 생성기",
        "DocUtil 보고서/문서 자동 이미지 채움용 Agent (DU-14, DU-19, DU-20)",
        "dalle", "dall-e-3", 0.7, 0,
        "당신은 한국어 보고서/문서에 들어갈 일러스트와 인포그래픽을 생성하는 이미지 AI 입니다. "
        "요청된 주제를 적절한 비유와 색감으로 시각화하며, 텍스트는 가급적 포함하지 않습니다(언어 의존성 회피). "
        "회사 로고, 실존 인물, 폭력적/선정적 요소는 생성하지 않습니다. 1024x1024 기본 해상도로 1장 생성합니다.",
        False, False, "Block", "External",
        '["docutil-user"]',
    ),
    # career 8개
    (
        "career-actionboard-orchestrator",
        "career ActionBoard 추천 오케스트레이터",
        "ai-service Tool Calling + Structured Outputs strict 진입점 (CA-7, CA-8, CA-19)",
        "chatgpt", "gpt-4o-mini", 0.3, 4096,
        "당신은 학생 진로 ActionBoard 추천 오케스트레이터입니다. "
        "입력으로 학생 프로필/현재 학기/목표 직무 데이터를 받아, get_student_profile / get_competency_scores / search_alumni_patterns / check_constraints "
        "4개 도구를 적절히 호출하여 데이터를 수집한 후, 학생에게 추천할 액션 리스트(JSON_SCHEMA_ACTIONBOARD strict) 를 생성합니다. "
        "학사 위험(check_constraints) 이 발견되면 위험 완화 액션을 우선합니다. 응답은 반드시 사전 정의된 JSON 스키마에 정확히 맞춥니다 — 자유 텍스트 금지.",
        False, True, "Mask", "Hybrid",
        '["career-student","career-coaching"]',
    ),
    (
        "career-rag-actionboard",
        "career RAG ActionBoard 추천기",
        "ai-service /ai/recommendations/rag (CA-9, CA-10) — 동문 RAG 컨텍스트 prepend",
        "chatgpt", "gpt-4o-mini", 0.3, 4096,
        "당신은 동문 진로 사례 RAG 컨텍스트를 활용하는 ActionBoard 추천기입니다. "
        "주어진 동문 패턴/유사 학생 사례를 근거로 현재 학생에게 가장 효과적인 액션을 JSON_SCHEMA_ACTIONBOARD strict 로 응답합니다. "
        "RAG 결과가 비어 있으면 일반 추천으로 폴백하되, 'rag_used': false 플래그를 응답에 포함합니다. "
        "학생의 개인 정보(이름/학번/연락처)는 절대 응답 본문에 노출하지 않습니다.",
        True, True, "Mask", "Hybrid",
        '["career-student","career-coaching"]',
    ),
    (
        "career-competency-analyzer",
        "career 역량 분석기",
        "competency-service / ai-service /ai/analyze (CA-4, CA-18)",
        "chatgpt", "gpt-4o-mini", 0.4, 4096,
        "당신은 학생 역량 분석 전문 AI 입니다. "
        "주어진 학생 데이터(성적, 활동 이력, 자격증, 프로젝트)와 역량 점수, 목표 직무를 분석하여 "
        "1) 강점 2) 약점 3) 격차 분석 4) 개선 제안 의 4단 구조 한국어 분석 결과를 작성합니다. "
        "정량 점수는 1~5 척도로 일관되게 표기합니다. 학생의 성장 가능성을 긍정적으로 격려하되 사실에 기반합니다.",
        False, True, "Mask", "Hybrid",
        '["career-student","career-coaching"]',
    ),
    (
        "career-action-recommender",
        "career 액션 추천기",
        "ai-service /ai/actions/{id} (CA-3) — 단일 액션 상세 추천",
        "chatgpt", "gpt-4o-mini", 0.5, 2048,
        "당신은 진로 액션 상세 추천 AI 입니다. "
        "지정된 액션 ID에 대해 학생 맞춤형 실행 가이드(예상 소요 시간, 사전 요구 사항, 단계별 체크리스트, 성공 지표)를 한국어로 작성합니다. "
        "현실적이고 구체적이어야 하며, 추상적인 동기 부여 문구만으로 채우지 않습니다.",
        False, True, "Mask", "Hybrid",
        '["career-student","career-coaching"]',
    ),
    (
        "career-chatbot",
        "career 코칭 챗봇",
        "coaching-service / ai-service /ai/chat (CA-5, CA-17). PII 위험 — Internal Nexus 강제",
        "nexus", "primary", 0.7, 4096,
        "당신은 학생 진로 코칭 챗봇입니다. "
        "학생의 진로 고민/감정/심리적 어려움을 경청하고 공감하는 어조로 한국어로 응답합니다. "
        "다만 의료/법률/정신과적 진단을 내리지 않으며, 위기 신호(자해/극단적 불안)가 감지되면 즉시 학생 상담 센터 연결을 권유합니다. "
        "학생의 이름·학번·연락처는 응답에 다시 표기하지 않습니다(개인정보 보호). "
        "본 Agent 는 사내 LAN-only Nexus 로 라우팅되어 외부 LLM 으로 데이터가 유출되지 않습니다.",
        False, True, "Block", "Internal",
        '["career-coaching"]',
    ),
    (
        "career-semester-planner",
        "career 학기 목표 플래너",
        "ai-service /ai/sprint/{id} (CA-6) — 학기 단위 목표/스프린트 생성",
        "chatgpt", "gpt-4o-mini", 0.4, 4096,
        "당신은 학기 단위 진로 학습 목표 플래너입니다. "
        "현재 학기/잔여 주차/학생 목표 직무를 입력받아 SMART 원칙에 따른 한 학기 목표 3~5개와 주차별 마일스톤을 한국어로 생성합니다. "
        "각 목표에는 측정 가능한 산출물(포트폴리오/프로젝트/자격증 등)을 포함하며, 학사 일정과 충돌이 없는지 확인합니다.",
        False, True, "Mask", "Hybrid",
        '["career-student"]',
    ),
    (
        "career-simulation-suggester",
        "career 시뮬레이션 추천기",
        "simulation-service _generate_ai_suggestions (CA-12) — 4개 시나리오 추천",
        "chatgpt", "gpt-4o-mini", 0.7, 2000,
        "당신은 학생 진로 시뮬레이션 시나리오 생성 AI 입니다. "
        "학생 현재 상태(전공/학년/관심분야) 기준으로 진로 가설 시나리오 4개를 한국어 JSON 배열로 추천합니다. "
        '각 시나리오는 {"title":..., "summary":..., "required_actions":[...], "expected_outcome":...} 구조이며, '
        "다양성을 위해 안전한 선택 1개 + 도전적 선택 2개 + 비전형 선택 1개를 균형 있게 포함합니다.",
        False, True, "Mask", "Hybrid",
        '["career-student"]',
    ),
    (
        "career-simulation-analyzer",
        "career 시뮬레이션 분석기",
        "simulation-service _generate_ai_analysis (CA-13) — 선택 결과 분석",
        "chatgpt", "gpt-4o-mini", 0.7, 1500,
        "당신은 학생이 선택한 진로 시뮬레이션 결과 분석 AI 입니다. "
        "선택된 시나리오와 학생의 현재 데이터를 비교하여 1) 성공 가능성 (0~100%) 2) 주요 위험 요소 3) 보완 액션 의 3단 분석을 한국어로 제공합니다. "
        "수치는 학생의 정량 데이터에 근거하여 산출하며, 근거가 부족하면 신뢰도(낮음/중간/높음)를 함께 표기합니다.",
        False, True, "Mask", "Hybrid",
        '["career-student"]',
    ),
    # 공통 3개
    (
        "embedding-default",
        "기본 임베딩",
        "모든 시스템의 임베딩 위임 (DU-18, CA-14~16). 1536D 표준 (ADR-10)",
        "chatgpt", "text-embedding-3-small", 0.0, 0,
        "(임베딩 전용 Agent — system prompt 미사용)",
        False, False, "Block", "External",
        '["docutil-user","career-student","career-coaching"]',
    ),
    (
        "web-search-default",
        "기본 웹 검색",
        "Tavily 검색 위임 Agent (AH-14). EnableWebSearch=true 로 동작",
        "chatgpt", "gpt-4o-mini", 0.3, 2048,
        "당신은 웹 검색 결과를 한국어로 요약하는 AI 입니다. "
        "사용자의 질문에 대해 Tavily 검색으로 수집된 최신 결과를 바탕으로 객관적으로 요약하며, 출처(URL)를 함께 표기합니다. "
        "검색 결과가 모순되면 양측 입장을 모두 제시하고, 단정적 주장은 피합니다. "
        "광고/홍보성 콘텐츠는 사실과 분리하여 표기합니다.",
        False, False, "Block", "External",
        '["docutil-user","career-student"]',
    ),
    (
        "agentic-search",
        "DocUtil Agentic Search",
        "DocUtil agentic_search 모듈 (DU-16) — factory 우회 P1 위반 정리용",
        "chatgpt", "gpt-4o-mini", 0.4, 4096,
        "당신은 다단계 에이전틱 검색 AI 입니다. "
        "사용자의 복잡한 질문을 하위 질문으로 분해하고, 각 하위 질문에 대해 RAG 검색을 수행한 후 결과를 종합하여 한국어로 응답합니다. "
        "각 단계의 추론 과정을 간결히 보여주며(Chain-of-Thought 요약), 최종 답변에는 사용된 문서 출처를 명시합니다. "
        "검색 단계가 5회를 초과할 경우 자체 종료하고 부분 답변을 반환합니다.",
        True, True, "Mask", "Hybrid",
        '["docutil-user"]',
    ),
]


# ── 유틸 ───────────────────────────────────────────────────────────────────

def _aes_key() -> bytes:
    """AgentHub ApiKeyService.LoadAesKey 의 폴백 분기와 동일하게 SHA-256(JWT_SECRET) 32바이트."""
    return hashlib.sha256(JWT_SECRET_KEY.encode("utf-8")).digest()


def encrypt_apikey(plaintext: str) -> tuple[bytes, bytes, bytes]:
    """
    AES-GCM 으로 평문을 암호화한다. ApiKeyService.EncryptApiKey 와 1:1 일치.
    반환: (ciphertext, iv 12바이트, tag 16바이트)

    cryptography 라이브러리의 AESGCM.encrypt 는 ciphertext+tag 를 합쳐 반환하므로
    마지막 16바이트(=tag)를 분리한다.
    """
    iv = os.urandom(12)
    aes = AESGCM(_aes_key())
    ct_with_tag = aes.encrypt(iv, plaintext.encode("utf-8"), None)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return ciphertext, iv, tag


def compute_keyhash(plaintext: str) -> str:
    """ApiKeyService.ComputeKeyHash — SHA-256(평문) HEX 대문자 64자."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest().upper()


def generate_random_apikey() -> str:
    """
    ApiKeyService.GenerateRandomAgentApiKey — `ak-{base64url 32바이트, padding 제거}`.
    secrets.token_urlsafe 는 길이 인자 = 바이트 수이므로 32 → 약 43자 base64url.
    """
    raw = secrets.token_bytes(32)
    b64 = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"ak-{b64}"


# ── 시드 작업 ───────────────────────────────────────────────────────────────

async def ensure_roles(conn: asyncpg.Connection, dry: bool) -> None:
    print("\n[1] Roles 시드")
    rows = await conn.fetch('SELECT "RoleName" FROM "AIAgentManagement"."Roles"')
    existing = {r["RoleName"] for r in rows}
    seeds = [
        ("Admin", "관리자", "시스템 전체 관리 권한"),
        ("Developer", "개발자", "Agent 생성 및 수정 권한"),
        ("User", "사용자", "기본 사용 권한"),
    ]
    for name, display, desc in seeds:
        if name in existing:
            print(f"    [skip] Role 존재: {name}")
            continue
        if dry:
            print(f"    [dry] INSERT Role: {name}")
            continue
        now = datetime.now(timezone.utc)
        await conn.execute(
            'INSERT INTO "AIAgentManagement"."Roles" '
            '("RoleName", "DisplayName", "Description", "IsActive", "CreatedAt", "UpdatedAt") '
            "VALUES ($1, $2, $3, TRUE, $4, $4)",
            name, display, desc, now,
        )
        print(f"    [insert] Role: {name}")


async def ensure_admin(conn: asyncpg.Connection, dry: bool) -> int | None:
    """admin@example.com 을 보장하고 UserId 를 반환한다."""
    print("\n[2] Admin 사용자 시드 (admin@example.com / Admin123!)")
    row = await conn.fetchrow(
        'SELECT "UserId" FROM "AIAgentManagement"."Users" WHERE "Email" = $1',
        "admin@example.com",
    )
    if row:
        print(f"    [skip] admin 존재: UserId={row['UserId']}")
        admin_id = row["UserId"]
    else:
        if dry:
            print("    [dry] INSERT admin 사용자 + UserRole")
            return None
        # BCrypt 11 라운드 — DatabaseInitializer 와 동일 ($2b$11$...)
        password_hash = bcrypt.hashpw(b"Admin123!", bcrypt.gensalt(rounds=11)).decode("ascii")
        now = datetime.now(timezone.utc)
        admin_id = await conn.fetchval(
            'INSERT INTO "AIAgentManagement"."Users" '
            '("Email", "PasswordHash", "FullName", "Status", "IsEmailVerified", "IsDeleted", '
            '"IsTwoFactorEnabled", "CreatedAt", "UpdatedAt") '
            'VALUES ($1, $2, $3, $4, TRUE, FALSE, FALSE, $5, $5) RETURNING "UserId"',
            "admin@example.com", password_hash, "관리자", "Active", now,
        )
        print(f"    [insert] admin UserId={admin_id}")

    # UserRole 매핑
    role_id = await conn.fetchval(
        'SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName" = $1',
        "Admin",
    )
    if role_id is None:
        print("    [WARN] Admin Role 미존재 — UserRole 매핑 skip")
        return admin_id

    has_mapping = await conn.fetchval(
        'SELECT 1 FROM "AIAgentManagement"."UserRoles" WHERE "UserId" = $1 AND "RoleId" = $2',
        admin_id, role_id,
    )
    if has_mapping:
        print(f"    [skip] UserRole 존재: User={admin_id} Role={role_id}")
    else:
        if dry:
            print(f"    [dry] INSERT UserRole UserId={admin_id} RoleId={role_id}")
        else:
            await conn.execute(
                'INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt") '
                "VALUES ($1, $2, $3)",
                admin_id, role_id, datetime.now(timezone.utc),
            )
            print(f"    [insert] UserRole UserId={admin_id} RoleId={role_id}")
    return admin_id


async def ensure_apiservices(conn: asyncpg.Connection, dry: bool) -> dict[str, int]:
    """
    필요한 ApiServices 3개(chatgpt/dalle/nexus)를 보장하고 ServiceCode → ServiceId 매핑을 반환.
    """
    print("\n[3] ApiServices 시드 (chatgpt / dalle / nexus)")
    seeds = [
        ("chatgpt", "ChatGPT", "OpenAI ChatGPT API", "bi-chat-square-text", "#00c9ff",
         "https://api.openai.com/v1", "gpt-4-turbo", 0.03, "Chat", 1),
        ("dalle", "DALL-E 3", "OpenAI DALL-E 3 이미지 생성", "bi-image", "#10a37f",
         "https://api.openai.com/v1", "dall-e-3", 0.04, "ImageGeneration", 10),
        ("nexus", "Project Nexus",
         "사내 LAN-only LLM 게이트웨이 (옵션 B 통합 — 세션/멀티테넌시 보존)",
         "bi-hdd-network", "#10B981",
         "http://192.168.22.28:8001/v1/chat", "primary", 0.0, "Chat", 8),
    ]
    mapping: dict[str, int] = {}
    for code, name, desc, icon, color, endpoint, default_model, cost, svc_type, sort in seeds:
        existing = await conn.fetchrow(
            'SELECT "ServiceId" FROM "AIAgentManagement"."ApiServices" WHERE "ServiceCode" = $1',
            code,
        )
        if existing:
            mapping[code] = existing["ServiceId"]
            print(f"    [skip] ApiService 존재: {code} ServiceId={existing['ServiceId']}")
            continue
        if dry:
            print(f"    [dry] INSERT ApiService: {code}")
            continue
        now = datetime.now(timezone.utc)
        sid = await conn.fetchval(
            'INSERT INTO "AIAgentManagement"."ApiServices" '
            '("ServiceCode", "ServiceName", "Description", "IconClass", "ColorCode", "ApiEndpoint", '
            '"DefaultModel", "CostPerRequest", "ServiceType", "IsActive", "SortOrder", "CreatedAt", "UpdatedAt") '
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, $10, $11, $11) RETURNING \"ServiceId\"",
            code, name, desc, icon, color, endpoint, default_model, cost, svc_type, sort, now,
        )
        mapping[code] = sid
        print(f"    [insert] ApiService: {code} ServiceId={sid}")
    return mapping


async def ensure_agents(
    conn: asyncpg.Connection,
    dry: bool,
    admin_id: int,
    service_mapping: dict[str, int],
) -> int:
    """15개 Agent 시드를 멱등 INSERT — 반환: 신규 INSERT 행 수."""
    print(f"\n[4] Agents 시드 ({len(AGENT_SEEDS)}개)")
    inserted = 0
    skipped = 0
    skipped_no_service: list[str] = []

    for seed in AGENT_SEEDS:
        (agent_code, agent_name, description, service_code, default_model,
         temperature, max_tokens, system_prompt, enable_rag,
         pii_enabled, pii_mode, llm_routing, consumer_systems) = seed

        # 멱등 가드 1: AgentCode UNIQUE
        existing = await conn.fetchval(
            'SELECT "AgentId" FROM "AIAgentManagement"."Agents" WHERE "AgentCode" = $1',
            agent_code,
        )
        if existing:
            skipped += 1
            print(f"    [skip] Agent 존재: {agent_code} AgentId={existing}")
            continue

        # 멱등 가드 2: ServiceCode 등록 여부
        service_id = service_mapping.get(service_code)
        if service_id is None:
            skipped += 1
            skipped_no_service.append(f"{agent_code}({service_code})")
            print(f"    [warn] Agent skip {agent_code}: ServiceCode '{service_code}' 미등록")
            continue

        if dry:
            print(f"    [dry] INSERT Agent: {agent_code} routing={llm_routing}")
            continue

        now = datetime.now(timezone.utc)
        kb_source = "DocUtil" if enable_rag else "AgentHub"
        await conn.execute(
            'INSERT INTO "AIAgentManagement"."Agents" '
            '("AgentCode", "AgentName", "Description", "ServiceId", "SystemPrompt", '
            '"IconClass", "ColorCode", "Temperature", "MaxTokens", "DefaultModel", '
            '"IsPublic", "CreatedBy", "IsActive", "SortOrder", "EnableRag", '
            '"LlmRouting", "RoutingPolicyJson", "KnowledgeBaseSource", "KnowledgeBaseRef", "ConsumerSystems", '
            '"PiiProtectionEnabled", "PiiProtectionMode", "AllowGuestChat", "ChatTheme", '
            '"CreatedAt", "UpdatedAt") '
            'VALUES ($1, $2, $3, $4, $5, '
            '$6, $7, $8, $9, $10, '
            'FALSE, $11, TRUE, $12, $13, '
            '$14, NULL, $15, NULL, $16, '
            '$17, $18, FALSE, $19, '
            '$20, $20)',
            agent_code, agent_name, description, service_id, system_prompt,
            "bi-robot", "#6366f1", temperature, max_tokens if max_tokens > 0 else None, default_model,
            admin_id, 100, enable_rag,
            llm_routing, kb_source, consumer_systems,
            pii_enabled, pii_mode, "light",
            now,
        )
        inserted += 1
        print(f"    [insert] Agent: {agent_code} routing={llm_routing} ServiceId={service_id}")

    print(f"    합계: inserted={inserted} skipped={skipped} (총 {len(AGENT_SEEDS)})")
    if skipped_no_service:
        print(f"    [warn] ServiceCode 미등록으로 skip 된 Agent: {skipped_no_service}")
    return inserted


async def ensure_apikeys(
    conn: asyncpg.Connection,
    dry: bool,
    admin_id: int,
    print_keys: bool,
) -> list[dict[str, Any]]:
    """
    시연용 master ApiKey 2개를 발급한다. 멱등 가드는 (UserId, KeyName) 기준.
    이미 존재하면 skip(평문 출력 불가) — 처음 발급 시에만 평문이 메모리에 존재한다.
    반환: [{key_name, plaintext, key_id}] — 새로 발급된 항목만
    """
    print("\n[5] ApiKeys 발급 (시연용 master 2개)")
    issued: list[dict[str, Any]] = []
    for spec in MASTER_KEYS:
        key_name = spec["key_name"]

        existing = await conn.fetchrow(
            'SELECT "ApiKeyId", "KeyHash" FROM "AIAgentManagement"."ApiKeys" '
            'WHERE "UserId" = $1 AND "KeyName" = $2',
            admin_id, key_name,
        )
        if existing:
            print(f"    [skip] ApiKey 존재: {key_name} ApiKeyId={existing['ApiKeyId']} "
                  "(평문 재출력 불가 — 분실 시 삭제 후 재발급)")
            continue

        if dry:
            print(f"    [dry] INSERT ApiKey: {key_name}")
            continue

        plaintext = generate_random_apikey()
        ciphertext, iv, tag = encrypt_apikey(plaintext)
        ct_b64 = base64.b64encode(ciphertext).decode("ascii")
        keyhash = compute_keyhash(plaintext)
        now = datetime.now(timezone.utc)
        key_id = await conn.fetchval(
            'INSERT INTO "AIAgentManagement"."ApiKeys" '
            '("UserId", "KeyName", "ServiceCode", "AgentId", "EncryptedKey", "KeyIv", "KeyTag", "KeyHash", '
            '"Description", "ExpiresAt", "IsActive", "UsageCount", "Scopes", "AllowedIps", '
            '"RateLimitPerMinute", "RateLimitPerDay", "CreatedAt", "UpdatedAt") '
            'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NULL, TRUE, 0, $10, NULL, NULL, NULL, $11, $11) '
            'RETURNING "ApiKeyId"',
            admin_id, key_name, spec["service_code"], spec["agent_id"],
            ct_b64, iv, tag, keyhash,
            spec["description"], spec["scopes"], now,
        )
        issued.append({
            "key_name": key_name,
            "plaintext": plaintext,
            "key_id": key_id,
            "key_hash": keyhash,
            "consumer_system": spec["consumer_system"],
        })
        print(f"    [insert] ApiKey: {key_name} ApiKeyId={key_id} hash={keyhash[:16]}...")

    if print_keys and issued:
        print("\n" + "=" * 78)
        print("[발급된 평문 ApiKey — 안전한 저장소(.env)에만 사용. git 커밋 금지]")
        print("=" * 78)
        for k in issued:
            print(f"# {k['key_name']} (ApiKeyId={k['key_id']}, consumer={k['consumer_system']})")
            print(f"AGENTHUB_API_KEY={k['plaintext']}")
        print("=" * 78)
    return issued


# ── 메인 ───────────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 7.2 시드 + ApiKey 발급")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 dry run")
    parser.add_argument("--print-keys", action="store_true",
                        help="발급된 ApiKey 평문을 stdout 으로 출력")
    args = parser.parse_args()

    print(f"[연결] DSN = {DSN}")
    print(f"[모드] dry_run={args.dry_run} print_keys={args.print_keys}")
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction():
            await ensure_roles(conn, args.dry_run)
            admin_id = await ensure_admin(conn, args.dry_run)
            if admin_id is None and not args.dry_run:
                raise RuntimeError("admin 사용자 보장 실패 — 후속 시드 중단")
            mapping = await ensure_apiservices(conn, args.dry_run)
            inserted_agents = 0
            issued_keys: list[dict[str, Any]] = []
            if admin_id is not None:
                inserted_agents = await ensure_agents(conn, args.dry_run, admin_id, mapping)
                issued_keys = await ensure_apikeys(conn, args.dry_run, admin_id, args.print_keys)

        print("\n" + "=" * 78)
        print("[Phase 7.2 시드 완료]")
        print("=" * 78)
        print(f"  - Agents 신규 INSERT: {inserted_agents}개")
        print(f"  - ApiKeys 신규 INSERT: {len(issued_keys)}개")
        if not args.dry_run and issued_keys and not args.print_keys:
            print("  - 발급된 평문 키 보기: --print-keys 옵션과 함께 재실행 (멱등 — 기존 키는 skip)")
            print("    또는 보고용 JSON 파일이 user_mig/tools/.phase72_keys.json 에 저장됨")
            # JSON 저장 (gitignore 차단)
            target = os.path.join(os.path.dirname(__file__), ".phase72_keys.json")
            with open(target, "w", encoding="utf-8") as f:
                json.dump(
                    [{"key_name": k["key_name"],
                      "plaintext": k["plaintext"],
                      "key_id": k["key_id"],
                      "key_hash": k["key_hash"],
                      "consumer_system": k["consumer_system"]}
                     for k in issued_keys],
                    f, ensure_ascii=False, indent=2,
                )
            print(f"  - 평문 키 저장: {target}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
