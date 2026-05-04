"""
Qdrant vector database wrapper for the Document Utilization System.

Provides the ``QdrantService`` class for managing org-scoped collections,
upserting dense + sparse vectors, performing hybrid search, and
collection-level operations.

Each organisation gets its own Qdrant collection named
``org_<org_id>`` with:
  - A ``dense`` named vector (2048-dimensional, cosine distance) for
    semantic search via Qwen3-Embedding-8B embeddings.
  - A ``sparse`` named vector for BM25-based keyword search.
"""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    NamedSparseVector,
    NamedVector,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# 임베딩 차원은 프로바이더에 따라 다름: OpenAI(1536), Qwen3(2048)
DENSE_VECTOR_SIZE = settings.embedding_dimension
DENSE_DISTANCE = Distance.COSINE
COLLECTION_PREFIX = "org_"


class QdrantService:
    """High-level wrapper around the Qdrant Python client.

    Manages per-organisation collections and provides methods for
    upserting vectors, performing hybrid search, and deleting data.
    """

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.url = url or f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        self.api_key = api_key or settings.qdrant_api_key
        self._client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=60,
        )

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _collection_name(org_id: str) -> str:
        """Derive the Qdrant collection name for an organisation."""
        return f"{COLLECTION_PREFIX}{org_id.replace('-', '_')}"

    def ensure_collection(self, org_id: str) -> None:
        """Create the org collection if it does not already exist.

        The collection is configured with:
          - ``dense``: 2048-dimensional cosine vector (Qwen3-Embedding-8B).
          - ``sparse``: sparse BM25 vector for keyword retrieval.
        """
        collection_name = self._collection_name(org_id)

        existing = [c.name for c in self._client.get_collections().collections]
        if collection_name in existing:
            logger.debug("Collection '%s' already exists", collection_name)
            return

        logger.info("Creating Qdrant collection: %s", collection_name)
        self._client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=DENSE_VECTOR_SIZE,
                    distance=DENSE_DISTANCE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(),
                ),
            },
        )

        # Create payload indices for common filter fields
        for field_name in ("document_id", "organization_id", "chunk_type"):
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema="keyword",
            )

        logger.info("Collection '%s' created successfully", collection_name)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def upsert_vectors(
        self,
        org_id: str,
        points: list[PointStruct],
    ) -> None:
        """Upsert a batch of points into the org's collection.

        Parameters
        ----------
        org_id:
            Organisation UUID whose collection receives the points.
        points:
            List of ``PointStruct`` objects with ``dense`` and ``sparse``
            named vectors and payload.
        """
        collection_name = self._collection_name(org_id)
        logger.info(
            "Upserting %d points to collection '%s'",
            len(points),
            collection_name,
        )
        self._client.upsert(
            collection_name=collection_name,
            points=points,
        )

    def hybrid_search(
        self,
        org_id: str,
        dense_vector: list[float],
        sparse_vector: SparseVector | dict[str, Any] | None = None,
        filters: Filter | None = None,
        limit: int = 10,
    ) -> list[Any]:
        """Perform a hybrid (dense + sparse) search with RRF fusion.

        If only a dense vector is provided, falls back to pure semantic
        search.  When both dense and sparse vectors are supplied, results
        from each are fused using Reciprocal Rank Fusion (RRF).

        Parameters
        ----------
        org_id:
            Organisation UUID whose collection is searched.
        dense_vector:
            2048-dimensional dense embedding for semantic similarity.
        sparse_vector:
            Optional sparse BM25 vector for keyword matching.
        filters:
            Qdrant ``Filter`` to restrict the search scope.
        limit:
            Maximum number of results to return.

        Returns
        -------
        list
            Scored search results, each containing payload and score.
        """
        collection_name = self._collection_name(org_id)

        # If no sparse vector, do a simple dense search
        if sparse_vector is None:
            results = self._client.search(
                collection_name=collection_name,
                query_vector=NamedVector(name="dense", vector=dense_vector),
                query_filter=filters,
                limit=limit,
                with_payload=True,
            )
            return results

        # Convert dict to SparseVector if needed
        if isinstance(sparse_vector, dict):
            sparse_vector = SparseVector(
                indices=sparse_vector["indices"],
                values=sparse_vector["values"],
            )

        # Perform both dense and sparse searches for RRF fusion
        prefetch_limit = limit * 3  # over-fetch for better fusion

        dense_results = self._client.search(
            collection_name=collection_name,
            query_vector=NamedVector(name="dense", vector=dense_vector),
            query_filter=filters,
            limit=prefetch_limit,
            with_payload=True,
        )

        sparse_results = self._client.search(
            collection_name=collection_name,
            query_vector=NamedSparseVector(name="sparse", vector=sparse_vector),
            query_filter=filters,
            limit=prefetch_limit,
            with_payload=True,
        )

        # Reciprocal Rank Fusion
        k = 60  # RRF constant
        scores: dict[str, float] = {}
        point_map: dict[str, Any] = {}

        for rank, result in enumerate(dense_results):
            pid = str(result.id)
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
            point_map[pid] = result

        for rank, result in enumerate(sparse_results):
            pid = str(result.id)
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
            if pid not in point_map:
                point_map[pid] = result

        # Sort by fused score and return top-k
        sorted_ids = sorted(scores, key=scores.get, reverse=True)[:limit]

        fused_results = []
        for pid in sorted_ids:
            result = point_map[pid]
            result.score = scores[pid]
            fused_results.append(result)

        return fused_results

    async def mmr_search(
        self,
        org_id: str,
        query_vector: list[float],
        filters: dict | None = None,
        limit: int = 10,
        lambda_mult: float = 0.7,
    ) -> list:
        """Maximal Marginal Relevance search for diversity-aware retrieval."""
        collection_name = self._collection_name(org_id)

        # Fetch more candidates than needed for MMR selection
        candidates_limit = min(limit * 4, 100)

        filter_obj = self._build_filter(filters) if filters else None

        candidates = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=filter_obj,
            limit=candidates_limit,
            with_vectors=True,
            with_payload=True,
        ).points

        if not candidates:
            return []

        # MMR selection
        selected = []
        candidate_list = list(candidates)

        while len(selected) < limit and candidate_list:
            best_score = -float("inf")
            best_idx = 0

            for i, candidate in enumerate(candidate_list):
                relevance = candidate.score

                # Max similarity to already selected
                max_sim = 0.0
                if selected:
                    for sel in selected:
                        sim = self._cosine_similarity(
                            candidate.vector.get("dense", []),
                            sel.vector.get("dense", []),
                        )
                        max_sim = max(max_sim, sim)

                mmr_score = lambda_mult * relevance - (1 - lambda_mult) * max_sim

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            selected.append(candidate_list.pop(best_idx))

        return selected

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import numpy as np

        a_arr, b_arr = np.array(a), np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr) + 1e-10))

    def _build_filter(self, filters: dict) -> Filter:
        """Build a Qdrant Filter from a simple dict of field->value pairs."""
        conditions = []
        for key, value in filters.items():
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        return Filter(must=conditions)

    def delete_by_document(self, org_id: str, document_id: str) -> None:
        """Delete all points associated with a specific document.

        Parameters
        ----------
        org_id:
            Organisation UUID whose collection is affected.
        document_id:
            Document UUID whose vectors should be removed.
        """
        collection_name = self._collection_name(org_id)
        logger.info(
            "Deleting points for document %s from collection '%s'",
            document_id,
            collection_name,
        )
        self._client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    ),
                ]
            ),
        )

    def scroll_document_ids(self, org_id: str) -> set[str]:
        """Scroll through all points in an org collection and return unique document_ids.

        Uses the Qdrant scroll API with pagination to collect every
        distinct ``document_id`` stored in the collection's payloads.

        Returns
        -------
        set[str]
            Unique document IDs found in the collection.
        """
        collection_name = self._collection_name(org_id)
        document_ids: set[str] = set()
        offset = None

        while True:
            results, next_offset = self._client.scroll(
                collection_name=collection_name,
                scroll_filter=None,
                limit=1000,
                offset=offset,
                with_payload=["document_id"],
                with_vectors=False,
            )

            for point in results:
                doc_id = point.payload.get("document_id")
                if doc_id:
                    document_ids.add(str(doc_id))

            if next_offset is None:
                break
            offset = next_offset

        logger.info(
            "Scrolled collection '%s': found %d unique document_ids",
            collection_name,
            len(document_ids),
        )
        return document_ids

    def get_collection_info(self, org_id: str) -> dict[str, Any]:
        """Retrieve metadata about the org's Qdrant collection.

        Returns
        -------
        dict
            Collection status, vector count, configuration, etc.
        """
        collection_name = self._collection_name(org_id)

        try:
            info = self._client.get_collection(collection_name=collection_name)
            return {
                "collection_name": collection_name,
                "status": info.status.value if info.status else "unknown",
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": len(info.segments) if info.segments else 0,
                "config": {
                    "dense_size": DENSE_VECTOR_SIZE,
                    "dense_distance": DENSE_DISTANCE.value,
                    "has_sparse": True,
                },
            }
        except Exception as exc:
            logger.warning(
                "Failed to get collection info for '%s': %s",
                collection_name,
                exc,
            )
            return {
                "collection_name": collection_name,
                "status": "not_found",
                "error": str(exc),
            }
