"""A fake AIProvider double for the companion (cover letter / LinkedIn)
engines. Unlike features.ai.tests.support.FakeAIProvider (which echoes back
candidate ids parsed from the prompt), these responses are prose text, so a
canned payload is enough -- there's no id-selection to make realistic."""

import json
from collections.abc import AsyncIterator

from app.core.ai_provider import GenerationResult

_COVER_LETTER_TEXT = (
    "Dear Hiring Manager,\n\n"
    "I am excited to apply for this role. I bring a strong work ethic, clear "
    "communication, and a proven ability to work closely with others to "
    "deliver results the team can rely on. I take pride in following "
    "through on commitments and continuously improving how I work.\n\n"
    "I would welcome the opportunity to discuss how my background aligns with "
    "your team's needs. Thank you for your consideration.\n\n"
    "Sincerely,\nThe Candidate"
)


class FakeCompanionProvider:
    def __init__(
        self,
        name: str = "fake",
        *,
        mode: str = "cover_letter",
        fail_times: int = 0,
        invalid_json_times: int = 0,
    ) -> None:
        self.name = name
        self.model = "fake-model"
        self._mode = mode
        self._fail_times = fail_times
        self._invalid_json_times = invalid_json_times
        self.call_count = 0

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult:
        self.call_count += 1

        if self.call_count <= self._fail_times:
            raise RuntimeError("simulated provider failure")

        if self.call_count <= self._fail_times + self._invalid_json_times:
            return GenerationResult(
                text="not valid json",
                provider=self.name,
                model=self.model,
                latency_ms=1,
                prompt_tokens=1,
                completion_tokens=1,
            )

        if self._mode == "cover_letter":
            payload = {"cover_letter": _COVER_LETTER_TEXT}
        else:
            payload = {
                "headline": "Engineer | Building things that last",
                "about": (
                    "I'm an engineer who cares about doing careful, dependable work "
                    "and communicating clearly with the people I work with. I take "
                    "ownership of what I build and enjoy mentoring the people around "
                    "me. Always open to connecting with fellow builders."
                ),
            }

        return GenerationResult(
            text=json.dumps(payload),
            provider=self.name,
            model=self.model,
            latency_ms=5,
            prompt_tokens=100,
            completion_tokens=50,
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
