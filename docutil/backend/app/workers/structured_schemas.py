"""
GPT-4o Structured Outputs용 JSON 스키마 정의.

PPTX(프레젠테이션)와 DOCX(문서) 생성 시 LLM이 반환할 JSON 구조를
OpenAI Structured Outputs의 ``strict: True`` 형식으로 정의한다.

모든 필드는 ``required``로 선언하고, ``additionalProperties: false``를
설정하여 LLM이 정확한 형태의 JSON만 반환하도록 강제한다.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 공통 하위 스키마: 표(table) 정의
# ---------------------------------------------------------------------------
# 표는 헤더(문자열 배열)와 데이터 행(2차원 문자열 배열)으로 구성된다.
_TABLE_SCHEMA = {
    "type": "object",
    "description": "표 데이터. 헤더와 행으로 구성된다.",
    "properties": {
        "headers": {
            "type": "array",
            "description": "표의 열 제목 목록 (예: ['항목', '수량', '비고'])",
            "items": {"type": "string"},
        },
        "rows": {
            "type": "array",
            "description": "표의 데이터 행. 각 행은 문자열 배열이다.",
            "items": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    "required": ["headers", "rows"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# 공통 하위 스키마: 차트(chart) 시리즈 정의
# ---------------------------------------------------------------------------
# 차트 시리즈는 이름과 숫자 값 배열로 구성된다.
_CHART_SERIES_SCHEMA = {
    "type": "object",
    "description": "차트의 데이터 시리즈 하나. 이름과 값으로 구성된다.",
    "properties": {
        "name": {
            "type": "string",
            "description": "시리즈 이름 (범례에 표시됨)",
        },
        "values": {
            "type": "array",
            "description": "카테고리별 숫자 데이터",
            "items": {"type": "number"},
        },
    },
    "required": ["name", "values"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# 공통 하위 스키마: 차트(chart) 정의
# ---------------------------------------------------------------------------
# 차트는 유형, 제목, 카테고리, 시리즈로 구성된다.
_CHART_SCHEMA = {
    "type": "object",
    "description": "차트 데이터. 유형·제목·카테고리·시리즈로 구성된다.",
    "properties": {
        "chart_type": {
            "type": "string",
            "description": "차트 유형: bar(막대), pie(원형), line(꺾은선)",
            "enum": ["bar", "pie", "line"],
        },
        "title": {
            "type": "string",
            "description": "차트 제목",
        },
        "categories": {
            "type": "array",
            "description": "X축 카테고리 라벨 (예: ['1월', '2월', '3월'])",
            "items": {"type": "string"},
        },
        "series": {
            "type": "array",
            "description": "차트 데이터 시리즈 목록 (여러 시리즈 가능)",
            "items": _CHART_SERIES_SCHEMA,
        },
    },
    "required": ["chart_type", "title", "categories", "series"],
    "additionalProperties": False,
}


# ===========================================================================
# PPTX 슬라이드 스키마
# ===========================================================================
# 프레젠테이션은 제목, 부제, 슬라이드 배열로 구성된다.
# 각 슬라이드는 레이아웃 유형에 따라 다른 콘텐츠를 가진다.

PPTX_SLIDE_SCHEMA = {
    "name": "pptx_presentation",
    "description": "PPTX 프레젠테이션 구조를 정의하는 JSON 스키마",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "presentation": {
                "type": "object",
                "description": "프레젠테이션 전체 구조",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "프레젠테이션 제목 (표지에 표시됨)",
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "프레젠테이션 부제 (표지에 표시됨)",
                    },
                    "slides": {
                        "type": "array",
                        "description": "슬라이드 목록. 순서대로 프레젠테이션에 배치된다.",
                        "items": {
                            "type": "object",
                            "description": "개별 슬라이드 정의",
                            "properties": {
                                "layout_type": {
                                    "type": "string",
                                    "description": (
                                        "슬라이드 레이아웃 유형. "
                                        "title=표지, index=목차, "
                                        "section_divider=소단원 구분, "
                                        "body_text=본문 텍스트, "
                                        "body_with_table=본문+표, "
                                        "body_with_chart=본문+차트, "
                                        "body_with_image=본문+이미지, "
                                        "two_column=2단 레이아웃, "
                                        "closing=마침 화면"
                                    ),
                                    "enum": [
                                        "title",
                                        "index",
                                        "section_divider",
                                        "body_text",
                                        "body_with_table",
                                        "body_with_chart",
                                        "body_with_image",
                                        "two_column",
                                        "closing",
                                    ],
                                },
                                "heading": {
                                    "type": "string",
                                    "description": "슬라이드 제목/헤딩",
                                },
                                "body": {
                                    "type": "string",
                                    "description": "슬라이드 본문 텍스트 (줄바꿈은 \\n 사용)",
                                },
                                "bullet_points": {
                                    "type": "array",
                                    "description": "글머리 기호 항목 목록 (4~6개 권장)",
                                    "items": {"type": "string"},
                                },
                                "table": {
                                    "anyOf": [_TABLE_SCHEMA, {"type": "null"}],
                                    "description": "표 데이터. 표가 없으면 null",
                                },
                                "chart": {
                                    "anyOf": [_CHART_SCHEMA, {"type": "null"}],
                                    "description": "차트 데이터. 차트가 없으면 null",
                                },
                                "image_query": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "description": ("이미지 검색 키워드 (영어 권장). 이미지가 불필요하면 null"),
                                },
                                "speaker_notes": {
                                    "type": "string",
                                    "description": "발표자 노트 (청중에게 보이지 않는 메모)",
                                },
                                "column_left": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "description": "2단 레이아웃의 왼쪽 열 내용. 미사용 시 null",
                                },
                                "column_right": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "description": "2단 레이아웃의 오른쪽 열 내용. 미사용 시 null",
                                },
                            },
                            "required": [
                                "layout_type",
                                "heading",
                                "body",
                                "bullet_points",
                                "table",
                                "chart",
                                "image_query",
                                "speaker_notes",
                                "column_left",
                                "column_right",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["title", "subtitle", "slides"],
                "additionalProperties": False,
            },
        },
        "required": ["presentation"],
        "additionalProperties": False,
    },
}


# ===========================================================================
# DOCX 문서 스키마
# ===========================================================================
# 문서는 제목과 섹션 배열로 구성된다.
# 각 섹션은 제목, 제목 수준, 문단, 표, 차트, 글머리 기호를 가진다.

# ---------------------------------------------------------------------------
# 회의록 전용 하위 스키마 (H6 핫픽스)
# ---------------------------------------------------------------------------
# 회의록은 자유형 문단보다 "참석자 / 안건 / 결정사항 / 액션아이템"을 구조적으로
# 기록해야 실무에서 사용 가치가 생긴다. LLM이 자유문으로 쏟아내는 걸 막기
# 위해 별도 JSON 스키마를 정의한다.

_ACTION_ITEM_SCHEMA = {
    "type": "object",
    "description": "액션아이템: 회의에서 도출된 할 일 항목",
    "properties": {
        "assignee": {
            "type": "string",
            "description": "담당자 이름 또는 역할. 불명확하면 '미정'",
        },
        "task": {
            "type": "string",
            "description": "수행해야 할 구체적인 업무 내용",
        },
        "due_date": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "description": "마감일 (YYYY-MM-DD 형식 권장). 없으면 null",
        },
    },
    "required": ["assignee", "task", "due_date"],
    "additionalProperties": False,
}


MINUTES_STRUCTURED_SCHEMA = {
    "name": "meeting_minutes",
    "description": "회의록 구조를 정의하는 JSON 스키마",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "minutes": {
                "type": "object",
                "description": "회의록 전체 구조",
                "properties": {
                    "meeting_title": {
                        "type": "string",
                        "description": "회의의 공식 명칭",
                    },
                    "meeting_date": {
                        "type": "string",
                        "description": "회의 일자 (YYYY-MM-DD 권장). 확인 불가하면 '일자 미상'",
                    },
                    "location": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "회의 장소 또는 화상회의 플랫폼. 미상이면 null",
                    },
                    "attendees": {
                        "type": "array",
                        "description": "참석자 목록. 이름/직함을 그대로 기재",
                        "items": {"type": "string"},
                    },
                    "agenda": {
                        "type": "array",
                        "description": "회의 안건 목록. 순번대로 나열",
                        "items": {"type": "string"},
                    },
                    "discussion_points": {
                        "type": "array",
                        "description": "주요 논의 내용 요약. 각 항목은 하나의 이슈/주제",
                        "items": {"type": "string"},
                    },
                    "decisions": {
                        "type": "array",
                        "description": "회의에서 확정된 결정사항 목록",
                        "items": {"type": "string"},
                    },
                    "action_items": {
                        "type": "array",
                        "description": "후속 조치 목록 (담당자·업무·기한)",
                        "items": _ACTION_ITEM_SCHEMA,
                    },
                    "next_meeting": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "다음 회의 일정 및 안건 개요. 없으면 null",
                    },
                },
                "required": [
                    "meeting_title",
                    "meeting_date",
                    "location",
                    "attendees",
                    "agenda",
                    "discussion_points",
                    "decisions",
                    "action_items",
                    "next_meeting",
                ],
                "additionalProperties": False,
            },
        },
        "required": ["minutes"],
        "additionalProperties": False,
    },
}


DOCX_DOCUMENT_SCHEMA = {
    "name": "docx_document",
    "description": "DOCX 문서 구조를 정의하는 JSON 스키마",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "document": {
                "type": "object",
                "description": "문서 전체 구조",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "문서 제목 (최상위 헤딩으로 표시됨)",
                    },
                    "sections": {
                        "type": "array",
                        "description": "문서 섹션 목록. 순서대로 문서에 배치된다.",
                        "items": {
                            "type": "object",
                            "description": "개별 섹션 정의",
                            "properties": {
                                "heading": {
                                    "type": "string",
                                    "description": "섹션 제목",
                                },
                                "heading_level": {
                                    "type": "integer",
                                    "description": ("제목 수준: 1=대제목, 2=중제목, 3=소제목"),
                                    "enum": [1, 2, 3],
                                },
                                "paragraphs": {
                                    "type": "array",
                                    "description": (
                                        "본문 문단 목록. 각 항목이 하나의 문단이다. 섹션당 2~4개 문단 권장."
                                    ),
                                    "items": {"type": "string"},
                                },
                                "table": {
                                    "anyOf": [_TABLE_SCHEMA, {"type": "null"}],
                                    "description": "표 데이터. 표가 없으면 null",
                                },
                                "chart": {
                                    "anyOf": [_CHART_SCHEMA, {"type": "null"}],
                                    "description": "차트 데이터. 차트가 없으면 null",
                                },
                                "bullet_points": {
                                    "type": "array",
                                    "description": "글머리 기호 항목 목록",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "heading",
                                "heading_level",
                                "paragraphs",
                                "table",
                                "chart",
                                "bullet_points",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["title", "sections"],
                "additionalProperties": False,
            },
        },
        "required": ["document"],
        "additionalProperties": False,
    },
}
