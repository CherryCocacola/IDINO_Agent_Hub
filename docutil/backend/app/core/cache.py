"""
Redis caching layer for embeddings and search results.

Provides transparent caching for expensive operations like
OpenAI embedding API calls. Uses SHA256 hashing for cache keys
and JSON serialization for vector storage.
"""

from __future__ import annotations

import hashlib
import json
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client = None


async def get_redis():
    """Return a cached Redis async client (singleton)."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        from redis.asyncio import Redis

        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable -- caching disabled.")
        return None


async def close_redis():
    """Close the Redis connection on shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _embedding_key(text: str) -> str:
    """Build a Redis key from query text using SHA256."""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
    return f"emb_cache:{h}"


async def get_cached_embedding(text: str) -> list[float] | None:
    """Retrieve a cached embedding vector for *text*, or None."""
    try:
        redis = await get_redis()
        if redis is None:
            return None
        raw = await redis.get(_embedding_key(text))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.debug("Embedding cache read failed", exc_info=True)
        return None


async def set_cached_embedding(
    text: str,
    embedding: list[float],
    ttl: int | None = None,
) -> None:
    """Store an embedding vector in Redis with TTL."""
    try:
        redis = await get_redis()
        if redis is None:
            return
        settings = get_settings()
        ttl = ttl or settings.embedding_cache_ttl
        await redis.set(
            _embedding_key(text),
            json.dumps(embedding),
            ex=ttl,
        )
    except Exception:
        logger.debug("Embedding cache write failed", exc_info=True)
