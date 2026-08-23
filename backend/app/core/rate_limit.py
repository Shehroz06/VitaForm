from redis.asyncio import Redis

from app.exceptions.base import RateLimitExceededException


async def enforce_rate_limit(
    redis_client: Redis, key: str, max_requests: int, window_seconds: int
) -> None:
    """Fixed-window counter: INCRs `key`, sets its TTL on the first hit in
    the window, and raises once the count exceeds `max_requests`."""
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)
    if current > max_requests:
        raise RateLimitExceededException("Too many requests. Please try again later.")
