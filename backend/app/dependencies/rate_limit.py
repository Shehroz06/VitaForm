from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.rate_limit import enforce_rate_limit
from app.core.redis import get_redis_client
from app.dependencies.auth import CurrentUser


class IpRateLimit:
    """Per-IP fixed-window limiter for endpoints reachable before login
    (register, login, forgot-password), where no account identity exists
    yet to scope the limit to. A stable, importable instance -- usable
    directly as `Depends(instance)` -- so tests can override it by identity,
    exactly like get_db / get_email_sender."""

    def __init__(self, scope: str, max_requests: int, window_seconds: int) -> None:
        self._scope = scope
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def __call__(
        self,
        request: Request,
        redis_client: Annotated[Redis, Depends(get_redis_client)],
    ) -> None:
        client_ip = request.client.host if request.client else "unknown"
        await enforce_rate_limit(
            redis_client,
            f"ratelimit:{self._scope}:{client_ip}",
            self._max_requests,
            self._window_seconds,
        )


class UserRateLimit:
    """Per-user fixed-window limiter for cost-bearing endpoints (AI
    generation, PDF/LaTeX rendering) -- scoped to the account rather than
    the network, so a shared office IP doesn't throttle unrelated users."""

    def __init__(self, scope: str, max_requests: int, window_seconds: int) -> None:
        self._scope = scope
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def __call__(
        self,
        user: CurrentUser,
        redis_client: Annotated[Redis, Depends(get_redis_client)],
    ) -> None:
        await enforce_rate_limit(
            redis_client,
            f"ratelimit:{self._scope}:{user.id}",
            self._max_requests,
            self._window_seconds,
        )
