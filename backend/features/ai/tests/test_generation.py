import pymupdf
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_provider import ProviderNotConfiguredError
from features.ai.models import AIProviderLog, GenerationHistory
from features.ai.tests.support import FakeAIProvider
from tests.support import auth_headers, create_verified_user_and_login

_LONG_JOB_DESCRIPTION = (
    "We are hiring a Senior Backend Engineer with strong Python and AWS experience "
    "to build scalable APIs and lead our platform team."
)


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def _classic_template_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/resume-templates")
    classic = next(t for t in response.json()["data"] if t["slug"] == "classic")
    template_id: str = classic["id"]
    return template_id


async def _seed_profile_data(client: AsyncClient, headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc Computer Science",
            "start_date": "2018-09-01",
            "end_date": "2022-06-01",
            "is_current": False,
        },
    )
    await client.post(
        "/api/v1/experience",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "job_title": "Backend Engineer",
            "employment_type": "full_time",
            "start_date": "2022-07-01",
            "is_current": True,
            "description": "Built Python APIs on AWS.",
        },
    )
    await client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "Python", "category": "technical", "level": "expert"},
    )


def _patch_providers(monkeypatch, providers: dict[str, FakeAIProvider]) -> None:
    def _fake_build_provider(name: str, settings: object) -> FakeAIProvider:
        if name not in providers:
            raise ProviderNotConfiguredError(f"{name.upper()}_API_KEY is not set.")
        return providers[name]

    monkeypatch.setattr("features.ai.provider_runner.build_provider", _fake_build_provider)


