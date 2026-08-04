from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_create_experience(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "exp1@example.com")

    response = await client.post(
        "/api/v1/experience",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "job_title": "Backend Engineer",
            "employment_type": "full_time",
            "start_date": "2022-01-01",
            "is_current": True,
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["employment_type"] == "full_time"
    assert data["is_current"] is True


async def test_create_experience_with_invalid_employment_type_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "exp2@example.com")

    response = await client.post(
        "/api/v1/experience",
        headers=headers,
        json={
            "company_name": "Acme",
            "job_title": "Engineer",
            "employment_type": "not-a-real-type",
            "start_date": "2022-01-01",
        },
    )

    assert response.status_code == 422


async def test_update_and_delete_experience(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "exp3@example.com")
    create_response = await client.post(
        "/api/v1/experience",
        headers=headers,
        json={
            "company_name": "Acme",
            "job_title": "Engineer",
            "employment_type": "internship",
            "start_date": "2021-06-01",
            "end_date": "2021-09-01",
        },
    )
    experience_id = create_response.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/experience/{experience_id}",
        headers=headers,
        json={"job_title": "Senior Engineer"},
    )
    assert update_response.json()["data"]["job_title"] == "Senior Engineer"

    delete_response = await client.delete(f"/api/v1/experience/{experience_id}", headers=headers)
    assert delete_response.status_code == 200

    list_response = await client.get("/api/v1/experience", headers=headers)
    assert list_response.json()["meta"]["total"] == 0


async def test_users_cannot_access_each_others_experience(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "expIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "expIsoB@example.com")

    create_response = await client.post(
        "/api/v1/experience",
        headers=headers_a,
        json={
            "company_name": "Acme",
            "job_title": "Engineer",
            "employment_type": "contract",
            "start_date": "2022-01-01",
        },
    )
    experience_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/experience/{experience_id}", headers=headers_b)
    assert response.status_code == 404
