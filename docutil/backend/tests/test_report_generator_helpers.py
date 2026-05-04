"""
Unit tests for H5·H6 헬퍼 함수들 (report_generator 워커).

이 테스트는 DB·MinIO·LLM 을 전혀 호출하지 않는 순수 함수만 대상으로 한다.

검증 대상:
- ``_minutes_to_docx_document``: MINUTES_STRUCTURED_SCHEMA → DOCX 섹션 매핑
- ``MINUTES_STRUCTURED_SCHEMA`` 필수 필드 정의
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# H6. 회의록 → DOCX 구조 변환기
# ---------------------------------------------------------------------------


def test_minutes_to_docx_document_builds_all_sections():
    """회의록 JSON 이 6개 섹션 (개요·안건·논의·결정·액션아이템·차기) 로 매핑된다."""
    from app.workers.report_generator import _minutes_to_docx_document

    minutes_data = {
        "minutes": {
            "meeting_title": "2026 Q2 제품 전략 회의",
            "meeting_date": "2026-04-19",
            "location": "본사 3층 회의실",
            "attendees": ["홍길동 PM", "김철수 개발팀장", "이영희 디자이너"],
            "agenda": ["Q2 로드맵 확정", "리소스 배분"],
            "discussion_points": [
                "리포트 기능 안정성 강화가 최우선이라는 의견이 있었다.",
                "디자인 시스템 재정비는 Q3 로 이월하자는 합의가 있었다.",
            ],
            "decisions": [
                "Q2 최우선 과제는 리포트 기능 안정화로 확정한다.",
            ],
            "action_items": [
                {
                    "assignee": "김철수",
                    "task": "리포트 워커 재시도 로직 설계",
                    "due_date": "2026-04-26",
                },
                {
                    "assignee": "미정",
                    "task": "디자인 시스템 자료 정리",
                    "due_date": None,
                },
            ],
            "next_meeting": "2026-05-03 오후 2시 — 리포트 안정화 중간 점검",
        }
    }

    doc = _minutes_to_docx_document(minutes_data, fallback_title="회의록")
    sections = doc["document"]["sections"]

    # 제목은 minutes.meeting_title 우선 사용
    assert doc["document"]["title"] == "2026 Q2 제품 전략 회의"

    # 섹션 순서가 고정되어 있는지 검증
    headings = [s["heading"] for s in sections]
    assert headings == [
        "회의 개요",
        "안건",
        "논의 내용",
        "결정사항",
        "액션아이템",
        "차기 회의",
    ]

    # 회의 개요: 일시/장소가 paragraphs 에 반영
    overview = sections[0]
    assert any("2026-04-19" in p for p in overview["paragraphs"])
    assert any("본사 3층 회의실" in p for p in overview["paragraphs"])
    # 참석자는 bullet_points 로 나열
    assert overview["bullet_points"] == [
        "참석자: 홍길동 PM",
        "참석자: 김철수 개발팀장",
        "참석자: 이영희 디자이너",
    ]

    # 안건: bullet_points
    assert sections[1]["bullet_points"] == ["Q2 로드맵 확정", "리소스 배분"]

    # 논의: paragraphs
    assert len(sections[2]["paragraphs"]) == 2

    # 결정사항: bullet_points
    assert sections[3]["bullet_points"] == [
        "Q2 최우선 과제는 리포트 기능 안정화로 확정한다.",
    ]

    # 액션아이템: 표로 구성 (담당자/업무/마감일)
    action_section = sections[4]
    assert action_section["table"] is not None
    assert action_section["table"]["headers"] == ["담당자", "업무", "마감일"]
    assert action_section["table"]["rows"] == [
        ["김철수", "리포트 워커 재시도 로직 설계", "2026-04-26"],
        ["미정", "디자인 시스템 자료 정리", "-"],
    ]


def test_minutes_to_docx_document_handles_empty_action_items():
    """액션아이템이 없는 경우에도 '별도의 액션아이템은 도출되지 않았습니다.' 문단을 남긴다."""
    from app.workers.report_generator import _minutes_to_docx_document

    minutes_data = {
        "minutes": {
            "meeting_title": "",
            "meeting_date": "일자 미상",
            "location": None,
            "attendees": [],
            "agenda": [],
            "discussion_points": [],
            "decisions": [],
            "action_items": [],
            "next_meeting": None,
        }
    }
    doc = _minutes_to_docx_document(minutes_data, fallback_title="폴백 회의록")
    assert doc["document"]["title"] == "폴백 회의록"

    # 액션아이템 섹션 찾기
    action = next(s for s in doc["document"]["sections"] if s["heading"] == "액션아이템")
    assert action["table"] is None
    assert any("별도의 액션아이템" in p for p in action["paragraphs"])

    # 차기 회의 섹션은 next_meeting 이 없으면 생성되지 않는다
    headings = [s["heading"] for s in doc["document"]["sections"]]
    assert "차기 회의" not in headings


# ---------------------------------------------------------------------------
# 스키마 자체 형태 검증 (H6: strict Structured Outputs 대응)
# ---------------------------------------------------------------------------


def test_minutes_schema_has_required_fields():
    """MINUTES_STRUCTURED_SCHEMA 가 필수 필드를 모두 required 에 포함한다."""
    from app.workers.structured_schemas import MINUTES_STRUCTURED_SCHEMA

    inner = MINUTES_STRUCTURED_SCHEMA["schema"]["properties"]["minutes"]
    required = set(inner["required"])
    expected = {
        "meeting_title",
        "meeting_date",
        "location",
        "attendees",
        "agenda",
        "discussion_points",
        "decisions",
        "action_items",
        "next_meeting",
    }
    assert expected.issubset(required)

    # 액션아이템의 하위 스키마도 assignee/task/due_date 를 required 로 강제해야 한다
    item_schema = inner["properties"]["action_items"]["items"]
    assert set(item_schema["required"]) == {"assignee", "task", "due_date"}


# ---------------------------------------------------------------------------
# H5 회귀 방어: _load_source_chunks 는 이미 async 이므로 구조만 호출 가능 여부 검증
# ---------------------------------------------------------------------------


def test_load_source_chunks_is_coroutine_function():
    """_load_source_chunks 가 빈 ID 목록에서 즉시 빈 문자열을 반환하는지 확인.

    DB 세션 생성 없이 조기 return 분기만 검증하여 환경 의존성을 제거한다.
    """
    import asyncio

    from app.workers.report_generator import _load_source_chunks

    result = asyncio.run(_load_source_chunks([]))
    assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
