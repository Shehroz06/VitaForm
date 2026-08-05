import json
import re
import uuid

from pydantic import ValidationError

from app.core.enums import SectionType
from features.ai.schemas import AIResumeResponse, AIResumeSection

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


class AIResponseValidationError(Exception):
    """Raised when the AI's response is malformed enough to warrant a retry
    (invalid JSON, wrong schema, empty summary) -- distinct from merely
    filtering out a hallucinated id, which is handled silently below."""


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def validate_ai_response(
    raw_text: str, candidate_ids_by_section: dict[SectionType, set[uuid.UUID]]
) -> AIResumeResponse:
    cleaned = _strip_code_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIResponseValidationError(f"AI response was not valid JSON: {exc}") from exc

    try:
        parsed = AIResumeResponse.model_validate(data)
    except ValidationError as exc:
        raise AIResponseValidationError(
            f"AI response did not match the expected schema: {exc}"
        ) from exc

    if not parsed.summary.strip():
        raise AIResponseValidationError("AI response had an empty summary.")

    # Defense in depth: silently drop any id the AI wasn't offered, rather
    # than failing the whole generation. The renderer re-validates ownership
    # from the database anyway, so a dropped id can never surface fabricated
    # content -- it can only result in an item being left out.
    filtered_sections = []
    for section in parsed.sections:
        allowed = candidate_ids_by_section.get(section.section_type, set())
        filtered_sections.append(
            AIResumeSection(
                section_type=section.section_type,
                item_ids=[item_id for item_id in section.item_ids if item_id in allowed],
            )
        )

    return AIResumeResponse(
        summary=parsed.summary.strip(), keywords=parsed.keywords, sections=filtered_sections
    )
