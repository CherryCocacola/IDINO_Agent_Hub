"""Phase 4 S1 D6 — DocumentServiceV2 (Mode A) 자동 테스트.

테스트 범위:
1. ``build_rag_context`` (B1-a 이관) — source_document_ids 분기 (3 케이스)
2. ``generate`` Mode A end-to-end — 성공 / 메타 주입 / Agent 결합 /
   비정규화 컬럼 / created_at UTC / citations 상위 10 제한 /
   LLM 실패 경로 / DocumentType 전수
3. ``build_system_prompt`` 전수 (7 타입)

실 API·DB 호출 금지 — ``db`` 는 ``AsyncMock`` 으로, LLM 은
``create_llm_client`` 을 patch, 검색 경로는 ``AgenticSearchService`` 를
patch 한다. conftest.py 의 ``db_session`` 은 SQLite 기반이라 JSONB 등
PostgreSQL 고유 타입을 갖는 ``tb_documents_v2`` 테이블이 없으므로
본 테스트는 의도적으로 in-memory mock 세션으로 진행한다.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.modules.documents_v2.constants import (
    DOCUMENT_TYPE_SYSTEM_PROMPTS,
    MAX_CITATIONS_STORED,
)
from app.modules.documents_v2.exceptions import (
    DocumentGenerationError,
    DocumentSchemaValidationError,
    RAGContextError,
)
from app.modules.documents_v2.models import DocumentV2
from app.modules.documents_v2.schemas import DocumentSchema
from app.modules.documents_v2.service import DocumentServiceV2
from app.modules.documents_v2.utils import build_system_prompt

# ---------------------------------------------------------------------------
# 고정 식별자 / 헬퍼
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
AGENT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
DOC_ID_1 = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
DOC_ID_2 = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
CHUNK_ID_1 = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")


def _make_llm_response_schema(
    *,
    document_type: str = "slide_report",
    n_citations: int = 0,
) -> DocumentSchema:
    """LLM 이 반환했다고 가정하는 DocumentSchema 인스턴스를 만든다.

    의도적으로 ``document_id`` 를 placeholder UUID 로 두어 서버 측 주입
    로직이 올바르게 덮어쓰는지 확인할 수 있게 한다.
    """
    now = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
    citations = [
        {
            "id": f"r{i}",
            "chunk_id": None,
            "document_id": None,
            "excerpt": f"LLM 생성 인용 {i}",
        }
        for i in range(1, n_citations + 1)
    ]
    payload = {
        "document_id": str(uuid.uuid4()),
        "schema_version": "1.0",
        "type": document_type,
        "mode": "free_generation",
        "template_id": None,
        "design_tokens": {},
        "pages": [
            {
                "id": "p1",
                "page_kind": "slide" if document_type == "slide_report" else "section",
                "layout": "title_slide",
                "title": "LLM 이 생성한 제목",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": "LLM 이 생성한 제목",
                        "locked": False,
                        "anchor": None,
                    }
                ],
            }
        ],
        "metadata": {
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "generated_by_user_id": None,
            "llm_provider": None,
            "llm_model": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "source_document_ids": [],
            "source_chat_session_id": None,
            "citations": citations,
            "degraded_components": [],
        },
    }
    return DocumentSchema.model_validate(payload)


def _make_agent(
    system_prompt: str = "너는 보고서 작성 전문가다.",
    llm_provider: str | None = None,
    llm_model: str = "gpt-4o",
    temperature: float = 0.2,
    max_tokens: int = 8192,
    organization_id: uuid.UUID | None = None,
) -> MagicMock:
    """AgentService.get_or DB query 대신 반환될 mock Agent 인스턴스."""
    agent = MagicMock()
    agent.id = AGENT_ID
    agent.organization_id = organization_id or ORG_ID
    agent.system_prompt = system_prompt
    agent.llm_provider = llm_provider
    agent.llm_model = llm_model
    agent.temperature = temperature
    agent.max_tokens = max_tokens
    return agent


def _make_mock_db(
    agent: MagicMock | None = None,
) -> MagicMock:
    """DocumentServiceV2.generate 내부에서 쓰이는 db 메서드 (add/flush/refresh/get)
    을 AsyncMock 으로 갖춘 세션을 반환한다."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock(return_value=None)
    db.refresh = AsyncMock(return_value=None)
    db.get = AsyncMock(return_value=agent)
    return db


