from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_competition(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "comp1@example.com")

    response = await client.post(
        "/api/v1/competitions",
        headers=headers,
        json={"name": "ACM ICPC", "result": "Finalist"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "ACM ICPC"


async def test_create_competition_missing_name_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "comp2@example.com")

    response = await client.post("/api/v1/competitions", headers=headers, json={})

    assert response.status_code == 422


async def test_get_update_delete_competition_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "comp3@example.com")
    create_response = await client.post(
        "/api/v1/competitions", headers=headers, json={"name": "ACM ICPC"}
    )
    competition_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/competitions/{competition_id}", headers=headers, json={"result": "Winner"}
    )
    assert update_response.json()["data"]["result"] == "Winner"

    delete_response = await client.delete(
        f"/api/v1/competitions/{competition_id}", headers=headers
    )
    assert delete_response.status_code == 200


async def test_users_cannot_access_each_others_competitions(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "compIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "compIsoB@example.com")

    create_response = await client.post(
        "/api/v1/competitions", headers=headers_a, json={"name": "ACM ICPC"}
    )
    competition_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/competitions/{competition_id}", headers=headers_b)
    assert response.status_code == 404
