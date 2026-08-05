from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_volunteer_experience(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "vol1@example.com")

    response = await client.post(
        "/api/v1/volunteer-experience",
        headers=headers,
        json={
            "organization_name": "Red Cross",
            "role": "Volunteer Coordinator",
            "start_date": "2021-01-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["organization_name"] == "Red Cross"


async def test_create_volunteer_experience_invalid_date_order_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "vol2@example.com")

    response = await client.post(
        "/api/v1/volunteer-experience",
        headers=headers,
        json={
            "organization_name": "Org",
            "role": "Role",
            "start_date": "2024-01-01",
            "end_date": "2020-01-01",
        },
    )

    assert response.status_code == 422


async def test_get_update_delete_volunteer_experience_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "vol3@example.com")
    create_response = await client.post(
        "/api/v1/volunteer-experience",
        headers=headers,
        json={"organization_name": "Org", "role": "Role", "start_date": "2021-01-01"},
    )
    entry_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/volunteer-experience/{entry_id}", headers=headers, json={"is_current": True}
    )
    assert update_response.json()["data"]["is_current"] is True

    delete_response = await client.delete(
        f"/api/v1/volunteer-experience/{entry_id}", headers=headers
    )
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_volunteer_experience(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "volIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "volIsoB@example.com")

    create_response = await client.post(
        "/api/v1/volunteer-experience",
        headers=headers_a,
        json={"organization_name": "Org", "role": "Role", "start_date": "2021-01-01"},
    )
    entry_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/volunteer-experience/{entry_id}", headers=headers_b)
    assert response.status_code == 404
