from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.rate_limit import (
    RateLimitStrategy,
    create_rate_limiter,
)

# Global rate limiter instance
global_rate_limiter = create_rate_limiter(
    requests=settings.RATE_LIMIT_GLOBAL_REQUESTS,
    window_seconds=settings.RATE_LIMIT_GLOBAL_WINDOW,
    strategy=RateLimitStrategy.IP,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for global rate limiting across all endpoints.

    This middleware applies rate limiting to all requests before they reach
    the route handlers. It can be enabled/disabled via RATE_LIMIT_ENABLED setting.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        endpoint = f"{request.method}:{request.url.path}"

        try:
            (
                is_allowed,
                remaining,
                retry_after,
            ) = await global_rate_limiter.check_rate_limit(request, endpoint, user=None)
        except Exception:
            return await call_next(request)

        if not is_allowed:
            error_msg = (
                f"Rate limit exceeded: {settings.RATE_LIMIT_GLOBAL_REQUESTS} "
                f"requests per {settings.RATE_LIMIT_GLOBAL_WINDOW} seconds"
            )
            response = Response(
                content=error_msg,
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_GLOBAL_REQUESTS),
                    "X-RateLimit-Window": str(settings.RATE_LIMIT_GLOBAL_WINDOW),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after)
                    if retry_after
                    else str(settings.RATE_LIMIT_GLOBAL_WINDOW),
                },
            )
            return response

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_GLOBAL_REQUESTS)
        response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_GLOBAL_WINDOW)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
