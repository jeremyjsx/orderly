import time
from enum import Enum

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.core.redis import get_redis
from app.modules.users.models import User

security = HTTPBearer(auto_error=False)


class RateLimitStrategy(str, Enum):
    IP = "ip"
    USER = "user"
    IP_OR_USER = "ip_or_user"


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window: int,
        remaining: int = 0,
        retry_after: int | None = None,
    ):
        self.limit = limit
        self.window = window
        self.remaining = remaining
        self.retry_after = retry_after

        detail = f"Rate limit exceeded: {limit} requests per {window} seconds"
        if retry_after:
            detail += f". Retry after {retry_after} seconds"

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build rate limit headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Window": str(self.window),
            "X-RateLimit-Remaining": str(self.remaining),
        }
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class RateLimiter:
    """
    Redis-based rate limiter using sliding window log algorithm.

    This implementation uses a sorted set in Redis to track requests
    within a time window, providing accurate rate limiting.
    """

    def __init__(
        self,
        requests: int,
        window_seconds: int,
        strategy: RateLimitStrategy = RateLimitStrategy.IP,
        key_prefix: str = "rate_limit",
    ):
        """
        Initialize rate limiter.

        Args:
            requests: Number of requests allowed
            window_seconds: Time window in seconds
            strategy: Strategy for identifying the client
            key_prefix: Prefix for Redis keys
        """
        self.requests = requests
        self.window_seconds = window_seconds
        self.strategy = strategy
        self.key_prefix = key_prefix

    def _get_client_identifier(self, request: Request, user: User | None = None) -> str:
        """Get client identifier based on strategy."""
        if self.strategy == RateLimitStrategy.IP:
            return self._get_ip_address(request)
        elif self.strategy == RateLimitStrategy.USER:
            if not user:
                return self._get_ip_address(request)
            return f"user:{user.id}"
        elif self.strategy == RateLimitStrategy.IP_OR_USER:
            if user:
                return f"user:{user.id}"
            return self._get_ip_address(request)
        else:
            return self._get_ip_address(request)

    @staticmethod
    def _get_ip_address(request: Request) -> str:
        """Extract IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        if request.client:
            return request.client.host

        return "unknown"

    def _get_redis_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"{self.key_prefix}:{endpoint}:{identifier}"

    async def check_rate_limit(
        self, request: Request, endpoint: str, user: User | None = None
    ) -> tuple[bool, int, int | None]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        redis_client = get_redis()
        identifier = self._get_client_identifier(request, user)
        key = self._get_redis_key(identifier, endpoint)

        now = time.time()
        window_start = now - self.window_seconds

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        current_count = results[0]

        if current_count >= self.requests:
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(oldest_time + self.window_seconds - now) + 1
            else:
                retry_after = self.window_seconds

            return False, 0, retry_after

        await redis_client.zadd(key, {str(now): now})
        await redis_client.expire(key, self.window_seconds + 1)

        remaining = max(0, self.requests - current_count - 1)
        return True, remaining, None

    async def __call__(
        self, request: Request, endpoint: str, user: User | None = None
    ) -> None:
        """
        Check rate limit and raise exception if exceeded.

        This allows the rate limiter to be used as a dependency.
        """
        is_allowed, remaining, retry_after = await self.check_rate_limit(
            request, endpoint, user
        )

        if not is_allowed:
            raise RateLimitExceeded(
                limit=self.requests,
                window=self.window_seconds,
                remaining=remaining,
                retry_after=retry_after,
            )


async def rate_limit_by_ip(
    request: Request,
    limiter: RateLimiter,
    user: User | None = None,
) -> None:
    """
    Dependency for rate limiting by IP address.

    Usage:
        @router.post("/endpoint")
        async def endpoint(
            request: Request,
            _: None = Depends(rate_limit_by_ip_dep)
        ):
            ...
    """
    endpoint = f"{request.method}:{request.url.path}"
    await limiter(request, endpoint, user)


async def rate_limit_by_user(
    request: Request,
    limiter: RateLimiter,
    user: User | None = None,
) -> None:
    """
    Dependency for rate limiting by authenticated user.

    Usage:
        @router.post("/endpoint")
        async def endpoint(
            request: Request,
            current_user: User = Depends(get_current_user),
            _: None = Depends(rate_limit_by_user_dep)
        ):
            ...
    """
    endpoint = f"{request.method}:{request.url.path}"
    await limiter(request, endpoint, user)


def create_rate_limiter(
    requests: int,
    window_seconds: int,
    strategy: RateLimitStrategy = RateLimitStrategy.IP,
) -> RateLimiter:
    """Factory function to create a rate limiter."""
    return RateLimiter(
        requests=requests,
        window_seconds=window_seconds,
        strategy=strategy,
    )
