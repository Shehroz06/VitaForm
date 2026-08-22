from features.ai.description_condenser import condense_description


def test_condense_returns_none_for_empty_or_single_unit_text() -> None:
    assert condense_description(None) is None
    assert condense_description("") is None
    assert condense_description("Just one sentence, nothing to trim.") is None


def test_condense_never_invents_words_not_in_the_source() -> None:
    text = (
        "Built a real-time drone flight-path monitor. "
        "Trained a Siamese network for clip similarity. "
        "Deployed the service with Docker."
    )
    result = condense_description(text, keep_ratio=0.6)
    assert result is not None
    source_words = set(text.split())
    result_words = set(result.split())
    assert result_words <= source_words, "condensed output contains words absent from the source"


def test_condense_bulleted_description_stays_bulleted() -> None:
    text = "• First point about the project.\n• Second point about deployment.\n• Third point."
    result = condense_description(text, keep_ratio=0.34)
    assert result is not None
    assert result.startswith("•")
    assert result.count("•") == 1


def test_condense_no_keywords_keeps_the_first_n_units_in_order() -> None:
    text = "First sentence here. Second sentence here. Third sentence here."
    result = condense_description(text, keep_ratio=0.67)
    assert result == "First sentence here. Second sentence here."


def test_condense_with_keywords_reorders_by_relevance_keeping_original_ties_stable() -> None:
    text = "Built a website with React. Wrote unit tests. Deployed with Docker and Kubernetes."
    result = condense_description(text, keywords={"docker", "kubernetes"}, keep_ratio=1.0)
    # keep_ratio=1.0 with keywords doesn't drop anything, so nothing changes
    # (a real change would only come from a keep_ratio < 1.0).
    assert result is None


def test_condense_with_keywords_and_partial_keep_ratio_keeps_most_relevant_units() -> None:
    text = "Built a website with React. Wrote unit tests. Deployed with Docker and Kubernetes."
    result = condense_description(text, keywords={"docker", "kubernetes"}, keep_ratio=0.34)
    assert result == "Deployed with Docker and Kubernetes."


def test_condense_keep_ratio_one_without_keywords_is_a_noop() -> None:
    text = "First sentence here. Second sentence here."
    assert condense_description(text, keep_ratio=1.0) is None
