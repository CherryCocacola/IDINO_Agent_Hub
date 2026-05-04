"""Phase 4 S2 D4~D5 — documents_v2 export 작업 라우터 + worker 테스트.

검증 범위:
D4 기준 (1~9):
1. POST /v2/documents/{id}/export 성공 (202 + job_id).
2. 문서 없음 → 404.
3. 타 조직 문서 → 403.
4. 미지원 포맷 → 422.
5. GET /v2/documents/exports/{job_id} 성공 (200 + status).
6. 존재하지 않는 job_id → 404.
7. Worker unit: generate_document_export 가 BuilderRegistry.get("pptx").build()
   를 호출하여 Redis 상태를 completed 로 전이 + MinIO 업로드 + presigned URL.
8. Worker unit: build 실패 시 Redis 상태가 failed 로 기록되고 예외 재-raise.
9. 타 사용자 job_id 조회 → 403.

D5 신규 (10~14):
10. Worker unit: 성공 경로에서 MinIOService.upload_file 이 올바른 버킷/키/
    content-type 으로 호출된다.
11. Worker unit: presigned URL 이 Redis `download_url` 에 정확히 기록된다.
12. Worker unit: 성공 후 tmp 파일이 삭제된다 (Path.exists()==False).
13. Worker unit: MinIO 업로드 실패 시 상태 `failed` + error 한국어 기록 +
    예외 재-raise.
14. Worker unit: MinIO 실패 시에도 tmp 파일 cleanup 이 호출된다.

Redis 는 실제 접속하지 않고 `get_redis` 를 AsyncMock 으로 교체하며, Celery 는
`CELERY_TASK_ALWAYS_EAGER=True` 대신 `.delay()` 자체를 mock 하여 dispatch 만 검증.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import TEST_ORG_ID, TEST_USER_ID

ROUTE_POST_EXPORT = "/api/v1/v2/documents/{id}/export"
ROUTE_GET_STATUS = "/api/v1/v2/documents/exports/{job_id}"


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------


def _make_mock_doc(
    *,
    doc_id: uuid.UUID,
    org_id: uuid.UUID = TEST_ORG_ID,
) -> MagicMock:
    """request_export 경로에서 조회되는 DocumentV2 mock."""
    doc = MagicMock()
    doc.id = doc_id
    doc.organization_id = org_id
    # 최소 유효 document_schema — worker unit 테스트에서 재사용.
    doc.document_schema = {
        "document_id": str(doc_id),
        "schema_version": "1.0",
        "type": "slide_report",
        "mode": "free_generation",
        "template_id": None,
        "design_tokens": {
            "primary_color": "#0A4FC2",
            "accent_color": "#FF6B35",
            "text_color": "#1F2937",
            "background_color": "#FFFFFF",
            "font_family": "Pretendard",
            "spacing": "normal",
            "brand_preset": "idino_default",
        },
        "pages": [
            {
                "id": "p1",
                "page_kind": "slide",
                "layout": "title_slide",
                "title": "테스트",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": "테스트",
                        "locked": False,
                        "anchor": None,
                    }
                ],
            }
        ],
        "metadata": {
            "created_at": "2026-04-19T10:00:00+00:00",
            "updated_at": "2026-04-19T10:00:00+00:00",
            "generated_by_user_id": str(TEST_USER_ID),
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "prompt_tokens": None,
            "completion_tokens": None,
            "source_document_ids": [],
            "source_chat_session_id": None,
            "citations": [],
            "degraded_components": [],
        },
    }
    return doc


class _FakeAsyncRedis:
    """테스트용 인메모리 async Redis 대체체 (set/get/ex 만 지원)."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.store[key] = value

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


