"""
이미지 생성 서비스 모듈.

두 가지 이미지 소스를 지원한다:
  - **DALL-E 3** (OpenAI): 프롬프트 기반 AI 이미지 생성
  - **Unsplash**: 무료 스톡 이미지 검색 및 다운로드

사용 예시::

    from app.integrations.image_generation.service import ImageGenerationService

    service = ImageGenerationService()

    # DALL-E 3로 이미지 생성
    image_bytes = await service.generate("사무실에서 회의하는 사람들")

    # Unsplash에서 스톡 이미지 검색
    image_bytes = await service.generate("office meeting", provider="unsplash")
"""

from __future__ import annotations

import base64
import logging

import httpx

from app.core.config import get_settings

# 로거 설정 — 이 모듈에서 발생하는 모든 로그에 모듈 이름이 표시된다
logger = logging.getLogger(__name__)

# 앱 설정을 한 번만 로드하여 재사용 (lru_cache로 캐싱됨)
settings = get_settings()

# ── 상수 정의 ──────────────────────────────────────────────────────────────
# DALL-E 3에서 허용하는 이미지 크기 목록
ALLOWED_DALLE3_SIZES = {"1024x1024", "1024x1792", "1792x1024"}

# DALL-E 3에서 허용하는 스타일 옵션
# - "natural": 사실적인 사진 스타일
# - "vivid": 밝고 선명한 색감의 일러스트 스타일
ALLOWED_DALLE3_STYLES = {"natural", "vivid"}

# HTTP 요청 타임아웃 (초) — 이미지 생성은 시간이 오래 걸릴 수 있으므로 넉넉하게 설정
HTTP_TIMEOUT = 60.0


