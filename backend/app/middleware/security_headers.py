from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

_HSTS_MAX_AGE_SECONDS = 63_072_000  # 2 years, the standard HSTS preload floor

_Scope = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
_Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]


def security_headers(*, secure: bool) -> dict[str, str]:
    """The header set SecurityHeadersMiddleware adds to every response --
    exposed as a plain function too, since handle_unexpected_error's
    catch-all Exception response needs to set these directly rather than
    relying on this middleware's own header injection (see that
    middleware's docstring for why)."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    if secure:
        headers["Strict-Transport-Security"] = f"max-age={_HSTS_MAX_AGE_SECONDS}; includeSubDomains"
    return headers


class SecurityHeadersMiddleware:
    """Adds the response headers CLAUDE.md's SECURITY section calls for
    that CORS/auth/validation don't already cover: clickjacking, MIME
    sniffing, and referrer leakage. HSTS is added only when `secure` is
    true (i.e. this is actually served over HTTPS) -- sending it over
    plain HTTP is a no-op in browsers but a misleading thing to emit.

    Deliberately a plain ASGI middleware, not BaseHTTPMiddleware: the
    latter runs the downstream app in a separate anyio task per layer,
    which (confirmed via RequestIdMiddleware's contextvar, in the same
    situation) doesn't reliably survive an exception-handler-produced
    response. Even as plain ASGI, testing showed the specific case of the
    catch-all `@app.exception_handler(Exception)` response still doesn't
    reliably pass back through this middleware's send wrapper (unlike
    every other response, including registered AppException handlers) --
    so that one handler sets these headers directly instead, via the
    `security_headers()` function above."""

    def __init__(self, app: Any, *, secure: bool) -> None:
        self._app = app
        self._secure = secure

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = [
            (key.encode("latin-1"), value.encode("latin-1"))
            for key, value in security_headers(secure=self._secure).items()
        ]

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = [*(message.get("headers") or []), *headers]
            await send(message)

        await self._app(scope, receive, send_wrapper)
