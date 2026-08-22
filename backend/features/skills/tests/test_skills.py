from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_skill(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "skill1@example.com")

    response = await client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "Python", "category": "technical", "level": "expert"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Python"
    assert data["category"] == "technical"
    assert data["level"] == "expert"


async def test_create_skill_without_level_is_optional(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "skill2@example.com")

    response = await client.post(
        "/api/v1/skills", headers=headers, json={"name": "Leadership", "category": "soft"}
    )

    assert response.status_code == 201
    assert response.json()["data"]["level"] is None


async def test_create_skill_with_invalid_category_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "skill3@example.com")

    response = await client.post(
        "/api/v1/skills", headers=headers, json={"name": "Python", "category": "bogus"}
    )

    assert response.status_code == 422


async def test_list_skills_sorted_by_name(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "skill4@example.com")
    for name in ["Zig", "Python", "Ada"]:
        await client.post(
            "/api/v1/skills", headers=headers, json={"name": name, "category": "technical"}
        )

    response = await client.get("/api/v1/skills", headers=headers)

    names = [item["name"] for item in response.json()["data"]]
    assert names == ["Ada", "Python", "Zig"]


async def test_resubmitting_same_skill_name_is_idempotent(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "skill5@example.com")

    first = await client.post(
        "/api/v1/skills", headers=headers, json={"name": "Python", "category": "technical"}
    )
    second = await client.post(
        "/api/v1/skills", headers=headers, json={"name": "python", "category": "technical"}
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]

    list_response = await client.get("/api/v1/skills", headers=headers)
    assert list_response.json()["meta"]["total"] == 1


async def test_users_cannot_access_each_others_skills(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "skillIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "skillIsoB@example.com")

    create_response = await client.post(
        "/api/v1/skills", headers=headers_a, json={"name": "Python", "category": "technical"}
    )
    skill_id = create_response.json()["data"]["id"]

    response = await client.delete(f"/api/v1/skills/{skill_id}", headers=headers_b)
    assert response.status_code == 404
