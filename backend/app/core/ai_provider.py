"""AI provider abstraction so the app never talks to a specific vendor's SDK
directly. Anthropic is implemented natively; OpenAI, Gemini, OpenRouter, and
Groq are all implemented by ONE class (OpenAICompatibleProvider) since they
all expose an OpenAI-compatible chat-completions endpoint -- only the
base_url, api_key, and model differ. Swapping the active provider is a
config change (AI_DEFAULT_PROVIDER), never a code change.
"""

import base64
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import tiktoken
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

if TYPE_CHECKING:
    from app.config.settings import Settings

_TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass(frozen=True)
class GenerationResult:
    text: str
    provider: str
    model: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int


class AIProvider(Protocol):
    name: str

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult: ...

    def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]: ...

    async def health(self) -> bool: ...

    def list_models(self) -> list[str]: ...

    def estimate_tokens(self, text: str) -> int: ...


class AnthropicProvider:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.name = "anthropic"
        self.model = model
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult:
        started = time.monotonic()
        content: Any = user_prompt
        if images:
            content = [{"type": "text", "text": user_prompt}] + [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(image).decode("ascii"),
                    },
                }
                for image in images
            ]
        response = await self._client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        text = "".join(block.text for block in response.content if block.type == "text")
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

    async def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def health(self) -> bool:
        try:
            await self._client.models.list(limit=1)
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        return [self.model]

    def estimate_tokens(self, text: str) -> int:
        return len(_TOKEN_ENCODING.encode(text))


_OPENAI_COMPATIBLE_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
}


class OpenAICompatibleProvider:
    """Used for OpenAI, Gemini (via its OpenAI-compatibility endpoint),
    OpenRouter, and Groq -- all speak the same chat-completions API."""

    def __init__(self, name: str, base_url: str, api_key: str | None, model: str) -> None:
        self.name = name
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key or "unset", base_url=base_url)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        images: list[bytes] | None = None,
    ) -> GenerationResult:
        started = time.monotonic()
        user_content: Any = user_prompt
        if images:
            user_content = [{"type": "text", "text": user_prompt}] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image).decode('ascii')}"
                    },
                }
                for image in images
            ]
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=cast(
                Any,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            ),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        text = response.choices[0].message.content or ""
        usage = response.usage
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

    async def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def health(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        return [self.model]

    def estimate_tokens(self, text: str) -> int:
        return len(_TOKEN_ENCODING.encode(text))


class ProviderNotConfiguredError(Exception):
    """Raised when a provider is selected but has no API key configured."""


def build_provider(name: str, settings: "Settings") -> AIProvider:
    if name == "anthropic":
        if not settings.anthropic_api_key:
            raise ProviderNotConfiguredError("ANTHROPIC_API_KEY is not set.")
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)

    if name in _OPENAI_COMPATIBLE_BASE_URLS:
        api_key = getattr(settings, f"{name}_api_key")
        model = getattr(settings, f"{name}_model")
        if not api_key:
            raise ProviderNotConfiguredError(f"{name.upper()}_API_KEY is not set.")
        return OpenAICompatibleProvider(name, _OPENAI_COMPATIBLE_BASE_URLS[name], api_key, model)

    raise ValueError(f"Unknown AI provider: {name}")
