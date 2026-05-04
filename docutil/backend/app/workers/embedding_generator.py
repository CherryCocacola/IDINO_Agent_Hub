"""
Embedding generation Celery worker.

Generates dense and sparse vector embeddings for document chunks and
upserts them into the Qdrant vector store for hybrid retrieval.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_worker_session():
    """Celery Worker 전용 async session factory."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


async def _load_chunks(chunk_ids: list[str]) -> list[dict[str, Any]]:
    """청크 레코드를 ID 목록으로 조회한다.

    ORM 모델을 사용하여 SQL Injection을 방지하고,
    올바른 테이블(tb_document_chunks)을 참조한다.
    """
    from sqlalchemy import select

    from app.modules.documents.models import DocumentChunk

    async with _get_worker_session()() as session:
        result = await session.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
        rows = result.scalars().all()
        return [
            {
                "id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "section_title": row.section_title,
                "chunk_type": row.chunk_type or "text",
                "page_number": row.page_number,
                "content_length": row.content_length,
            }
            for row in rows
        ]


async def _update_chunk_qdrant_ids(
    chunk_qdrant_map: dict[str, str],
) -> None:
    """청크 레코드에 Qdrant point ID를 업데이트한다.

    ORM update를 사용하여 올바른 테이블(tb_document_chunks)과 컬럼명을 참조한다.
    """
    from sqlalchemy import update

    from app.modules.documents.models import DocumentChunk

    async with _get_worker_session()() as session:
        for chunk_id, point_id in chunk_qdrant_map.items():
            await session.execute(
                update(DocumentChunk).where(DocumentChunk.id == chunk_id).values(qdrant_point_id=point_id)
            )
        await session.commit()


async def _get_document_org_id(document_id: str) -> str | None:
    """문서의 조직 ID를 조회한다.

    ORM 모델로 올바른 테이블(tb_documents)을 참조한다.
    """
    from sqlalchemy import select

    from app.modules.documents.models import Document

    async with _get_worker_session()() as session:
        result = await session.execute(select(Document.organization_id).where(Document.id == document_id))
        row = result.scalar_one_or_none()
        return str(row) if row else None


async def _get_document_name(document_id: str) -> str:
    """문서 이름을 조회한다."""
    from sqlalchemy import select

    from app.modules.documents.models import Document

    async with _get_worker_session()() as session:
        result = await session.execute(select(Document.name).where(Document.id == document_id))
        row = result.scalar_one_or_none()
        return str(row) if row else ""


async def _update_document_chunk_count(document_id: str) -> None:
    """문서의 임베딩 완료 청크 수를 재계산하여 업데이트한다.

    ORM을 사용하여 올바른 테이블(tb_documents, tb_document_chunks)을 참조한다.
    """
    from sqlalchemy import func, select, update

    from app.modules.documents.models import Document, DocumentChunk

    async with _get_worker_session()() as session:
        result = await session.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.qdrant_point_id.isnot(None),
            )
        )
        embedded_count = result.scalar() or 0

        await session.execute(update(Document).where(Document.id == document_id).values(chunk_count=embedded_count))
        await session.commit()


