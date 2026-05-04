"""
Embedding Service for RAG Pipeline
Phase 2-3: Vector Embeddings using OpenAI text-embedding-3-small

This service generates embeddings for text content to be stored in PostgreSQL
with pgvector extension for semantic search.
"""

import logging
from typing import List, Optional

from openai import AsyncOpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's embedding model.

    Attributes:
        model: The embedding model to use (text-embedding-3-small for 1536 dimensions)
        dimensions: Output embedding dimensions
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # 1536 dimensions
        self.dimensions = 1536

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimensions

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Maximum number of texts per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts and track their positions
        non_empty_texts = []
        empty_indices = set()

        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
            else:
                empty_indices.add(i)

        if not non_empty_texts:
            return [[0.0] * self.dimensions] * len(texts)

        embeddings = []

        try:
            # Process in batches
            for i in range(0, len(non_empty_texts), batch_size):
                batch = non_empty_texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

            # Reconstruct with empty placeholders
            result = []
            embed_idx = 0
            for i in range(len(texts)):
                if i in empty_indices:
                    result.append([0.0] * self.dimensions)
                else:
                    result.append(embeddings[embed_idx])
                    embed_idx += 1

            return result

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)
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
        """
        Format embedding for PostgreSQL pgvector insertion.

        Args:
            embedding: The embedding vector

        Returns:
            String formatted for pgvector (e.g., "[0.1,0.2,0.3]")
        """
        return "[" + ",".join(str(x) for x in embedding) + "]"
