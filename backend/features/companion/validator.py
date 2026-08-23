import json
import re

from pydantic import ValidationError

from features.ai.description_rewriter import passes_fact_check
from features.ai.validator import AIResponseValidationError
from features.companion.schemas import CoverLetterAIResponse, LinkedinAIResponse

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)

_FACT_CHECK_FAILURE_MESSAGE = (
    "Generated content introduced a number or skill not present in the "
    "candidate's actual profile data."
)


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def validate_cover_letter_response(raw_text: str, source_text: str) -> CoverLetterAIResponse:
    """`source_text` is the exact prompt the model was given (company/role/
    job description/candidate summary) -- the only thing this content is
    allowed to draw numbers or skills from. Raising here (rather than
    checking after the fact) lets provider_runner's existing retry/fallback
    loop just try again, the same as a malformed-JSON response."""
    cleaned = _strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIResponseValidationError(f"AI response was not valid JSON: {exc}") from exc
    try:
        parsed = CoverLetterAIResponse.model_validate(data)
    except ValidationError as exc:
        raise AIResponseValidationError(
            f"AI response did not match the expected schema: {exc}"
        ) from exc

    cover_letter = parsed.cover_letter.strip()
    if not cover_letter:
        raise AIResponseValidationError("AI response had an empty cover letter.")
    if not passes_fact_check(source_text, cover_letter):
        raise AIResponseValidationError(_FACT_CHECK_FAILURE_MESSAGE)
    return CoverLetterAIResponse(cover_letter=cover_letter)


def validate_linkedin_response(raw_text: str, source_text: str) -> LinkedinAIResponse:
    """See validate_cover_letter_response's docstring -- same source-text
    fact-check, applied to the headline and about section together."""
    cleaned = _strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIResponseValidationError(f"AI response was not valid JSON: {exc}") from exc
    try:
        parsed = LinkedinAIResponse.model_validate(data)
    except ValidationError as exc:
        raise AIResponseValidationError(
            f"AI response did not match the expected schema: {exc}"
        ) from exc

    headline = parsed.headline.strip()
    about = parsed.about.strip()
    if not headline or not about:
        raise AIResponseValidationError("AI response had an empty headline or about section.")
    if not passes_fact_check(source_text, f"{headline}\n{about}"):
        raise AIResponseValidationError(_FACT_CHECK_FAILURE_MESSAGE)
    return LinkedinAIResponse(headline=headline, about=about)