def _generate_dense_embeddings(texts: list[str]) -> list[list[float]]:
    """Dense 임베딩을 생성한다.

    EMBEDDING_PROVIDER 설정에 따라 OpenAI API 또는 내부 GPU 서비스를 사용한다.
    - "openai": OpenAI text-embedding-3-small (1536D) 사용
    - "local": 내부 GPU의 Qwen3-Embedding-8B (2048D) 사용

    두 프로바이더 모두 OpenAI-compatible API 형식을 사용하므로
    엔드포인트 URL과 모델명만 바꾸면 스왑된다.
    """
    import httpx

    if settings.embedding_provider == "openai":
        # OpenAI Embedding API 사용
        url = "https://api.openai.com/v1/embeddings"
        model = settings.openai_embedding_model
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    else:
        # 내부 GPU 임베딩 서비스 사용
        url = f"{settings.vllm_url}/embeddings"
        model = settings.embedding_model
        headers = {}
        if settings.openai_api_key:
            headers["Authorization"] = f"Bearer {settings.openai_api_key}"

    response = httpx.post(
        url,
        json={"model": model, "input": texts},
        headers=headers,
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()

    embeddings = [item["embedding"] for item in data["data"]]
    return embeddings


def _generate_sparse_embeddings(
    texts: list[str],
) -> list[dict[str, Any]]:
    """Generate sparse BM25 vectors using fastembed.

    Returns a list of dicts with 'indices' and 'values' keys suitable
    for Qdrant sparse vector upload.
    """
    try:
        from fastembed import SparseTextEmbedding

        model = SparseTextEmbedding(model_name="Qdrant/bm25")
        sparse_results = list(model.embed(texts))

        sparse_vectors = []
        for result in sparse_results:
            sparse_vectors.append(
                {
                    "indices": result.indices.tolist(),
                    "values": result.values.tolist(),
                }
            )
        return sparse_vectors

    except ImportError:
        logger.error("fastembed is not installed. Install with: pip install fastembed")
        raise
    except Exception as exc:
        logger.error("Sparse embedding generation failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="workers.embedding_generator.generate_embeddings",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    track_started=True,
)
def generate_embeddings(
    self,
    document_id: str,
    chunk_ids: list[str],
) -> dict[str, Any]:
    """Generate dense and sparse embeddings for a batch of document chunks.

    Steps:
      1. Load chunk records from the database.
      2. Generate dense embeddings via the KURE-v1 embedding service.
      3. Generate sparse BM25 vectors via fastembed.
      4. Upsert vectors to the org-specific Qdrant collection.
      5. Update chunk records with their Qdrant point IDs.
      6. Update the document's embedded chunk count.
    """
    logger.info(
        "Generating embeddings for document %s, %d chunks",
        document_id,
        len(chunk_ids),
    )

    try:
        # Step 1: Load chunks from DB
        chunks = _run_async(_load_chunks(chunk_ids))
        if not chunks:
            logger.warning("No chunks found for IDs: %s", chunk_ids)
            return {
                "document_id": document_id,
                "status": "skipped",
                "reason": "no_chunks_found",
            }

        texts = [chunk["content"] for chunk in chunks]

        # Step 2: Generate dense embeddings
        logger.info("Generating dense embeddings for %d chunks", len(texts))
        dense_embeddings = _generate_dense_embeddings(texts)

        # Step 3: Generate sparse BM25 vectors
        logger.info("Generating sparse BM25 vectors for %d chunks", len(texts))
        sparse_vectors = _generate_sparse_embeddings(texts)

        # Step 4: Upsert to Qdrant
        org_id = _run_async(_get_document_org_id(document_id))
        if org_id is None:
            raise ValueError(f"Could not determine organisation for document: {document_id}")

        document_name = _run_async(_get_document_name(document_id))

        from app.integrations.vector_store.qdrant_client import QdrantService

        qdrant = QdrantService(
            url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
            api_key=settings.qdrant_api_key,
        )

        # Ensure collection exists
        qdrant.ensure_collection(org_id)

        # Build point structs for Qdrant
        from qdrant_client.models import PointStruct, SparseVector

        points: list[PointStruct] = []
        chunk_qdrant_map: dict[str, str] = {}

        for i, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            chunk_id = str(chunk["id"])
            chunk_qdrant_map[chunk_id] = point_id

            payload = {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_id": chunk_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "section_title": chunk.get("section_title", ""),
                "chunk_type": chunk.get("chunk_type", "text"),
                "page_number": chunk.get("page_number"),
                "token_count": chunk.get("token_count", 0),
                "organization_id": org_id,
            }

            point = PointStruct(
                id=point_id,
                vector={
                    "dense": dense_embeddings[i],
                    "sparse": SparseVector(
                        indices=sparse_vectors[i]["indices"],
                        values=sparse_vectors[i]["values"],
                    ),
                },
                payload=payload,
            )
            points.append(point)

        logger.info(
            "Upserting %d points to Qdrant collection for org %s",
            len(points),
            org_id,
        )
        qdrant.upsert_vectors(org_id, points)

        # Step 5: Update chunk records with Qdrant point IDs
        _run_async(_update_chunk_qdrant_ids(chunk_qdrant_map))

        # Step 6: Update document's embedded chunk count
        _run_async(_update_document_chunk_count(document_id))

        logger.info(
            "Embedding generation complete for document %s: %d vectors",
            document_id,
            len(points),
        )

        return {
            "document_id": document_id,
            "status": "completed",
            "vectors_created": len(points),
            "chunk_ids": list(chunk_qdrant_map.keys()),
        }

    except Exception as exc:
        logger.exception(
            "Embedding generation failed for document %s: %s",
            document_id,
            exc,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                "Max retries exceeded for embedding generation, document %s",
                document_id,
            )
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(exc)[:500],
            }
