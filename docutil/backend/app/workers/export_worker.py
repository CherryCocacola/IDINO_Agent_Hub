"""export_worker — DocumentV2 → 파일 포맷 비동기 export Celery 태스크.

Phase 4 S2 D4 ~ D5 산출물. 프론트 `export-menu/use-export-status.ts` 의 2 초 폴링
훅과 짝을 이루는 서버 측 진입점.

파이프라인 (generate_document_export)
------------------------------------
1. Redis 상태 `pending` → `running (progress=10)` 으로 갱신.
2. DB 에서 :class:`DocumentV2` 로드 (org_id 체크는 dispatch 측에서 완료 가정).
3. JSONB `document_schema` → :class:`DocumentSchema` 재검증 (스키마 드리프트 방지).
4. `BuilderRegistry.get(format)` 으로 빌더 조회 → `build(schema)` 호출.
   - `build()` 는 async 이므로 `asyncio.run()` 으로 래핑 (Celery worker 가
     동기 컨텍스트에서 돌아가기 때문).
5. 결과 bytes 를 임시 디렉터리에 단기 버퍼링 (progress=70).
6. D5: MinIOService 로 버킷 업로드 → presigned URL 발급 → Redis 에
   `result_key` (MinIO object key) + `download_url` (presigned URL) 기록.
   업로드 단계는 progress=95, 최종 완료는 progress=100.
7. try/finally 로 tmp 파일을 반드시 삭제한다 (업로드 성공/실패 무관).
8. 예외는 Redis 에 `failed` + 한국어 메시지를 저장한 뒤 raise 하여 Celery 재시도
   정책 (`task_max_retries=2`) 에 맡긴다.

Redis 상태 스키마 (`export_job:{job_id}`) — TTL 3600 초
--------------------------------------------------------
    status: pending | running | completed | failed
    progress: 0~100 (int)
    document_id: str(UUID)
    user_id: str(UUID)            # 상태 조회 권한 검증에 사용
    org_id: str(UUID)
    format: pptx | docx | hwpx | pdf | html
    result_key: str | None        # D5: MinIO object key (documents_v2/exports/...)
    download_url: str | None      # D5: MinIO presigned GET URL (TTL=3600s)
    error: str | None             # 한국어 메시지
    created_at: ISO8601 str
    updated_at: ISO8601 str

설계 판단 포인트:
- **Redis 를 SoT 로 사용**하는 이유: 요청마다 DB row 를 만들면 단순 export 작업
  로그가 수천 건씩 쌓여 운영 부담 가중. Redis TTL (1 시간) 로 자동 청소.
- **tmp 파일 vs base64 in Redis**: 평균 PPTX ~500KB–5MB 이므로 Redis string 에
  base64 로 넣으면 메모리 압박. tempfile 경유가 합리적. MinIO 업로드 후 tmp 는
  삭제되어 디스크 점유를 남기지 않는다.
- **presigned URL TTL 과 Redis TTL 모두 3600s** — 동일 시간 축으로 맞춰 "상태
  조회가 가능한 동안은 다운로드도 가능" 을 보장. TTL 이 만료되면 FE 훅이
  404 를 만나게 되므로, 사용자가 그 이전에 다운로드를 트리거해야 한다.
- **외부 접근 URL 주의**: presigned URL 은 ``MINIO_ENDPOINT`` 를 그대로 host
  로 박는다. 개발 환경에서 ``localhost:9000`` 이면 컨테이너 내부에서만 유효.
  운영 서버에서는 외부에서 접근 가능한 host 를 ``MINIO_ENDPOINT`` 에 설정해야
  FE 가 직접 URL 을 열 수 있다 (.env 에서 조정).
- **progress 세분화**: build 시작 10% → build 완료 70% → MinIO 업로드 완료 95%
  → 최종 완료 100%. 빌더 내부의 세밀한 진행률은 추후 S2 후반에서 확장 가능.

참조:
- docs/phase3_execution_roadmap.md §2.2 S2 D4 / D5
- docs/techspec.md §9.4 (P7 DocumentBuilder ABC)
- backend/app/modules/reports/service.py (MinIO 업로드/presigned 기존 패턴)
- frontend/src/components/document-designer/export-menu/use-export-status.ts (짝)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Redis 키 스키마 & TTL
# ---------------------------------------------------------------------------

# 단일 export 작업의 상태를 담는 Redis string key prefix.
# `export_job:{uuid}` 로 저장하며 값은 JSON 직렬화된 dict.
EXPORT_JOB_KEY_PREFIX = "export_job:"

# Redis TTL — 작업 완료 후 1 시간까지 상태 조회 가능. 그 뒤 자동 만료.
# 운영 관점에서 "내가 방금 요청한 작업은 일정 시간 내 반드시 조회" 전제.
EXPORT_JOB_TTL_SECONDS = 3600

# presigned URL 유효기간 — Redis TTL 과 동일하게 3600 초로 맞춘다.
# 상태가 만료되지 않은 동안은 presigned URL 로 다운로드도 가능해야 사용자 혼란
# 을 막을 수 있다.
PRESIGNED_URL_EXPIRES_SECONDS = 3600

# build 진행률 단계값. D5 에서 업로드 완료 후 100 까지 간다.
#   10  : Celery worker pickup 직후 build 시작
#   70  : BuilderRegistry.build() 반환, bytes 를 tmp 파일에 저장
#   95  : MinIO 업로드 + presigned URL 발급 완료
#   100 : Redis 최종 completed 전이 + tmp cleanup 완료
PROGRESS_BUILD_START = 10
PROGRESS_BUILD_DONE = 70
PROGRESS_UPLOAD_DONE = 95
PROGRESS_COMPLETED = 100

# ---------------------------------------------------------------------------
# 포맷별 MIME 타입 매핑 (MinIO Content-Type 지정)
# ---------------------------------------------------------------------------
#
# PPTX/DOCX 는 OOXML 표준 MIME. HWPX 는 공식 IANA 등록이 없어 관례상
# ``application/haansoft-hwpx`` 혹은 ``application/vnd.hancom.hwpx`` 을 쓴다.
# 후자가 `reports/service.py` 와 일치하므로 일관성을 위해 그대로 채택.
FORMAT_CONTENT_TYPE: dict[str, str] = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "html": "text/html; charset=utf-8",
    "hwpx": "application/vnd.hancom.hwpx",
}


def export_job_key(job_id: str | UUID) -> str:
    """Redis 에 저장되는 export job 상태 key 를 반환."""
    return f"{EXPORT_JOB_KEY_PREFIX}{job_id}"


# ---------------------------------------------------------------------------
# Redis 동기 클라이언트 헬퍼 (Celery worker 는 동기 컨텍스트)
# ---------------------------------------------------------------------------


def _get_sync_redis():
    """Celery worker 전용 동기 Redis 클라이언트.

    app.core.cache 의 async 클라이언트는 이벤트 루프가 필요해 worker 의 동기
    경로에서 다루기 번거롭다. 동기 `redis.Redis.from_url` 로 별도 접속.
    """
    from redis import Redis  # type: ignore[import-not-found]

    return Redis.from_url(settings.redis_url, decode_responses=True)


def _write_job_state(
    job_id: str,
    state: dict[str, Any],
) -> None:
    """Redis 에 상태 dict 를 JSON 직렬화하여 저장 (TTL 갱신)."""
    try:
        redis = _get_sync_redis()
        redis.set(
            export_job_key(job_id),
            json.dumps(state, ensure_ascii=False),
            ex=EXPORT_JOB_TTL_SECONDS,
        )
    except Exception:
        # Redis 장애는 치명적이지만, 이미 진행 중인 build 를 중단할 이유는 없음.
        # 상위에서 상태 조회 실패 시 404 로 매핑되며, worker 로그로 원인 추적.
        logger.exception("Redis 상태 저장 실패: job_id=%s", job_id)


def _read_job_state(job_id: str) -> dict[str, Any] | None:
    """Redis 에서 상태 dict 를 조회. 없으면 None."""
    try:
        redis = _get_sync_redis()
        raw = redis.get(export_job_key(job_id))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.exception("Redis 상태 조회 실패: job_id=%s", job_id)
        return None


def _merge_state(
    job_id: str,
    updates: dict[str, Any],
) -> None:
    """기존 상태를 읽어 updates 를 병합한 뒤 다시 기록."""
    current = _read_job_state(job_id) or {}
    current.update(updates)
    current["updated_at"] = datetime.now(UTC).isoformat()
    _write_job_state(job_id, current)


# ---------------------------------------------------------------------------
# 동기 DB 로더 (Celery worker 컨텍스트)
# ---------------------------------------------------------------------------


def _load_document_schema_sync(document_id: str) -> dict[str, Any] | None:
    """DB 에서 DocumentV2.document_schema JSONB 를 로드해 dict 로 반환.

    org/권한 체크는 dispatch 측 (Router → Service.request_export) 에서 이미
    수행된 뒤 넘어오므로 worker 는 단순 ID 조회만 한다.
    """

    async def _load() -> dict[str, Any] | None:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from app.modules.documents_v2.models import DocumentV2

        engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with factory() as session:
                result = await session.execute(select(DocumentV2).where(DocumentV2.id == UUID(document_id)))
                doc = result.scalars().first()
                if doc is None:
                    return None
                return dict(doc.document_schema)
        finally:
            await engine.dispose()

    return asyncio.run(_load())


# ---------------------------------------------------------------------------
# MinIO 업로드 + presigned URL (Phase 4 S2 D5)
# ---------------------------------------------------------------------------


def _build_export_object_name(document_id: str, job_id: str, fmt: str) -> str:
    """MinIO object key 규칙을 한 곳에 모은다.

    reports 모듈의 ``reports/{org_id}/{report_id}/{filename}`` 패턴을 참고하여
    documents_v2 전용 export 네임스페이스를 분리한다. document_id 를 중간
    경로에 두면 특정 문서의 과거 export 를 prefix 조회로 묶을 수 있다.

    Args:
        document_id: DocumentV2 UUID 문자열.
        job_id: export job UUID 문자열 (파일 basename).
        fmt: 포맷 키 (pptx/docx/hwpx/pdf/html).

    Returns:
        ``documents_v2/exports/{document_id}/{job_id}.{ext}`` 형식의 key.
    """
    ext = fmt if fmt in {"pptx", "docx", "hwpx", "pdf", "html"} else "bin"
    return f"documents_v2/exports/{document_id}/{job_id}.{ext}"


def _upload_and_presign(
    *,
    bucket: str,
    object_name: str,
    payload: bytes,
    content_type: str,
    expires: int,
) -> tuple[str, str]:
    """MinIO 업로드 + presigned GET URL 발급을 한 번에 처리한다.

    P1 원칙: MinIO SDK 를 직접 import 하지 않고 ``MinIOService`` 게이트웨이만
    경유한다. ``reports/service.py`` 와 동일한 패턴 — 지연 import 로 worker
    부팅 비용 최소화.

    Notes:
        Phase 4 S2 D10 에서 ``download_url`` 정책이 API 프록시로 바뀌면서
        본 함수는 generate_document_export 의 성공 경로에서 더 이상 호출되지
        않는다. 다만 다른 경로 (수동 디버그 · 향후 외부 CDN 연동) 에서 재사용
        가능성이 있어 남겨둔다. 실제 write path 는 :func:`_upload_only` 를 사용.

    Args:
        bucket: 업로드 대상 버킷 이름.
        object_name: 버킷 내 object key.
        payload: 업로드할 바이트 페이로드 (빌더 결과물).
        content_type: MIME 타입 문자열.
        expires: presigned URL TTL (초 단위).

    Returns:
        ``(presigned_url, object_name)`` 튜플.

    Raises:
        Exception: 업로드 또는 presigned URL 발급 중 발생한 MinIO 예외.
    """
    # 지연 import 이유:
    # 1) P1 단일 구현 원칙을 __init__ 로 통일된 경로로 관철.
    # 2) Celery worker 부팅 시 Minio SDK 를 항상 로드할 필요가 없다 — 실제
    #    첫 export 태스크 실행 시점에 import 하면 충분하다.
    from app.integrations.object_storage import MinIOService

    minio_svc = MinIOService()
    minio_svc.upload_file(
        bucket=bucket,
        object_name=object_name,
        file_data=payload,
        content_type=content_type,
    )
    presigned = minio_svc.get_presigned_url(
        bucket=bucket,
        object_name=object_name,
        expires=expires,
    )
    return presigned, object_name


def _upload_only(
    *,
    bucket: str,
    object_name: str,
    payload: bytes,
    content_type: str,
) -> str:
    """MinIO 업로드만 수행하고 object key 를 돌려준다 (Phase 4 S2 D10).

    ``_upload_and_presign`` 과 달리 presigned URL 을 발급하지 않는다. D10 정책
    변경으로 Redis 에 내려가는 ``download_url`` 은 API 프록시 상대 경로이고,
    실제 파일은 :meth:`MinIOService.get_object_bytes` 로 서버에서 직접 읽는다.
    presigned URL 발급 호출을 생략해 (1) 내부 hostname 노출을 원천 차단하고,
    (2) MinIO 서명 계산을 한 번 아낀다.

    Args:
        bucket: 업로드 대상 버킷 이름.
        object_name: 버킷 내 object key.
        payload: 업로드할 바이트 페이로드.
        content_type: MIME 타입 문자열.

    Returns:
        업로드된 object key (=``object_name``). Redis ``result_key`` 로 그대로
        저장되어, 다운로드 엔드포인트에서 MinIO 재조회에 사용된다.

    Raises:
        Exception: MinIO 업로드 중 발생한 모든 예외 (상위에서 failed 로 기록).
    """
    from app.integrations.object_storage import MinIOService

    minio_svc = MinIOService()
    minio_svc.upload_file(
        bucket=bucket,
        object_name=object_name,
        file_data=payload,
        content_type=content_type,
    )
    return object_name


def _cleanup_tmp_file(path: str) -> None:
    """tmp 파일을 조용히 삭제한다.

    업로드 성공/실패 양쪽에서 호출되므로 실패해도 태스크 실행 결과에 영향을
    주면 안 된다. FileNotFoundError 는 이미 정리된 상태 — 무시. OSError 는
    운영 중 디스크 권한 문제 등 드물지만 발생 가능하므로 경고 로그 기록 후
    삼킨다 (bare except 는 P5 위반이므로 사용하지 않음).

    Args:
        path: 삭제할 절대 경로.
    """
    try:
        os.remove(path)
    except FileNotFoundError:
        # 이미 삭제됐거나 애초에 생성되지 않았다면 OK.
        return
    except OSError as exc:
        # 권한/경쟁 상태 등. 운영에선 세션 디스크가 주기적 정리되므로 치명적
        # 이진 않지만, 반복 발생 시 누수 우려 → 경고 로그로 추적 가능하게.
        logger.warning("tmp 파일 삭제 실패 — path=%s, error=%s", path, exc)


# ---------------------------------------------------------------------------
# Celery 태스크
# ---------------------------------------------------------------------------


@celery_app.task(
    name="workers.export_worker.generate_document_export",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=30,
    max_retries=2,
)
def generate_document_export(
    self,
    job_id: str,
    document_id: str,
    format: str,  # noqa: A002 - FE API 스펙(ExportFormat)과 1:1 매칭 유지
    organization_overrides: dict | None = None,
) -> dict[str, Any]:
    """DocumentV2 를 지정 포맷으로 변환해 MinIO 에 저장하고 presigned URL 을 반환한다.

    Celery task — 동기 컨텍스트에서 `BuilderRegistry.get(format).build(schema)`
    를 `asyncio.run()` 으로 래핑해 호출한 뒤, 결과 bytes 를 MinIO 버킷에 업로드
    하고 presigned GET URL 을 Redis 에 저장한다.

    Args:
        job_id: `DocumentServiceV2.request_export` 가 발급한 UUID 문자열.
        document_id: 대상 DocumentV2 의 UUID 문자열.
        format: BuildTarget Literal 값 (pptx/docx/hwpx/pdf/html).
        organization_overrides: layout_resolver 에 전달할 조직별 레이아웃 오버라이드.
            D4 에서는 전달만 받고 빌더가 자동 소비하는 구조가 아직이라면 None 허용.

    Returns:
        Celery result backend 에 저장되는 dict (상태 조회는 Redis 경로 사용).

    Raises:
        Exception: 빌드 또는 MinIO 업로드 실패 시 상태를 `failed` 로 기록한 뒤
            재-raise 하여 Celery 재시도 정책을 트리거한다. 최대 재시도 초과 시
            worker 가 최종 실패로 기록하고 Redis 에 `failed` 가 남는다.
    """

    logger.info("generate_document_export 시작: job_id=%s, document_id=%s, format=%s", job_id, document_id, format)

    # ---- 1) running 상태 전이 ----------------------------------------------
    _merge_state(
        job_id,
        {
            "status": "running",
            "progress": PROGRESS_BUILD_START,
        },
    )

    try:
        # ---- 2) DocumentV2 로드 ------------------------------------------
        schema_dict = _load_document_schema_sync(document_id)
        if schema_dict is None:
            error_msg = f"문서를 찾을 수 없습니다: document_id={document_id}"
            _merge_state(job_id, {"status": "failed", "error": error_msg})
            raise ValueError(error_msg)

        # ---- 3) Pydantic 재검증 -------------------------------------------
        # 지연 import: 모듈 로딩 순서를 늦춰 Celery worker 초기 부팅 시 LLM/
        # DocumentSchema 체인을 전부 import 하지 않도록 한다.
        from app.modules.documents_v2.schemas import DocumentSchema

        try:
            schema = DocumentSchema.model_validate(schema_dict)
        except Exception as exc:  # noqa: BLE001 - pydantic ValidationError 포함
            error_msg = f"문서 스키마 검증 실패: {exc}"
            _merge_state(job_id, {"status": "failed", "error": error_msg})
            raise

        # ---- 4) 빌더 조회 + build() ---------------------------------------
        # 반드시 BuilderRegistry.get() 을 거친다 (P1 단일 구현).
        # PptxBuilder 등 구체 빌더를 직접 import 하지 않는다.
        from app.integrations.document_builders.base import BuilderRegistry

        # 포맷 유효성은 Registry.get() 내부에서 검증 + 한국어 HTTPException 반환.
        # worker 경로에서는 HTTPException 을 그대로 raise 해도 Celery 가 일반
        # Exception 으로 취급하므로 메시지만 사용자에게 전달되는 장점 유지.
        builder = BuilderRegistry.get(format)  # type: ignore[arg-type]
        try:
            payload_bytes = asyncio.run(builder.build(schema))
        except Exception as exc:  # noqa: BLE001 - 빌더 내부 실패 포괄
            error_msg = f"{format} 빌드 중 오류가 발생했습니다: {exc}"
            _merge_state(job_id, {"status": "failed", "error": error_msg})
            raise

        # ---- 5) 임시파일 저장 (MinIO 업로드 전 단기 버퍼) -----------------
        # Celery worker + FastAPI 가 같은 호스트/컨테이너를 공유한다는 전제는
        # 더 이상 필요하지 않다(아래 MinIO 업로드 후 tmp 는 즉시 삭제).
        suffix_map = {
            "pptx": ".pptx",
            "docx": ".docx",
            "hwpx": ".hwpx",
            "pdf": ".pdf",
            "html": ".html",
        }
        suffix = suffix_map.get(format, ".bin")

        tmp_dir = Path(tempfile.gettempdir()) / "docutil_exports"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        tmp_path = tmp_dir / f"{job_id}{suffix}"
        tmp_path.write_bytes(payload_bytes)

        # build 완료 단계 진행률 업데이트 (70%). 업로드 단계로 진입.
        _merge_state(
            job_id,
            {
                "status": "running",
                "progress": PROGRESS_BUILD_DONE,
                "result_key": None,
                "download_url": None,
                "error": None,
            },
        )

        # ---- 6) MinIO 업로드 + 프록시 다운로드 경로 (D10) -----------------
        # try/finally 로 tmp 파일 cleanup 을 업로드 결과와 무관하게 보장한다.
        # MinIO 실패 시 Redis 를 failed 로 쓰고 raise → Celery 재시도 로직에
        # 맡긴다 (재시도 시에는 build 부터 다시 수행).
        #
        # D10 정책 변경 (W4 블로커 대응):
        # - 기존 presigned URL 방식은 ``MINIO_ENDPOINT`` 에 박힌 내부 hostname
        #   (``minio:9000``) 이 그대로 URL 에 포함돼 FE 브라우저가 resolve 불가.
        # - presigned URL 발급은 중단하고, Redis ``download_url`` 필드에는
        #   API 프록시 엔드포인트 상대 경로를 기록한다. 실제 다운로드 시 FE 는
        #   ``GET /api/v1/v2/documents/exports/{job_id}/download`` 를 호출하고,
        #   백엔드가 ``MinIOService.get_object_bytes`` 로 읽어 StreamingResponse
        #   로 흘려준다.
        # - result_key (MinIO object name) 는 내부 조회용으로 계속 기록한다.
        try:
            object_name = _build_export_object_name(document_id, job_id, format)
            content_type = FORMAT_CONTENT_TYPE.get(format, "application/octet-stream")

            result_key = _upload_only(
                bucket=settings.minio_bucket,
                object_name=object_name,
                payload=payload_bytes,
                content_type=content_type,
            )
        except Exception as exc:  # noqa: BLE001 — MinIO 장애/네트워크 포괄
            error_msg = f"결과 파일을 스토리지에 업로드하지 못했습니다: {exc}"
            _merge_state(job_id, {"status": "failed", "error": error_msg})
            # tmp 파일 제거 후 예외 재-raise (Celery 재시도 정책에 위임).
            _cleanup_tmp_file(str(tmp_path))
            raise
        else:
            # 업로드 성공 — tmp 파일은 더 이상 필요 없으므로 cleanup.
            _cleanup_tmp_file(str(tmp_path))

        # API 프록시 상대 경로. FE `apiClient` 와 `use-export-status` 훅이 그대로
        # 수용한다 (`/reports/{id}/download` 와 동일 패턴).
        download_url = f"/api/v1/v2/documents/exports/{job_id}/download"

        # ---- 7) 완료 상태 전이 (progress=100, download_url 채움) ----------
        _merge_state(
            job_id,
            {
                "status": "completed",
                "progress": PROGRESS_COMPLETED,
                "result_key": result_key,
                "download_url": download_url,
                "error": None,
            },
        )

        logger.info(
            "generate_document_export 완료: job_id=%s, bytes=%d, object=%s",
            job_id,
            len(payload_bytes),
            result_key,
        )

        return {
            "job_id": job_id,
            "document_id": document_id,
            "format": format,
            "bytes": len(payload_bytes),
            "result_key": result_key,
            "download_url": download_url,
        }

    except Exception as exc:
        # Celery 재시도 정책과 결합. 최대 재시도 초과 시 최종 failed 유지.
        if self.request.retries >= (self.max_retries or 0):
            logger.exception(
                "generate_document_export 최종 실패 (재시도 소진): job_id=%s",
                job_id,
            )
        else:
            logger.warning(
                "generate_document_export 실패 (재시도 예정 %d/%d): job_id=%s, error=%s",
                self.request.retries + 1,
                self.max_retries or 0,
                job_id,
                exc,
            )
        # Redis 상태는 위 분기에서 이미 failed 로 기록됨. raise 로 재시도 유도.
        raise
