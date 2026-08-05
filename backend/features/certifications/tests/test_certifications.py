from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_certification(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cert1@example.com")

    response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={
            "name": "AWS Certified Solutions Architect",
            "issuing_organization": "Amazon",
            "issue_date": "2023-01-01",
            "expiration_date": "2026-01-01",
            "credential_url": "https://aws.example.com/cert/123",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "AWS Certified Solutions Architect"


async def test_create_certification_with_invalid_date_order_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cert2@example.com")

    response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={
            "name": "Cert",
            "issuing_organization": "Org",
            "issue_date": "2024-01-01",
            "expiration_date": "2020-01-01",
        },
    )

    assert response.status_code == 422


async def test_create_certification_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cert3@example.com")

    response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "Cert", "issuing_organization": "Org", "credential_url": "not-a-url"},
    )

    assert response.status_code == 422


async def test_get_update_delete_certification_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cert4@example.com")
    create_response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "Cert", "issuing_organization": "Org"},
    )
    certification_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/certifications/{certification_id}",
        headers=headers,
        json={"credential_id": "ABC123"},
    )
    assert update_response.json()["data"]["credential_id"] == "ABC123"

    delete_response = await client.delete(
        f"/api/v1/certifications/{certification_id}", headers=headers
    )
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_certifications(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "certIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "certIsoB@example.com")

    create_response = await client.post(
        "/api/v1/certifications",
        headers=headers_a,
        json={"name": "Cert", "issuing_organization": "Org"},
    )
    certification_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/certifications/{certification_id}", headers=headers_b)
    assert response.status_code == 404
