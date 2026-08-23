from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def test_response_carries_a_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.headers.get("X-Request-ID")


async def test_each_request_gets_a_distinct_request_id(client: AsyncClient) -> None:
    first = await client.get("/api/v1/health")
    second = await client.get("/api/v1/health")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


async def test_inbound_request_id_is_echoed_back(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "trace-abc-123"})
    assert response.headers["X-Request-ID"] == "trace-abc-123"


async def test_unhandled_exception_response_includes_the_request_id() -> None:
    """Builds a fresh app with one route that always raises, to exercise
    the catch-all exception handler's request_id wiring without needing a
    real bug to trigger it through the normal feature routes."""
    app = create_app()

    @app.get("/api/v1/_boom")
    async def _boom() -> None:
        raise RuntimeError("deliberate failure for this test")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/_boom", headers={"X-Request-ID": "trace-boom-1"}
        )

    assert response.status_code == 500
    body = response.json()
    assert body["request_id"] == "trace-boom-1"
    assert response.headers["X-Request-ID"] == "trace-boom-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
