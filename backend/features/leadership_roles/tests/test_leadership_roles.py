from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_leadership_role(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "lead1@example.com")

    response = await client.post(
        "/api/v1/leadership-roles",
        headers=headers,
        json={
            "organization_name": "Student Council",
            "title": "President",
            "start_date": "2021-01-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["title"] == "President"


async def test_create_leadership_role_invalid_date_order_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "lead2@example.com")

    response = await client.post(
        "/api/v1/leadership-roles",
        headers=headers,
        json={
            "organization_name": "Org",
            "title": "Title",
            "start_date": "2024-01-01",
            "end_date": "2020-01-01",
        },
    )

    assert response.status_code == 422


async def test_get_update_delete_leadership_role_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "lead3@example.com")
    create_response = await client.post(
        "/api/v1/leadership-roles",
        headers=headers,
        json={"organization_name": "Org", "title": "Title", "start_date": "2021-01-01"},
    )
    role_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/leadership-roles/{role_id}", headers=headers, json={"title": "VP"}
    )
    assert update_response.json()["data"]["title"] == "VP"

    delete_response = await client.delete(f"/api/v1/leadership-roles/{role_id}", headers=headers)
    assert delete_response.status_code == 204


async def test_users_cannot_access_each_others_leadership_roles(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "leadIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "leadIsoB@example.com")

    create_response = await client.post(
        "/api/v1/leadership-roles",
        headers=headers_a,
        json={"organization_name": "Org", "title": "Title", "start_date": "2021-01-01"},
    )
    role_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/leadership-roles/{role_id}", headers=headers_b)
    assert response.status_code == 404
