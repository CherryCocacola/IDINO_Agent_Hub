"""
ASGI middleware: structured request logging, Redis-backed rate limiting,
and CORS configuration helper.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .config import get_settings

if TYPE_CHECKING:
    from starlette.types import ASGIApp

logger = logging.getLogger("document_utilization")


# ---------------------------------------------------------------------------
# 1. Request logging
# ---------------------------------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration.

    A unique ``X-Request-ID`` is injected into each request/response so
    that log lines can be correlated with client-side traces.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            uuid.uuid4().hex,
        )
        # Stash for downstream handlers
        request.state.request_id = request_id

        # Extract and store client IP for audit context
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = (
            forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        )
        request.state.client_ip = client_ip

        start = time.perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        except Exception:
            logger.exception(
                "Unhandled exception | %s %s | request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            status_code = response.status_code if response else 500

            log_data: dict[str, Any] = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params) if request.query_params else None,
                "status": status_code,
                "duration_ms": round(elapsed_ms, 2),
                "client_ip": (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                    or (request.client.host if request.client else "unknown")
                ),
                "user_agent": request.headers.get("User-Agent", ""),
            }

            log_line = (
                f"{log_data['method']} {log_data['path']} "
                f"-> {log_data['status']} ({log_data['duration_ms']}ms) "
                f"[{log_data['request_id']}]"
            )

            if status_code >= 500:
                logger.error(log_line, extra=log_data)
            elif status_code >= 400:
                logger.warning(log_line, extra=log_data)
            else:
                logger.info(log_line, extra=log_data)

            if response is not None:
                response.headers["X-Request-ID"] = request_id


# ---------------------------------------------------------------------------
# 2. Redis-backed rate limiter middleware
# ---------------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter that uses Redis for cross-worker state.

    Parameters
    ----------
    app:
        The ASGI app.
    redis_url:
        Redis connection string.  If ``None``, the middleware is a no-op so
        that the application can boot without Redis during development.
    max_requests:
        Maximum allowed requests within *window_seconds*.
    window_seconds:
        Length of the sliding window.
    exclude_paths:
        URL path prefixes that are exempt from rate limiting (e.g. health
        checks, OpenAPI schema).
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str | None = None,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self._redis: Any | None = None  # lazily initialised

    async def _get_redis(self) -> Any | None:
        """Lazy-connect to Redis using ``redis.asyncio``."""
        if self._redis is not None:
            return self._redis
        if self.redis_url is None:
            return None
        try:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            return self._redis
        except Exception:
            logger.warning("Redis unavailable -- rate limiting disabled.")
            return None

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        return f"rate_limit:{ip}:{request.url.path}"

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        redis = await self._get_redis()
        if redis is None:
            return await call_next(request)

        key = self._client_key(request)
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipe = redis.pipeline()
            # Remove entries outside the window
            await pipe.zremrangebyscore(key, "-inf", window_start)
            # Count remaining
            await pipe.zcard(key)
            # Add current request
            await pipe.zadd(key, {str(now): now})
            # Ensure key expires even if not cleaned up
            await pipe.expire(key, self.window_seconds * 2)
            results = await pipe.execute()

            request_count: int = results[1]
        except Exception:
            logger.warning("Redis error during rate limiting -- allowing request.")
            return await call_next(request)

        if request_count >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.window_seconds)),
                },
            )

        response = await call_next(request)
        remaining = max(0, self.max_requests - request_count - 1)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))
        return response


# ---------------------------------------------------------------------------
# 3. CORS helper
# ---------------------------------------------------------------------------
def setup_cors(app: FastAPI) -> None:
    """Attach ``CORSMiddleware`` to *app* using values from settings."""
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    )


# ---------------------------------------------------------------------------
# 4. Registration helper
# ---------------------------------------------------------------------------
def register_middleware(app: FastAPI) -> None:
    """Register all custom middleware on the FastAPI application.

    Call this **once** during application startup, *after* routers have been
    included, because Starlette middleware wraps the app from outside-in::

        app = FastAPI(...)
        # ... include_routers ...
        register_middleware(app)
    """
    settings = get_settings()

    # CORS must be outermost
    setup_cors(app)

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
        max_requests=100,
        window_seconds=60,
    )

    # Request logging (innermost -- runs first on the way in)
    app.add_middleware(RequestLoggingMiddleware)
