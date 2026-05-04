#!/usr/bin/env python3
"""문서 유형별 기본 에이전트 3종을 생성하여 DB에 등록한다.

사용법:
    python scripts/create_default_agents.py
    python scripts/create_default_agents.py --base-url http://192.168.10.39:8040/api/v1
"""

from __future__ import annotations

import argparse
import sys

import requests

# ---------------------------------------------------------------------------
# 기본 에이전트 정의 (3종)
# ---------------------------------------------------------------------------
# NOTE: agent_type은 스키마 제약(chatbot|report|proposal)에 따라 지정.
#       회의록 에이전트는 보고서 계열이므로 'report'를 사용한다.

DEFAULT_AGENTS = [
    {
        "name": "보고서 작성 AI",
        "description": "참고 문서를 기반으로 전문적인 업무 보고서를 작성하는 에이전트입니다.",
        "agent_type": "report",
        "system_prompt": (
            "당신은 전문적인 업무 보고서를 작성하는 AI 어시스턴트입니다.\n\n"
            "작성 규칙:\n"
            "- 참고 문서의 핵심 내용을 정확히 파악하여 보고서에 반영하세요.\n"
            "- 보고 내용은 구체적이고 명확하게, 최소 3문단 이상 작성하세요.\n"
            "- 문제점은 실질적이고 건설적인 내용을 기술하세요.\n"
            "- 정보 출처는 참고한 문서명과 핵심 내용을 요약하세요.\n"
            "- 공식적이고 격식있는 어조를 사용하세요.\n"
            "- 불필요한 수식어를 피하고 핵심만 간결하게 전달하세요."
        ),
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    {
        "name": "제안서 작성 AI",
        "description": "설득력 있는 사업 제안서를 작성하는 에이전트입니다.",
        "agent_type": "proposal",
        "system_prompt": (
            "당신은 설득력 있는 사업 제안서를 작성하는 AI 어시스턴트입니다.\n\n"
            "작성 규칙:\n"
            "- 사업의 필요성과 기대효과를 논리적으로 제시하세요.\n"
            "- 추진 전략은 단계별로 구체적인 실행 방안을 포함하세요.\n"
            "- 예산은 항목별로 근거를 제시하세요.\n"
            "- 차별화 포인트와 경쟁 우위를 강조하세요.\n"
            "- 비즈니스 어조를 유지하되 전문성을 보여주세요.\n"
            "- 표와 데이터를 활용하여 설득력을 높이세요."
        ),
        "temperature": 0.4,
        "max_tokens": 8192,
    },
    {
        "name": "회의록 작성 AI",
        "description": "정확하고 체계적인 회의록을 작성하는 에이전트입니다.",
        "agent_type": "minutes",
        "system_prompt": (
            "당신은 정확하고 체계적인 회의록을 작성하는 AI 어시스턴트입니다.\n\n"
            "작성 규칙:\n"
            "- 안건별로 논의 내용을 명확히 구분하여 기록하세요.\n"
            "- 결정사항은 담당자와 기한을 포함하여 구체적으로 기술하세요.\n"
            "- 참석자 발언은 핵심 의견 위주로 요약하세요.\n"
            "- 미결 사항과 후속 조치를 명확히 기록하세요.\n"
            "- 객관적이고 사실적인 어조를 유지하세요.\n"
            "- 차기 회의 일정과 주요 안건을 정리하세요."
        ),
        "temperature": 0.2,
        "max_tokens": 4096,
    },
]

# ---------------------------------------------------------------------------
# 로그인 → 기존 목록 확인 → 에이전트 생성
# ---------------------------------------------------------------------------

LOGIN_ID = "dongun"
LOGIN_PW = "idino!@#$"


def login(base_url: str) -> str:
    """dongun 계정으로 로그인하여 access_token을 반환한다."""
    url = f"{base_url}/auth/login"
    resp = requests.post(
        url,
        json={"username": LOGIN_ID, "password": LOGIN_PW},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[ERROR] 로그인 실패 ({resp.status_code}): {resp.text}")
        sys.exit(1)

    token = resp.json().get("access_token")
    if not token:
        print("[ERROR] 응답에 access_token이 없습니다.")
        sys.exit(1)

    print(f"[OK] 로그인 성공 (사용자: {LOGIN_ID})")
    return token


def get_existing_agents(base_url: str, token: str) -> list[str]:
    """현재 등록된 에이전트 이름 목록을 반환한다."""
    url = f"{base_url}/agents"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params={"size": 100}, timeout=10)
    if resp.status_code != 200:
        print(f"[WARN] 에이전트 목록 조회 실패 ({resp.status_code}): {resp.text}")
        return []

    items = resp.json().get("items", [])
    return [item["name"] for item in items]


def create_agents(base_url: str = "http://localhost:8040/api/v1") -> None:
    """기본 에이전트 3종을 생성한다. 같은 이름이 이미 있으면 건너뛴다."""
    token = login(base_url)
    existing_names = get_existing_agents(base_url, token)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    created = 0
    skipped = 0

    for agent_def in DEFAULT_AGENTS:
        name = agent_def["name"]

        # 중복 검사
        if name in existing_names:
            print(f"[SKIP] 이미 존재: {name}")
            skipped += 1
            continue

        url = f"{base_url}/agents"
        resp = requests.post(url, json=agent_def, headers=headers, timeout=15)

        if resp.status_code == 201:
            agent_id = resp.json().get("id", "?")
            print(f"[OK] 생성 완료: {name} (id={agent_id})")
            created += 1
        else:
            print(f"[ERROR] 생성 실패: {name} ({resp.status_code}): {resp.text}")

    print(f"\n완료 — 생성: {created}, 건너뜀: {skipped}, 총: {len(DEFAULT_AGENTS)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="문서 유형별 기본 에이전트 3종을 생성합니다.",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8040/api/v1",
        help="API 서버 주소 (기본: http://localhost:8040/api/v1)",
    )
    args = parser.parse_args()
    create_agents(args.base_url)
