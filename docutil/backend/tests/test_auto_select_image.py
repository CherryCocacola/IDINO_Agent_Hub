"""Phase 4 S3 D3 — 이미지 자동 선택 (auto_select_image) 단위 테스트.

테스트 범위:
    1. Unsplash 성공 → URL 반환, DALL-E 미호출
    2. Unsplash 실패 → DALL-E 호출 + MinIO 업로드 → minio:// 스킴 반환
    3. prompt 빈 문자열 → ValueError
    4. 전체 실패 → None 반환 (degrade)
    5. DocumentServiceV2.generate 가 prompt-only ImageComponent 의 src 를
       자동으로 채워 넣는다 (통합 시나리오).
    6. src 가 이미 있는 ImageComponent 는 건드리지 않는다 (idempotent).

외부 호출 (httpx, MinIOService, DALL-E) 은 모두 mock 한다.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.image_generation import auto_select as auto_select_mod
from app.modules.documents_v2.schemas import DocumentSchema
from app.modules.documents_v2.service import DocumentServiceV2

ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


# ---------------------------------------------------------------------------
# 유틸: httpx.AsyncClient 를 context manager 로 mock 하는 헬퍼
# ---------------------------------------------------------------------------


def _make_httpx_client_mock(*, response_json: dict | None, status_raises: bool = False) -> MagicMock:
    """async httpx.AsyncClient 패치용 mock factory.

    ``async with httpx.AsyncClient(...) as http_client:`` 구문을 흉내내기 위해
    context manager 프로토콜을 구현한 mock 을 반환한다.
    """

    fake_response = MagicMock()
    fake_response.json = MagicMock(return_value=response_json or {"results": []})
    if status_raises:
        import httpx

        def _raise() -> None:
            raise httpx.HTTPError("fake http failure")

        fake_response.raise_for_status = MagicMock(side_effect=_raise)
    else:
        fake_response.raise_for_status = MagicMock(return_value=None)

    inner_client = MagicMock()
    inner_client.get = AsyncMock(return_value=fake_response)

    # async context manager
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner_client)
    cm.__aexit__ = AsyncMock(return_value=False)

    # httpx.AsyncClient(...) 을 호출했을 때 cm 을 반환하는 factory
    factory = MagicMock(return_value=cm)
    return factory


# ---------------------------------------------------------------------------
# 1. Unsplash 성공 → URL 반환, DALL-E 미호출
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_select_image_unsplash_success_returns_url_without_calling_dalle():
    fake_json = {
        "results": [
            {
                "id": "abc123",
                "urls": {"regular": "https://images.unsplash.com/photo-xyz"},
            }
        ]
    }
    http_factory = _make_httpx_client_mock(response_json=fake_json)

    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=b"should_not_be_called")

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
    ):
        httpx_mod.AsyncClient = http_factory
        # httpx.HTTPError 는 실제 클래스 유지 — except 분기용.
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        result = await auto_select_mod.auto_select_image(
            "office team meeting",
            alt="팀 미팅",
            organization_id=ORG_ID,
            service=fake_service,
        )

    assert result == "https://images.unsplash.com/photo-xyz"
    fake_service.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# 2. Unsplash 실패 → DALL-E 호출 + MinIO 업로드 → minio:// URL 반환
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_select_image_unsplash_empty_falls_back_to_dalle_and_uploads_to_minio():
    # Unsplash 는 빈 결과 (results: [])
    http_factory = _make_httpx_client_mock(response_json={"results": []})

    # DALL-E 는 바이트 반환
    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=b"\x89PNG\r\n\x1a\nFAKE")

    # MinIO upload_file spy
    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(return_value="irrelevant")

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
    ):
        httpx_mod.AsyncClient = http_factory
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        result = await auto_select_mod.auto_select_image(
            "Q1 sales chart with upward trend",
            alt="",
            organization_id=ORG_ID,
            service=fake_service,
            minio_service=fake_minio,
        )

    # 반환값은 minio:// 스킴이어야 한다
    assert result is not None
    assert result.startswith("minio://documents/generated_images/")
    assert result.endswith(".png")

    # DALL-E 가 호출되었다
    fake_service.generate.assert_awaited_once()
    call_kwargs = fake_service.generate.await_args.kwargs
    assert call_kwargs["provider"] == "dalle3"

    # MinIO 업로드도 호출되었다
    fake_minio.upload_file.assert_called_once()
    up_kwargs = fake_minio.upload_file.call_args.kwargs
    assert up_kwargs["bucket"] == "documents"
    assert up_kwargs["content_type"] == "image/png"
    assert up_kwargs["file_data"] == b"\x89PNG\r\n\x1a\nFAKE"


# ---------------------------------------------------------------------------
# 3. prompt 가 비어있으면 ValueError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_select_image_raises_value_error_when_prompt_blank():
    fake_service = MagicMock()
    fake_service.generate = AsyncMock()

    with pytest.raises(ValueError):
        await auto_select_mod.auto_select_image("", alt="alt", service=fake_service)

    with pytest.raises(ValueError):
        await auto_select_mod.auto_select_image("   ", alt="alt", service=fake_service)

    fake_service.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# 4. 모든 경로 실패 → None 반환 (예외 먹고 degrade)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_select_image_all_paths_fail_returns_none():
    # Unsplash: 빈 결과
    http_factory = _make_httpx_client_mock(response_json={"results": []})

    # DALL-E 도 None 반환 (API 키 미설정 시 실제 서비스가 None 을 돌려준다)
    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=None)

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
    ):
        httpx_mod.AsyncClient = http_factory
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        result = await auto_select_mod.auto_select_image(
            "fallback completely fails",
            alt="",
            service=fake_service,
        )

    assert result is None


# ---------------------------------------------------------------------------
# 5. DocumentServiceV2.generate 통합 — prompt-only Image 를 자동으로 채운다
# ---------------------------------------------------------------------------


def _make_schema_with_prompt_only_image() -> DocumentSchema:
    """prompt 만 있고 src 가 None 인 ImageComponent 를 포함하는 스키마."""

    now = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
    payload = {
        "document_id": str(uuid.uuid4()),
        "schema_version": "1.0",
        "type": "slide_report",
        "mode": "free_generation",
        "template_id": None,
        "design_tokens": {},
        "pages": [
            {
                "id": "p1",
                "page_kind": "slide",
                "layout": "content_body",
                "title": "팀",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": "우리 팀 소개",
                        "locked": False,
                        "anchor": None,
                    },
                    {
                        "id": "c2",
                        "type": "Image",
                        "src": None,
                        "prompt": "modern office team collaboration",
                        "alt": "팀 이미지",
                        "caption": None,
                        "locked": False,
                        "anchor": None,
                    },
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
            "citations": [],
            "degraded_components": [],
        },
    }
    return DocumentSchema.model_validate(payload)


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock(return_value=None)
    db.refresh = AsyncMock(return_value=None)
    db.get = AsyncMock(return_value=None)
    return db


@pytest.mark.asyncio
async def test_generate_injects_auto_selected_src_into_prompt_only_image_component():
    schema = _make_schema_with_prompt_only_image()
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
        patch(
            "app.modules.documents_v2.service.auto_select_image",
            new=AsyncMock(return_value="https://cdn.example.com/photo.jpg"),
        ) as mock_auto,
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="팀 소개 슬라이드",
            document_type="slide_report",
        )

    # auto_select_image 가 정확히 1회 호출되었다 (prompt-only 1건)
    mock_auto.assert_awaited_once()
    auto_kwargs = mock_auto.await_args.kwargs
    assert auto_kwargs["organization_id"] == ORG_ID

    # 저장된 schema 의 Image 컴포넌트 src 가 주입되었는지 확인
    stored_components = doc.document_schema["pages"][0]["components"]
    image_comp = next(c for c in stored_components if c["type"] == "Image")
    assert image_comp["src"] == "https://cdn.example.com/photo.jpg"
    # alt 는 그대로 유지 (스키마상 alt 는 min_length=1 이므로 LLM 이 채워 보냈을 것)
    assert image_comp["alt"] == "팀 이미지"


# ---------------------------------------------------------------------------
# 6. src 가 이미 있는 ImageComponent 는 건드리지 않는다 (idempotent)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_does_not_overwrite_existing_src_on_image_component():
    """src 가 이미 세팅된 ImageComponent 는 자동 선택이 건너뛰어야 한다."""

    # src 가 있고 prompt 도 있는 경우 — 자동 선택 대상 아님
    existing_src = "https://cdn.example.com/already-there.png"
    now = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
    payload = {
        "document_id": str(uuid.uuid4()),
        "schema_version": "1.0",
        "type": "slide_report",
        "mode": "free_generation",
        "template_id": None,
        "design_tokens": {},
        "pages": [
            {
                "id": "p1",
                "page_kind": "slide",
                "layout": "content_body",
                "title": None,
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "Image",
                        "src": existing_src,
                        "prompt": "unused fallback prompt",
                        "alt": "기존 alt",
                        "caption": None,
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
            "citations": [],
            "degraded_components": [],
        },
    }
    schema = DocumentSchema.model_validate(payload)

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
        patch(
            "app.modules.documents_v2.service.auto_select_image",
            new=AsyncMock(return_value="https://should.not/be.used"),
        ) as mock_auto,
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="자동 선택 스킵 시나리오",
            document_type="slide_report",
        )

    # auto_select_image 는 호출되지 않아야 한다
    mock_auto.assert_not_awaited()

    stored_components = doc.document_schema["pages"][0]["components"]
    image_comp = next(c for c in stored_components if c["type"] == "Image")
    assert image_comp["src"] == existing_src
    assert image_comp["alt"] == "기존 alt"


# ---------------------------------------------------------------------------
# 7. Phase 4 S3 D5 — 쿼터 초과 시 DalleQuotaExceededError 발생
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_select_image_raises_quota_exceeded_when_quota_denied():
    """Unsplash 실패 후 DALL-E fallback 직전 쿼터 체크 False → 예외."""

    # Unsplash 는 빈 결과 (DALL-E fallback 으로 진행)
    http_factory = _make_httpx_client_mock(response_json={"results": []})

    # DALL-E 는 호출되면 안 된다 (쿼터 체크에서 차단).
    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=b"NEVER_CALLED")

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    fake_db = MagicMock()  # AsyncSession stand-in — check_and_consume_quota 가 mock.

    # QuotaService.check_and_consume_quota → False (쿼터 초과).
    from app.integrations.image_generation.auto_select import DalleQuotaExceededError

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
        patch(
            "app.modules.organizations.service.QuotaService.check_and_consume_quota",
            new=AsyncMock(return_value=False),
        ) as mock_quota,
    ):
        httpx_mod.AsyncClient = http_factory
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        with pytest.raises(DalleQuotaExceededError):
            await auto_select_mod.auto_select_image(
                "quota exceeded scenario",
                alt="",
                organization_id=ORG_ID,
                db=fake_db,
                service=fake_service,
            )

    # 쿼터 서비스가 dalle_monthly 로 호출되었고 DALL-E 는 호출되지 않았다.
    mock_quota.assert_awaited_once()
    call_kwargs = mock_quota.await_args.kwargs
    assert call_kwargs["organization_id"] == ORG_ID
    assert call_kwargs["quota_type"] == "dalle_monthly"
    assert call_kwargs["amount"] == 1
    fake_service.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_auto_select_image_consumes_quota_when_available_and_calls_dalle():
    """쿼터 잔여 → check_and_consume 성공 → DALL-E 호출 + MinIO 업로드."""

    http_factory = _make_httpx_client_mock(response_json={"results": []})

    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=b"\x89PNGFAKE")

    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(return_value="irrelevant")

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    fake_db = MagicMock()

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
        patch(
            "app.modules.organizations.service.QuotaService.check_and_consume_quota",
            new=AsyncMock(return_value=True),
        ) as mock_quota,
    ):
        httpx_mod.AsyncClient = http_factory
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        result = await auto_select_mod.auto_select_image(
            "quota available scenario",
            alt="",
            organization_id=ORG_ID,
            db=fake_db,
            service=fake_service,
            minio_service=fake_minio,
        )

    assert result is not None
    assert result.startswith("minio://documents/generated_images/")
    mock_quota.assert_awaited_once()
    fake_service.generate.assert_awaited_once()
    fake_minio.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_auto_select_image_skips_quota_check_when_db_not_provided():
    """db=None 이면 쿼터 체크 skip — 기존 D3 호환 경로 유지."""

    http_factory = _make_httpx_client_mock(response_json={"results": []})
    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value=b"\x89PNGFAKE")

    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(return_value="irrelevant")

    fake_settings = MagicMock()
    fake_settings.unsplash_access_key = "test-key"
    fake_settings.minio_bucket = "documents"

    with (
        patch.object(auto_select_mod, "httpx") as httpx_mod,
        patch.object(auto_select_mod, "get_settings", return_value=fake_settings),
        patch(
            "app.modules.organizations.service.QuotaService.check_and_consume_quota",
            new=AsyncMock(return_value=False),
        ) as mock_quota,
    ):
        httpx_mod.AsyncClient = http_factory
        import httpx as _real_httpx

        httpx_mod.HTTPError = _real_httpx.HTTPError

        result = await auto_select_mod.auto_select_image(
            "no-db scenario",
            alt="",
            organization_id=ORG_ID,
            # db 전달 안 함 — 쿼터 체크 skip.
            service=fake_service,
            minio_service=fake_minio,
        )

    # 쿼터 서비스는 전혀 호출되지 않아야 한다.
    mock_quota.assert_not_awaited()
    # DALL-E 는 정상 호출된다.
    fake_service.generate.assert_awaited_once()
    assert result is not None
    assert result.startswith("minio://documents/generated_images/")


# ---------------------------------------------------------------------------
# 8. generate 통합 — 쿼터 초과 시 해당 이미지만 soft degrade + id 기록
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_soft_degrades_image_on_quota_exceeded():
    """쿼터 초과 이미지는 src=None 유지 + metadata.degraded_components 에 id."""

    from app.integrations.image_generation.auto_select import DalleQuotaExceededError

    schema = _make_schema_with_prompt_only_image()
    # 해당 스키마의 이미지 컴포넌트 id 는 'c2'.
    llm_client = MagicMock()
    llm_client.generate_with_schema = AsyncMock(return_value=schema)

    db = _make_mock_db()

    # auto_select_image 자체를 mock 해서 DalleQuotaExceededError 를 던지게 한다.
    async def _raise_quota_exceeded(*_args, **_kwargs):
        raise DalleQuotaExceededError(ORG_ID)

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
        patch(
            "app.modules.documents_v2.service.auto_select_image",
            new=_raise_quota_exceeded,
        ),
    ):
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=USER_ID,
            org_id=ORG_ID,
            prompt="쿼터 초과 soft degrade 시나리오",
            document_type="slide_report",
        )

    # 문서 자체는 생성 성공 (status=completed).
    assert doc.status == "completed"

    # 이미지 컴포넌트의 src 는 여전히 None 이어야 한다.
    stored_components = doc.document_schema["pages"][0]["components"]
    image_comp = next(c for c in stored_components if c["type"] == "Image")
    assert image_comp["src"] is None

    # metadata.degraded_components 에 이미지 컴포넌트 id 가 기록되었다.
    degraded = doc.document_schema["metadata"]["degraded_components"]
    assert "c2" in degraded
