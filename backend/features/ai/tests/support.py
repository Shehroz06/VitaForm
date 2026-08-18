"""A fake AIProvider double that parses real candidate ids out of the actual
generated prompt text (matching the format features.ai.prompts produces),
so tests exercise the real ranking/context/prompt-building pipeline and
only fake the network call itself."""

import json
import re
from collections.abc import AsyncIterator

from app.core.ai_provider import GenerationResult

_ID_RE = re.compile(r"^- id=([0-9a-fA-F-]{36}):", re.MULTILINE)


class FakeAIProvider:
    def __init__(
        self,
        name: str = "fake",
        *,
        fail_times: int = 0,
        invalid_json_times: int = 0,
    ) -> None:
        self.name = name
        self.model = "fake-model"
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

        ids_by_section: dict[str, list[str]] = {}
        current_type: str | None = None
        for line in user_prompt.splitlines():
            if line and line.rstrip(":").isupper() and line.endswith(":"):
                current_type = line[:-1].lower()
                ids_by_section[current_type] = []
                continue
            match = _ID_RE.match(line)
            if match and current_type:
                ids_by_section[current_type].append(match.group(1))

        payload = {
            "summary": "Experienced engineer tailored for this role based on the given profile.",
            "keywords": ["python", "backend"],
            "sections": [
                {"section_type": section_type, "item_ids": ids}
                for section_type, ids in ids_by_section.items()
            ],
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
