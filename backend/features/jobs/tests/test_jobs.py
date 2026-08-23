from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login

_JD_TEXT = """
We are hiring a Backend Engineer.

Requirements:
- Strong Python and PostgreSQL experience
- Experience with Docker

Preferred:
- Experience with Kubernetes
"""


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_analyze_job_without_saving(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs1@example.com")

    response = await client.post(
        "/api/v1/jobs/analyze", headers=headers, json={"raw_text": _JD_TEXT}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "Python" in data["required_skills"]
    assert "Kubernetes" in data["preferred_skills"]


async def test_create_job_saves_with_analysis_and_company(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs2@example.com")

    response = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "raw_text": _JD_TEXT,
            "company_name": "Acme Corp",
            "location": "Remote",
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Backend Engineer"
    assert data["company_id"] is not None
    assert data["company_name"] == "Acme Corp"
    assert "Python" in data["required_skills"]


async def test_saving_two_jobs_for_same_company_reuses_the_company(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs3@example.com")

    first = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "raw_text": _JD_TEXT, "company_name": "Acme Corp"},
    )
    second = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Senior Backend Engineer",
            "raw_text": _JD_TEXT + "\n- Leads a small team",
            "company_name": "Acme Corp",
        },
    )

    assert first.json()["data"]["company_id"] == second.json()["data"]["company_id"]


async def test_resubmitting_same_job_text_is_idempotent(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs9@example.com")

    first = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "raw_text": _JD_TEXT, "company_name": "Acme Corp"},
    )
    second = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "raw_text": _JD_TEXT, "company_name": "Acme Corp"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]

    list_response = await client.get("/api/v1/jobs", headers=headers)
    assert list_response.json()["meta"]["total"] == 1


async def test_get_update_delete_job_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs4@example.com")
    create_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert get_response.status_code == 200

    delete_response = await client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert missing_response.status_code == 404


async def test_users_cannot_access_each_others_jobs(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "jobsIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "jobsIsoB@example.com")

    create_response = await client.post(
        "/api/v1/jobs", headers=headers_a, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers_b)
    assert response.status_code == 404


async def test_ats_score_against_matching_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs5@example.com")
    await client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "Python", "category": "technical", "level": "expert"},
    )
    await client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "PostgreSQL", "category": "technical", "level": "advanced"},
    )
    await client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "Docker", "category": "tool", "level": "advanced"},
    )

    create_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    score_response = await client.post(f"/api/v1/jobs/{job_id}/ats-score", headers=headers)
    assert score_response.status_code == 200
    data = score_response.json()["data"]
    assert data["overall_score"] > 0
    assert "Python" in data["matched_skills"]

    latest_response = await client.get(f"/api/v1/jobs/{job_id}/ats-score", headers=headers)
    assert latest_response.status_code == 200
    assert latest_response.json()["data"]["overall_score"] == data["overall_score"]


async def test_ats_score_without_prior_computation_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs6@example.com")
    create_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}/ats-score", headers=headers)
    assert response.status_code == 404


async def test_ats_score_flags_missing_skills_for_unrelated_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs7@example.com")
    create_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    score_response = await client.post(f"/api/v1/jobs/{job_id}/ats-score", headers=headers)
    data = score_response.json()["data"]
    assert data["overall_score"] < 50
    assert "Python" in data["missing_skills"]
    assert len(data["recommendations"]) > 0


async def test_update_job_corrects_metadata_without_touching_analysis(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs8@example.com")
    create_response = await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "raw_text": _JD_TEXT, "location": "Remote"},
    )
    job_id = create_response.json()["data"]["id"]
    original_keywords = create_response.json()["data"]["keywords"]

    response = await client.patch(
        f"/api/v1/jobs/{job_id}",
        headers=headers,
        json={"title": "Senior Backend Engineer", "location": "Berlin"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Senior Backend Engineer"
    assert data["location"] == "Berlin"
    assert data["raw_text"] == _JD_TEXT
    assert data["keywords"] == original_keywords


async def test_update_job_sets_and_clears_company(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs9@example.com")
    create_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["company_name"] is None

    set_response = await client.patch(
        f"/api/v1/jobs/{job_id}", headers=headers, json={"company_name": "Globex"}
    )
    assert set_response.json()["data"]["company_name"] == "Globex"

    clear_response = await client.patch(
        f"/api/v1/jobs/{job_id}", headers=headers, json={"company_name": None}
    )
    assert clear_response.json()["data"]["company_name"] is None
    assert clear_response.json()["data"]["company_id"] is None


async def test_update_job_with_unknown_id_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobs10@example.com")

    response = await client.patch(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000",
        headers=headers,
        json={"title": "New Title"},
    )
    assert response.status_code == 404


async def test_users_cannot_update_each_others_jobs(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "jobsIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "jobsIsoB@example.com")
    create_response = await client.post(
        "/api/v1/jobs", headers=headers_a, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = create_response.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/jobs/{job_id}", headers=headers_b, json={"title": "Hijacked"}
    )
    assert response.status_code == 404


async def test_list_jobs_supports_sort_query_param(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobsSort@example.com")
    await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Alpha Role", "raw_text": _JD_TEXT}
    )
    await client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"title": "Beta Role", "raw_text": _JD_TEXT + "\nExtra line to change the hash."},
    )

    response = await client.get("/api/v1/jobs?sort=title", headers=headers)
    titles = [item["title"] for item in response.json()["data"]]
    assert titles == ["Alpha Role", "Beta Role"]


async def test_list_jobs_rejects_invalid_sort_field(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "jobsSortBad@example.com")

    response = await client.get("/api/v1/jobs?sort=not_a_field", headers=headers)
    assert response.status_code == 422
