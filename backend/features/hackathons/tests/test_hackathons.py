from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_hackathon(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "hack1@example.com")

    response = await client.post(
        "/api/v1/hackathons",
        headers=headers,
        json={"name": "HackMIT", "project_name": "Career OS", "result": "Winner"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "HackMIT"


async def test_create_hackathon_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "hack2@example.com")

    response = await client.post(
        "/api/v1/hackathons", headers=headers, json={"name": "HackMIT", "url": "not-a-url"}
    )

    assert response.status_code == 422


async def test_get_update_delete_hackathon_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "hack3@example.com")
    create_response = await client.post(
        "/api/v1/hackathons", headers=headers, json={"name": "HackMIT"}
    )
    hackathon_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/hackathons/{hackathon_id}", headers=headers, json={"result": "2nd place"}
    )
    assert update_response.json()["data"]["result"] == "2nd place"

    delete_response = await client.delete(f"/api/v1/hackathons/{hackathon_id}", headers=headers)
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_hackathons(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "hackIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "hackIsoB@example.com")

    create_response = await client.post(
        "/api/v1/hackathons", headers=headers_a, json={"name": "HackMIT"}
    )
    hackathon_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/hackathons/{hackathon_id}", headers=headers_b)
    assert response.status_code == 404
