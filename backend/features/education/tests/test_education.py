from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_education(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "edu1@example.com")

    response = await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc Computer Science",
            "start_date": "2020-09-01",
            "end_date": "2024-06-01",
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["institution_name"] == "MIT"
    assert data["is_current"] is False


async def test_create_education_with_invalid_date_order_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "edu2@example.com")

    response = await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc",
            "start_date": "2024-01-01",
            "end_date": "2020-01-01",
        },
    )

    assert response.status_code == 422


async def test_create_education_missing_required_field_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "edu3@example.com")

    response = await client.post(
        "/api/v1/education", headers=headers, json={"degree": "BSc"}
    )

    assert response.status_code == 422


async def test_list_education_is_paginated(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "edu4@example.com")
    for i in range(3):
        await client.post(
            "/api/v1/education",
            headers=headers,
            json={
                "institution_name": f"School {i}",
                "degree": "BSc",
                "start_date": "2020-01-01",
            },
        )

    response = await client.get("/api/v1/education?page=1&limit=2", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"] == {"page": 1, "limit": 2, "total": 3, "pages": 2}


async def test_get_update_delete_education_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "edu5@example.com")
    create_response = await client.post(
        "/api/v1/education",
        headers=headers,
        json={"institution_name": "MIT", "degree": "BSc", "start_date": "2020-01-01"},
    )
    education_id = create_response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/education/{education_id}", headers=headers)
    assert get_response.status_code == 200

    update_response = await client.patch(
        f"/api/v1/education/{education_id}", headers=headers, json={"grade": "3.9"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["grade"] == "3.9"

    delete_response = await client.delete(f"/api/v1/education/{education_id}", headers=headers)
    assert delete_response.status_code == 200

    get_after_delete = await client.get(f"/api/v1/education/{education_id}", headers=headers)
    assert get_after_delete.status_code == 404


async def test_get_nonexistent_education_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "edu6@example.com")

    response = await client.get(
        "/api/v1/education/00000000-0000-0000-0000-000000000000", headers=headers
    )

    assert response.status_code == 404


async def test_education_list_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/education")

    assert response.status_code == 401


async def test_users_cannot_access_each_others_education(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "eduIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "eduIsoB@example.com")

    create_response = await client.post(
        "/api/v1/education",
        headers=headers_a,
        json={"institution_name": "MIT", "degree": "BSc", "start_date": "2020-01-01"},
    )
    education_id = create_response.json()["data"]["id"]

    get_as_b = await client.get(f"/api/v1/education/{education_id}", headers=headers_b)
    assert get_as_b.status_code == 404

    update_as_b = await client.patch(
        f"/api/v1/education/{education_id}", headers=headers_b, json={"grade": "hacked"}
    )
    assert update_as_b.status_code == 404

    delete_as_b = await client.delete(f"/api/v1/education/{education_id}", headers=headers_b)
    assert delete_as_b.status_code == 404

    list_as_b = await client.get("/api/v1/education", headers=headers_b)
    assert list_as_b.json()["meta"]["total"] == 0
