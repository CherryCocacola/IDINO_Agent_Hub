"""PPTX 이미지 fetch 헬퍼 (Phase 4 S2 D6).

`ImageComponent.src` 에 담기는 세 가지 source 유형(URL / base64 data-URI /
MinIO object key) 을 단일 `BytesIO` 로 정규화해 렌더러(`components.render_image`)
가 python-pptx 의 `slide.shapes.add_picture()` 에 바로 넘길 수 있게 한다.

설계 판단 포인트:

1. **단일 진입점 `fetch_image_bytes()`**: 세 가지 source 스킴을 내부에서 분기.
   호출부는 source 의 종류를 알 필요가 없다 → P1(단일 구현) 을 지키면서
   components.py 는 렌더링에만 집중.

2. **`httpx.Client` 재사용**: 모듈 전역 싱글톤을 lazy 초기화하여 슬라이드마다
   새 커넥션 풀을 생성하지 않는다. 테스트에서는 monkeypatch 로 교체 가능.
   (httpx 는 thread-safe; PPTX 빌드는 단일 스레드에서 순차 실행되므로 락 불필요)

3. **MinIO 접근은 `MinIOService` 경유**: 프로젝트 P1/anti-patterns 규칙대로
   minio SDK 를 직접 호출하지 않는다. 스킴은 `minio://{bucket}/{object_key}`.
   기본 버킷은 `settings.minio_bucket` (버킷 생략 시 `minio:///{key}` 형태도 허용).

4. **1 회 retry + timeout**: URL fetch 는 일시적 네트워크 오류가 잦아 단순
   1 회 재시도를 포함. timeout 은 호출부에서 오버라이드 가능.

5. **에러 메시지는 한국어, 예외는 `ImageFetchError`**: P5 대로 렌더러가
   fallback 처리할 수 있도록 전용 예외로 감싼다 — 빌드 전체를 중단시키지 않는다.

참조:
- backend/app/integrations/object_storage/minio_client.py (MinIOService.download_file)
- backend/app/core/config.py (settings.minio_bucket)
- backend/app/modules/documents_v2/schemas.py ImageComponent.src 의미
"""

from __future__ import annotations

import base64
import binascii
import contextlib
import logging
import re
from io import BytesIO
from typing import Final
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.integrations.object_storage.minio_client import MinIOService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 설정 상수
# ---------------------------------------------------------------------------

# 기본 HTTP fetch 타임아웃 (초). 테스트·호출부가 override 가능.
DEFAULT_FETCH_TIMEOUT_SEC: Final[int] = 10

# 1 회 재시도 한도 — 네트워크 불안정성 완화용. 2 회 이상은 빌드 지연만 키운다.
FETCH_RETRY_ATTEMPTS: Final[int] = 1

# base64 data-URI 매처. 예: "data:image/png;base64,iVBORw0KGgo..."
_DATA_URI_RE: Final[re.Pattern[str]] = re.compile(
    r"^data:image/[a-zA-Z0-9.+-]+;base64,(?P<payload>.+)$",
    re.DOTALL,
)

# MinIO 스킴 prefix.
_MINIO_SCHEME: Final[str] = "minio://"


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------


class ImageFetchError(RuntimeError):
    """이미지 fetch 실패 시 발생하는 예외.

    렌더러는 이 예외를 잡아 placeholder 로 degrade 한다 (빌드는 계속 진행).
    """


# ---------------------------------------------------------------------------
# httpx.Client 싱글톤
# ---------------------------------------------------------------------------


_http_client: httpx.Client | None = None


def _get_http_client() -> httpx.Client:
    """모듈 전역 `httpx.Client` 싱글톤을 lazy 초기화해 반환.

    매 이미지마다 Client 를 새로 만들지 않아 커넥션 재사용이 가능하다.
    follow_redirects=True 로 Unsplash 등 리다이렉트 기반 CDN 도 지원.
    """
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(
            timeout=DEFAULT_FETCH_TIMEOUT_SEC,
            follow_redirects=True,
        )
    return _http_client


def _reset_http_client_for_tests() -> None:
    """테스트 전용 — 싱글톤 Client 를 초기화.

    monkeypatch 로 httpx.Client 자체를 바꾸기 어려운 경우, 본 함수로 싱글톤을
    리셋 후 해당 테스트에서 `_get_http_client()` 가 다시 생성되게 한다.
    """
    global _http_client
    if _http_client is not None:
        # close 실패는 무시 — 테스트 유틸로만 쓰이며 실제 빌드 경로에 영향 없음.
        with contextlib.suppress(Exception):
            _http_client.close()
    _http_client = None


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


