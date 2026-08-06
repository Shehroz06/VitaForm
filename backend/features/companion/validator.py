import json
import re

from pydantic import ValidationError

from features.ai.validator import AIResponseValidationError
from features.companion.schemas import CoverLetterAIResponse, LinkedinAIResponse

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def validate_cover_letter_response(raw_text: str) -> CoverLetterAIResponse:
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
    if not parsed.cover_letter.strip():
        raise AIResponseValidationError("AI response had an empty cover letter.")
    return CoverLetterAIResponse(cover_letter=parsed.cover_letter.strip())


def validate_linkedin_response(raw_text: str) -> LinkedinAIResponse:
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
    if not parsed.headline.strip() or not parsed.about.strip():
        raise AIResponseValidationError("AI response had an empty headline or about section.")
    return LinkedinAIResponse(headline=parsed.headline.strip(), about=parsed.about.strip())
