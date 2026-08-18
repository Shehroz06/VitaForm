"""Shared "call an AI provider, retry, fall back to the next configured
provider" loop. Extracted out of Phase 6's resume GenerationService so
Phase 8's cover-letter and LinkedIn engines reuse the exact same
retry/fallback/logging behavior instead of a second (or third) copy of it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.config.settings import Settings
from app.core.ai_provider import ProviderNotConfiguredError, build_provider


@dataclass
class ProviderRunResult[T]:
    value: T | None
    provider: str | None
    attempt_logs: list[dict[str, Any]]
    error_message: str | None


def provider_order(settings: Settings) -> list[str]:
    order = [settings.ai_default_provider]
    for name in settings.ai_fallback_providers:
        if name not in order:
            order.append(name)
    return order


async def run_with_fallback[T](
    settings: Settings,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
    max_tokens: int,
    validate: Callable[[str], T],
    images: list[bytes] | None = None,
    providers: list[str] | None = None,
) -> ProviderRunResult[T]:
    """Tries each configured provider in order, retrying AI_MAX_RETRIES times
    within a provider before moving to the next one. `validate` parses and
    validates the raw response text; any exception it raises is treated the
    same as a provider/network failure and triggers a retry. `providers`
    overrides the default/fallback chain from settings -- used by callers
    that need a specific capability (e.g. vision) not every configured
    provider has."""
    attempt_logs: list[dict[str, Any]] = []
    error_message: str | None = None

    for provider_name in (providers if providers is not None else provider_order(settings)):
        try:
            provider = build_provider(provider_name, settings)
        except ProviderNotConfiguredError as exc:
            error_message = str(exc)
            continue

        for attempt in range(settings.ai_max_retries + 1):
            try:
                result = await provider.generate(
                    system_prompt,
                    user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    images=images,
                )
                value = validate(result.text)
            except Exception as exc:  # noqa: BLE001
                error_message = str(exc)[:2000]
                attempt_logs.append(
                    {
                        "provider": provider_name,
                        "model": getattr(provider, "model", ""),
                        "latency_ms": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "retry_attempt": attempt,
                        "success": False,
                        "error_message": error_message,
                    }
                )
                continue
            else:
                attempt_logs.append(
                    {
                        "provider": result.provider,
                        "model": result.model,
                        "latency_ms": result.latency_ms,
                        "prompt_tokens": result.prompt_tokens,
                        "completion_tokens": result.completion_tokens,
                        "retry_attempt": attempt,
                        "success": True,
                        "error_message": None,
                    }
                )
                return ProviderRunResult(value, provider_name, attempt_logs, None)

    return ProviderRunResult(None, None, attempt_logs, error_message)
