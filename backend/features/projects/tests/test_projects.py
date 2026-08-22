from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def _create_skill(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.post(
        "/api/v1/skills", headers=headers, json={"name": name, "category": "technical"}
    )
    skill_id: str = response.json()["data"]["id"]
    return skill_id


async def test_create_project_without_skills(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj1@example.com")

    response = await client.post(
        "/api/v1/projects", headers=headers, json={"title": "Career OS"}
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Career OS"
    assert data["status"] == "in_progress"
    assert data["skills"] == []


async def test_create_project_with_skills(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj2@example.com")
    skill_id = await _create_skill(client, headers, "Python")

    response = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Career OS", "skill_ids": [skill_id]},
    )

    assert response.status_code == 201
    skills = response.json()["data"]["skills"]
    assert len(skills) == 1
    assert skills[0]["name"] == "Python"


async def test_create_project_with_foreign_skill_id_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "projForeignA@example.com")
    headers_b = await _auth(client, captured_emails, "projForeignB@example.com")
    other_users_skill_id = await _create_skill(client, headers_b, "Rust")

    response = await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"title": "Career OS", "skill_ids": [other_users_skill_id]},
    )

    assert response.status_code == 422


async def test_update_project_replaces_skill_list(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj3@example.com")
    python_id = await _create_skill(client, headers, "Python")
    rust_id = await _create_skill(client, headers, "Rust")

    create_response = await client.post(
        "/api/v1/projects", headers=headers, json={"title": "Career OS", "skill_ids": [python_id]}
    )
    project_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}", headers=headers, json={"skill_ids": [rust_id]}
    )

    skills = update_response.json()["data"]["skills"]
    assert len(skills) == 1
    assert skills[0]["name"] == "Rust"


async def test_update_project_without_skill_ids_leaves_skills_untouched(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj4@example.com")
    skill_id = await _create_skill(client, headers, "Python")
    create_response = await client.post(
        "/api/v1/projects", headers=headers, json={"title": "Career OS", "skill_ids": [skill_id]}
    )
    project_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}", headers=headers, json={"title": "Renamed"}
    )

    data = update_response.json()["data"]
    assert data["title"] == "Renamed"
    assert len(data["skills"]) == 1


async def test_update_project_with_empty_skill_ids_clears_skills(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj5@example.com")
    skill_id = await _create_skill(client, headers, "Python")
    create_response = await client.post(
        "/api/v1/projects", headers=headers, json={"title": "Career OS", "skill_ids": [skill_id]}
    )
    project_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}", headers=headers, json={"skill_ids": []}
    )

    assert update_response.json()["data"]["skills"] == []


async def test_create_project_with_invalid_url_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "proj6@example.com")

    response = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Career OS", "repository_url": "not-a-url"},
    )

    assert response.status_code == 422


async def test_delete_project(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "proj7@example.com")
    create_response = await client.post(
        "/api/v1/projects", headers=headers, json={"title": "Career OS"}
    )
    project_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_response.status_code == 404


async def test_users_cannot_access_each_others_projects(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "projIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "projIsoB@example.com")

    create_response = await client.post(
        "/api/v1/projects", headers=headers_a, json={"title": "Career OS"}
    )
    project_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert response.status_code == 404
