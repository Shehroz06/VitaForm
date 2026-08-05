from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def _classic_template_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/resume-templates")
    templates = response.json()["data"]
    classic = next(t for t in templates if t["slug"] == "classic")
    template_id: str = classic["id"]
    return template_id


async def test_list_resume_templates_includes_seeded_classic_template(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/resume-templates")
    assert response.status_code == 200
    slugs = [t["slug"] for t in response.json()["data"]]
    assert "classic" in slugs


async def test_create_resume_creates_initial_version(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resume1@example.com")
    template_id = await _classic_template_id(client)

    response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Software Engineer Resume", "template_id": template_id},
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["title"] == "Software Engineer Resume"
    assert body["latest_version_number"] == 1

    content_response = await client.get(f"/api/v1/resumes/{body['id']}/content", headers=headers)
    assert content_response.json()["data"]["version_number"] == 1
    assert content_response.json()["data"]["content"]["sections"] == []


async def test_create_resume_with_invalid_template_returns_422(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resume2@example.com")

    response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Resume", "template_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 422


async def test_updating_content_creates_new_version_and_preserves_old(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resume3@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    update_response = await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={"summary": "Experienced engineer.", "contact_visibility": {}, "sections": []},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["version_number"] == 2
    assert update_response.json()["data"]["content"]["summary"] == "Experienced engineer."

    versions_response = await client.get(f"/api/v1/resumes/{resume_id}/versions", headers=headers)
    version_numbers = [v["version_number"] for v in versions_response.json()["data"]]
    assert sorted(version_numbers) == [1, 2]

    first_version_id = next(
        v["id"] for v in versions_response.json()["data"] if v["version_number"] == 1
    )
    old_version_response = await client.get(
        f"/api/v1/resumes/{resume_id}/versions/{first_version_id}", headers=headers
    )
    assert old_version_response.json()["data"]["content"]["summary"] is None


async def test_content_update_rejects_item_ids_not_owned_by_caller(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "resumeIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "resumeIsoB@example.com")
    template_id = await _classic_template_id(client)

    education_response = await client.post(
        "/api/v1/education",
        headers=headers_b,
        json={
            "institution_name": "MIT",
            "degree": "BSc",
            "field_of_study": "CS",
            "start_date": "2018-01-01",
            "is_current": False,
        },
    )
    other_education_id = education_response.json()["data"]["id"]

    create_response = await client.post(
        "/api/v1/resumes", headers=headers_a, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers_a,
        json={
            "summary": None,
            "contact_visibility": {},
            "sections": [
                {
                    "section_type": "education",
                    "visible": True,
                    "item_ids": [other_education_id],
                }
            ],
        },
    )
    assert response.status_code == 422


async def test_users_cannot_access_each_others_resumes(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "resumeIsoC@example.com")
    headers_b = await _auth(client, captured_emails, "resumeIsoD@example.com")
    template_id = await _classic_template_id(client)

    create_response = await client.post(
        "/api/v1/resumes", headers=headers_a, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert response.status_code == 404


async def test_export_resume_produces_downloadable_pdf(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeExport1@example.com")
    template_id = await _classic_template_id(client)

    education_response = await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc",
            "field_of_study": "Computer Science",
            "start_date": "2018-01-01",
            "end_date": "2022-01-01",
            "is_current": False,
        },
    )
    education_id = education_response.json()["data"]["id"]

    create_response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "My Resume", "template_id": template_id},
    )
    resume_id = create_response.json()["data"]["id"]

    await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": "Experienced software engineer.",
            "contact_visibility": {},
            "sections": [
                {"section_type": "summary", "visible": True, "item_ids": []},
                {"section_type": "education", "visible": True, "item_ids": [education_id]},
            ],
        },
    )

    export_response = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
    assert export_response.status_code == 200
    file_data = export_response.json()["data"]
    assert file_data["content_type"] == "application/pdf"
    assert file_data["size_bytes"] > 0

    pdf_response = await client.get(file_data["url"])
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content[:4] == b"%PDF"


async def test_re_exporting_replaces_the_previous_rendered_file(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeExport2@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    first_export = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
    first_file_id = first_export.json()["data"]["id"]

    second_export = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
    second_file_id = second_export.json()["data"]["id"]

    assert first_file_id != second_file_id

    stale_lookup = await client.get(f"/api/v1/files/{first_file_id}")
    assert stale_lookup.status_code == 404


async def test_delete_resume(client: AsyncClient, captured_emails: list[dict[str, str]]) -> None:
    headers = await _auth(client, captured_emails, "resumeDelete1@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert delete_response.status_code == 200

    get_response = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_response.status_code == 404