# ---------------------------------------------------------------------------
# 1. POST export — 성공 202
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_export_returns_202_with_job_id(client, db_session):
    """정상 케이스: 문서 존재 + dispatch 성공 → 202 + UUID job_id."""
    target_id = uuid.uuid4()
    fake_doc = _make_mock_doc(doc_id=target_id)

    async def fake_get(model, pk):  # noqa: ARG001
        assert pk == target_id
        return fake_doc

    fake_redis = _FakeAsyncRedis()

    with (
        patch.object(db_session, "get", new=fake_get),
        patch(
            "app.core.cache.get_redis",
            new=AsyncMock(return_value=fake_redis),
        ),
        patch(
            "app.workers.export_worker.generate_document_export.delay",
            return_value=MagicMock(id="celery-task-id"),
        ) as mock_delay,
    ):
        response = await client.post(
            ROUTE_POST_EXPORT.format(id=target_id),
            json={"format": "pptx"},
        )

    assert response.status_code == 202, response.text
    body = response.json()
    assert "job_id" in body
    # UUID 형식 검증 (Pydantic 이 validate 하지만 이중 안전장치).
    uuid.UUID(body["job_id"])

    # Celery dispatch 호출 확인.
    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs["document_id"] == str(target_id)
    assert kwargs["format"] == "pptx"

    # Redis 에 pending 상태가 저장되었는지 확인.
    keys = [k for k in fake_redis.store if k.startswith("export_job:")]
    assert len(keys) == 1
    state = json.loads(fake_redis.store[keys[0]])
    assert state["status"] == "pending"
    assert state["document_id"] == str(target_id)
    assert state["format"] == "pptx"


