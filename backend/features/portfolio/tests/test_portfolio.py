from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_portfolio_item(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolio1@example.com")

    response = await client.post(
        "/api/v1/portfolio",
        headers=headers,
        json={
            "title": "Brand Redesign",
            "description": "Full visual identity refresh for a fintech client.",
            "url": "https://example.com/case-studies/brand-redesign",
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Brand Redesign"
    assert data["url"] == "https://example.com/case-studies/brand-redesign"


async def test_create_portfolio_item_without_url_is_optional(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolio2@example.com")

    response = await client.post(
        "/api/v1/portfolio", headers=headers, json={"title": "Brand Redesign"}
    )

    assert response.status_code == 201
    assert response.json()["data"]["url"] is None


async def test_create_portfolio_item_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolio3@example.com")

    response = await client.post(
        "/api/v1/portfolio",
        headers=headers,
        json={"title": "Brand Redesign", "url": "not-a-url"},
    )
    assert response.status_code == 422


async def test_get_update_delete_portfolio_item_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolio4@example.com")
    create_response = await client.post(
        "/api/v1/portfolio", headers=headers, json={"title": "Brand Redesign"}
    )
    item_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/portfolio/{item_id}",
        headers=headers,
        json={"title": "Brand Redesign (2024)"},
    )
    assert update_response.json()["data"]["title"] == "Brand Redesign (2024)"

    delete_response = await client.delete(f"/api/v1/portfolio/{item_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/api/v1/portfolio/{item_id}", headers=headers)
    assert missing_response.status_code == 404


async def test_list_portfolio_items_supports_sort_query_param(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolioSort@example.com")
    await client.post("/api/v1/portfolio", headers=headers, json={"title": "Zebra Project"})
    await client.post("/api/v1/portfolio", headers=headers, json={"title": "Apple Project"})

    response = await client.get("/api/v1/portfolio?sort=title", headers=headers)
    titles = [item["title"] for item in response.json()["data"]]
    assert titles == ["Apple Project", "Zebra Project"]


async def test_list_portfolio_items_rejects_invalid_sort_field(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "portfolioSortBad@example.com")

    response = await client.get("/api/v1/portfolio?sort=not_a_field", headers=headers)
    assert response.status_code == 422


async def test_users_cannot_access_each_others_portfolio_items(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "portfolioIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "portfolioIsoB@example.com")

    create_response = await client.post(
        "/api/v1/portfolio", headers=headers_a, json={"title": "Brand Redesign"}
    )
    item_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/portfolio/{item_id}", headers=headers_b)
    assert response.status_code == 404
