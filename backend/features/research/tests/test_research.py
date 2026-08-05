from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_research(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "res1@example.com")

    response = await client.post(
        "/api/v1/research",
        headers=headers,
        json={
            "title": "Deep Learning for X",
            "publication_venue": "NeurIPS",
            "url": "https://arxiv.org/abs/1234",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["title"] == "Deep Learning for X"


async def test_create_research_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "res2@example.com")

    response = await client.post(
        "/api/v1/research", headers=headers, json={"title": "Paper", "url": "not-a-url"}
    )

    assert response.status_code == 422


async def test_get_update_delete_research_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "res3@example.com")
    create_response = await client.post(
        "/api/v1/research", headers=headers, json={"title": "Paper"}
    )
    research_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/research/{research_id}", headers=headers, json={"publication_venue": "ICML"}
    )
    assert update_response.json()["data"]["publication_venue"] == "ICML"

    delete_response = await client.delete(f"/api/v1/research/{research_id}", headers=headers)
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_research(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "resIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "resIsoB@example.com")

    create_response = await client.post(
        "/api/v1/research", headers=headers_a, json={"title": "Paper"}
    )
    research_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/research/{research_id}", headers=headers_b)
    assert response.status_code == 404
