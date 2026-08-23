from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_interest(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interest1@example.com")

    response = await client.post(
        "/api/v1/interests",
        headers=headers,
        json={"name": "Chess", "description": "Competitive club player."},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Chess"
    assert data["description"] == "Competitive club player."


async def test_create_interest_without_description_is_optional(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interest2@example.com")

    response = await client.post(
        "/api/v1/interests", headers=headers, json={"name": "Photography"}
    )

    assert response.status_code == 201
    assert response.json()["data"]["description"] is None


async def test_create_interest_with_blank_name_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interest3@example.com")

    response = await client.post("/api/v1/interests", headers=headers, json={"name": ""})
    assert response.status_code == 422


async def test_get_update_delete_interest_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interest4@example.com")
    create_response = await client.post(
        "/api/v1/interests", headers=headers, json={"name": "Chess"}
    )
    interest_id = create_response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/interests/{interest_id}", headers=headers)
    assert get_response.json()["data"]["name"] == "Chess"

    update_response = await client.patch(
        f"/api/v1/interests/{interest_id}", headers=headers, json={"name": "Chess (Club Level)"}
    )
    assert update_response.json()["data"]["name"] == "Chess (Club Level)"

    delete_response = await client.delete(f"/api/v1/interests/{interest_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/api/v1/interests/{interest_id}", headers=headers)
    assert missing_response.status_code == 404


async def test_list_interests_supports_sort_query_param(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interestSort@example.com")
    await client.post("/api/v1/interests", headers=headers, json={"name": "Zebra"})
    await client.post("/api/v1/interests", headers=headers, json={"name": "Apple"})

    response = await client.get("/api/v1/interests?sort=name", headers=headers)
    names = [item["name"] for item in response.json()["data"]]
    assert names == ["Apple", "Zebra"]


async def test_list_interests_rejects_invalid_sort_field(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "interestSortBad@example.com")

    response = await client.get("/api/v1/interests?sort=not_a_field", headers=headers)
    assert response.status_code == 422


async def test_users_cannot_access_each_others_interests(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "interestIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "interestIsoB@example.com")

    create_response = await client.post(
        "/api/v1/interests", headers=headers_a, json={"name": "Chess"}
    )
    interest_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/interests/{interest_id}", headers=headers_b)
    assert response.status_code == 404
