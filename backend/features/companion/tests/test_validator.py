import json

import pytest

from features.ai.validator import AIResponseValidationError
from features.companion.validator import validate_cover_letter_response, validate_linkedin_response


def test_validate_cover_letter_response_parses_valid_json() -> None:
    body = "Dear Hiring Manager, " + ("I am a great fit. " * 20)
    result = validate_cover_letter_response(json.dumps({"cover_letter": body}), source_text=body)
    assert result.cover_letter.startswith("Dear Hiring Manager")


def test_validate_cover_letter_response_strips_code_fences() -> None:
    body = "Dear Hiring Manager, " + ("I am a great fit. " * 20)
    raw = f'```json\n{json.dumps({"cover_letter": body})}\n```'
    result = validate_cover_letter_response(raw, source_text=body)
    assert result.cover_letter.startswith("Dear Hiring Manager")


def test_validate_cover_letter_response_rejects_invalid_json() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response("not json", source_text="")


def test_validate_cover_letter_response_rejects_too_short_body() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response(
            json.dumps({"cover_letter": "Too short."}), source_text="Too short."
        )


def test_validate_cover_letter_response_rejects_fabricated_numbers() -> None:
    source = "Candidate summary:\n- Software Engineer at Acme (2020-2022)"
    body = "Dear Hiring Manager, " + ("I led a team of 15 engineers and shipped 42 features. " * 4)
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response(json.dumps({"cover_letter": body}), source_text=source)


def test_validate_cover_letter_response_rejects_fabricated_skills() -> None:
    source = "Candidate summary:\n- Software Engineer at Acme (2020-2022)"
    body = "Dear Hiring Manager, " + (
        "I have deep expertise in Kubernetes and Rust and TensorFlow. " * 4
    )
    with pytest.raises(AIResponseValidationError):
        validate_cover_letter_response(json.dumps({"cover_letter": body}), source_text=source)


def test_validate_linkedin_response_parses_valid_json() -> None:
    about = "Experienced engineer. " * 5
    result = validate_linkedin_response(
        json.dumps({"headline": "Senior Backend Engineer", "about": about}),
        source_text=f"Senior Backend Engineer {about}",
    )
    assert result.headline == "Senior Backend Engineer"


def test_validate_linkedin_response_rejects_missing_headline() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_linkedin_response(
            json.dumps({"about": "Experienced engineer. " * 5}), source_text=""
        )


def test_validate_linkedin_response_rejects_empty_about() -> None:
    with pytest.raises(AIResponseValidationError):
        validate_linkedin_response(
            json.dumps({"headline": "Engineer", "about": "short"}), source_text=""
        )


def test_validate_linkedin_response_rejects_fabricated_content() -> None:
    source = "Candidate summary:\n- Software Engineer at Acme (2020-2022)"
    about = "I have shipped 30 products using Kubernetes and GraphQL. " * 3
    with pytest.raises(AIResponseValidationError):
        validate_linkedin_response(
            json.dumps({"headline": "Senior Engineer", "about": about}), source_text=source
        )