# ---------------------------------------------------------------------------
# 1~3. build_rag_context — 3 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_rag_context_with_source_document_ids_returns_serialized_chunks():
    """source_document_ids 있으면 DB chunks 를 직접 로드해 직렬화한다."""

    chunk = SimpleNamespace(
        id=CHUNK_ID_1,
        document_id=DOC_ID_1,
        chunk_index=0,
        content="매출은 전년 대비 15% 증가했다.",
        page_number=3,
        section_title="재무 성과",
    )
    document = SimpleNamespace(
        id=DOC_ID_1,
        name="2024 연간보고서.pdf",
        organization_id=ORG_ID,
    )

    db = _make_mock_db()

    with patch.object(
        DocumentServiceV2,
        "_load_chunks_for_documents",
        new=AsyncMock(return_value=[(chunk, document)]),
    ):
        context, citations = await DocumentServiceV2.build_rag_context(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="재무 성과 요약",
            source_document_ids=[DOC_ID_1],
        )

    assert "[r1]" in context
    assert "2024 연간보고서.pdf" in context
    assert "p.3" in context
    assert "재무 성과" in context
    assert "전년 대비 15%" in context

    assert len(citations) == 1
    c0 = citations[0]
    assert c0["id"] == "r1"
    assert c0["chunk_id"] == str(CHUNK_ID_1)
    assert c0["document_id"] == DOC_ID_1
    assert "전년 대비 15%" in c0["excerpt"]


@pytest.mark.asyncio
async def test_build_rag_context_without_source_document_ids_calls_agentic_search():
    """source_document_ids 가 None 이면 AgenticSearchService 경로로 간다."""

    # SearchResult 구조는 search.schemas 를 따르지만, service.py 는 속성 접근만
    # 하므로 SimpleNamespace 로도 충분하다.
    fake_result = SimpleNamespace(
        document_id=DOC_ID_2,
        document_name="정책자료.docx",
        chunk_id=CHUNK_ID_1,
        chunk_index=0,
        content="개인정보 처리방침은 반기별로 갱신한다.",
        score=0.87,
        page_number=None,
        section_title="제3조",
        chunk_type="text",
        highlights=None,
    )
    fake_response = SimpleNamespace(
        query="개인정보 처리",
        results=[fake_result],
        total_results=1,
        search_type="agentic",
        latency_ms=42,
    )

    db = _make_mock_db()

    with patch(
        "app.modules.search.agentic_search.AgenticSearchService.agentic_search",
        new=AsyncMock(return_value=fake_response),
    ) as mock_search:
        context, citations = await DocumentServiceV2.build_rag_context(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="개인정보 처리",
            source_document_ids=None,
        )

    mock_search.assert_awaited_once()
    call_kwargs = mock_search.call_args.kwargs
    assert call_kwargs["org_id"] == ORG_ID
    assert call_kwargs["query"] == "개인정보 처리"

    assert "[r1]" in context
    assert "정책자료.docx" in context
    assert "제3조" in context
    assert len(citations) == 1
    assert citations[0]["document_id"] == DOC_ID_2


@pytest.mark.asyncio
async def test_build_rag_context_empty_search_returns_empty_context_and_citations():
    """검색 결과가 비어있을 때 컨텍스트는 빈 문자열, citations 은 빈 리스트."""

    fake_response = SimpleNamespace(
        query="데이터 없음",
        results=[],
        total_results=0,
        search_type="agentic",
        latency_ms=10,
    )
    db = _make_mock_db()

    with patch(
        "app.modules.search.agentic_search.AgenticSearchService.agentic_search",
        new=AsyncMock(return_value=fake_response),
    ):
        context, citations = await DocumentServiceV2.build_rag_context(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="데이터 없음",
            source_document_ids=None,
        )

    assert context == ""
    assert citations == []


@pytest.mark.asyncio
async def test_build_rag_context_search_exception_wrapped_as_rag_context_error():
    """외부 검색 오류는 RAGContextError 로 래핑된다."""
    db = _make_mock_db()

    with (
        patch(
            "app.modules.search.agentic_search.AgenticSearchService.agentic_search",
            new=AsyncMock(side_effect=RuntimeError("qdrant down")),
        ),
        pytest.raises(RAGContextError),
    ):
        await DocumentServiceV2.build_rag_context(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="뭐든",
            source_document_ids=None,
        )