async def test_generate_resume_happy_path(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGen1@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={
            "template_id": template_id,
            "job_description": _LONG_JOB_DESCRIPTION,
            "target_role": "Backend Engineer",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["resume_id"]
    assert body["file"]["content_type"] == "application/pdf"
    assert body["file"]["size_bytes"] > 0

    pdf_response = await client.get(body["file"]["url"])
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


async def test_generate_resume_defaults_to_classic_template_when_omitted(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGenTemplateDefault@example.com")
    await _seed_profile_data(client, headers)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 200
    resume_id = response.json()["data"]["resume_id"]

    resume_response = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    templates_response = await client.get("/api/v1/resume-templates")
    classic_id = next(
        t["id"] for t in templates_response.json()["data"] if t["slug"] == "classic"
    )
    assert resume_response.json()["data"]["template_id"] == classic_id


async def test_generate_resume_applies_requested_accent_color(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGenAccentColor@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={
            "template_id": template_id,
            "job_description": _LONG_JOB_DESCRIPTION,
            "accent_color": "#2c4a6e",
        },
    )

    assert response.status_code == 200
    resume_id = response.json()["data"]["resume_id"]

    content_response = await client.get(f"/api/v1/resumes/{resume_id}/content", headers=headers)
    assert content_response.json()["data"]["content"]["style"]["accent_color"] == "#2c4a6e"


async def test_generate_resume_retries_and_succeeds_after_invalid_json(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGen2@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    fake = FakeAIProvider("gemini", invalid_json_times=1)
    _patch_providers(monkeypatch, {"gemini": fake})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 200
    # >= 2, not ==: proves the invalid-JSON response was retried and the
    # generation call succeeded on the 2nd attempt, without coupling this
    # test to the exact call count of the separate, best-effort description
    # rewrite step (service.py's rewrite_descriptions) that also shares
    # this fake provider and adds its own call(s) afterward.
    assert fake.call_count >= 2


async def test_generate_resume_falls_back_to_second_provider(
    client: AsyncClient,
    captured_emails: list[dict[str, str]],
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    headers = await _auth(client, captured_emails, "aiGen3@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(
        monkeypatch,
        {
            "gemini": FakeAIProvider("gemini", fail_times=999),
            "groq": FakeAIProvider("groq"),
        },
    )

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 200

    generation = (
        await db_session.execute(
            select(GenerationHistory).order_by(GenerationHistory.created_at.desc())
        )
    ).scalars().first()
    assert generation is not None
    assert generation.provider == "groq"
    assert generation.status.value == "success"


async def test_generate_resume_returns_friendly_error_when_all_providers_fail(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGen4@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(
        monkeypatch,
        {
            "gemini": FakeAIProvider("gemini", fail_times=999),
            "groq": FakeAIProvider("groq", fail_times=999),
        },
    )

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 503
    assert response.json()["success"] is False


async def test_failed_generation_is_logged_without_creating_a_resume(
    client: AsyncClient,
    captured_emails: list[dict[str, str]],
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    headers = await _auth(client, captured_emails, "aiGen5@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(
        monkeypatch,
        {
            "gemini": FakeAIProvider("gemini", fail_times=999),
            "groq": FakeAIProvider("groq", fail_times=999),
        },
    )

    await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    generation = (
        await db_session.execute(
            select(GenerationHistory).order_by(GenerationHistory.created_at.desc())
        )
    ).scalars().first()
    assert generation is not None
    assert generation.status.value == "failed"
    assert generation.resume_id is None

    resumes_response = await client.get("/api/v1/resumes", headers=headers)
    assert resumes_response.json()["data"] == []


async def test_successful_generation_records_provider_logs(
    client: AsyncClient,
    captured_emails: list[dict[str, str]],
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    headers = await _auth(client, captured_emails, "aiGen6@example.com")
    await _seed_profile_data(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    logs = (await db_session.execute(select(AIProviderLog))).scalars().all()
    assert len(logs) >= 1
    assert logs[-1].success is True
    assert logs[-1].provider == "gemini"


_ROLE_DESCRIPTION_PARAGRAPH = (
    "Led backend engineering for a high-traffic Python and AWS platform, designing "
    "scalable REST APIs, distributed queues, and observability tooling used by dozens "
    "of downstream teams. Owned the service's reliability roadmap end to end, from "
    "incident response through capacity planning, and mentored a growing group of "
    "backend engineers on API design, testing, and deployment practices. "
)
_LONG_ROLE_DESCRIPTION = _ROLE_DESCRIPTION_PARAGRAPH * 3
# Near the Experience.description field's 2000-char max -- condensing every
# item to ~50% still leaves far more than one page can hold.
_SEVERELY_LONG_ROLE_DESCRIPTION = _ROLE_DESCRIPTION_PARAGRAPH * 5


async def _seed_page_overflowing_profile(client: AsyncClient, headers: dict[str, str]) -> None:
    """Six long-description experiences plus a real education entry -- more
    content than a single A4 page can hold at the classic template's default
    styling, so the AI-selected content is guaranteed to need trimming."""
    await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc Computer Science",
            "start_date": "2014-09-01",
            "end_date": "2018-06-01",
            "is_current": False,
        },
    )
    for i in range(6):
        await client.post(
            "/api/v1/experience",
            headers=headers,
            json={
                "company_name": f"Company {i}",
                "job_title": "Senior Backend Engineer",
                "employment_type": "full_time",
                "start_date": f"{2018 + i}-01-01",
                "end_date": f"{2018 + i}-12-01",
                "is_current": False,
                "description": _LONG_ROLE_DESCRIPTION,
            },
        )


async def test_generate_resume_trims_content_to_fit_one_page(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "aiGen7@example.com")
    await _seed_page_overflowing_profile(client, headers)
    template_id = await _classic_template_id(client)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 200
    body = response.json()["data"]

    pdf_response = await client.get(body["file"]["url"])
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        assert doc.page_count == 1

    resume_id = body["resume_id"]
    version_response = await client.get(f"/api/v1/resumes/{resume_id}/content", headers=headers)
    resume_content = version_response.json()["data"]["content"]
    experience_section = next(
        s for s in resume_content["sections"] if s["section_type"] == "experience"
    )
    # The AI was offered all 6 (the FakeAIProvider selects everything it's
    # given). The fit pipeline now condenses descriptions (page_fit.py's
    # _condense_lowest_relevance_descriptions) before it ever deletes an
    # item outright, so all 6 survive here -- proof of trimming work is the
    # presence of shortened, extractive-only description_overrides rather
    # than a smaller item count.
    assert len(experience_section["item_ids"]) == 6
    assert resume_content["description_overrides"], "expected at least one condensed description"
    for item_id, override_text in resume_content["description_overrides"].items():
        assert item_id in experience_section["item_ids"]
        # Extractive only: every word in the override must already exist in
        # the original text -- nothing invented.
        assert set(override_text.replace("•", "").split()) <= set(
            _LONG_ROLE_DESCRIPTION.split()
        )


async def test_generate_resume_still_deletes_items_when_condensing_is_not_enough(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    """Condensing (see the test above) is tried first, but it's not a
    substitute for deletion -- content severe enough to still overflow
    after every description is condensed must still fall through to
    page_fit.py's item-removal loop, same as before condensing existed."""
    headers = await _auth(client, captured_emails, "aiGen8@example.com")
    await client.post(
        "/api/v1/education",
        headers=headers,
        json={
            "institution_name": "MIT",
            "degree": "BSc Computer Science",
            "start_date": "2014-09-01",
            "end_date": "2018-06-01",
            "is_current": False,
        },
    )
    for i in range(6):
        await client.post(
            "/api/v1/experience",
            headers=headers,
            json={
                "company_name": f"Company {i}",
                "job_title": "Senior Backend Engineer",
                "employment_type": "full_time",
                "start_date": f"{2018 + i}-01-01",
                "end_date": f"{2018 + i}-12-01",
                "is_current": False,
                "description": _SEVERELY_LONG_ROLE_DESCRIPTION,
            },
        )
    template_id = await _classic_template_id(client)
    _patch_providers(monkeypatch, {"gemini": FakeAIProvider("gemini")})

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 200
    body = response.json()["data"]

    pdf_response = await client.get(body["file"]["url"])
    with pymupdf.open(stream=pdf_response.content, filetype="pdf") as doc:
        assert doc.page_count == 1

    resume_id = body["resume_id"]
    version_response = await client.get(f"/api/v1/resumes/{resume_id}/content", headers=headers)
    experience_section = next(
        s
        for s in version_response.json()["data"]["content"]["sections"]
        if s["section_type"] == "experience"
    )
    assert 0 < len(experience_section["item_ids"]) < 6
