from features.ai.ranking import extract_keywords


def test_extract_keywords_lowercases_and_drops_stopwords() -> None:
    keywords = extract_keywords("We are looking for a Senior Python Backend Engineer with AWS.")
    assert "python" in keywords
    assert "backend" in keywords
    assert "engineer" in keywords
    assert "aws" in keywords
    assert "for" not in keywords
    assert "with" not in keywords
    assert "a" not in keywords


def test_extract_keywords_handles_empty_text() -> None:
    assert extract_keywords("") == set()
    assert extract_keywords(None) == set()  # type: ignore[arg-type]