# ---------------------------------------------------------------------------
# 4~10. generate — Mode A end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_mode_a_happy_path_returns_document_v2_with_completed_status():
    """정상 흐름: LLM→스키마 검증→DB 저장 후 completed 상태의 row 가 남는다."""

    schema = _make_llm_response_schema(document_type="slide_report", n_citations=2)
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)

    db = _make_mock_db()

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("(컨텍스트)", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="Q1 매출 슬라이드 보고서 3장 만들어줘",
            document_type="slide_report",
        )

    assert isinstance(doc, DocumentV2)
    assert doc.status == "completed"
    assert doc.document_type == "slide_report"
    assert doc.mode == "free_generation"
    assert doc.organization_id == ORG_ID
    assert doc.generated_by_user_id == USER_ID
    assert doc.template_id is None
    assert doc.llm_provider == "openai"
    # db.add 는 완료 row 1 회만 호출
    db.add.assert_called_once()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_overrides_document_id_from_llm_response():
    """LLM 이 지어낸 document_id 는 서버 생성 UUID 로 덮어써진다."""

    schema = _make_llm_response_schema()
    llm_document_id = schema.document_id  # LLM 이 만든 더미 UUID
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)

    db = _make_mock_db()

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="뭐든",
            document_type="slide_report",
        )

    # 저장된 schema 의 document_id 는 서버가 만든 row 의 id 와 일치해야 한다
    stored = doc.document_schema
    assert stored["document_id"] == str(doc.id)
    assert stored["document_id"] != str(llm_document_id)
    # 서버 주입 필드 확인
    assert stored["mode"] == "free_generation"
    assert stored["template_id"] is None


@pytest.mark.asyncio
async def test_generate_with_agent_id_includes_agent_system_prompt_in_llm_call():
    """agent_id 를 주면 build_system_prompt 가 agent.system_prompt 를 포함한다."""

    agent_prompt_text = "너는 한국어 회의록 전문가다. 간결하게 써라."
    agent = _make_agent(
        system_prompt=agent_prompt_text,
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet",
        temperature=0.15,
        max_tokens=9000,
    )

    schema = _make_llm_response_schema(document_type="minutes")
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)
    db = _make_mock_db(agent=agent)

    created_provider = {}

    def _spy_create(provider, **kwargs):
        created_provider["provider"] = provider
        created_provider["model"] = kwargs.get("model")
        return llm_client

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            side_effect=_spy_create,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="3월 1일 정기회의 회의록",
            document_type="minutes",
            agent_id=AGENT_ID,
        )

    # Agent 프로바이더·모델이 사용됨 (agent override 우선)
    assert created_provider["provider"] == "anthropic"
    assert created_provider["model"] == "claude-3-5-sonnet"
    assert doc.llm_provider == "anthropic"
    assert doc.llm_model == "claude-3-5-sonnet"
    assert doc.agent_id == AGENT_ID

    # LLM 에 전달된 system_prompt 가 agent 지시를 포함하는지
    call_kwargs = llm_client.generate_with_schema.call_args.kwargs
    assert agent_prompt_text in call_kwargs["system_prompt"]
    # 온도/토큰도 agent 설정이 반영되는지
    assert call_kwargs["temperature"] == 0.15
    assert call_kwargs["max_tokens"] == 9000


@pytest.mark.asyncio
async def test_generate_denormalized_columns_mirror_schema_fields():
    """비정규화 컬럼 (document_type/mode/organization_id) 과 source_document_ids 저장 확인."""

    schema = _make_llm_response_schema(document_type="weekly_status")
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)
    db = _make_mock_db()

    source_ids = [DOC_ID_1, DOC_ID_2]

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="이번 주 진행 사항",
            document_type="weekly_status",
            source_document_ids=source_ids,
        )

    assert doc.document_type == "weekly_status"
    assert doc.mode == "free_generation"
    assert doc.organization_id == ORG_ID
    assert list(doc.source_document_ids) == source_ids
    # JSONB 저장값에도 일관성 있게 반영
    assert doc.document_schema["type"] == "weekly_status"
    assert doc.document_schema["mode"] == "free_generation"


@pytest.mark.asyncio
async def test_generate_metadata_created_at_is_utc_timezone_aware():
    """metadata.created_at / updated_at 는 UTC 타임존 포함 datetime 이어야 한다."""

    schema = _make_llm_response_schema()
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)
    db = _make_mock_db()

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="뭐든",
            document_type="slide_report",
        )

    # JSON 직렬화된 metadata.created_at 을 파싱해 tz 확인
    stored_meta = doc.document_schema["metadata"]
    created_at_iso = stored_meta["created_at"]
    parsed = datetime.fromisoformat(created_at_iso)
    assert parsed.tzinfo is not None, "created_at 은 timezone-aware 여야 한다"
    assert parsed.utcoffset() == UTC.utcoffset(parsed), "created_at 은 UTC 오프셋이어야 한다"


