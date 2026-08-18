from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def test_get_my_profile_auto_creates_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    token = await create_verified_user_and_login(client, captured_emails, "profile1@example.com")

    response = await client.get("/api/v1/profiles/me", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["headline"] is None
    assert data["completion_percentage"] == 0


async def test_get_my_profile_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/profiles/me")

    assert response.status_code == 401


async def test_update_my_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    token = await create_verified_user_and_login(client, captured_emails, "profile2@example.com")

    response = await client.patch(
        "/api/v1/profiles/me",
        headers=auth_headers(token),
        json={"headline": "Engineer", "bio": "Building things.", "location": "Remote"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["headline"] == "Engineer"
    assert data["location"] == "Remote"


async def test_update_profile_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    token = await create_verified_user_and_login(client, captured_emails, "profile3@example.com")

    response = await client.patch(
        "/api/v1/profiles/me",
        headers=auth_headers(token),
        json={"github_url": "not-a-url"},
    )

    assert response.status_code == 422


async def test_completion_percentage_increases_with_each_section(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    token = await create_verified_user_and_login(client, captured_emails, "profile4@example.com")
    headers = auth_headers(token)

    await client.patch(
        "/api/v1/auth/me", headers=headers, json={"first_name": "Test", "last_name": "User"}
    )
    first = await client.get("/api/v1/profiles/me", headers=headers)
    assert first.json()["data"]["completion_percentage"] == 20

    await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc",
            "start_date": "2020-01-01",
        },
    )
    second = await client.get("/api/v1/profiles/me", headers=headers)
    assert second.json()["data"]["completion_percentage"] == 40


async def test_profile_is_isolated_per_user(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    token_a = await create_verified_user_and_login(client, captured_emails, "isoA@example.com")
    token_b = await create_verified_user_and_login(client, captured_emails, "isoB@example.com")

    await client.patch(
        "/api/v1/profiles/me", headers=auth_headers(token_a), json={"headline": "A's headline"}
    )

    response_b = await client.get("/api/v1/profiles/me", headers=auth_headers(token_b))
    assert response_b.json()["data"]["headline"] is None
