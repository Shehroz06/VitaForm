import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from app.core.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_HEADER_BYTES = REQUEST_ID_HEADER.encode("latin-1")

_Scope = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
_Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]


class RequestIdMiddleware:
    """Assigns a request id -- reusing an inbound X-Request-ID if a
    trusted upstream proxy already set one, otherwise generating one --
    so every log line for this request can be correlated, and echoes it
    back so a client or support ticket can quote it.

    Sets both a contextvar (request_id_var, read by the JSON log
    formatter -- works for arbitrary code deep in services/repositories
    with no Request object at hand) and scope["state"] (read by
    handle_unexpected_error). Both are needed: testing showed a
    contextvar set here doesn't reliably survive FastAPI/Starlette's
    nested exception-handling wrappers by the time an `@app.exception_handler`
    runs, even though it's still visible everywhere during normal
    execution -- scope["state"] is a plain dict passed by reference, so
    it's immune to whatever's truncating the contextvar across that
    specific boundary."""

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        inbound = dict(scope.get("headers") or []).get(b"x-request-id")
        request_id = inbound.decode("latin-1") if inbound else str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                message = dict(message)
                headers = list(message.get("headers") or [])
                headers.append((_REQUEST_ID_HEADER_BYTES, request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)
