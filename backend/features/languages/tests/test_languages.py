from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_language(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "lang1@example.com")

    response = await client.post(
        "/api/v1/languages",
        headers=headers,
        json={"name": "French", "proficiency": "fluent"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["proficiency"] == "fluent"


async def test_create_language_with_invalid_proficiency_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "lang2@example.com")

    response = await client.post(
        "/api/v1/languages", headers=headers, json={"name": "French", "proficiency": "bogus"}
    )

    assert response.status_code == 422


async def test_get_update_delete_language_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "lang3@example.com")
    create_response = await client.post(
        "/api/v1/languages", headers=headers, json={"name": "French", "proficiency": "basic"}
    )
    language_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/languages/{language_id}", headers=headers, json={"proficiency": "native"}
    )
    assert update_response.json()["data"]["proficiency"] == "native"

    delete_response = await client.delete(f"/api/v1/languages/{language_id}", headers=headers)
    assert delete_response.status_code == 204


async def test_users_cannot_access_each_others_languages(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "langIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "langIsoB@example.com")

    create_response = await client.post(
        "/api/v1/languages", headers=headers_a, json={"name": "French", "proficiency": "basic"}
    )
    language_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/languages/{language_id}", headers=headers_b)
    assert response.status_code == 404
