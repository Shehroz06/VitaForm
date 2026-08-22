import uuid

from features.ai.description_rewriter import (
    _parse_response,
    build_rewrite_prompt,
    passes_fact_check,
)


def test_passes_fact_check_allows_pure_rephrasing() -> None:
    original = "Built a REST API using Python and Docker for a 5-person team."
    rewritten = "Developed a Python-based REST API, containerized with Docker for a 5-person team."
    assert passes_fact_check(original, rewritten) is True


def test_passes_fact_check_rejects_an_invented_metric() -> None:
    original = "Built a backend service that handles user authentication."
    rewritten = "Built a backend service that handles user authentication, improving speed by 40%."
    assert passes_fact_check(original, rewritten) is False


def test_passes_fact_check_rejects_an_invented_technology() -> None:
    original = "Built a REST API using Python."
    rewritten = "Built a scalable REST API using Python and Kubernetes."
    assert passes_fact_check(original, rewritten) is False


def test_passes_fact_check_allows_dropping_content_never_adding() -> None:
    # Shortening (fewer facts survive) is always safe -- only new facts
    # appearing that weren't in the original should fail the check.
    original = "Built a REST API using Python and Docker, deployed on AWS with 99.9% uptime."
    rewritten = "Built a REST API using Python and Docker."
    assert passes_fact_check(original, rewritten) is True


def test_passes_fact_check_allows_reusing_the_same_number_differently_phrased() -> None:
    original = "Reduced latency by 30% across the service."
    rewritten = "Cut service latency by 30%."
    assert passes_fact_check(original, rewritten) is True


def test_build_rewrite_prompt_includes_every_item_and_context() -> None:
    item_id = uuid.uuid4()
    prompt = build_rewrite_prompt(
        [(item_id, "Built a thing.")],
        job_description="We need a backend engineer.",
        target_role="Backend Engineer",
    )
    assert str(item_id) in prompt
    assert "Built a thing." in prompt
    assert "backend engineer" in prompt.lower()
    assert "Backend Engineer" in prompt


def test_parse_response_extracts_valid_items() -> None:
    item_id = uuid.uuid4()
    raw = f'{{"items": [{{"id": "{item_id}", "text": "Rewritten text."}}]}}'
    result = _parse_response(raw, {item_id})
    assert result == {item_id: "Rewritten text."}


def test_parse_response_strips_code_fences() -> None:
    item_id = uuid.uuid4()
    raw = f'```json\n{{"items": [{{"id": "{item_id}", "text": "Rewritten."}}]}}\n```'
    result = _parse_response(raw, {item_id})
    assert result == {item_id: "Rewritten."}


def test_parse_response_drops_ids_it_was_not_asked_about() -> None:
    known_id = uuid.uuid4()
    unknown_id = uuid.uuid4()
    raw = (
        f'{{"items": [{{"id": "{known_id}", "text": "A"}}, '
        f'{{"id": "{unknown_id}", "text": "B"}}]}}'
    )
    result = _parse_response(raw, {known_id})
    assert result == {known_id: "A"}
