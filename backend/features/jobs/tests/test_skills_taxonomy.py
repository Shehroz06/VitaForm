from features.jobs.skills_taxonomy import canonicalize, match_skills


def test_match_skills_finds_multi_word_alias_as_one_unit() -> None:
    # Regression test for the audited "machine"/"learning" split-token bug:
    # a multi-word alias must match as a phrase, not as separate keywords.
    matched = match_skills("Strong background in machine learning and computer vision.")
    assert matched == {"Machine Learning", "Computer Vision"}


def test_match_skills_respects_word_boundaries() -> None:
    # "ml" is a real alias for Machine Learning, but must not match inside
    # unrelated words like "html" -- the HTML skill should match on its own
    # alias, not accidentally also credit Machine Learning.
    matched = match_skills("Built responsive HTML pages.")
    assert matched == {"HTML"}
    assert match_skills("Solid ML fundamentals.") == {"Machine Learning"}


def test_match_skills_ignores_generic_words() -> None:
    matched = match_skills("Worked across multiple teams within one organization, step by step.")
    assert matched == set()


def test_match_skills_symbol_aliases() -> None:
    assert match_skills("Proficient in C++ and Node.js.") == {"C++", "Node.js"}


def test_match_skills_dotted_framework_name_does_not_leak_bare_js() -> None:
    # "Node.js"/"Vue.js"/"Next.js" all end in ".js" -- a bare "js" alias
    # would false-match JavaScript as a second skill inside each of them.
    for text, expected in (
        ("Built APIs with Node.js.", "Node.js"),
        ("Built a landing page with Next.js.", "Next.js"),
    ):
        assert match_skills(text) == {expected}


def test_canonicalize_known_alias() -> None:
    assert canonicalize("react.js") == "React"
    assert canonicalize("Python3") == "Python"


def test_canonicalize_unknown_skill_falls_back_to_trimmed_name() -> None:
    assert canonicalize("  Underwater Basket Weaving  ") == "Underwater Basket Weaving"
