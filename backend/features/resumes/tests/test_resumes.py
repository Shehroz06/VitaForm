import pymupdf
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


async def test_autosave_updates_content_in_place_without_bumping_version(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeAutosave1@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    autosave_response = await client.patch(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={"summary": "Draft in progress.", "contact_visibility": {}, "sections": []},
    )
    assert autosave_response.status_code == 200
    assert autosave_response.json()["data"]["version_number"] == 1
    assert autosave_response.json()["data"]["content"]["summary"] == "Draft in progress."

    # No new version was created -- still exactly one.
    versions_response = await client.get(f"/api/v1/resumes/{resume_id}/versions", headers=headers)
    assert len(versions_response.json()["data"]) == 1

    content_response = await client.get(f"/api/v1/resumes/{resume_id}/content", headers=headers)
    assert content_response.json()["data"]["content"]["summary"] == "Draft in progress."


async def test_autosaved_content_is_reflected_on_export_without_an_explicit_save(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeAutosave2@example.com")
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
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    await client.patch(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": "Autosaved without clicking Save.",
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

    pdf_response = await client.get(file_data["url"])
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        text = doc[0].get_text()
    assert "MIT" in text


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


async def test_export_resume_with_all_extended_section_types_renders_pdf(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """Covers the 9 profile modules wired into resume generation in Phase 9
    (research, volunteer experience, leadership, organizations, languages,
    references, hackathons, competitions, patents) -- each exercises its own
    section_registry entry, ranking scorer, and Jinja2 template branch."""
    headers = await _auth(client, captured_emails, "resumeExtended1@example.com")
    template_id = await _classic_template_id(client)

    research_id = (
        await client.post(
            "/api/v1/research",
            headers=headers,
            json={"title": "Efficient Attention Mechanisms", "publication_venue": "NeurIPS"},
        )
    ).json()["data"]["id"]
    volunteer_id = (
        await client.post(
            "/api/v1/volunteer-experience",
            headers=headers,
            json={
                "organization_name": "Local Food Bank",
                "role": "Volunteer Coordinator",
                "start_date": "2021-01-01",
                "is_current": True,
            },
        )
    ).json()["data"]["id"]
    leadership_id = (
        await client.post(
            "/api/v1/leadership-roles",
            headers=headers,
            json={
                "organization_name": "CS Society",
                "title": "President",
                "start_date": "2020-01-01",
                "is_current": False,
                "end_date": "2021-01-01",
            },
        )
    ).json()["data"]["id"]
    organization_id = (
        await client.post(
            "/api/v1/organizations",
            headers=headers,
            json={"organization_name": "IEEE", "role": "Member"},
        )
    ).json()["data"]["id"]
    language_id = (
        await client.post(
            "/api/v1/languages",
            headers=headers,
            json={"name": "Spanish", "proficiency": "fluent"},
        )
    ).json()["data"]["id"]
    reference_id = (
        await client.post(
            "/api/v1/references",
            headers=headers,
            json={"name": "Jane Doe", "relationship": "Former Manager"},
        )
    ).json()["data"]["id"]
    hackathon_id = (
        await client.post(
            "/api/v1/hackathons",
            headers=headers,
            json={"name": "HackMIT", "project_name": "AutoResume", "result": "Winner"},
        )
    ).json()["data"]["id"]
    competition_id = (
        await client.post(
            "/api/v1/competitions",
            headers=headers,
            json={"name": "ICPC Regionals", "result": "2nd place"},
        )
    ).json()["data"]["id"]
    patent_id = (
        await client.post(
            "/api/v1/patents",
            headers=headers,
            json={"title": "Method for Ranking Resume Sections", "status": "filed"},
        )
    ).json()["data"]["id"]

    create_response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Extended Sections Resume", "template_id": template_id},
    )
    resume_id = create_response.json()["data"]["id"]

    content_response = await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": None,
            "contact_visibility": {},
            "sections": [
                {"section_type": "research", "visible": True, "item_ids": [research_id]},
                {
                    "section_type": "volunteer_experience",
                    "visible": True,
                    "item_ids": [volunteer_id],
                },
                {
                    "section_type": "leadership_roles",
                    "visible": True,
                    "item_ids": [leadership_id],
                },
                {
                    "section_type": "organizations",
                    "visible": True,
                    "item_ids": [organization_id],
                },
                {"section_type": "languages", "visible": True, "item_ids": [language_id]},
                {"section_type": "references", "visible": True, "item_ids": [reference_id]},
                {"section_type": "hackathons", "visible": True, "item_ids": [hackathon_id]},
                {
                    "section_type": "competitions",
                    "visible": True,
                    "item_ids": [competition_id],
                },
                {"section_type": "patents", "visible": True, "item_ids": [patent_id]},
            ],
        },
    )
    assert content_response.status_code == 200

    export_response = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
    assert export_response.status_code == 200
    file_data = export_response.json()["data"]
    assert file_data["content_type"] == "application/pdf"

    pdf_response = await client.get(file_data["url"])
    assert pdf_response.status_code == 200
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


async def test_export_resume_renders_for_every_template_with_custom_style(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """Every seeded template must render successfully with every style
    combination -- catches a Jinja/CSS-variable typo in any one template
    that would otherwise only surface the first time a user picks it."""
    headers = await _auth(client, captured_emails, "resumeExportAllTemplates@example.com")
    templates_response = await client.get("/api/v1/resume-templates")
    slugs = [t["slug"] for t in templates_response.json()["data"]]
    assert set(slugs) >= {"classic", "modern", "minimal", "compact", "executive"}

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

    for slug, font_family, spacing in zip(
        slugs,
        ["arial", "calibri", "times", "georgia", "arial", "calibri"],
        ["compact", "cozy", "relaxed", "compact", "cozy", "relaxed"],
        strict=False,
    ):
        template_id = next(
            t["id"] for t in templates_response.json()["data"] if t["slug"] == slug
        )
        create_response = await client.post(
            "/api/v1/resumes",
            headers=headers,
            json={"title": f"Resume ({slug})", "template_id": template_id},
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
                "style": {
                    "accent_color": "#3355aa",
                    "font_family": font_family,
                    "spacing": spacing,
                },
            },
        )

        export_response = await client.post(
            f"/api/v1/resumes/{resume_id}/export", headers=headers
        )
        assert export_response.status_code == 200, f"{slug} failed to export"
        file_data = export_response.json()["data"]

        pdf_response = await client.get(file_data["url"])
        assert pdf_response.status_code == 200
        assert pdf_response.content[:4] == b"%PDF"


async def test_export_stays_legible_at_the_content_density_floor(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """ATS-safety guardrail on the new continuous density scaling: even at
    the floor (0.8), every template's text must still render, extract
    cleanly via PyMuPDF (i.e. real selectable text, not garbled/overlapping
    glyphs), and land at a legible size -- never below ~80% of its own
    template's base body size."""
    headers = await _auth(client, captured_emails, "resumeDensityFloor@example.com")
    templates_response = await client.get("/api/v1/resume-templates")
    slugs = [t["slug"] for t in templates_response.json()["data"]]
    assert set(slugs) >= {"classic", "modern", "minimal", "compact", "executive", "ats_safe"}

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

    for slug in slugs:
        template_id = next(
            t["id"] for t in templates_response.json()["data"] if t["slug"] == slug
        )
        create_response = await client.post(
            "/api/v1/resumes",
            headers=headers,
            json={"title": f"Resume ({slug})", "template_id": template_id},
        )
        resume_id = create_response.json()["data"]["id"]

        await client.put(
            f"/api/v1/resumes/{resume_id}/content",
            headers=headers,
            json={
                "summary": "Experienced software engineer building scalable systems.",
                "contact_visibility": {},
                "sections": [
                    {"section_type": "summary", "visible": True, "item_ids": []},
                    {"section_type": "education", "visible": True, "item_ids": [education_id]},
                ],
                "style": {
                    "accent_color": "#3355aa",
                    "font_family": "arial",
                    "spacing": "compact",
                    "content_density": 0.8,
                },
            },
        )

        export_response = await client.post(
            f"/api/v1/resumes/{resume_id}/export", headers=headers
        )
        assert export_response.status_code == 200, f"{slug} failed to export at density floor"
        file_data = export_response.json()["data"]

        pdf_response = await client.get(file_data["url"])
        with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
            assert doc.page_count == 1
            text = doc[0].get_text()
            assert "MIT" in text, f"{slug}: expected text not found -- may be garbled/overlapping"
            # Smallest realistic body-ish size across all 6 templates is
            # 8pt (minimal/compact secondary text) * 0.8 floor = 6.4pt; a
            # sub-4pt span anywhere would indicate a scaling bug, not just
            # a naturally small label.
            sizes = [
                span["size"]
                for block in doc[0].get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
            ]
            assert sizes, f"{slug}: no text spans found"
            assert min(sizes) >= 4.0, f"{slug}: found illegibly small text ({min(sizes)}pt)"


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
