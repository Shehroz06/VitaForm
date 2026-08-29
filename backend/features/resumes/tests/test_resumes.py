import shutil

import pymupdf
import pytest
from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login

# ats_safe compiles through real pdflatex (see latex_renderer.py), which
# isn't installed on every machine this suite runs on -- it always is in
# the Docker image (docker/backend.Dockerfile) where full coverage runs.
_HAS_PDFLATEX = shutil.which("pdflatex") is not None


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

    pdf_response = await client.get(file_data["url"], headers=headers)
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


async def test_title_and_subtitle_overrides_render_without_touching_the_profile_record(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "titleOverride@example.com")
    template_id = await _classic_template_id(client)

    experience_response = await client.post(
        "/api/v1/experience",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "job_title": "Software Engineering Intern",
            "employment_type": "internship",
            "start_date": "2024-01-01",
            "is_current": True,
        },
    )
    experience_id = experience_response.json()["data"]["id"]

    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    await client.patch(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": None,
            "contact_visibility": {},
            "sections": [
                {"section_type": "experience", "visible": True, "item_ids": [experience_id]}
            ],
            "title_overrides": {experience_id: "Backend Engineering Intern"},
            "subtitle_overrides": {experience_id: "Acme Corp (Tailored)"},
        },
    )

    export_response = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
    assert export_response.status_code == 200
    pdf_response = await client.get(export_response.json()["data"]["url"], headers=headers)
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        text = doc[0].get_text()

    assert "Backend Engineering Intern" in text
    assert "Acme Corp (Tailored)" in text
    assert "Software Engineering Intern" not in text

    # The override must be resume-scoped only -- the real profile record is
    # untouched, exactly like description_overrides already guarantees.
    experience_get = await client.get(f"/api/v1/experience/{experience_id}", headers=headers)
    assert experience_get.json()["data"]["job_title"] == "Software Engineering Intern"
    assert experience_get.json()["data"]["company_name"] == "Acme Corp"


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

    pdf_response = await client.get(file_data["url"], headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content[:4] == b"%PDF"


async def _resume_with_education(
    client: AsyncClient, headers: dict[str, str], template_id: str
) -> str:
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
    resume_id: str = create_response.json()["data"]["id"]

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
    return resume_id


async def test_preview_resume_returns_png_of_real_render(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """The live builder preview shows this image directly instead of a
    second, hand-maintained React re-implementation of the template -- this
    is what guarantees the preview can never drift from the real export."""
    headers = await _auth(client, captured_emails, "resumePreview1@example.com")
    template_id = await _classic_template_id(client)
    resume_id = await _resume_with_education(client, headers, template_id)

    preview_response = await client.get(f"/api/v1/resumes/{resume_id}/preview", headers=headers)

    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "image/png"
    assert preview_response.headers["cache-control"] == "no-store"
    assert preview_response.headers["x-page-count"] == "1"
    assert preview_response.content[:8] == b"\x89PNG\r\n\x1a\n"


async def test_preview_resume_page_query_param_returns_later_pages(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """A resume built manually (no auto-fit applied) can genuinely overflow
    to multiple pages -- the builder's preview needs to be able to show
    page 2+, not just silently crop to page 1."""
    headers = await _auth(client, captured_emails, "resumePreviewMultiPage@example.com")
    template_id = await _classic_template_id(client)

    education_ids = []
    for i in range(10):
        education_response = await client.post(
            "/api/v1/education",
            headers=headers,
            json={
                "institution_name": f"University {i}",
                "degree": "BSc",
                "field_of_study": "Computer Science",
                "description": "Relevant coursework and extensive extracurricular activities. " * 6,
                "start_date": "2018-01-01",
                "end_date": "2022-01-01",
                "is_current": False,
            },
        )
        education_ids.append(education_response.json()["data"]["id"])

    create_response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Overflowing Resume", "template_id": template_id},
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
                {"section_type": "education", "visible": True, "item_ids": education_ids},
            ],
            "style": {"spacing": "relaxed"},
        },
    )

    page1_response = await client.get(f"/api/v1/resumes/{resume_id}/preview", headers=headers)
    assert page1_response.status_code == 200
    page_count = int(page1_response.headers["x-page-count"])
    assert page_count > 1, "expected this deliberately overloaded resume to overflow one page"

    page2_response = await client.get(
        f"/api/v1/resumes/{resume_id}/preview", headers=headers, params={"page": 2}
    )
    assert page2_response.status_code == 200
    assert page2_response.headers["x-page-count"] == str(page_count)
    assert page2_response.content != page1_response.content

    # Out-of-range page numbers clamp to the last real page rather than 404ing.
    last_page_response = await client.get(
        f"/api/v1/resumes/{resume_id}/preview", headers=headers, params={"page": page_count}
    )
    overshoot_response = await client.get(
        f"/api/v1/resumes/{resume_id}/preview", headers=headers, params={"page": 999}
    )
    assert overshoot_response.status_code == 200
    assert overshoot_response.content == last_page_response.content


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed on this machine")
async def test_preview_resume_works_for_latex_engine_template(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumePreview2@example.com")
    templates_response = await client.get("/api/v1/resume-templates")
    ats_safe_id = next(
        t["id"] for t in templates_response.json()["data"] if t["slug"] == "ats_safe"
    )
    resume_id = await _resume_with_education(client, headers, ats_safe_id)

    preview_response = await client.get(f"/api/v1/resumes/{resume_id}/preview", headers=headers)

    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "image/png"
    assert preview_response.content[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.skipif(not _HAS_PDFLATEX, reason="pdflatex not installed on this machine")
async def test_export_tex_returns_the_raw_latex_source(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeExportTex1@example.com")
    templates_response = await client.get("/api/v1/resume-templates")
    ats_safe_id = next(
        t["id"] for t in templates_response.json()["data"] if t["slug"] == "ats_safe"
    )
    resume_id = await _resume_with_education(client, headers, ats_safe_id)

    response = await client.get(f"/api/v1/resumes/{resume_id}/export-tex", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/x-tex")
    assert "attachment" in response.headers["content-disposition"]
    assert response.text.startswith("\\documentclass")
    assert "MIT" in response.text


async def test_export_tex_rejects_non_latex_templates(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeExportTex2@example.com")
    template_id = await _classic_template_id(client)
    resume_id = await _resume_with_education(client, headers, template_id)

    response = await client.get(f"/api/v1/resumes/{resume_id}/export-tex", headers=headers)

    assert response.status_code == 422


async def test_preview_with_renders_unsaved_content_against_a_candidate_template(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumePreviewWith1@example.com")
    templates_response = await client.get("/api/v1/resume-templates")
    templates = templates_response.json()["data"]
    classic_id = next(t["id"] for t in templates if t["slug"] == "classic")
    modern_id = next(t["id"] for t in templates if t["slug"] == "modern")

    education_response = await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc",
            "start_date": "2018-01-01",
            "is_current": False,
        },
    )
    education_id = education_response.json()["data"]["id"]

    resume_id = await _resume_with_education(client, headers, classic_id)

    # Ask for a render against `modern`, a template this resume was never
    # saved with -- nothing about the resume itself should change.
    response = await client.post(
        f"/api/v1/resumes/{resume_id}/preview-with",
        headers=headers,
        json={
            "content": {
                "summary": "Preview-only content.",
                "contact_visibility": {},
                "sections": [
                    {"section_type": "summary", "visible": True, "item_ids": []},
                    {"section_type": "education", "visible": True, "item_ids": [education_id]},
                ],
                "style": {},
                "description_overrides": {},
                "title_overrides": {},
                "subtitle_overrides": {},
            },
            "template_id": modern_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    unchanged_response = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert unchanged_response.json()["data"]["template_id"] == classic_id


async def test_template_sample_preview_renders_the_callers_own_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """The pre-resume-creation template browser's preview -- no resume_id
    involved at all, just the caller's own profile data against whichever
    template they're looking at."""
    headers = await _auth(client, captured_emails, "templateSample1@example.com")
    template_id = await _classic_template_id(client)

    await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "Sample University",
            "degree": "BSc",
            "start_date": "2018-01-01",
            "is_current": False,
        },
    )

    response = await client.post(
        f"/api/v1/resume-templates/{template_id}/preview", headers=headers, json={}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


async def test_template_sample_preview_requires_auth(client: AsyncClient) -> None:
    template_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/api/v1/resume-templates/{template_id}/preview", json={})
    assert response.status_code == 401


async def test_preview_resume_requires_ownership(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "resumePreviewIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "resumePreviewIsoB@example.com")
    template_id = await _classic_template_id(client)
    resume_id = await _resume_with_education(client, headers_a, template_id)

    response = await client.get(f"/api/v1/resumes/{resume_id}/preview", headers=headers_b)
    assert response.status_code == 404


async def test_autofit_settles_on_relaxed_spacing_when_content_easily_fits(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """Auto-fit always searches from "relaxed" outward (see page_fit.py's
    fit_spacing_and_density), not forward from whatever spacing the resume
    happened to already be at -- content this short settles at the loosest,
    best-looking preset rather than staying at its previous setting."""
    headers = await _auth(client, captured_emails, "resumeAutofit1@example.com")
    template_id = await _classic_template_id(client)
    resume_id = await _resume_with_education(client, headers, template_id)

    response = await client.post(f"/api/v1/resumes/{resume_id}/autofit", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["overflowing"] is False
    assert data["version"]["content"]["style"]["spacing"] == "relaxed"


async def test_autofit_tightens_spacing_for_content_that_overflows(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """The manual builder's auto-fit action, run against a resume built by
    hand (not AI generation) -- confirms the same lossless spacing/density
    search AI generation uses is reachable from the manual content-editing
    path, not just /resumes/generate."""
    headers = await _auth(client, captured_emails, "resumeAutofit2@example.com")
    template_id = await _classic_template_id(client)

    education_ids = []
    for i in range(12):
        education_response = await client.post(
            "/api/v1/education",
            headers=headers,
            json={
                "institution_name": f"University {i}",
                "degree": "BSc",
                "field_of_study": "Computer Science",
                "description": "Relevant coursework and extensive extracurricular activities. " * 5,
                "start_date": "2018-01-01",
                "end_date": "2022-01-01",
                "is_current": False,
            },
        )
        education_ids.append(education_response.json()["data"]["id"])

    create_response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Overflowing Resume", "template_id": template_id},
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
                {"section_type": "education", "visible": True, "item_ids": education_ids},
            ],
            "style": {"spacing": "relaxed"},
        },
    )

    response = await client.post(f"/api/v1/resumes/{resume_id}/autofit", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    style = data["version"]["content"]["style"]
    # Either it found a lossless fit (spacing tightened past "relaxed",
    # possibly with content_density below 1.0) or it's honestly reporting
    # that even the tightest lossless setting isn't enough -- either way,
    # every education entry must still be present (autofit never deletes).
    assert style["spacing"] != "relaxed" or style["content_density"] < 1.0
    assert len(data["version"]["content"]["sections"][1]["item_ids"]) == 12


async def test_autofit_aggressive_condenses_or_removes_items_plain_autofit_would_leave_alone(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """`aggressive=true` is the manual builder's opt-in "extreme fit"
    escalation -- unlike plain autofit (never touches content), this may
    shorten descriptions or drop the lowest-priority items. Reuses the
    same overflowing-by-design dataset as
    test_autofit_tightens_spacing_for_content_that_overflows, where plain
    autofit is forced to report overflowing=True with every item intact."""
    headers = await _auth(client, captured_emails, "resumeAutofitAggressive1@example.com")
    template_id = await _classic_template_id(client)

    education_ids = []
    for i in range(12):
        education_response = await client.post(
            "/api/v1/education",
            headers=headers,
            json={
                "institution_name": f"University {i}",
                "degree": "BSc",
                "field_of_study": "Computer Science",
                "description": "Relevant coursework and extensive extracurricular activities. " * 5,
                "start_date": "2018-01-01",
                "end_date": "2022-01-01",
                "is_current": False,
            },
        )
        education_ids.append(education_response.json()["data"]["id"])

    create_response = await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Overflowing Resume", "template_id": template_id},
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
                {"section_type": "education", "visible": True, "item_ids": education_ids},
            ],
            "style": {"spacing": "relaxed"},
        },
    )

    response = await client.post(
        f"/api/v1/resumes/{resume_id}/autofit", headers=headers, params={"aggressive": "true"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    education_section = data["version"]["content"]["sections"][1]
    # At least one lever beyond plain spacing/density was actually used --
    # either some descriptions were condensed (an override recorded) or the
    # lowest-priority (last-listed) entries were dropped outright.
    assert (
        data["version"]["content"]["description_overrides"]
        or len(education_section["item_ids"]) < 12
    )
    # Whichever earlier-listed entries survive must still be present in
    # order -- aggressive fit drops from the *end* (lowest position score),
    # never reorders or drops from the middle/front.
    assert education_section["item_ids"] == education_ids[: len(education_section["item_ids"])]


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

    pdf_response = await client.get(file_data["url"], headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


async def test_leadership_awards_achievements_render_compact_with_bold_markdown(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    """The three short-form sections render one bullet per entry
    (``Title, Org -- description``), and a ``**bold**`` span a user typed
    into a description reaches the PDF as bold text with the ``**`` markers
    gone -- never as literal asterisks."""
    headers = await _auth(client, captured_emails, "resumeCompactBold@example.com")
    template_id = await _classic_template_id(client)

    leadership_id = (
        await client.post(
            "/api/v1/leadership-roles",
            headers=headers,
            json={
                "organization_name": "NXC",
                "title": "Vice President",
                "start_date": "2024-08-01",
                "is_current": True,
                "description": "Led operations and grew participation by **30%**.",
            },
        )
    ).json()["data"]["id"]
    award_id = (
        await client.post(
            "/api/v1/awards",
            headers=headers,
            json={
                "title": "Best Intern",
                "issuer": "PureLogics",
                "date_received": "2025-09-01",
                "description": "Ranked **1st** among 10 peers.",
            },
        )
    ).json()["data"]["id"]
    achievement_id = (
        await client.post(
            "/api/v1/achievements",
            headers=headers,
            json={
                "title": "Runner Up",
                "issuer": "Quantum Hackathon",
                "description": "Placed **2nd overall** at the national event.",
            },
        )
    ).json()["data"]["id"]

    resume_id = (
        await client.post(
            "/api/v1/resumes",
            headers=headers,
            json={"title": "Compact Sections Resume", "template_id": template_id},
        )
    ).json()["data"]["id"]

    content_response = await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": None,
            "contact_visibility": {},
            "sections": [
                {"section_type": "leadership_roles", "visible": True, "item_ids": [leadership_id]},
                {"section_type": "awards", "visible": True, "item_ids": [award_id]},
                {"section_type": "achievements", "visible": True, "item_ids": [achievement_id]},
            ],
        },
    )
    assert content_response.status_code == 200

    file_data = (await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)).json()[
        "data"
    ]
    pdf_response = await client.get(file_data["url"], headers=headers)
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        text = doc[0].get_text()

    assert "**" not in text
    assert "30%" in text
    assert "2nd overall" in text
    # Title and organization sit on the same flowing line now, not a
    # header row split from a date column.
    assert "Vice President, NXC" in " ".join(text.split())
    assert "Best Intern, PureLogics" in " ".join(text.split())

    # With the bold-keywords toggle off, the same **markers** are stripped
    # to plain prose -- still never literal asterisks in the PDF.
    style_off = await client.put(
        f"/api/v1/resumes/{resume_id}/content",
        headers=headers,
        json={
            "summary": None,
            "contact_visibility": {},
            "style": {"bold_markup": False},
            "sections": [
                {"section_type": "leadership_roles", "visible": True, "item_ids": [leadership_id]},
                {"section_type": "awards", "visible": True, "item_ids": [award_id]},
                {"section_type": "achievements", "visible": True, "item_ids": [achievement_id]},
            ],
        },
    )
    assert style_off.status_code == 200
    file_data = (await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)).json()[
        "data"
    ]
    pdf_response = await client.get(file_data["url"], headers=headers)
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        text_off = doc[0].get_text()
    assert "**" not in text_off
    assert "30%" in text_off
    assert "2nd overall" in text_off


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

    stale_lookup = await client.get(f"/api/v1/files/{first_file_id}", headers=headers)
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
        if slug == "ats_safe" and not _HAS_PDFLATEX:
            continue
        template_id = next(t["id"] for t in templates_response.json()["data"] if t["slug"] == slug)
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

        export_response = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
        assert export_response.status_code == 200, f"{slug} failed to export"
        file_data = export_response.json()["data"]

        pdf_response = await client.get(file_data["url"], headers=headers)
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
        if slug == "ats_safe" and not _HAS_PDFLATEX:
            continue
        template_id = next(t["id"] for t in templates_response.json()["data"] if t["slug"] == slug)
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

        export_response = await client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
        assert export_response.status_code == 200, f"{slug} failed to export at density floor"
        file_data = export_response.json()["data"]

        pdf_response = await client.get(file_data["url"], headers=headers)
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
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert get_response.status_code == 404


async def test_list_resumes_supports_sort_query_param(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeSortList@example.com")
    template_id = await _classic_template_id(client)
    await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Alpha Resume", "template_id": template_id},
    )
    await client.post(
        "/api/v1/resumes",
        headers=headers,
        json={"title": "Beta Resume", "template_id": template_id},
    )

    response = await client.get("/api/v1/resumes?sort=title", headers=headers)
    titles = [item["title"] for item in response.json()["data"]]
    assert titles == ["Alpha Resume", "Beta Resume"]


async def test_list_resumes_rejects_invalid_sort_field(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "resumeSortListBad@example.com")

    response = await client.get("/api/v1/resumes?sort=not_a_field", headers=headers)
    assert response.status_code == 422