def fetch_image_bytes(source: str, *, timeout: int | None = None) -> BytesIO:
    """`ImageComponent.src` 값을 받아 이미지 바이트 스트림을 반환한다.

    지원 스킴:
        - ``data:image/...;base64,...`` — 인라인 base64 (디코드만 수행)
        - ``http://`` / ``https://`` — HTTP fetch (retry 1회)
        - ``minio://{bucket}/{key}``  — MinIOService 경유
        - ``minio:///{key}``          — 기본 버킷(`settings.minio_bucket`) + key
        - 그 외 절대/상대 경로는 지원하지 않음 (운영 보안 — 임의 로컬 파일 읽기 차단).

    Args:
        source: `ImageComponent.src` 원문 문자열.
        timeout: HTTP fetch 타임아웃 (초). None 이면 DEFAULT_FETCH_TIMEOUT_SEC.

    Returns:
        이미지 원본 바이트가 담긴 `BytesIO` (stream 위치는 0).

    Raises:
        ImageFetchError: 스킴 미지원, 네트워크/스토리지 오류, 잘못된 base64 등.
    """
    if not source or not source.strip():
        raise ImageFetchError("이미지 source 가 비어 있습니다.")

    src = source.strip()

    # 1) base64 data-URI — 네트워크/스토리지 접근 없이 바로 디코드.
    data_match = _DATA_URI_RE.match(src)
    if data_match is not None:
        return _decode_base64_payload(data_match.group("payload"))

    # 2) MinIO 스킴 — MinIOService 로 위임.
    if src.startswith(_MINIO_SCHEME):
        return _fetch_from_minio(src)

    # 3) HTTP(S) URL — httpx 로 GET + 1 회 재시도.
    parsed = urlparse(src)
    if parsed.scheme in ("http", "https"):
        return _fetch_from_http(src, timeout=timeout or DEFAULT_FETCH_TIMEOUT_SEC)

    # 4) 그 외 — 로컬 파일 경로 접근 등은 허용하지 않는다 (운영 보안).
    raise ImageFetchError(
        f"지원하지 않는 이미지 source 스킴입니다: {src[:60]!r} (허용: http/https, data:image/*;base64, minio://)"
    )


# ---------------------------------------------------------------------------
# 내부 — 스킴별 fetch
# ---------------------------------------------------------------------------


def _decode_base64_payload(payload: str) -> BytesIO:
    """data-URI 의 base64 payload 를 BytesIO 로 디코드."""
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageFetchError("이미지 base64 디코딩에 실패했습니다. data-URI 형식이 올바른지 확인하세요.") from exc

    if not raw:
        raise ImageFetchError("이미지 base64 디코딩 결과가 비어 있습니다.")

    return BytesIO(raw)


def _parse_minio_source(source: str) -> tuple[str, str]:
    """`minio://{bucket}/{key}` 또는 `minio:///{key}` 를 (bucket, key) 로 파싱.

    key 는 '/' 포함 경로 전체. bucket 이 생략된 경우 settings.minio_bucket 사용.
    """
    # Prefix 제거 후 나머지 문자열을 bucket/key 로 분리.
    remainder = source[len(_MINIO_SCHEME) :]
    # `minio:///path` 처럼 host 가 비어있는 형태 처리.
    if remainder.startswith("/"):
        bucket = get_settings().minio_bucket
        key = remainder.lstrip("/")
    else:
        # 첫 '/' 까지가 bucket, 이후는 key.
        first_slash = remainder.find("/")
        if first_slash == -1:
            raise ImageFetchError(f"MinIO source 에 object key 가 없습니다: {source!r} (형식: minio://bucket/key)")
        bucket = remainder[:first_slash]
        key = remainder[first_slash + 1 :]

    if not bucket:
        raise ImageFetchError(f"MinIO source 의 bucket 이 비어 있습니다: {source!r}")
    if not key:
        raise ImageFetchError(f"MinIO source 의 object key 가 비어 있습니다: {source!r}")
    return bucket, key


def _fetch_from_minio(source: str) -> BytesIO:
    """MinIO object 를 다운로드해 BytesIO 로 반환."""
    bucket, key = _parse_minio_source(source)

    # P1 — minio SDK 직접 호출 금지. MinIOService 경유.
    service = MinIOService()
    try:
        data = service.download_file(bucket, key)
    except Exception as exc:  # MinIOService 는 S3Error 를 로깅 후 re-raise.
        raise ImageFetchError(f"MinIO 에서 이미지를 불러오지 못했습니다: bucket={bucket!r}, key={key!r}") from exc

    if not data:
        raise ImageFetchError(f"MinIO object 가 비어 있습니다: bucket={bucket!r}, key={key!r}")
    return BytesIO(data)


def _fetch_from_http(url: str, *, timeout: int) -> BytesIO:
    """HTTP(S) URL 에서 이미지 바이트를 가져온다. 1 회 재시도 포함."""
    client = _get_http_client()
    last_error: Exception | None = None

    # 초기 시도 + FETCH_RETRY_ATTEMPTS 회 재시도.
    for attempt in range(FETCH_RETRY_ATTEMPTS + 1):
        try:
            response = client.get(url, timeout=timeout)
            response.raise_for_status()
            content = response.content
            if not content:
                raise ImageFetchError(f"이미지 응답이 비어 있습니다: url={url!r} (HTTP {response.status_code})")
            return BytesIO(content)
        except (httpx.HTTPError, ImageFetchError) as exc:
            last_error = exc
            logger.warning(
                "이미지 HTTP fetch 실패 (attempt %d/%d): url=%s, err=%s",
                attempt + 1,
                FETCH_RETRY_ATTEMPTS + 1,
                url,
                exc,
            )

    # 모든 재시도 실패.
    raise ImageFetchError(
        f"이미지 HTTP fetch 가 {FETCH_RETRY_ATTEMPTS + 1} 회 모두 실패했습니다: url={url!r}"
    ) from last_error
