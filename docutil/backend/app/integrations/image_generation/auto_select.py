"""이미지 자동 선택 헬퍼 (Phase 4 S3 D3 + D5 쿼터 연동).

Mode A 자유 생성의 DocumentSchema 내 `ImageComponent.src` 가 비어 있고
`prompt` 만 제공된 경우, 다음 정책으로 자동으로 이미지 소스를 채운다.

정책 (Unsplash 우선, DALL-E 3 fallback)
-----------------------------------------
1. **Unsplash 검색 우선** — 조직 외부 HTTPS URL 을 그대로 `src` 로 사용.
   MinIO 업로드를 생략해 빠르고, 저작권/비용 이슈가 없다.
2. **Unsplash 실패/결과 없음 → DALL-E 3 fallback** — 이미지 바이트를
   MinIO 의 `documents` 버킷에 `generated_images/{uuid}.png` 로 업로드 후
   `minio://{bucket}/generated_images/{uuid}.png` 형태로 반환한다.
   (PPTX 빌더의 `fetch_image_bytes` 가 해당 스킴을 인식한다.)
3. **쿼터 체크 (S3 D5)** — DALL-E fallback 직전에 ``organization_id`` + ``db``
   가 모두 주어지면 ``QuotaService.check_and_consume_quota(quota_type=
   'dalle_monthly', amount=1)`` 를 호출한다. 결과가 False (한도 초과) 이면
   ``DalleQuotaExceededError`` 를 던져 호출부가 per-image soft degrade 를
   수행하도록 한다. ``db`` 가 None 이면 쿼터 체크를 건너뛴다 (단위 테스트
   호환성 유지).

반환값 타입
-----------
- 성공: ``str`` — `ImageComponent.src` 에 바로 주입 가능한 URL / MinIO 스킴.
- 모든 경로 실패: ``None`` — 호출부가 degrade (src=None 유지 → placeholder).
- 쿼터 초과: ``DalleQuotaExceededError`` raise — 호출부가 degrade 처리.

P1/P3 준수: 본 모듈은 `ImageGenerationService` 를 경유해 DALL-E/Unsplash 를
호출하며, OpenAI/Unsplash SDK 를 직접 import 하지 않는다. MinIO 접근도
`MinIOService` 경유.
"""

from __future__ import annotations

import logging
import uuid as uuid_module
from typing import Final
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.image_generation.service import ImageGenerationService
from app.integrations.object_storage.minio_client import MinIOService

logger = logging.getLogger(__name__)


class DalleQuotaExceededError(Exception):
    """조직의 월 DALL-E 쿼터가 초과된 경우 발생하는 예외.

    ``auto_select_image`` 는 쿼터 초과 시 내부적으로 degrade 하지 않고
    이 예외를 던져 호출부(`_auto_fill_image_sources`)가 정책적으로
    대응할 수 있게 한다.

    - Soft degrade (기본) — 해당 이미지 컴포넌트만 src=None 유지 + metadata
      의 ``degraded_components`` 에 id 기록. 문서 생성 자체는 계속 진행.
    - Strict 모드(미구현) — 상위에서 붙잡아 HTTPException 403 으로 변환.
    """

    def __init__(self, organization_id: UUID, message: str | None = None):
        self.organization_id = organization_id
        super().__init__(message or "이 조직의 월 DALL-E 쿼터가 초과되었습니다. 관리자에게 문의하세요.")


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

# DALL-E 결과물을 MinIO 에 저장할 때 쓰는 prefix.
# tb_documents_v2 원본 문서와 구분할 수 있게 별도 폴더에 적재한다.
_GENERATED_IMAGE_PREFIX: Final[str] = "generated_images"

# Unsplash URL 을 그대로 prompt 기반 키에 쓰지 않고 프롬프트를 영어권 키워드로
# 간단 정규화할 때 활용. 현재는 프롬프트 전문을 그대로 전달하나, 향후 LLM 번역
# 훅을 끼울 수 있도록 상수 자리만 예약.
_UNSPLASH_QUERY_MAX_LEN: Final[int] = 100


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


