"""documents_v2 유틸리티 — 프롬프트 조립 및 RAG 직렬화 헬퍼.

Phase 4 S1 D6 산출물. ``service.py`` 가 길어지지 않도록 순수 함수 형태의
헬퍼만 이 모듈에 분리한다.

- 프롬프트 조립 (system/user) : ``build_system_prompt``, ``build_user_prompt``.
- RAG 직렬화 : ``serialize_rag_chunk``, ``build_citations_from_results``.

*외부 의존 (DB, Qdrant, LLM) 을 직접 호출하지 않는다.* 호출부에서 결과를
dict/list 로 넘겨받아 가공하는 순수 함수들만 둔다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.modules.documents_v2.constants import (
    COMMON_INSTRUCTIONS,
    DOCUMENT_TYPE_SYSTEM_PROMPTS,
    EMPTY_RAG_CONTEXT_PLACEHOLDER,
    MAX_CHUNK_SNIPPET_CHARS,
    MAX_RAG_CONTEXT_CHARS,
    USER_PROMPT_TEMPLATE,
)
from app.modules.documents_v2.exceptions import DocumentV2Error

if TYPE_CHECKING:
    from uuid import UUID

# ---------------------------------------------------------------------------
# System / User 프롬프트 조립
# ---------------------------------------------------------------------------


def build_system_prompt(
    document_type: str,
    agent_prompt: str | None = None,
    rag_context: str | None = None,
) -> str:
    """DocumentType 별 시스템 프롬프트를 조합한다.

    Parameters
    ----------
    document_type:
        DocumentSchema 의 type 문자열 (예: 'slide_report').
    agent_prompt:
        에이전트의 system_prompt. 있으면 타입 프롬프트보다 **앞**에 붙여
        역할·톤 설정을 선행시킨다.
    rag_context:
        RAG 검색 결과로 조립된 근거 문서 본문. 트랙 #106 결함 8 (자해/다단계 등
        일반어 false positive 차단) 해소 위해 **system message 에 포함**한다.
        AgentHub BannedWordService 는 마지막 user message 만 검사하므로
        RAG context 안 일반어가 차단 트리거되지 않는다.

    Raises
    ------
    DocumentV2Error
        알 수 없는 document_type 이 전달된 경우.
    """

    if document_type not in DOCUMENT_TYPE_SYSTEM_PROMPTS:
        raise DocumentV2Error(
            f"지원하지 않는 문서 타입입니다: '{document_type}'. 허용 값: {sorted(DOCUMENT_TYPE_SYSTEM_PROMPTS.keys())}"
        )

    type_prompt = DOCUMENT_TYPE_SYSTEM_PROMPTS[document_type]

    parts: list[str] = []
    if agent_prompt:
        parts.append(agent_prompt.strip())
    parts.append(type_prompt)
    parts.append(COMMON_INSTRUCTIONS)
    # 트랙 #106 — RAG context 를 system message 끝에 추가. user 검사 우회.
    if rag_context and rag_context.strip():
        parts.append("## 참고 문서 (근거)\n" + rag_context.strip())
    return "\n\n".join(parts)


def build_user_prompt(user_prompt: str, rag_context: str) -> str:
    """사용자 프롬프트와 RAG 컨텍스트를 사용자 역할 메시지로 합친다."""

    trimmed = (user_prompt or "").strip()
    if not trimmed:
        raise DocumentV2Error("사용자 프롬프트가 비어있습니다.")

    rag = rag_context.strip() if rag_context else ""
    if not rag:
        rag = EMPTY_RAG_CONTEXT_PLACEHOLDER

    return USER_PROMPT_TEMPLATE.format(user_prompt=trimmed, rag_context=rag)


# ---------------------------------------------------------------------------
# RAG 결과 직렬화
# ---------------------------------------------------------------------------


def serialize_rag_chunk(
    index: int,
    *,
    document_title: str | None,
    section_title: str | None,
    page_number: int | None,
    content: str,
    citation_id: str | None = None,
) -> str:
    """단일 chunk 를 프롬프트 삽입용 문자열로 직렬화한다.

    출력 형식::

        [r1] 문서A (2장 · p.3)
        ... 내용 ...

    ``citation_id`` 를 주면 ``[rN]`` 마커를 앞에 붙여 LLM 이 인용 시
    동일 ID 를 사용하도록 유도한다. chunk 본문은
    :data:`MAX_CHUNK_SNIPPET_CHARS` 로 트리밍된다.
    """

    snippet = (content or "").strip()
    if not snippet:
        snippet = "(본문 없음)"
    if len(snippet) > MAX_CHUNK_SNIPPET_CHARS:
        snippet = snippet[:MAX_CHUNK_SNIPPET_CHARS].rstrip() + " …"

    header_parts: list[str] = []
    if citation_id:
        header_parts.append(f"[{citation_id}]")
    else:
        header_parts.append(f"[근거{index}]")

    name = document_title or "(이름 없음)"
    location: list[str] = []
    if section_title:
        location.append(section_title)
    if page_number is not None:
        location.append(f"p.{page_number}")
    locator = f" ({' · '.join(location)})" if location else ""

    header_parts.append(f"{name}{locator}")

    return f"{' '.join(header_parts)}\n{snippet}"


def join_rag_chunks(serialized: list[str]) -> str:
    """직렬화된 chunk 문자열 목록을 하나의 컨텍스트 블록으로 합친다.

    총 길이가 :data:`MAX_RAG_CONTEXT_CHARS` 를 넘으면 초과분을 버린다.
    호출부는 이 함수의 결과를 ``build_user_prompt`` 에 직접 넣을 수 있다.
    """

    if not serialized:
        return ""

    out: list[str] = []
    running = 0
    for block in serialized:
        if not block:
            continue
        addition = len(block) + 4  # "\n\n---\n\n" 분리자 대략치
        if running + addition > MAX_RAG_CONTEXT_CHARS:
            break
        out.append(block)
        running += addition

    return "\n\n---\n\n".join(out)


# ---------------------------------------------------------------------------
# Citations 변환
# ---------------------------------------------------------------------------


def citation_dict_from_result(
    citation_id: str,
    *,
    chunk_id: Any | None,
    document_id: UUID | str | None,
    excerpt: str,
) -> dict[str, Any]:
    """DocumentMetadata.citations 에 저장할 dict 를 반환한다.

    ``schemas.Citation`` 과 동일한 키 집합을 보장한다 (id, chunk_id,
    document_id, excerpt). document_id 는 UUID 또는 str 을 그대로 두어
    Pydantic 이 검증 시 UUID 로 변환하게 한다.

    ``excerpt`` 는 :data:`MAX_CHUNK_SNIPPET_CHARS` 로 트리밍된다.
    """

    text = (excerpt or "").strip()
    if not text:
        text = "(본문 없음)"
    if len(text) > MAX_CHUNK_SNIPPET_CHARS:
        text = text[:MAX_CHUNK_SNIPPET_CHARS].rstrip() + " …"

    return {
        "id": citation_id,
        "chunk_id": None if chunk_id is None else str(chunk_id),
        "document_id": document_id,
        "excerpt": text,
    }
