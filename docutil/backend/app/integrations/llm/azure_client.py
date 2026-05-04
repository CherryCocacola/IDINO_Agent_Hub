"""Azure OpenAI 클라이언트 모듈.

Azure OpenAI Service는 OpenAI API와 거의 동일하지만 다음이 다르다:
  1. base_url 형식: https://{endpoint}/openai/deployments/{deployment}
  2. 인증 헤더: ``Authorization: Bearer`` 대신 ``api-key: {key}`` 헤더 사용
  3. URL에 ``?api-version={version}`` 쿼리 파라미터가 필요

OpenAICompatibleClient를 상속하여 위 3가지만 오버라이드하면
generate, generate_stream, generate_structured, 동기 메서드 모두 그대로 사용 가능.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.integrations.llm.client import OpenAICompatibleClient

logger = logging.getLogger(__name__)
settings = get_settings()


class AzureOpenAIClient(OpenAICompatibleClient):
    """Azure OpenAI Service 클라이언트.

    Azure는 OpenAI와 동일한 /chat/completions 엔드포인트를 사용하지만,
    URL 구조와 인증 방식이 다르다. 이 클래스는 그 차이점만 오버라이드한다.

    사용 예시::

        client = AzureOpenAIClient()
        response = await client.generate(messages=[
            {"role": "user", "content": "안녕하세요"}
        ])
    """

    def __init__(
        self,
        api_key: str | None = None,
        deployment: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
    ) -> None:
        """Azure OpenAI 클라이언트를 초기화한다.

        Parameters
        ----------
        api_key:
            Azure OpenAI API 키. 미지정 시 settings에서 가져온다.
        deployment:
            배포된 모델 이름 (예: ``gpt-4o``). 미지정 시 settings에서 가져온다.
        endpoint:
            Azure 리소스 엔드포인트 (예: ``https://myresource.openai.azure.com``).
            미지정 시 settings에서 가져온다.
        api_version:
            Azure OpenAI API 버전 (예: ``2024-08-01-preview``).
            미지정 시 settings에서 가져온다.
        """
        self.api_version = api_version or settings.azure_openai_api_version

        # deployment 이름은 model 파라미터와 동일한 역할 (페이로드의 "model" 필드)
        resolved_deployment = deployment or settings.azure_openai_deployment
        resolved_endpoint = (endpoint or settings.azure_openai_endpoint).rstrip("/")

        # Azure base_url: https://{endpoint}/openai/deployments/{deployment}
        azure_base_url = f"{resolved_endpoint}/openai/deployments/{resolved_deployment}"

        super().__init__(
            api_key=api_key or settings.azure_openai_api_key,
            model=resolved_deployment,
            base_url=azure_base_url,
        )

        logger.info(
            "Azure OpenAI 클라이언트 초기화 완료: endpoint=%s, deployment=%s, api_version=%s",
            resolved_endpoint,
            resolved_deployment,
            self.api_version,
        )

    def _headers(self) -> dict[str, str]:
        """Azure 전용 인증 헤더를 구성한다.

        OpenAI는 ``Authorization: Bearer {key}`` 를 사용하지만,
        Azure는 ``api-key: {key}`` 헤더를 사용한다.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def _completions_url(self) -> str:
        """Azure 전용 chat/completions URL을 반환한다.

        Azure는 URL 끝에 ``?api-version=YYYY-MM-DD`` 쿼리 파라미터가 필수이다.
        예시: https://myresource.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview
        """
        return f"{self.base_url}/chat/completions?api-version={self.api_version}"