# ---------------------------------------------------------------------------
# 2. POST export — 문서 없음 → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_export_returns_404_when_document_missing(client, db_session):
    """db.get 이 None 을 반환 → 404."""
    target_id = uuid.uuid4()

    async def fake_get(model, pk):  # noqa: ARG001
        return None

    with (
        patch.object(db_session, "get", new=fake_get),
        patch(
            "app.core.cache.get_redis",
            new=AsyncMock(return_value=_FakeAsyncRedis()),
        ),
    ):
        response = await client.post(
            ROUTE_POST_EXPORT.format(id=target_id),
            json={"format": "pptx"},
        )

    assert response.status_code == 404
    assert "찾을 수 없" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 3. POST export — 타 조직 문서 → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_export_returns_403_for_other_org_document(client, db_session):
    """문서가 존재하지만 organization_id 가 다르면 403."""
    target_id = uuid.uuid4()
    other_org = uuid.UUID("99999999-9999-9999-9999-999999999999")
    fake_doc = _make_mock_doc(doc_id=target_id, org_id=other_org)

    async def fake_get(model, pk):  # noqa: ARG001
        return fake_doc

    with (
        patch.object(db_session, "get", new=fake_get),
        patch(
            "app.core.cache.get_redis",
            new=AsyncMock(return_value=_FakeAsyncRedis()),
        ),
    ):
        response = await client.post(
            ROUTE_POST_EXPORT.format(id=target_id),
            json={"format": "pptx"},
        )

    assert response.status_code == 403
    assert "다른 조직" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 4. POST export — 미지원 포맷 → 422 (Pydantic) 또는 400
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_export_rejects_unsupported_format(client):
    """Pydantic Literal 검증 단계에서 거부되어 422 로 반환된다.

    ExportFormat Literal 은 (pptx/docx/hwpx/pdf/html) 로 고정이므로 그 외 값은
    FastAPI 가 422 Unprocessable Entity 를 돌려준다. 서비스 레이어의
    "지원하지 않는 문서 포맷입니다" 400 경로는 빌더 Registry 에 아직 등록되지
    않은 포맷 (현재 BuildTarget 값이지만 runtime 등록 안 된 경우) 에서만 도달.
    """
    target_id = uuid.uuid4()
    response = await client.post(
        ROUTE_POST_EXPORT.format(id=target_id),
        json={"format": "xlsx"},  # BuildTarget 에 없는 값.
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 5. GET status — 성공 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_returns_200_with_running_state(client):
    """Redis 에 running 상태가 있으면 200 + 해당 뷰."""
    job_id = uuid.uuid4()
    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = json.dumps(
        {
            "status": "running",
            "progress": 10,
            "document_id": str(uuid.uuid4()),
            "user_id": str(TEST_USER_ID),
            "org_id": str(TEST_ORG_ID),
            "format": "pptx",
            "result_key": None,
            "download_url": None,
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_GET_STATUS.format(job_id=job_id))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "running"
    assert body["progress"] == 10
    assert body["download_url"] is None
    assert body["error"] is None


# ---------------------------------------------------------------------------
# 6. GET status — 존재하지 않는 job_id → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_returns_404_for_missing_job(client):
    """Redis 에 키가 없으면 404."""
    job_id = uuid.uuid4()
    fake_redis = _FakeAsyncRedis()  # 비어 있음

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_GET_STATUS.format(job_id=job_id))

    assert response.status_code == 404
    assert "찾을 수 없" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 7. GET status — 타 사용자 job → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_status_returns_403_for_other_user_job(client):
    """다른 사용자가 만든 job 조회 시도 → 403."""
    job_id = uuid.uuid4()
    other_user = uuid.UUID("77777777-7777-7777-7777-777777777777")
    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = json.dumps(
        {
            "status": "running",
            "progress": 50,
            "document_id": str(uuid.uuid4()),
            "user_id": str(other_user),  # 요청자 ≠ 소유자
            "org_id": str(TEST_ORG_ID),
            "format": "pptx",
            "result_key": None,
            "download_url": None,
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_GET_STATUS.format(job_id=job_id))

    assert response.status_code == 403
    assert "다른 사용자" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 8. Worker unit — 성공 경로
# ---------------------------------------------------------------------------


def test_worker_generate_document_export_calls_builder_and_writes_completed_state(tmp_path):
    """generate_document_export 가 BuilderRegistry.get("pptx").build() 를 호출하고
    Redis 상태를 completed 로 전이하는지 확인.

    D5 확장: MinIO 업로드까지 완료되어 `download_url` 이 채워지고 `progress=100`.

    Celery 태스크의 sync 경로만 검증하므로 실제 async 이벤트 루프는 worker 내부의
    `asyncio.run()` 이 담당한다. MinIOService 는 모듈 경로 전체를 mock 해 실제
    Minio SDK 로 접속하지 않는다.
    """
    from app.workers import export_worker as ew

    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    # ---- Redis mock (in-memory) ---------------------------------------
    redis_store: dict[str, str] = {}

    class _FakeSyncRedis:
        def get(self, key: str) -> str | None:
            return redis_store.get(key)

        def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
            redis_store[key] = value

    fake_sync_redis = _FakeSyncRedis()

    # ---- DB loader mock: document_schema dict 반환 --------------------
    fake_doc = _make_mock_doc(doc_id=uuid.UUID(document_id))
    schema_dict = fake_doc.document_schema

    # ---- Builder mock: 고정 bytes 반환 --------------------------------
    fake_builder = MagicMock()

    async def _fake_build(schema):  # noqa: ARG001
        return b"FAKE-PPTX-BYTES"

    fake_builder.build = _fake_build

    # ---- MinIOService mock --------------------------------------------
    # worker 내부는 `from app.integrations.object_storage import MinIOService`
    # 경로로 지연 import — 동일 경로에서 클래스를 교체한다.
    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(return_value="dummy-object-name")
    fake_minio.get_presigned_url = MagicMock(
        return_value="http://minio.local/documents/documents_v2/exports/xxx.pptx?X-Amz-Signature=abc"
    )

    # Celery eager mode 로 동기 실행 — autoretry 래퍼와 bind 인자 주입을
    # 모두 Celery 가 담당하므로 테스트 쪽에서 self 를 수동 생성할 필요가 없다.
    ew.celery_app.conf.task_always_eager = True
    ew.celery_app.conf.task_eager_propagates = True

    try:
        with (
            patch.object(ew, "_get_sync_redis", return_value=fake_sync_redis),
            patch.object(ew, "_load_document_schema_sync", return_value=schema_dict),
            patch(
                "app.integrations.document_builders.base.BuilderRegistry.get",
                return_value=fake_builder,
            ),
            # tempfile 디렉터리를 테스트 전용으로 고정.
            patch("app.workers.export_worker.tempfile.gettempdir", return_value=str(tmp_path)),
            # MinIOService 는 패키지 __init__ 을 통한 re-export 를 mock.
            patch(
                "app.integrations.object_storage.MinIOService",
                return_value=fake_minio,
            ),
        ):
            async_result = ew.generate_document_export.apply(
                kwargs={
                    "job_id": job_id,
                    "document_id": document_id,
                    "format": "pptx",
                }
            )
            result = async_result.get()
    finally:
        ew.celery_app.conf.task_always_eager = False
        ew.celery_app.conf.task_eager_propagates = False

    # ---- 검증: Celery 반환값 -------------------------------------------
    assert result["job_id"] == job_id
    assert result["format"] == "pptx"
    assert result["bytes"] == len(b"FAKE-PPTX-BYTES")
    assert "result_key" in result
    # D10: download_url 은 API 프록시 상대 경로 (presigned URL 아님).
    assert "download_url" in result
    assert result["download_url"] == f"/api/v1/v2/documents/exports/{job_id}/download"

    # ---- 검증: Redis 상태 (D10) ----------------------------------------
    key = f"export_job:{job_id}"
    assert key in redis_store
    state = json.loads(redis_store[key])
    assert state["status"] == "completed"
    assert state["progress"] == ew.PROGRESS_COMPLETED  # 100
    # result_key 는 MinIO object key 형식 (내부 조회용).
    assert state["result_key"].startswith("documents_v2/exports/")
    assert state["result_key"].endswith(".pptx")
    # D10 정책: download_url 은 프록시 엔드포인트 상대 경로이며 presigned URL
    # (내부 hostname 포함) 은 더 이상 내려가지 않는다.
    assert state["download_url"] == f"/api/v1/v2/documents/exports/{job_id}/download"
    assert "X-Amz-Signature" not in state["download_url"]
    assert "minio:" not in state["download_url"]


# ---------------------------------------------------------------------------
# 9. Worker unit — build 실패 시 failed 상태 + re-raise
# ---------------------------------------------------------------------------


def test_worker_generate_document_export_records_failed_state_on_build_error():
    """빌더 예외 발생 시 Redis 상태 `failed` 기록 + 예외 재-raise."""
    from app.workers import export_worker as ew

    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    redis_store: dict[str, str] = {}

    class _FakeSyncRedis:
        def get(self, key: str) -> str | None:
            return redis_store.get(key)

        def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
            redis_store[key] = value

    fake_sync_redis = _FakeSyncRedis()
    fake_doc = _make_mock_doc(doc_id=uuid.UUID(document_id))

    fake_builder = MagicMock()

    async def _failing_build(schema):  # noqa: ARG001
        raise RuntimeError("빌더 폭발")

    fake_builder.build = _failing_build

    # Celery eager + max_retries=0 로 조정해 즉시 failed 가 되도록 강제.
    # (기본 max_retries=2 면 eager 로도 재시도 → 테스트 지연)
    original_max_retries = ew.generate_document_export.max_retries
    ew.generate_document_export.max_retries = 0
    ew.celery_app.conf.task_always_eager = True
    ew.celery_app.conf.task_eager_propagates = True

    try:
        with (
            patch.object(ew, "_get_sync_redis", return_value=fake_sync_redis),
            patch.object(ew, "_load_document_schema_sync", return_value=fake_doc.document_schema),
            patch(
                "app.integrations.document_builders.base.BuilderRegistry.get",
                return_value=fake_builder,
            ),
            pytest.raises(RuntimeError, match="빌더 폭발"),
        ):
            async_result = ew.generate_document_export.apply(
                kwargs={
                    "job_id": job_id,
                    "document_id": document_id,
                    "format": "pptx",
                }
            )
            async_result.get()
    finally:
        ew.generate_document_export.max_retries = original_max_retries
        ew.celery_app.conf.task_always_eager = False
        ew.celery_app.conf.task_eager_propagates = False

    # 상태가 failed 로 기록되었는지.
    key = f"export_job:{job_id}"
    assert key in redis_store
    state = json.loads(redis_store[key])
    assert state["status"] == "failed"
    assert "빌더 폭발" in (state.get("error") or "")


# ---------------------------------------------------------------------------
# D5 신규 테스트용 공통 헬퍼
# ---------------------------------------------------------------------------


class _FakeSyncRedisStore:
    """D5 신규 워커 테스트에서 재사용하는 인메모리 Redis 대체체."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.store[key] = value


def _run_export_task_with_mocks(
    *,
    job_id: str,
    document_id: str,
    fmt: str,
    tmp_path,
    build_bytes: bytes = b"FAKE-PPTX-BYTES",
    fake_minio: MagicMock | None = None,
    builder_raises: Exception | None = None,
    max_retries: int = 0,
):
    """D5 테스트 공통 실행 루틴 — Celery eager 로 태스크를 돌린다.

    Returns:
        (async_result | None, redis_store_dict, fake_minio) — builder 가 예외
        경로로 끝나면 첫 번째 요소는 None.
    """
    from app.workers import export_worker as ew

    fake_redis_obj = _FakeSyncRedisStore()
    fake_doc = _make_mock_doc(doc_id=uuid.UUID(document_id))

    fake_builder = MagicMock()

    async def _build(schema):  # noqa: ARG001
        if builder_raises is not None:
            raise builder_raises
        return build_bytes

    fake_builder.build = _build

    if fake_minio is None:
        fake_minio = MagicMock()
        fake_minio.upload_file = MagicMock(return_value="obj")
        fake_minio.get_presigned_url = MagicMock(return_value="http://minio.local/signed?X-Amz-Signature=xyz")

    original_max_retries = ew.generate_document_export.max_retries
    ew.generate_document_export.max_retries = max_retries
    ew.celery_app.conf.task_always_eager = True
    ew.celery_app.conf.task_eager_propagates = True

    result = None
    try:
        with (
            patch.object(ew, "_get_sync_redis", return_value=fake_redis_obj),
            patch.object(ew, "_load_document_schema_sync", return_value=fake_doc.document_schema),
            patch(
                "app.integrations.document_builders.base.BuilderRegistry.get",
                return_value=fake_builder,
            ),
            patch(
                "app.workers.export_worker.tempfile.gettempdir",
                return_value=str(tmp_path),
            ),
            patch(
                "app.integrations.object_storage.MinIOService",
                return_value=fake_minio,
            ),
        ):
            try:
                async_result = ew.generate_document_export.apply(
                    kwargs={
                        "job_id": job_id,
                        "document_id": document_id,
                        "format": fmt,
                    }
                )
                result = async_result.get()
            except Exception:  # noqa: BLE001 — 테스트 헬퍼 — 상위 assert 에서 검증
                result = None
    finally:
        ew.generate_document_export.max_retries = original_max_retries
        ew.celery_app.conf.task_always_eager = False
        ew.celery_app.conf.task_eager_propagates = False

    return result, fake_redis_obj.store, fake_minio


# ---------------------------------------------------------------------------
# 10. D5 — MinIO upload_file 이 올바른 인자로 호출된다
# ---------------------------------------------------------------------------


def test_worker_uploads_to_minio_with_correct_bucket_key_and_content_type(tmp_path):
    """성공 경로에서 MinIOService.upload_file 이 documents_v2/exports/{doc}/{job}.pptx
    object key + PPTX MIME 타입으로 호출되는지 검증한다."""
    from app.core.config import get_settings
    from app.workers import export_worker as ew

    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    result, redis_store, fake_minio = _run_export_task_with_mocks(
        job_id=job_id,
        document_id=document_id,
        fmt="pptx",
        tmp_path=tmp_path,
    )

    assert result is not None
    fake_minio.upload_file.assert_called_once()
    kwargs = fake_minio.upload_file.call_args.kwargs

    # 버킷: settings.minio_bucket 과 일치.
    assert kwargs["bucket"] == get_settings().minio_bucket
    # object_name: documents_v2/exports/{doc}/{job}.pptx
    assert kwargs["object_name"] == f"documents_v2/exports/{document_id}/{job_id}.pptx"
    # content_type: PPTX OOXML MIME
    assert kwargs["content_type"] == ew.FORMAT_CONTENT_TYPE["pptx"]
    assert kwargs["content_type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    # file_data 는 빌더가 반환한 bytes 그대로.
    assert kwargs["file_data"] == b"FAKE-PPTX-BYTES"


# ---------------------------------------------------------------------------
# 11. D10 — download_url 은 API 프록시 경로, presigned URL 은 발급되지 않는다
# ---------------------------------------------------------------------------


def test_worker_writes_proxy_download_url_and_skips_presigned(tmp_path):
    """D10 W4 블로커 해소 회귀 테스트.

    - Redis `download_url` 은 `/api/v1/v2/documents/exports/{job_id}/download`
      상대 경로여야 한다 (Docker 내부 hostname 노출 금지).
    - 성공 경로에서는 `get_presigned_url` 이 호출되지 않아야 한다 (업로드만 수행).
    - 반환 dict 의 download_url 도 동일한 상대 경로.
    """
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    # get_presigned_url 은 호출되지 않아야 하지만, 호출될 경우를 대비해
    # 식별 가능한 반환값을 남겨 assert 로 걸러낸다.
    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(return_value="obj")
    fake_minio.get_presigned_url = MagicMock(return_value="SHOULD-NOT-BE-USED?X-Amz-Signature=forbidden")

    result, redis_store, _ = _run_export_task_with_mocks(
        job_id=job_id,
        document_id=document_id,
        fmt="pptx",
        tmp_path=tmp_path,
        fake_minio=fake_minio,
    )

    assert result is not None
    # D10 정책: presigned URL 은 발급하지 않는다.
    fake_minio.get_presigned_url.assert_not_called()

    # Redis 에 최종 download_url 은 API 프록시 상대 경로.
    expected_proxy = f"/api/v1/v2/documents/exports/{job_id}/download"
    key = f"export_job:{job_id}"
    state = json.loads(redis_store[key])
    assert state["download_url"] == expected_proxy
    assert state["status"] == "completed"
    assert state["progress"] == 100
    # 내부 hostname / 서명 파라미터가 노출되지 않아야 한다.
    assert "minio:" not in state["download_url"]
    assert "X-Amz-Signature" not in state["download_url"]
    # Celery 반환값 dict 에도 동일 경로.
    assert result["download_url"] == expected_proxy


# ---------------------------------------------------------------------------
# 12. D5 — 업로드 성공 후 tmp 파일이 삭제된다
# ---------------------------------------------------------------------------


def test_worker_cleans_up_tmp_file_after_successful_upload(tmp_path):
    """업로드 성공 경로에서 tmp 파일이 디스크에 남지 않는지 확인.

    worker 는 `tempfile.gettempdir()/docutil_exports/{job_id}.pptx` 경로에 쓴 뒤
    업로드 후 즉시 제거해야 한다.
    """
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    result, _, _ = _run_export_task_with_mocks(
        job_id=job_id,
        document_id=document_id,
        fmt="pptx",
        tmp_path=tmp_path,
    )

    assert result is not None
    expected_tmp = tmp_path / "docutil_exports" / f"{job_id}.pptx"
    # Path.exists() 로 확인 — _cleanup_tmp_file 이 os.remove 를 호출해 제거한다.
    assert not expected_tmp.exists(), f"성공 경로에서 tmp 파일이 제거되지 않았습니다: {expected_tmp}"


# ---------------------------------------------------------------------------
# 13. D5 — MinIO 업로드 실패 시 Redis 상태 failed + 한국어 에러 + 재-raise
# ---------------------------------------------------------------------------


def test_worker_records_failed_state_when_minio_upload_fails(tmp_path):
    """MinIO.upload_file 이 예외를 던지면 상태가 failed 로 기록되고 태스크는
    재-raise 해야 한다. 에러 메시지는 한국어로 "스토리지에 업로드하지 못했습니다"
    를 포함한다."""
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(side_effect=RuntimeError("S3 연결 거부"))
    # get_presigned_url 은 호출될 일이 없지만 안전망으로 둔다.
    fake_minio.get_presigned_url = MagicMock(return_value="should-not-be-used")

    result, redis_store, _ = _run_export_task_with_mocks(
        job_id=job_id,
        document_id=document_id,
        fmt="pptx",
        tmp_path=tmp_path,
        fake_minio=fake_minio,
    )

    # 헬퍼가 예외를 삼켜 result=None 으로 반환 (위의 try/except).
    assert result is None

    key = f"export_job:{job_id}"
    state = json.loads(redis_store[key])
    assert state["status"] == "failed"
    # 한국어 에러 메시지 포함 — 원인 세부 문자열도 함께.
    assert "스토리지에 업로드하지 못했습니다" in (state.get("error") or "")
    assert "S3 연결 거부" in (state.get("error") or "")
    # download_url 은 채워지지 않아야 한다.
    assert state.get("download_url") is None


# ---------------------------------------------------------------------------
# 14. D5 — MinIO 실패 시에도 tmp 파일은 반드시 제거된다
# ---------------------------------------------------------------------------


def test_worker_cleans_up_tmp_file_even_on_minio_failure(tmp_path):
    """업로드 실패 시에도 tmp 파일이 누수되지 않아야 한다 (try/finally 보장)."""
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    fake_minio = MagicMock()
    fake_minio.upload_file = MagicMock(side_effect=OSError("MinIO 5xx"))
    fake_minio.get_presigned_url = MagicMock()

    _, _, _ = _run_export_task_with_mocks(
        job_id=job_id,
        document_id=document_id,
        fmt="pptx",
        tmp_path=tmp_path,
        fake_minio=fake_minio,
    )

    expected_tmp = tmp_path / "docutil_exports" / f"{job_id}.pptx"
    assert not expected_tmp.exists(), f"MinIO 실패 경로에서도 tmp 파일이 제거돼야 하는데 남아 있음: {expected_tmp}"


# ---------------------------------------------------------------------------
# Phase 4 S2 D10 — /exports/{job_id}/download 프록시 엔드포인트 테스트
# ---------------------------------------------------------------------------
#
# W4 블로커 (Docker 내부 hostname 의 presigned URL 이 FE 에서 resolve 불가) 를
# 해소하기 위해 도입된 엔드포인트. 다음 6 케이스로 전체 계약을 검증한다.
#
#  15. 200 + PPTX MIME + RFC 5987 한글 파일명 헤더
#  16. 존재하지 않는 job_id → 404
#  17. 완료되지 않은 job (running) → 409 Conflict
#  18. 타 조직 job → 403
#  19. MinIO NoSuchKey (object 만료) → 410 Gone
#  20. /exports/{job_id} 응답의 download_url 이 프록시 상대 경로 형식

ROUTE_DOWNLOAD = "/api/v1/v2/documents/exports/{job_id}/download"


def _completed_state(
    *,
    job_id: str,
    document_id: str,
    user_id: uuid.UUID = TEST_USER_ID,
    org_id: uuid.UUID = TEST_ORG_ID,
    fmt: str = "pptx",
    result_key: str | None = None,
) -> str:
    """`completed` 상태의 Redis 값 JSON 문자열을 조립한다."""
    key = result_key or f"documents_v2/exports/{document_id}/{job_id}.{fmt}"
    return json.dumps(
        {
            "status": "completed",
            "progress": 100,
            "document_id": document_id,
            "user_id": str(user_id),
            "org_id": str(org_id),
            "format": fmt,
            "result_key": key,
            "download_url": f"/api/v1/v2/documents/exports/{job_id}/download",
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# 15. GET /download — 200 + PPTX bytes + Content-Disposition 헤더
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_export_returns_200_with_pptx_bytes_and_headers(client):
    """completed 상태 + MinIO bytes 반환 → 200 + 올바른 MIME + attachment 헤더."""
    job_id = uuid.uuid4()
    document_id = uuid.uuid4()

    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = _completed_state(
        job_id=str(job_id),
        document_id=str(document_id),
    )

    # MinIOService 는 서비스가 `app.integrations.object_storage.MinIOService`
    # 경로로 import 하므로 동일 경로를 mock.
    fake_minio = MagicMock()
    fake_minio.get_object_bytes = MagicMock(return_value=b"FAKE-PPTX-BYTES")

    with (
        patch(
            "app.core.cache.get_redis",
            new=AsyncMock(return_value=fake_redis),
        ),
        patch(
            "app.integrations.object_storage.MinIOService",
            return_value=fake_minio,
        ),
    ):
        response = await client.get(ROUTE_DOWNLOAD.format(job_id=job_id))

    assert response.status_code == 200, response.text
    # PPTX OOXML MIME
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    # body bytes 일치
    assert response.content == b"FAKE-PPTX-BYTES"
    # Content-Disposition 은 RFC 5987 (``filename*=UTF-8''...``)
    cd = response.headers["content-disposition"]
    assert cd.startswith("attachment;")
    assert "filename*=UTF-8''" in cd
    # 기본 파일명: {document_id}.pptx
    assert f"{document_id}.pptx" in cd

    # MinIO 호출 인자 검증
    fake_minio.get_object_bytes.assert_called_once()
    call_kwargs = fake_minio.get_object_bytes.call_args.kwargs
    assert call_kwargs["object_name"].endswith(f"{job_id}.pptx")


# ---------------------------------------------------------------------------
# 16. GET /download — 존재하지 않는 job → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_export_returns_404_when_job_missing(client):
    """Redis 에 키가 없으면 404 (TTL 만료 또는 잘못된 job_id)."""
    job_id = uuid.uuid4()
    fake_redis = _FakeAsyncRedis()  # 비어 있음

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_DOWNLOAD.format(job_id=job_id))

    assert response.status_code == 404
    assert "찾을 수 없" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 17. GET /download — 완료되지 않은 작업 → 409 Conflict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_export_returns_409_when_not_completed(client):
    """status=running 인 job 을 다운로드 시도하면 409 Conflict.

    FE 는 409 를 받으면 폴링을 재개하도록 분기할 수 있다 (404 와 구분 필요).
    """
    job_id = uuid.uuid4()
    document_id = uuid.uuid4()
    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = json.dumps(
        {
            "status": "running",
            "progress": 50,
            "document_id": str(document_id),
            "user_id": str(TEST_USER_ID),
            "org_id": str(TEST_ORG_ID),
            "format": "pptx",
            "result_key": None,
            "download_url": None,
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_DOWNLOAD.format(job_id=job_id))

    assert response.status_code == 409
    assert "완료되지 않은" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 18. GET /download — 타 조직 job → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_export_returns_403_for_other_org_job(client):
    """다른 조직이 만든 job 조회 시도 → 403."""
    job_id = uuid.uuid4()
    document_id = uuid.uuid4()
    other_org = uuid.UUID("99999999-9999-9999-9999-999999999999")

    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = _completed_state(
        job_id=str(job_id),
        document_id=str(document_id),
        org_id=other_org,  # 요청자 ≠ 소유자 조직
    )

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_DOWNLOAD.format(job_id=job_id))

    assert response.status_code == 403
    assert "다른 조직" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 19. GET /download — MinIO NoSuchKey → 410 Gone
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_export_returns_410_when_object_expired(client):
    """MinIO 에 object 가 이미 지워진 경우 (NoSuchKey) 410 Gone 응답.

    운영상 버킷 lifecycle 로 오래된 export 가 제거되거나, 재시도 중 과거
    object 가 소실된 케이스. FE 는 "파일이 만료되었습니다" 메시지로 재생성을
    유도할 수 있다.
    """
    from minio.error import S3Error

    job_id = uuid.uuid4()
    document_id = uuid.uuid4()

    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = _completed_state(
        job_id=str(job_id),
        document_id=str(document_id),
    )

    fake_minio = MagicMock()
    # S3Error 생성자 시그니처는 버전에 따라 다르므로 code 속성만 강제로 세팅한다.
    try:
        s3_err = S3Error(
            code="NoSuchKey",
            message="Object does not exist",
            resource="/bucket/key",
            request_id="rid",
            host_id="hid",
            response=MagicMock(),
        )
    except TypeError:
        # 최소 인자로 생성 후 code 만 주입.
        s3_err = S3Error.__new__(S3Error)
        s3_err.code = "NoSuchKey"
        s3_err.args = ("Object does not exist",)
    fake_minio.get_object_bytes = MagicMock(side_effect=s3_err)

    with (
        patch(
            "app.core.cache.get_redis",
            new=AsyncMock(return_value=fake_redis),
        ),
        patch(
            "app.integrations.object_storage.MinIOService",
            return_value=fake_minio,
        ),
    ):
        response = await client.get(ROUTE_DOWNLOAD.format(job_id=job_id))

    assert response.status_code == 410
    assert "만료" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 20. GET /exports/{job_id} (status) — download_url 이 프록시 상대 경로
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_status_download_url_is_proxy_relative_path(client):
    """D10 정책 회귀 테스트.

    status 응답의 download_url 은 프록시 상대 경로
    (`/api/v1/v2/documents/exports/.../download`) 이어야 하며, MinIO 내부
    hostname 이나 AWS 서명 파라미터가 섞여 있으면 안 된다.
    """
    job_id = uuid.uuid4()
    document_id = uuid.uuid4()
    fake_redis = _FakeAsyncRedis()
    fake_redis.store[f"export_job:{job_id}"] = _completed_state(
        job_id=str(job_id),
        document_id=str(document_id),
    )

    with patch(
        "app.core.cache.get_redis",
        new=AsyncMock(return_value=fake_redis),
    ):
        response = await client.get(ROUTE_GET_STATUS.format(job_id=job_id))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["download_url"] == f"/api/v1/v2/documents/exports/{job_id}/download"
    # 내부 hostname 이나 presigned URL 흔적이 없어야 한다.
    assert "minio:" not in body["download_url"]
    assert "X-Amz-Signature" not in body["download_url"]
    assert "?" not in body["download_url"]
