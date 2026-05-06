"""
Embedding Service — Phase 7.5 (AgentHubClient.embed() 위임으로 통합)
======================================================================

Phase 7.4 → 7.5 변경 요약:
    - 7.4: 별도 httpx.AsyncClient 인스턴스 보유, `/v1/embeddings` 직접 호출.
    - 7.5: `shared.common.agenthub_client.AgentHubClient.embed()` 위임으로 통합.
           AgentHub `OpenAICompatController.EmbeddingsAsync` 가 라우팅을 처리.

설계 원칙:
    - **R2 단일 진입점**: 모든 임베딩 호출은 AgentHub `/v1/embeddings` 경유.
      OpenAI SDK 직접 호출 금지 (anti-patterns.md §1).
    - **Single Implementation**: 본 모듈은 AgentHubClient 싱글턴을 재사용 — chat 호출과
      connection pool 공유. 별도 httpx.AsyncClient 보유 X.
    - **R5 한국어 주석**: 초보자도 이해할 수 있도록 한국어로.

호출 흐름:
    EmbeddingService.embed_text()
        → AgentHubClient.embed(agent_code="embedding-default", input=text)
        → AgentHub `/v1/embeddings`
        → AgentHub 가 ApiService 분기 (OpenAI/Azure OpenAI Embeddings)
        → 1536D 벡터 반환

대상 차원:
    - 1536D 표준 (TECHSPEC ADR-10) — Qdrant collection 단일성 보장.
    - AgentCode "embedding-default" 가 `text-embedding-3-small` 시드됨 (Phase 7.1).
"""

import logging
from typing import List, Optional

from shared.common.agenthub_client import (
    AgentHubClient,
    AgentHubError,
    get_agenthub_client,
)

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    AgentHub `embedding-default` Agent 위임 임베딩 서비스 (Phase 7.5).

    초보자 가이드:
        - 텍스트(예: 학생 자기소개) 를 1536차원 벡터로 변환한다.
        - 이전(7.4)에는 본 모듈이 직접 httpx 로 AgentHub 를 호출했지만,
          이제 7.5 부터는 공용 `AgentHubClient` 싱글턴의 `embed()` 메서드를 사용한다.
        - AgentHub 가 OpenAI `text-embedding-3-small` 호출을 라우팅한다.

    Attributes:
        model:        AgentCode (`"embedding-default"`)
        dimensions:   출력 임베딩 차원 (1536, TECHSPEC ADR-10 표준)
    """

    def __init__(self, settings=None, agenthub_client: Optional[AgentHubClient] = None):
        # settings 는 향후 호환용 — 현재는 사용하지 않음 (AgentHubClient 가 환경변수 직접 로드).
        self.settings = settings or get_settings()
        # 1536D 표준 — TECHSPEC ADR-10 / W1 (단일 차원 정책으로 Qdrant collection 통일)
        self.model = "embedding-default"  # AgentCode (Phase 7.1 시드 등록됨)
        self.dimensions = 1536

        # 의존성 주입 패턴 — 테스트에서 mock AgentHubClient 주입 가능.
        # 운영 환경에서는 싱글턴 재사용으로 connection pool 효율 확보.
        self._agenthub: AgentHubClient = agenthub_client or get_agenthub_client()

    async def aclose(self) -> None:
        """
        FastAPI lifespan shutdown 에서 호출.

        주의: AgentHubClient 자체는 싱글턴(@lru_cache)으로 다른 모듈도 공유 사용한다 —
        본 모듈에서 aclose() 를 호출하면 chat 호출도 죽는다. 따라서 lifespan 의 shutdown
        에서는 AgentHubClient 직접 aclose 를 1회만 호출하고, 본 메서드는 no-op 으로 둔다.
        """
        # Phase 7.5: 의도적으로 no-op — 싱글턴 보호.
        return

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
            # AgentHubClient.embed 는 OpenAI 호환 dict 를 반환.
            response = await self._agenthub.embed(
                agent_code=self.model,
                input=text.strip(),
            )
            return response["data"][0]["embedding"]
        except AgentHubError as ex:
            logger.error("Failed to generate embedding via AgentHub: %s", ex)
            raise
        except (KeyError, IndexError) as ex:
            logger.error(
                "AgentHub embedding 응답 파싱 실패: %s (response=%r)",
                ex, response if "response" in locals() else None,
            )
            raise

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        다중 텍스트의 임베딩을 배치로 AgentHub 에 위임한다.

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 한 번의 API 호출에 보낼 최대 텍스트 수
                        (OpenAI 권장 ≤ 2048, 기본 100 으로 보수적 설정)

        Returns:
            각 입력에 대응하는 1536차원 임베딩 리스트.
            빈 텍스트 위치에는 0 벡터를 끼워 입력 인덱스를 보존.
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
                response = await self._agenthub.embed(
                    agent_code=self.model,
                    input=batch,
                )
                # OpenAI 호환 응답: data["data"] = [{"embedding": [...], "index": N}, ...]
                # AgentHub 가 index 순서를 보존하므로 그대로 사용.
                batch_embeddings = [item["embedding"] for item in response["data"]]
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

        except AgentHubError as ex:
            logger.error("Failed to generate batch embeddings via AgentHub: %s", ex)
            raise
        except (KeyError, IndexError) as ex:
            logger.error("AgentHub batch embedding 응답 파싱 실패: %s", ex)
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
