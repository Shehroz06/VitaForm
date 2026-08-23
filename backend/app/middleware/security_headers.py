from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_HSTS_MAX_AGE_SECONDS = 63_072_000  # 2 years, the standard HSTS preload floor


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds the response headers CLAUDE.md's SECURITY section calls for
    that CORS/auth/validation don't already cover: clickjacking, MIME
    sniffing, and referrer leakage. HSTS is added only when `secure` is
    true (i.e. this is actually served over HTTPS) -- sending it over
    plain HTTP is a no-op in browsers but a misleading thing to emit."""

    def __init__(self, app, *, secure: bool) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._secure = secure

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if self._secure:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={_HSTS_MAX_AGE_SECONDS}; includeSubDomains"
            )
        return response
