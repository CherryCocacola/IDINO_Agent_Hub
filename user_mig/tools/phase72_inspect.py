"""
Phase 7.2 — 운영 PG 점검 스크립트
=====================================
목적: AGENT_HUB DB 의 다음 항목을 read-only 로 확인하여 시드 가능 여부 진단
  1) 연결 동작 여부
  2) admin@example.com 존재 (Agent.CreatedBy NOT NULL FK 충족 필요)
  3) ApiServices 등록 현황 (Agent.ServiceId FK 충족 필요)
  4) 기존 Agents 행 (15개 시드 멱등 가드 — AgentCode UNIQUE)
  5) 기존 ApiKeys 행 (docutil/career master 발급 전 충돌 점검)

본 스크립트는 INSERT 를 수행하지 않는다 — 후속 phase72_seed.py 에서만 INSERT.
"""
from __future__ import annotations

import asyncio
import sys

import asyncpg

DSN = "postgresql://AGENT_HUB:idino%21%40%23%24@192.168.10.39:5440/AGENT_HUB"


async def main() -> None:
    print(f"[연결] DSN = {DSN}")
    try:
        conn = await asyncpg.connect(DSN)
    except Exception as ex:
        print(f"[ERROR] 연결 실패: {type(ex).__name__}: {ex}")
        sys.exit(1)

    try:
        # 1) 사용자 — admin@example.com (DatabaseInitializer.SeedAgentsAsync 가 요구)
        print("\n[1] admin 사용자 확인")
        # 먼저 Users 컬럼을 확인 (스키마가 정확히 어떻게 매핑돼 있는지)
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='AIAgentManagement' AND table_name='Users' ORDER BY ordinal_position"
        )
        col_names = [c["column_name"] for c in cols]
        print(f"    Users 컬럼 목록: {col_names}")

        admin = await conn.fetchrow(
            'SELECT * FROM "AIAgentManagement"."Users" WHERE "Email" = $1',
            "admin@example.com",
        )
        if admin:
            print(f"    OK admin UserId={admin['UserId']} email={admin['Email']}")
        else:
            print("    NG admin@example.com 미존재 — Agent 시드 불가")
            users = await conn.fetch(
                'SELECT "UserId", "Email" FROM "AIAgentManagement"."Users" ORDER BY "UserId" LIMIT 10'
            )
            print(f"    상위 사용자 10명: {[(u['UserId'], u['Email']) for u in users]}")

        # 2) ApiServices — chatgpt / dalle / nexus 필수
        print("\n[2] ApiServices 등록 현황")
        rows = await conn.fetch(
            'SELECT "ServiceId", "ServiceCode", "ServiceName" FROM "AIAgentManagement"."ApiServices" ORDER BY "ServiceCode"'
        )
        for r in rows:
            print(f"    {r['ServiceCode']:<16} ServiceId={r['ServiceId']} {r['ServiceName']}")
        codes = {r["ServiceCode"] for r in rows}
        for need in ("chatgpt", "dalle", "nexus"):
            mark = "OK" if need in codes else "NG"
            print(f"    [{mark}] '{need}'")

        # 3) Agents — 15 시드 멱등 가드
        print("\n[3] 기존 Agents")
        rows = await conn.fetch(
            'SELECT "AgentId", "AgentCode", "AgentName", "ServiceId", "LlmRouting" FROM "AIAgentManagement"."Agents" ORDER BY "AgentCode"'
        )
        print(f"    행 수 = {len(rows)}")
        for r in rows:
            print(f"    {r['AgentCode']:<32} ServiceId={r['ServiceId']} routing={r['LlmRouting']}")

        # 4) ApiKeys — 발급 전 충돌 점검
        print("\n[4] 기존 ApiKeys (KeyName + ServiceCode + AgentId)")
        rows = await conn.fetch(
            'SELECT "ApiKeyId", "UserId", "KeyName", "ServiceCode", "AgentId", "IsActive", "Scopes" '
            'FROM "AIAgentManagement"."ApiKeys" ORDER BY "ApiKeyId"'
        )
        print(f"    행 수 = {len(rows)}")
        for r in rows:
            print(
                f"    Id={r['ApiKeyId']} User={r['UserId']} '{r['KeyName']}' "
                f"svc={r['ServiceCode']} AgentId={r['AgentId']} active={r['IsActive']} scopes={r['Scopes']}"
            )

        # 5) ApiKeys 컬럼 스키마 확인 (Phase 3.3c GCM/KeyHash 적용 여부)
        print("\n[5] ApiKeys 컬럼 스키마")
        cols = await conn.fetch(
            "SELECT column_name, data_type, is_nullable, character_maximum_length "
            "FROM information_schema.columns "
            "WHERE table_schema = 'AIAgentManagement' AND table_name = 'ApiKeys' "
            "ORDER BY ordinal_position"
        )
        for c in cols:
            print(
                f"    {c['column_name']:<22} {c['data_type']:<24} nullable={c['is_nullable']} max_len={c['character_maximum_length']}"
            )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
