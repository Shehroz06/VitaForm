from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        return providers[name]

    monkeypatch.setattr("features.ai.service.build_provider", _fake_build_provider)


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
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] > 0

    pdf_response = await client.get(body["url"])
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


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
    assert fake.call_count == 2


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
            "anthropic": FakeAIProvider("anthropic"),
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
    assert generation.provider == "anthropic"
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
            "anthropic": FakeAIProvider("anthropic", fail_times=999),
        },
    )

    response = await client.post(
        "/api/v1/resumes/generate",
        headers=headers,
        json={"template_id": template_id, "job_description": _LONG_JOB_DESCRIPTION},
    )

    assert response.status_code == 400
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
            "anthropic": FakeAIProvider("anthropic", fail_times=999),
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