async def auto_select_image(
    prompt: str,
    alt: str,  # noqa: ARG001 — alt 는 호출부 컨텍스트 로깅/향후 확장을 위해 예약.
    *,
    organization_id: UUID | None = None,
    db: AsyncSession | None = None,
    service: ImageGenerationService | None = None,
    minio_service: MinIOService | None = None,
) -> str | None:
    """프롬프트로부터 이미지 URL/MinIO 키를 자동 선택한다.

    Args:
        prompt: 이미지 설명 프롬프트 (한/영 모두 가능).
            빈 문자열이면 ``ValueError``.
        alt: 접근성 텍스트. 현재는 로깅 용도로만 사용하며 반환값에
            영향을 주지 않는다. (캡션/alt 자동 보정은 호출부에서 수행.)
        organization_id: 조직 ID. DALL-E fallback 시 월 쿼터 체크 대상.
            None 이면 쿼터 체크 생략 (테스트/시스템 내부 호출 호환).
        db: AsyncSession. organization_id 와 함께 제공된 경우에만 쿼터
            체크를 수행한다. None 이면 쿼터 훅 비활성 — D3 단위 테스트
            호환을 위해 제공.
        service: DI 를 위한 ImageGenerationService 인스턴스. None 이면
            기본 생성자로 만든다 (테스트에서는 mock 주입).
        minio_service: DI 를 위한 MinIOService 인스턴스. None 이면 기본.

    Returns:
        - Unsplash 성공 → 원격 HTTPS URL (str)
        - DALL-E 성공 → ``minio://{bucket}/generated_images/{uuid}.png`` (str)
        - 전부 실패 → ``None`` (호출부는 src=None 유지하여 placeholder 렌더)

    Raises:
        ValueError: prompt 가 비어있거나 공백만 있는 경우. 호출부는 이를
            "자동 선택 건너뛰기" 신호로 해석해 src=None 으로 둘 수도 있다.
        DalleQuotaExceededError: Unsplash 실패 → DALL-E fallback 단계에서
            조직 월 쿼터가 초과된 경우. 호출부는 degrade 처리.
    """

    if prompt is None or not prompt.strip():
        # 빈 프롬프트는 자동 선택 대상이 아니다 — 명시적으로 거절.
        raise ValueError("이미지 자동 선택을 위해서는 prompt 가 필요합니다.")

    svc = service or ImageGenerationService()

    # ---- 1) Unsplash 우선 시도 ------------------------------------------
    try:
        unsplash_url = await _try_unsplash(svc, prompt)
    except Exception:  # noqa: BLE001 - 외부 호출 실패는 DALL-E 로 fallback.
        # _try_unsplash 가 자체적으로 내부 예외를 먹지만, 예외 계약 안정성을 위해
        # 상위에서도 한 번 더 방어한다 (추후 구현 변경에도 안전).
        logger.exception("Unsplash 이미지 선택 실패 (예외) — DALL-E 로 fallback")
        unsplash_url = None

    if unsplash_url:
        logger.info(
            "자동 이미지 선택: prompt='%s', provider=unsplash, url='%s'",
            prompt[:80],
            unsplash_url,
        )
        return unsplash_url

    # ---- 2) 쿼터 체크 (S3 D5) ------------------------------------------
    #
    # ``tb_organization_quotas`` 에서 당월 `dalle_monthly` 사용량을 확인하고
    # 한도 내라면 amount=1 만큼 차감한다. 한도 초과시 ``DalleQuotaExceededError``
    # 를 던져 상위(`_auto_fill_image_sources`)가 soft degrade 처리한다.
    #
    # ``db`` 혹은 ``organization_id`` 가 없으면 쿼터 체크를 건너뛴다.
    # (D3 단위 테스트 호환 + 시스템 내부 호출 경로 방어)
    if organization_id is not None and db is not None:
        # 순환 import 방지 — 조직 서비스는 integrations 계층 밖에 위치.
        from app.modules.organizations.service import QuotaService

        quota_ok = await QuotaService.check_and_consume_quota(
            db,
            organization_id=organization_id,
            quota_type="dalle_monthly",
            amount=1,
        )
        if not quota_ok:
            logger.warning(
                "DALL-E 쿼터 초과 — 조직=%s, prompt='%s'",
                organization_id,
                prompt[:80],
            )
            raise DalleQuotaExceededError(organization_id)

    # ---- 3) DALL-E 3 fallback + MinIO 업로드 ----------------------------
    try:
        minio_src = await _try_dalle_and_upload(
            svc,
            prompt,
            minio_service=minio_service,
        )
    except Exception:  # noqa: BLE001 - DALL-E/MinIO 실패도 degrade.
        logger.exception("DALL-E fallback 실패")
        minio_src = None

    if minio_src:
        logger.info(
            "자동 이미지 선택: prompt='%s', provider=dalle, url='%s'",
            prompt[:80],
            minio_src,
        )
        return minio_src

    # 모든 경로 실패 — None 반환 (호출부가 src=None 유지).
    logger.warning(
        "자동 이미지 선택 실패 — 모든 provider 가 결과를 반환하지 않았습니다. prompt='%s'",
        prompt[:80],
    )
    return None


