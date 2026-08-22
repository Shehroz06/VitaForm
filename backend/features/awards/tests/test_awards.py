from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_award(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "award1@example.com")

    response = await client.post(
        "/api/v1/awards", headers=headers, json={"title": "Best Paper", "issuer": "IEEE"}
    )

    assert response.status_code == 201
    assert response.json()["data"]["title"] == "Best Paper"


async def test_create_award_missing_title_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "award2@example.com")

    response = await client.post("/api/v1/awards", headers=headers, json={})

    assert response.status_code == 422


async def test_get_update_delete_award_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "award3@example.com")
    create_response = await client.post(
        "/api/v1/awards", headers=headers, json={"title": "Award"}
    )
    award_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/awards/{award_id}", headers=headers, json={"description": "Great honor"}
    )
    assert update_response.json()["data"]["description"] == "Great honor"

    delete_response = await client.delete(f"/api/v1/awards/{award_id}", headers=headers)
    assert delete_response.status_code == 204


async def test_users_cannot_access_each_others_awards(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "awardIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "awardIsoB@example.com")

    create_response = await client.post(
        "/api/v1/awards", headers=headers_a, json={"title": "Award"}
    )
    award_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/awards/{award_id}", headers=headers_b)
    assert response.status_code == 404
