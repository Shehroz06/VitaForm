"""Extracted CV text (+ page images) -> AI-classified structured proposal.
Deliberately scoped to the default provider only: vision support isn't
guaranteed across every configured provider (Gemini supports it; some free
OpenRouter/Groq text models don't), and accuracy matters more here than
fallback availability. Reuses the exact retry/logging infra every other
generator in this codebase uses."""

from dataclasses import dataclass
from typing import Any

from app.config.settings import Settings
from features.ai.provider_runner import ProviderRunResult, run_with_fallback
from features.cv_import.extraction import ExtractedPage, extract_pages
from features.cv_import.prompts import (
    CLASSIFY_SYSTEM_PROMPT,
    CLASSIFY_TEMPERATURE,
    build_classify_user_prompt,
)
from features.cv_import.validator import ClassificationResult, validate_classification_response

_MAX_OUTPUT_TOKENS = 4000
# Vision input is expensive and most CVs are 1-2 pages; cap pages sent as
# images so a long document doesn't balloon a single request.
_MAX_IMAGE_PAGES = 3


@dataclass
class ClassifyOutcome:
    result: ClassificationResult | None
    provider: str | None
    attempt_logs: list[dict[str, Any]]
    error_message: str | None


async def classify_pdf(settings: Settings, pdf_bytes: bytes) -> ClassifyOutcome:
    pages: list[ExtractedPage] = extract_pages(pdf_bytes)
    combined_text = "\n\n--- page break ---\n\n".join(page.text for page in pages)
    images = [page.image_png for page in pages[:_MAX_IMAGE_PAGES]]

    user_prompt = build_classify_user_prompt(combined_text)

    run_result: ProviderRunResult[ClassificationResult] = await run_with_fallback(
        settings,
        CLASSIFY_SYSTEM_PROMPT,
        user_prompt,
        temperature=CLASSIFY_TEMPERATURE,
        max_tokens=_MAX_OUTPUT_TOKENS,
        validate=validate_classification_response,
        images=images,
        providers=[settings.ai_default_provider],
    )
    return ClassifyOutcome(
        result=run_result.value,
        provider=run_result.provider,
        attempt_logs=run_result.attempt_logs,
        error_message=run_result.error_message,
    )
