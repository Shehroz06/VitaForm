"""Parses and validates the classifier's JSON response. Two failure modes,
handled differently: the whole response being unparseable/malformed raises
(triggers a retry via run_with_fallback, same as every other AI response
validator in this codebase); an individual item failing its resource's own
CreateRequest schema is silently dropped, never coerced -- the same
hallucination-defense posture as features/ai/validator.py, just applied per
item instead of per id."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.enums import SectionType
from features.cv_import.target_schemas import IMPORT_TARGET_SCHEMAS

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


class ClassificationValidationError(Exception):
    """Raised when the AI response is malformed enough to warrant a retry
    (invalid JSON, wrong top-level shape) -- distinct from a single item
    failing its own schema, which is dropped silently below."""


@dataclass
class ClassificationResult:
    bio: str | None
    items_by_section: dict[SectionType, list[BaseModel]] = field(default_factory=dict)
    dropped_count: int = 0


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def validate_classification_response(raw_text: str) -> ClassificationResult:
    cleaned = _strip_code_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ClassificationValidationError(f"AI response was not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ClassificationValidationError("AI response was not a JSON object.")

    bio = data.get("bio")
    if bio is not None and not isinstance(bio, str):
        raise ClassificationValidationError("AI response 'bio' was not a string.")

    sections = data.get("sections", {})
    if not isinstance(sections, dict):
        raise ClassificationValidationError("AI response 'sections' was not an object.")

    result = ClassificationResult(bio=bio.strip() if bio and bio.strip() else None)
    for section_key, raw_items in sections.items():
        try:
            section_type = SectionType(section_key)
        except ValueError:
            continue
        schema = IMPORT_TARGET_SCHEMAS.get(section_type)
        if schema is None or not isinstance(raw_items, list):
            continue

        validated: list[BaseModel] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                result.dropped_count += 1
                continue
            try:
                validated.append(schema.model_validate(_strip_unknown_keys(schema, raw_item)))
            except ValidationError:
                result.dropped_count += 1
        if validated:
            result.items_by_section[section_type] = validated

    return result


def _strip_unknown_keys(schema: type[BaseModel], raw_item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in raw_item.items() if key in schema.model_fields}
