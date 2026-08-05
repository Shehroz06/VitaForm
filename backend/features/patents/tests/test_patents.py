from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_patent(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "pat1@example.com")

    response = await client.post(
        "/api/v1/patents",
        headers=headers,
        json={"title": "Novel Widget", "status": "granted", "patent_number": "US123456"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "granted"


async def test_create_patent_with_invalid_status_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "pat2@example.com")

    response = await client.post(
        "/api/v1/patents", headers=headers, json={"title": "Widget", "status": "bogus"}
    )

    assert response.status_code == 422


async def test_create_patent_defaults_to_filed_status(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "pat3@example.com")

    response = await client.post("/api/v1/patents", headers=headers, json={"title": "Widget"})

    assert response.json()["data"]["status"] == "filed"


async def test_get_update_delete_patent_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "pat4@example.com")
    create_response = await client.post(
        "/api/v1/patents", headers=headers, json={"title": "Widget"}
    )
    patent_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/patents/{patent_id}", headers=headers, json={"status": "granted"}
    )
    assert update_response.json()["data"]["status"] == "granted"

    delete_response = await client.delete(f"/api/v1/patents/{patent_id}", headers=headers)
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_patents(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "patIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "patIsoB@example.com")

    create_response = await client.post(
        "/api/v1/patents", headers=headers_a, json={"title": "Widget"}
    )
    patent_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/patents/{patent_id}", headers=headers_b)
    assert response.status_code == 404
