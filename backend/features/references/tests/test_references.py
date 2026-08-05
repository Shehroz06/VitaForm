from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_reference(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "ref1@example.com")

    response = await client.post(
        "/api/v1/references",
        headers=headers,
        json={
            "name": "Jane Doe",
            "relationship": "Former Manager",
            "contact_email": "jane@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["contact_email"] == "jane@example.com"


async def test_create_reference_with_invalid_email_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "ref2@example.com")

    response = await client.post(
        "/api/v1/references",
        headers=headers,
        json={"name": "Jane Doe", "contact_email": "not-an-email"},
    )

    assert response.status_code == 422


async def test_get_update_delete_reference_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "ref3@example.com")
    create_response = await client.post(
        "/api/v1/references", headers=headers, json={"name": "Jane Doe"}
    )
    reference_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/references/{reference_id}", headers=headers, json={"contact_phone": "555-1234"}
    )
    assert update_response.json()["data"]["contact_phone"] == "555-1234"

    delete_response = await client.delete(f"/api/v1/references/{reference_id}", headers=headers)
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_references(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "refIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "refIsoB@example.com")

    create_response = await client.post(
        "/api/v1/references", headers=headers_a, json={"name": "Jane Doe"}
    )
    reference_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/references/{reference_id}", headers=headers_b)
    assert response.status_code == 404