@pytest.mark.asyncio
async def test_generate_limits_metadata_citations_to_top_n():
    """citations 는 최대 MAX_CITATIONS_STORED 개로 잘린다."""

    schema = _make_llm_response_schema()
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)
    db = _make_mock_db()

    # 20 개의 citation dict 준비
    many_citations = [
        {
            "id": f"r{i}",
            "chunk_id": None,
            "document_id": None,
            "excerpt": f"근거 {i}",
        }
        for i in range(1, 21)
    ]

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("(컨텍스트)", many_citations)),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="뭐든",
            document_type="slide_report",
        )

    citations = doc.document_schema["metadata"]["citations"]
    assert len(citations) == MAX_CITATIONS_STORED
    assert citations[0]["id"] == "r1"
    assert citations[-1]["id"] == f"r{MAX_CITATIONS_STORED}"


@pytest.mark.asyncio
async def test_generate_llm_failure_persists_error_row_and_raises():
    """LLM 호출 실패 시 status='error' row 가 저장되고 DocumentGenerationError 가 raise 된다."""

    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(side_effect=RuntimeError("timeout"))
    db = _make_mock_db()

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
        pytest.raises(DocumentGenerationError),
    ):
        await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="망할 거임",
            document_type="slide_report",
        )

    # 실패 row 가 정확히 1회 추가되었는지 확인
    assert db.add.call_count == 1
    added = db.add.call_args.args[0]
    assert isinstance(added, DocumentV2)
    assert added.status == "error"
    assert added.error_message is not None
    assert "LLM" in added.error_message or "timeout" in added.error_message.lower()


@pytest.mark.asyncio
async def test_generate_schema_validation_failure_raises_schema_validation_error():
    """LLM 응답이 DocumentSchema 검증을 통과하지 못하면 DocumentSchemaValidationError."""

    # 검증 오류를 만들기 위해 ValidationError 를 직접 던진다
    fake_validation_error = ValidationError.from_exception_data(
        "DocumentSchema",
        [{"type": "missing", "loc": ("pages",), "msg": "Field required", "input": {}}],
    )
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(side_effect=fake_validation_error)
    db = _make_mock_db()

    with (
        patch.object(
            DocumentServiceV2,
            "build_rag_context",
            new=AsyncMock(return_value=("", [])),
        ),
        patch(
            "app.modules.documents_v2.service.create_llm_client",
            return_value=llm_client,
        ),
        patch(
            "app.modules.documents_v2.service.get_provider_for_task",
            return_value="openai",
        ),
        pytest.raises(DocumentSchemaValidationError),
    ):
        await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="스키마 오류 유발",
            document_type="slide_report",
        )

    # 실패 row 저장 확인
    assert db.add.call_count == 1
    added = db.add.call_args.args[0]
    assert added.status == "error"


@pytest.mark.asyncio
async def test_generate_rejects_unknown_document_type():
    """지원 목록에 없는 document_type 은 즉시 거절한다."""
    db = _make_mock_db()

    with pytest.raises(DocumentGenerationError):
        await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="이상한 타입",
            document_type="unknown_type",
        )
    # 스키마 거절은 RAG / LLM / DB 전에 발생 (가드 성공)
    db.add.assert_not_called()
    db.flush.assert_not_called()


# ---------------------------------------------------------------------------
# 11. DocumentType 전수에 대해 build_system_prompt 가 각 타입 힌트를 포함하는지
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "document_type",
    [
        "slide_report",
        "docx_report",
        "proposal",
        "minutes",
        "one_pager",
        "weekly_status",
        "freeform_doc",
    ],
)
def test_build_system_prompt_covers_all_document_types(document_type: str):
    """7 타입 모두에서 build_system_prompt 가 정상적으로 문자열을 반환한다."""
    prompt = build_system_prompt(document_type)
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    # 카탈로그의 본문이 결과 프롬프트에 포함되어야 한다
    assert DOCUMENT_TYPE_SYSTEM_PROMPTS[document_type] in prompt
    # 공통 지침 (한국어) 도 포함
    assert "한국어" in prompt
