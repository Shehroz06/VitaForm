import json

import pytest

from features.ai.validator import AIResponseValidationError
from features.companion.validator import validate_cover_letter_response, validate_linkedin_response


def test_validate_cover_letter_response_parses_valid_json() -> None:
    body = "Dear Hiring Manager, " + ("I am a great fit. " * 20)
    result = validate_cover_letter_response(json.dumps({"cover_letter": body}))
    assert result.cover_letter.startswith("Dear Hiring Manager")


def test_validate_cover_letter_response_strips_code_fences() -> None:
    body = "Dear Hiring Manager, " + ("I am a great fit. " * 20)
    raw = f'```json\n{json.dumps({"cover_letter": body})}\n```'
    result = validate_cover_letter_response(raw)
    assert result.cover_letter.startswith("Dear Hiring Manager")


def test_validate_cover_letter_response_rejects_invalid_json() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response("not json")


def test_validate_cover_letter_response_rejects_too_short_body() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response(json.dumps({"cover_letter": "Too short."}))


def test_validate_linkedin_response_parses_valid_json() -> None:
    about = "Experienced engineer. " * 5
    result = validate_linkedin_response(
        json.dumps({"headline": "Senior Backend Engineer", "about": about})
    )
    assert result.headline == "Senior Backend Engineer"


def test_validate_linkedin_response_rejects_missing_headline() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_linkedin_response(json.dumps({"about": "Experienced engineer. " * 5}))


def test_validate_linkedin_response_rejects_empty_about() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_linkedin_response(json.dumps({"headline": "Engineer", "about": "short"}))