class ImageGenerationService:
    """이미지 생성 서비스 — DALL-E 3 및 Unsplash 스톡 이미지 지원.

    이 서비스는 슬라이드나 보고서에 넣을 이미지가 필요할 때 사용한다.
    ``generate()`` 메서드를 호출하면, 지정한 provider에 따라
    AI로 이미지를 만들거나 스톡 사진을 검색하여 바이트(bytes)로 반환한다.

    Attributes
    ----------
    default_provider : str
        설정 파일(config.py)에서 읽어온 기본 이미지 제공자.
        ``"dalle3"`` 또는 ``"unsplash"`` 중 하나.
    """

    def __init__(self) -> None:
        """서비스 초기화 — 설정에서 기본 provider를 읽어온다."""
        # config.py의 image_generation_provider 값 사용
        self.default_provider: str = settings.image_generation_provider

    # ══════════════════════════════════════════════════════════════════════
    # 공개 인터페이스 (외부에서 호출하는 메서드)
    # ══════════════════════════════════════════════════════════════════════

    async def generate(
        self,
        prompt: str,
        provider: str | None = None,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> bytes | None:
        """이미지를 생성하거나 검색하여 바이트(bytes)로 반환한다.

        Parameters
        ----------
        prompt : str
            이미지 생성에 사용할 프롬프트 (예: "사무실에서 회의하는 사람들").
            DALL-E 3: 한글/영어 모두 가능 (OpenAI가 내부 번역).
            Unsplash: 영어 키워드 권장 (예: "office meeting").
        provider : str | None
            이미지 제공자. ``"dalle3"`` 또는 ``"unsplash"``.
            None이면 설정 파일의 기본값(``image_generation_provider``)을 사용.
        size : str
            이미지 크기. DALL-E 3 전용.
            허용값: ``"1024x1024"``, ``"1024x1792"``, ``"1792x1024"``.
        style : str
            이미지 스타일. DALL-E 3 전용.
            ``"natural"`` (사실적) 또는 ``"vivid"`` (선명한 일러스트).

        Returns
        -------
        bytes | None
            성공 시 이미지 바이너리 데이터 (PNG/JPEG).
            실패 시 None (에러 로그가 기록되며, 서비스 전체가 중단되지 않음).
        """
        # provider가 지정되지 않으면 설정 파일의 기본값 사용
        use_provider = (provider or self.default_provider).lower().strip()

        logger.info(
            "이미지 생성 요청 — provider=%s, prompt='%s', size=%s, style=%s",
            use_provider,
            prompt[:80],  # 로그에는 프롬프트 앞부분만 표시 (너무 길면 잘림)
            size,
            style,
        )

        # provider에 따라 적절한 내부 메서드로 분기
        if use_provider == "dalle3":
            return await self._generate_dalle3(prompt, size, style)
        elif use_provider == "unsplash":
            return await self._fetch_unsplash(prompt)
        else:
            # 지원하지 않는 provider가 지정된 경우
            logger.error(
                "지원하지 않는 이미지 provider: '%s'. 'dalle3' 또는 'unsplash'만 사용 가능합니다.",
                use_provider,
            )
            return None

    # ══════════════════════════════════════════════════════════════════════
    # DALL-E 3 (OpenAI AI 이미지 생성)
    # ══════════════════════════════════════════════════════════════════════

    async def _generate_dalle3(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural",
    ) -> bytes | None:
        """OpenAI DALL-E 3 API를 사용하여 이미지를 생성한다.

        동작 흐름:
        1. OpenAI API 키가 설정되어 있는지 확인
        2. 크기(size)와 스타일(style) 파라미터 유효성 검증
        3. OpenAI의 images/generations 엔드포인트에 요청
        4. Base64로 인코딩된 응답을 디코딩하여 바이트로 반환

        Parameters
        ----------
        prompt : str
            이미지 생성 프롬프트. 한글도 지원됨.
        size : str
            이미지 크기. 기본값 "1024x1024" (정사각형).
        style : str
            이미지 스타일. "natural" 또는 "vivid".

        Returns
        -------
        bytes | None
            생성된 이미지의 PNG 바이트 데이터. 실패 시 None.
        """
        # ── 1단계: API 키 확인 ────────────────────────────────────────────
        if not settings.openai_api_key:
            logger.error(
                "DALL-E 3 이미지 생성 실패: OPENAI_API_KEY가 설정되지 않았습니다. "
                ".env 파일에 OPENAI_API_KEY를 추가하세요."
            )
            return None

        # ── 2단계: 파라미터 유효성 검증 ────────────────────────────────────
        # 잘못된 크기가 들어오면 기본값으로 대체 (에러 대신 경고)
        if size not in ALLOWED_DALLE3_SIZES:
            logger.warning(
                "잘못된 DALL-E 3 크기 '%s' → 기본값 '1024x1024'으로 대체합니다. 허용 크기: %s",
                size,
                ALLOWED_DALLE3_SIZES,
            )
            size = "1024x1024"

        # 잘못된 스타일이 들어오면 기본값으로 대체
        if style not in ALLOWED_DALLE3_STYLES:
            logger.warning(
                "잘못된 DALL-E 3 스타일 '%s' → 기본값 'natural'로 대체합니다. 허용 스타일: %s",
                style,
                ALLOWED_DALLE3_STYLES,
            )
            style = "natural"

        # ── 3단계: OpenAI API 호출 ────────────────────────────────────────
        try:
            # openai 패키지의 AsyncOpenAI 클라이언트 사용
            from openai import AsyncOpenAI

            # 비동기 OpenAI 클라이언트 생성
            client = AsyncOpenAI(api_key=settings.openai_api_key)

            # DALL-E 3 이미지 생성 요청
            # response_format="b64_json" → URL 대신 Base64 인코딩된 이미지 직접 수신
            # 이렇게 하면 별도의 이미지 다운로드 과정이 필요 없음
            response = await client.images.generate(
                model="dall-e-3",  # DALL-E 3 모델 사용
                prompt=prompt,  # 이미지 설명 프롬프트
                size=size,  # 이미지 크기 (예: 1024x1024)
                style=style,  # 스타일 (natural 또는 vivid)
                quality="standard",  # 품질 (standard 또는 hd)
                response_format="b64_json",  # Base64 JSON으로 응답 받기
                n=1,  # 1장만 생성
            )

            # ── 4단계: Base64 디코딩 ──────────────────────────────────────
            # API 응답에서 Base64로 인코딩된 이미지 데이터 추출
            b64_data = response.data[0].b64_json
            if not b64_data:
                logger.error("DALL-E 3 응답에 이미지 데이터(b64_json)가 없습니다.")
                return None

            # Base64 문자열을 바이트로 디코딩
            image_bytes = base64.b64decode(b64_data)

            logger.info(
                "DALL-E 3 이미지 생성 성공 — 크기: %s, %d 바이트",
                size,
                len(image_bytes),
            )
            return image_bytes

        except Exception as exc:
            # 모든 예외를 잡아서 로그에 기록하고 None 반환
            # 이미지 생성 실패가 전체 서비스를 중단시키지 않도록 함
            logger.error(
                "DALL-E 3 이미지 생성 중 오류 발생: %s",
                exc,
                exc_info=True,  # 스택 트레이스도 로그에 포함
            )
            return None

    # ══════════════════════════════════════════════════════════════════════
    # Unsplash (무료 스톡 이미지 검색)
    # ══════════════════════════════════════════════════════════════════════

    async def _fetch_unsplash(self, query: str) -> bytes | None:
        """Unsplash API에서 스톡 이미지를 검색하고 다운로드한다.

        동작 흐름:
        1. Unsplash Access Key 확인
        2. 검색 API로 이미지 검색 (query는 영어 키워드 권장)
        3. 검색 결과에서 첫 번째 이미지의 URL 추출
        4. 이미지 파일을 다운로드하여 바이트로 반환

        Parameters
        ----------
        query : str
            검색 키워드. **영어로 입력해야 정확한 결과**를 얻을 수 있다.
            예: "office meeting", "nature landscape", "technology"

        Returns
        -------
        bytes | None
            다운로드된 이미지의 바이트 데이터 (JPEG).
            검색 결과가 없거나 실패 시 None.
        """
        # ── 1단계: Access Key 확인 ────────────────────────────────────────
        if not settings.unsplash_access_key:
            logger.error(
                "Unsplash 이미지 검색 실패: UNSPLASH_ACCESS_KEY가 설정되지 않았습니다. "
                ".env 파일에 UNSPLASH_ACCESS_KEY를 추가하세요."
            )
            return None

        try:
            # httpx.AsyncClient를 사용하여 비동기 HTTP 요청 수행
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as http_client:
                # ── 2단계: Unsplash 검색 API 호출 ─────────────────────────
                # Unsplash API 문서: https://unsplash.com/documentation#search-photos
                search_url = "https://api.unsplash.com/search/photos"
                search_params = {
                    "query": query,  # 검색 키워드
                    "per_page": 1,  # 결과 1개만 요청 (첫 번째 이미지 사용)
                    "orientation": "landscape",  # 가로형 이미지 선호 (슬라이드에 적합)
                }
                search_headers = {
                    # Unsplash API 인증 — Access Key를 헤더에 포함
                    "Authorization": f"Client-ID {settings.unsplash_access_key}",
                }

                search_response = await http_client.get(
                    search_url,
                    params=search_params,
                    headers=search_headers,
                )
                search_response.raise_for_status()

                # ── 3단계: 검색 결과 파싱 ─────────────────────────────────
                search_data = search_response.json()
                results = search_data.get("results", [])

                if not results:
                    # 검색 결과가 없는 경우
                    logger.warning(
                        "Unsplash 검색 결과 없음 — query='%s'. 다른 영어 키워드로 다시 시도해 보세요.",
                        query,
                    )
                    return None

                # 첫 번째 검색 결과에서 이미지 URL 추출
                # "regular" 크기는 약 1080px 너비 — 슬라이드에 적당한 해상도
                first_result = results[0]
                image_url = first_result.get("urls", {}).get("regular")

                if not image_url:
                    logger.error(
                        "Unsplash 검색 결과에 이미지 URL이 없습니다 — query='%s'",
                        query,
                    )
                    return None

                # ── 4단계: 이미지 다운로드 ────────────────────────────────
                # 추출한 URL에서 실제 이미지 파일을 다운로드
                image_response = await http_client.get(image_url)
                image_response.raise_for_status()

                image_bytes = image_response.content

                logger.info(
                    "Unsplash 이미지 다운로드 성공 — query='%s', photo_id='%s', %d 바이트",
                    query,
                    first_result.get("id", "unknown"),
                    len(image_bytes),
                )
                return image_bytes

        except httpx.HTTPStatusError as exc:
            # HTTP 에러 (4xx, 5xx) — API 키 오류, 요청 한도 초과 등
            logger.error(
                "Unsplash API HTTP 에러: status=%d, query='%s', detail=%s",
                exc.response.status_code,
                query,
                exc.response.text[:200],  # 에러 응답 본문 앞부분만 로그
            )
            return None

        except Exception as exc:
            # 네트워크 오류, 타임아웃 등 기타 예외
            logger.error(
                "Unsplash 이미지 검색 중 오류 발생: %s",
                exc,
                exc_info=True,
            )
            return None
