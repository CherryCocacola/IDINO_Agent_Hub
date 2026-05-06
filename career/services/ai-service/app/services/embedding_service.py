"""
Embedding Service — Phase 7.4 (AgentHub `embedding-default` Agent 위임)
=======================================================================

Phase 7.4 변경 요약:
    - 기존: `from openai import AsyncOpenAI` 직접 호출 (OPENAI_API_KEY 필요)
    - 변경: AgentHub `embedding-default` Agent 의 `/v1/embeddings` 엔드포인트로 위임
    - 사유: 통합 R2 단일 진입점. AgentHub 가 ApiKeyPool / 차원 정책(1536D 표준) /
      사용량 추적을 일괄 관리한다 (TECHSPEC ADR-10 / W1).

호출 패턴:
    - `httpx.AsyncClient` 으로 `POST {AGENTHUB_URL}/v1/embeddings`
    - 헤더: `X-API-Key: {AGENTHUB_API_KEY}`
    - body: `{"model": "embedding-default", "input": "text" or [text,...]}`

주의:
    - AgentHubClient (career/shared/common/agenthub_client.py) 는 chat 만 노출하므로
      본 모듈은 임베딩 전용 httpx 클라이언트를 별도 보유한다.
    - Phase 7.5 에서 AgentHubClient.embed() 메서드 추가 시 본 모듈도 연계 변경한다.
"""

import logging
import os
from typing import List, Optional

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    AgentHub `embedding-default` Agent 위임 임베딩 서비스.

    초보자 가이드:
        - 텍스트(예: 학생 자기소개) 를 1536차원 벡터로 변환한다.
        - 이전에는 OpenAI SDK 로 직접 호출했지만, 이제는 AgentHub 게이트웨이를 거친다.
        - AgentHub 가 OpenAI `text-embedding-3-small` 호출을 라우팅한다.

    Attributes:
        model:        AgentCode (`"embedding-default"`)
        dimensions:   출력 임베딩 차원 (1536, TECHSPEC ADR-10 표준)
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        # 1536D 표준 — TECHSPEC ADR-10 / W1 (단일 차원 정책으로 Qdrant collection 통일)
        self.model = "embedding-default"  # AgentCode (Phase 7.1 시드 등록됨)
        self.dimensions = 1536

        # AgentHub 임베딩 엔드포인트 — chat 과 동일한 base_url, 다른 path
        base_url = os.environ.get("AGENTHUB_URL", "").strip().rstrip("/")
        api_key = os.environ.get("AGENTHUB_API_KEY", "").strip()
        if not base_url or not api_key:
            logger.warning(
                "AGENTHUB_URL/AGENTHUB_API_KEY 미설정 — 임베딩 호출 시 실패 예상. "
                "Phase 7.2 발급된 career-master-key 가 환경변수에 주입되었는지 확인."
            )

        # httpx.AsyncClient 인스턴스를 보유하여 connection pool 재사용
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "career-ai-service/embedding/1.0",
            },
        )

    async def aclose(self) -> None:
        """FastAPI lifespan shutdown 에서 호출 — connection pool 정리."""
        await self._client.aclose()

    async def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트의 임베딩을 AgentHub 로 위임 생성한다.

        Args:
            text: 임베딩할 텍스트 (빈 문자열은 0 벡터로 처리)

        Returns:
            1536차원 float 리스트
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimensions

        try:
            response = await self._client.post(
                "/v1/embeddings",
                json={
                    "model": self.model,
                    "input": text.strip(),
                },
            )
            if response.status_code >= 400:
                logger.error(
                    f"AgentHub embedding 호출 실패: status={response.status_code} body={response.text[:300]}"
                )
                raise httpx.HTTPStatusError(
                    f"AgentHub /v1/embeddings returned {response.status_code}",
                    request=response.request,
                    response=response,
                )
            data = response.json()
            return data["data"][0]["embedding"]
        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
            logger.error(f"Failed to generate embedding via AgentHub: {e}")
            raise

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        다중 텍스트의 임베딩을 배치로 AgentHub 에 위임한다.

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 한 번의 API 호출에 보낼 최대 텍스트 수

        Returns:
            각 입력에 대응하는 1536차원 임베딩 리스트
        """
        if not texts:
            return []

        # 빈 텍스트는 별도 0벡터로 채워 인덱스를 보존
        non_empty_texts: List[str] = []
        empty_indices = set()

        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
            else:
                empty_indices.add(i)

        if not non_empty_texts:
            return [[0.0] * self.dimensions] * len(texts)

        embeddings: List[List[float]] = []

        try:
            # batch_size 단위로 잘라 AgentHub 호출
            for i in range(0, len(non_empty_texts), batch_size):
                batch = non_empty_texts[i:i + batch_size]
                response = await self._client.post(
                    "/v1/embeddings",
                    json={
                        "model": self.model,
                        "input": batch,
                    },
                )
                if response.status_code >= 400:
                    logger.error(
                        f"AgentHub batch embedding 호출 실패: status={response.status_code} body={response.text[:300]}"
                    )
                    raise httpx.HTTPStatusError(
                        f"AgentHub /v1/embeddings returned {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                data = response.json()
                # OpenAI 호환 응답: data["data"] = [{"embedding": [...], "index": N}, ...]
                batch_embeddings = [item["embedding"] for item in data["data"]]
                embeddings.extend(batch_embeddings)

            # 빈 텍스트 위치에 0 벡터를 끼워 원래 순서 복원
            result: List[List[float]] = []
            embed_idx = 0
            for i in range(len(texts)):
                if i in empty_indices:
                    result.append([0.0] * self.dimensions)
                else:
                    result.append(embeddings[embed_idx])
                    embed_idx += 1

            return result

        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as e:
            logger.error(f"Failed to generate batch embeddings via AgentHub: {e}")
            raise

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        두 임베딩의 코사인 유사도(0~1) 를 계산한다. 임베딩 자체는 변경 없음.
        """
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def format_for_pgvector(self, embedding: List[float]) -> str:
        """pgvector 컬럼에 INSERT 할 수 있는 문자열 형식 (`[0.1,0.2,...]`) 으로 변환."""
        return "[" + ",".join(str(x) for x in embedding) + "]"