# ---------------------------------------------------------------------------
# 내부 — provider 별 호출
# ---------------------------------------------------------------------------


async def _try_unsplash(
    service: ImageGenerationService,
    prompt: str,
) -> str | None:
    """Unsplash 검색 API 로 첫 결과 URL 을 반환하거나 None.

    ``ImageGenerationService._fetch_unsplash`` 는 이미지 바이트를 반환하는데,
    자동 선택 경로에서는 **바이트 다운로드가 불필요** (브라우저/PPTX 빌더가
    Unsplash CDN 을 다시 GET). 저작권 표기 요구사항도 Unsplash 정책상 CDN URL
    직링크가 더 명확하다. 따라서 바이트 경로 대신 검색 API 만 직접 호출해
    URL 만 추출한다 (중복 다운로드/메모리 사용 절감).

    실패 (키 미설정, 결과 없음, 네트워크 에러) 시 None 을 반환.
    """

    settings = get_settings()
    if not settings.unsplash_access_key:
        logger.debug("Unsplash ACCESS_KEY 미설정 — Unsplash 경로 건너뜀")
        return None

    # 프롬프트 길이 방어 — API 오류 방지 목적.
    query = prompt.strip()[:_UNSPLASH_QUERY_MAX_LEN]

    # _fetch_unsplash 는 바이트를 반환하므로 재사용하지 못하지만, service 인스턴스의
    # default_provider 값과 무관하게 Unsplash 검색 URL 을 그대로 히트한다.
    # 중복 유지보수를 피하기 위해 HTTP 호출 형태는 service.py 의 _fetch_unsplash 와
    # 동일한 엔드포인트/파라미터를 사용한다.
    search_url = "https://api.unsplash.com/search/photos"
    params = {"query": query, "per_page": 1, "orientation": "landscape"}
    headers = {"Authorization": f"Client-ID {settings.unsplash_access_key}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(search_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Unsplash API HTTP 오류: %s (query=%r)", exc, query)
        # service 인자 사용 유지 — 테스트에서 해당 인스턴스의 unsplash 헬퍼를
        # 직접 patch 할 수 있게 참조점을 남긴다.
        _ = service
        return None

    results = data.get("results") or []
    if not results:
        logger.info("Unsplash 검색 결과 없음 (query=%r)", query)
        _ = service
        return None

    first = results[0]
    url = (first.get("urls") or {}).get("regular")
    if not url:
        logger.warning("Unsplash 결과에 regular URL 누락 (query=%r)", query)
    _ = service  # service 인자 의도적 참조 (DI 일관성 유지).
    return url


async def _try_dalle_and_upload(
    service: ImageGenerationService,
    prompt: str,
    *,
    minio_service: MinIOService | None = None,
) -> str | None:
    """DALL-E 3 로 이미지를 생성 후 MinIO 에 업로드, 스킴 문자열을 반환.

    ``ImageGenerationService.generate(prompt, provider='dalle3')`` 를 재활용해
    바이트를 얻은 뒤, `MinIOService.upload_file` 로 `documents` 버킷에 적재한다.
    반환 값 형식:

        minio://{settings.minio_bucket}/generated_images/{uuid}.png

    이 스킴은 `pptx/image_fetcher.py::fetch_image_bytes` 가 인식해 빌드 시
    자동 다운로드한다.

    실패 시 None.
    """

    # DALL-E 호출 — 바이트 반환 또는 None.
    image_bytes = await service.generate(prompt=prompt, provider="dalle3")
    if not image_bytes:
        return None

    # MinIO 업로드. minio_service 미주입 시 기본 생성자.
    storage = minio_service or MinIOService()
    settings = get_settings()
    bucket = settings.minio_bucket
    object_key = f"{_GENERATED_IMAGE_PREFIX}/{uuid_module.uuid4()}.png"

    try:
        storage.upload_file(
            bucket=bucket,
            object_name=object_key,
            file_data=image_bytes,
            content_type="image/png",
        )
    except Exception as exc:  # noqa: BLE001 - MinIO 실패는 degrade.
        logger.exception("MinIO 업로드 실패 — DALL-E 결과 폐기: %s", exc)
        return None

    return f"minio://{bucket}/{object_key}"
