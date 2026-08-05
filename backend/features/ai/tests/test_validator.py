import json
import uuid

import pytest

from app.core.enums import SectionType
from features.ai.validator import AIResponseValidationError, validate_ai_response


def test_validate_ai_response_parses_valid_json() -> None:
    education_id = uuid.uuid4()
    candidates = {SectionType.EDUCATION: {education_id}}
    raw = json.dumps(
        {
            "summary": "A great candidate.",
            "keywords": ["python"],
            "sections": [{"section_type": "education", "item_ids": [str(education_id)]}],
        }
    )

    result = validate_ai_response(raw, candidates)

    assert result.summary == "A great candidate."
    assert result.sections[0].item_ids == [education_id]


def test_validate_ai_response_strips_markdown_code_fences() -> None:
    raw = '```json\n{"summary": "Summary text.", "keywords": [], "sections": []}\n```'
    result = validate_ai_response(raw, {})
    assert result.summary == "Summary text."


def test_validate_ai_response_drops_ids_not_offered_as_candidates() -> None:
    real_id = uuid.uuid4()
    fabricated_id = uuid.uuid4()
    candidates = {SectionType.EDUCATION: {real_id}}
    raw = json.dumps(
        {
            "summary": "Summary.",
            "keywords": [],
            "sections": [
                {"section_type": "education", "item_ids": [str(real_id), str(fabricated_id)]}
            ],
        }
    )

    result = validate_ai_response(raw, candidates)

    assert result.sections[0].item_ids == [real_id]


def test_validate_ai_response_rejects_invalid_json() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_ai_response("not json at all", {})


def test_validate_ai_response_rejects_missing_summary() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_ai_response(json.dumps({"keywords": [], "sections": []}), {})


def test_validate_ai_response_rejects_empty_summary() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_ai_response(json.dumps({"summary": "   ", "keywords": [], "sections": []}), {})
