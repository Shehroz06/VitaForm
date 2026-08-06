from httpx import AsyncClient

from app.core.ai_provider import ProviderNotConfiguredError
from features.companion.tests.support import FakeCompanionProvider
from tests.support import auth_headers, create_verified_user_and_login

_JD_TEXT = (
    "We are hiring a Senior Backend Engineer with strong Python and AWS "
    "experience to build scalable APIs and lead our platform team."
)


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def _seed_profile_data(client: AsyncClient, headers: dict[str, str]) -> None:
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


def _patch_providers(monkeypatch, providers: dict[str, FakeCompanionProvider]) -> None:
    def _fake_build_provider(name: str, settings: object) -> FakeCompanionProvider:
        if name not in providers:
            raise ProviderNotConfiguredError(f"{name.upper()}_API_KEY is not set.")
        return providers[name]

    monkeypatch.setattr("features.ai.provider_runner.build_provider", _fake_build_provider)


async def test_generate_cover_letter_happy_path(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion1@example.com")
    await _seed_profile_data(client, headers)
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="cover_letter")})

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "role_title": "Backend Engineer",
            "job_description_text": _JD_TEXT,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "Dear" in data["body"]
    assert data["company_name"] == "Acme Corp"


async def test_generate_cover_letter_using_a_saved_job_description(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion2@example.com")
    await _seed_profile_data(client, headers)
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="cover_letter")})

    job_response = await client.post(
        "/api/v1/jobs", headers=headers, json={"title": "Backend Engineer", "raw_text": _JD_TEXT}
    )
    job_id = job_response.json()["data"]["id"]

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "role_title": "Backend Engineer",
            "job_description_id": job_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["job_description_id"] == job_id


async def test_generate_cover_letter_with_unknown_job_id_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion3@example.com")
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="cover_letter")})

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers,
        json={
            "company_name": "Acme Corp",
            "role_title": "Backend Engineer",
            "job_description_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


async def test_cover_letter_falls_back_and_lists_history(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion4@example.com")
    await _seed_profile_data(client, headers)
    _patch_providers(
        monkeypatch,
        {
            "gemini": FakeCompanionProvider("gemini", mode="cover_letter", fail_times=999),
            "groq": FakeCompanionProvider("groq", mode="cover_letter"),
        },
    )

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers,
        json={"company_name": "Acme Corp", "role_title": "Backend Engineer"},
    )
    assert response.status_code == 200
    cover_letter_id = response.json()["data"]["id"]

    list_response = await client.get("/api/v1/cover-letters", headers=headers)
    assert len(list_response.json()["data"]) == 1

    get_response = await client.get(f"/api/v1/cover-letters/{cover_letter_id}", headers=headers)
    assert get_response.status_code == 200

    delete_response = await client.delete(
        f"/api/v1/cover-letters/{cover_letter_id}", headers=headers
    )
    assert delete_response.status_code == 200


async def test_cover_letter_generation_returns_friendly_error_when_all_providers_fail(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion5@example.com")
    _patch_providers(
        monkeypatch,
        {"gemini": FakeCompanionProvider("gemini", mode="cover_letter", fail_times=999)},
    )

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers,
        json={"company_name": "Acme Corp", "role_title": "Backend Engineer"},
    )
    assert response.status_code == 400
    assert response.json()["success"] is False


async def test_users_cannot_access_each_others_cover_letters(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers_a = await _auth(client, captured_emails, "companionIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "companionIsoB@example.com")
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="cover_letter")})

    response = await client.post(
        "/api/v1/ai/generate-cover-letter",
        headers=headers_a,
        json={"company_name": "Acme Corp", "role_title": "Backend Engineer"},
    )
    cover_letter_id = response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/cover-letters/{cover_letter_id}", headers=headers_b)
    assert get_response.status_code == 404


async def test_generate_linkedin_happy_path(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion6@example.com")
    await _seed_profile_data(client, headers)
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="linkedin")})

    response = await client.post(
        "/api/v1/ai/generate-linkedin",
        headers=headers,
        json={"target_role": "Backend Engineer"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["headline"]) > 0
    assert len(data["about"]) > 0


async def test_linkedin_generation_lists_and_deletes_history(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion7@example.com")
    _patch_providers(monkeypatch, {"gemini": FakeCompanionProvider("gemini", mode="linkedin")})

    response = await client.post(
        "/api/v1/ai/generate-linkedin", headers=headers, json={"target_role": None}
    )
    generation_id = response.json()["data"]["id"]

    list_response = await client.get("/api/v1/linkedin-generations", headers=headers)
    assert len(list_response.json()["data"]) == 1

    delete_response = await client.delete(
        f"/api/v1/linkedin-generations/{generation_id}", headers=headers
    )
    assert delete_response.status_code == 200

    missing_response = await client.get(
        f"/api/v1/linkedin-generations/{generation_id}", headers=headers
    )
    assert missing_response.status_code == 404


async def test_linkedin_generation_retries_after_invalid_json(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    headers = await _auth(client, captured_emails, "companion8@example.com")
    fake = FakeCompanionProvider("gemini", mode="linkedin", invalid_json_times=1)
    _patch_providers(monkeypatch, {"gemini": fake})

    response = await client.post(
        "/api/v1/ai/generate-linkedin", headers=headers, json={"target_role": "Engineer"}
    )
    assert response.status_code == 200
    assert fake.call_count == 2
