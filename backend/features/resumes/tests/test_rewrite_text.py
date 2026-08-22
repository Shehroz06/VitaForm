"""POST /resumes/{id}/rewrite-text -- the manual builder's on-demand
"Rephrase with AI" action. Stateless: doesn't read/write the resume's saved
content, just takes text in and (best-effort) returns a rewritten version
of the exact same text, reusing description_rewriter.py's fact-checked
rewrite (see features/ai/tests/test_description_rewriter.py for the
fact-check's own unit tests)."""

import json
import re
from collections.abc import AsyncIterator

from httpx import AsyncClient

from app.core.ai_provider import GenerationResult, ProviderNotConfiguredError
from tests.support import auth_headers, create_verified_user_and_login

_ITEM_ID_RE = re.compile(r"- id=([0-9a-fA-F-]{36})\n\s*text: (.+)")


class _FakeRewriteProvider:
    """Parses the sentinel item id GenerationService.rewrite_text generates
    internally out of the real prompt text (same trick as
    features/ai/tests/support.py's FakeAIProvider), so this exercises the
    real prompt-building/parsing/fact-check pipeline and only fakes the
    network call."""

    name = "fake"
    model = "fake-model"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult:
        match = _ITEM_ID_RE.search(user_prompt)
        assert match is not None, user_prompt
        item_id, original_text = match.group(1), match.group(2).strip()
        payload = {"items": [{"id": item_id, "text": f"{original_text} (rewritten)"}]}
        return GenerationResult(
            text=json.dumps(payload),
            provider=self.name,
            model=self.model,
            latency_ms=1,
            prompt_tokens=1,
            completion_tokens=1,
        )

    def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        async def _empty() -> AsyncIterator[str]:
            return
            yield ""

        return _empty()

    async def health(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return [self.model]

    def estimate_tokens(self, text: str) -> int:
        return len(text)


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


def _patch_provider(monkeypatch) -> None:
    def _fake_build_provider(name: str, settings: object) -> _FakeRewriteProvider:
        if name != "gemini":
            raise ProviderNotConfiguredError(f"{name.upper()}_API_KEY is not set.")
        return _FakeRewriteProvider()

    monkeypatch.setattr("features.ai.provider_runner.build_provider", _fake_build_provider)


async def test_rewrite_text_returns_the_fact_checked_rewrite(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    _patch_provider(monkeypatch)
    headers = await _auth(client, captured_emails, "rewriteText1@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/resumes/{resume_id}/rewrite-text",
        headers=headers,
        json={"text": "Built Python APIs on AWS.", "job_description": "Backend role."},
    )

    assert response.status_code == 200
    assert response.json()["data"]["rewritten_text"] == "Built Python APIs on AWS. (rewritten)"


async def test_rewrite_text_returns_none_when_no_provider_is_configured(
    client: AsyncClient, captured_emails: list[dict[str, str]], monkeypatch
) -> None:
    def _fail_build_provider(name: str, settings: object) -> None:
        raise ProviderNotConfiguredError(f"{name.upper()}_API_KEY is not set.")

    monkeypatch.setattr("features.ai.provider_runner.build_provider", _fail_build_provider)
    headers = await _auth(client, captured_emails, "rewriteText2@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/resumes/{resume_id}/rewrite-text",
        headers=headers,
        json={"text": "Built Python APIs on AWS."},
    )

    assert response.status_code == 200
    assert response.json()["data"]["rewritten_text"] is None


async def test_rewrite_text_requires_resume_ownership(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "rewriteTextA@example.com")
    headers_b = await _auth(client, captured_emails, "rewriteTextB@example.com")
    template_id = await _classic_template_id(client)
    create_response = await client.post(
        "/api/v1/resumes", headers=headers_a, json={"title": "Resume", "template_id": template_id}
    )
    resume_id = create_response.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/resumes/{resume_id}/rewrite-text",
        headers=headers_b,
        json={"text": "Built Python APIs on AWS."},
    )

    assert response.status_code == 404
