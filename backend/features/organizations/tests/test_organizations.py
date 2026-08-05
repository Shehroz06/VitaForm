from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_organization(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "org1@example.com")

    response = await client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"organization_name": "ACM", "role": "Member"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["organization_name"] == "ACM"


async def test_create_organization_missing_name_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "org2@example.com")

    response = await client.post("/api/v1/organizations", headers=headers, json={})

    assert response.status_code == 422


async def test_get_update_delete_organization_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "org3@example.com")
    create_response = await client.post(
        "/api/v1/organizations", headers=headers, json={"organization_name": "ACM"}
    )
    organization_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/organizations/{organization_id}", headers=headers, json={"role": "Officer"}
    )
    assert update_response.json()["data"]["role"] == "Officer"

    delete_response = await client.delete(
        f"/api/v1/organizations/{organization_id}", headers=headers
    )
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_organizations(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "orgIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "orgIsoB@example.com")

    create_response = await client.post(
        "/api/v1/organizations", headers=headers_a, json={"organization_name": "ACM"}
    )
    organization_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/organizations/{organization_id}", headers=headers_b)
    assert response.status_code == 404
