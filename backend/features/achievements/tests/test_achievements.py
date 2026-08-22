from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_achievement(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "ach1@example.com")

    response = await client.post(
        "/api/v1/achievements",
        headers=headers,
        json={"title": "Employee of the Year", "issuer": "Acme Corp"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["title"] == "Employee of the Year"


async def test_create_achievement_missing_title_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "ach2@example.com")

    response = await client.post("/api/v1/achievements", headers=headers, json={})

    assert response.status_code == 422


async def test_get_update_delete_achievement_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "ach3@example.com")
    create_response = await client.post(
        "/api/v1/achievements", headers=headers, json={"title": "First place"}
    )
    achievement_id = create_response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/achievements/{achievement_id}", headers=headers)
    assert get_response.status_code == 200

    update_response = await client.patch(
        f"/api/v1/achievements/{achievement_id}", headers=headers, json={"issuer": "Updated Co"}
    )
    assert update_response.json()["data"]["issuer"] == "Updated Co"

    delete_response = await client.delete(
        f"/api/v1/achievements/{achievement_id}", headers=headers
    )
    assert delete_response.status_code == 204

    get_after_delete = await client.get(f"/api/v1/achievements/{achievement_id}", headers=headers)
    assert get_after_delete.status_code == 404


async def test_users_cannot_access_each_others_achievements(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "achIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "achIsoB@example.com")

    create_response = await client.post(
        "/api/v1/achievements", headers=headers_a, json={"title": "Secret"}
    )
    achievement_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/achievements/{achievement_id}", headers=headers_b)
    assert response.status_code == 404
