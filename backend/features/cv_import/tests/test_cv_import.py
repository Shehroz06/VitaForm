from httpx import AsyncClient

from features.cv_import.tests.support import FakeClassifierProvider, build_sample_pdf
from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


def _patch_provider(monkeypatch, provider: FakeClassifierProvider) -> None:
    def _fake_build_provider(name: str, settings: object) -> FakeClassifierProvider:
        if name != provider.name:
            raise AssertionError(f"unexpected provider requested: {name}")
        return provider

    monkeypatch.setattr("features.ai.provider_runner.build_provider", _fake_build_provider)


async def test_upload_rejects_non_pdf(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cvimport1@example.com")

    response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 422


async def test_upload_rejects_pdf_extension_with_wrong_magic_bytes(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "cvimport2@example.com")

    response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", b"not-really-a-pdf", "application/pdf")},
    )
    assert response.status_code == 422


async def test_create_session_extracts_and_classifies_pdf(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport3@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["status"] == "pending"
    assert data["source_filename"] == "resume.pdf"
    assert "experience" in data["proposed_data"]["sections"]
    assert data["proposed_data"]["sections"]["experience"][0]["company_name"] == "Acme Corp"
    # The classifier is given real page images -- confirms the vision path
    # actually ran, not just text extraction.
    assert fake.received_images[0] is not None
    assert len(fake.received_images[0]) >= 1


async def test_create_session_records_failure_when_provider_unavailable(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport4@example.com")
    fake = FakeClassifierProvider("gemini", fail_times=999)
    _patch_provider(monkeypatch, fake)

    response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


async def test_confirm_writes_items_to_profile_and_sets_bio(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport5@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]
    proposed = create_response.json()["data"]["proposed_data"]

    confirm_response = await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/confirm",
        headers=headers,
        json={"bio": "Experienced backend engineer.", "sections": proposed["sections"]},
    )
    assert confirm_response.status_code == 200, confirm_response.text
    body = confirm_response.json()["data"]
    assert body["created_counts"] == {"experience": 1, "education": 1}
    assert body["profile_headline_updated"] is True

    experience_response = await client.get("/api/v1/experience", headers=headers)
    experiences = experience_response.json()["data"]
    assert len(experiences) == 1
    assert experiences[0]["company_name"] == "Acme Corp"

    education_response = await client.get("/api/v1/education", headers=headers)
    assert len(education_response.json()["data"]) == 1

    profile_response = await client.get("/api/v1/profiles/me", headers=headers)
    assert profile_response.json()["data"]["bio"] == "Experienced backend engineer."

    session_response = await client.get(
        f"/api/v1/cv-import/sessions/{session_id}", headers=headers
    )
    assert session_response.json()["data"]["status"] == "confirmed"


async def test_confirm_does_not_overwrite_existing_profile_bio(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport6@example.com")
    await client.patch(
        "/api/v1/profiles/me", headers=headers, json={"bio": "Already have a bio."}
    )
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]

    confirm_response = await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/confirm",
        headers=headers,
        json={"bio": "New bio from import.", "sections": {}},
    )
    assert confirm_response.json()["data"]["profile_headline_updated"] is False

    profile_response = await client.get("/api/v1/profiles/me", headers=headers)
    assert profile_response.json()["data"]["bio"] == "Already have a bio."


async def test_confirm_rejects_invalid_item_and_writes_nothing(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport7@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]

    confirm_response = await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/confirm",
        headers=headers,
        json={
            "sections": {
                "education": [{"institution_name": "MIT"}],  # missing required "degree"/start_date
            }
        },
    )
    assert confirm_response.status_code == 422

    education_response = await client.get("/api/v1/education", headers=headers)
    assert education_response.json()["data"] == []


async def test_confirm_twice_is_rejected(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport8@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]

    await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/confirm",
        headers=headers,
        json={"sections": {}},
    )
    second_response = await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/confirm",
        headers=headers,
        json={"sections": {}},
    )
    assert second_response.status_code == 400


async def test_reject_session(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "cvimport9@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]

    reject_response = await client.post(
        f"/api/v1/cv-import/sessions/{session_id}/reject", headers=headers
    )
    assert reject_response.json()["data"]["status"] == "rejected"

    education_response = await client.get("/api/v1/education", headers=headers)
    assert education_response.json()["data"] == []


async def test_users_cannot_access_each_others_import_sessions(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers_a = await _auth(client, captured_emails, "cvimportIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "cvimportIsoB@example.com")
    fake = FakeClassifierProvider("gemini")
    _patch_provider(monkeypatch, fake)

    create_response = await client.post(
        "/api/v1/cv-import/sessions",
        headers=headers_a,
        files={"file": ("resume.pdf", build_sample_pdf(), "application/pdf")},
    )
    session_id = create_response.json()["data"]["id"]

    response = await client.get(f"/api/v1/cv-import/sessions/{session_id}", headers=headers_b)
    assert response.status_code == 404
