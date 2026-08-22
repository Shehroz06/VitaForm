from features.resumes.latex_utils import format_description, format_paragraph, latex_escape


def test_latex_escape_handles_every_special_character() -> None:
    assert latex_escape("100%") == r"100\%"
    assert latex_escape("A & B") == r"A \& B"
    assert latex_escape("#tag") == r"\#tag"
    assert latex_escape("$5") == r"\$5"
    assert latex_escape("{braces}") == r"\{braces\}"
    assert latex_escape("^caret") == r"\textasciicircum{}caret"
    assert latex_escape("_score") == r"\_score"
    assert latex_escape("~tilde") == r"\textasciitilde{}tilde"
    assert latex_escape("back\\slash") == r"back\textbackslash{}slash"


def test_latex_escape_neutralizes_write18_injection_attempt() -> None:
    injection = r"\write18{touch /tmp/pwned}"
    escaped = latex_escape(injection)

    assert "\\write18" not in escaped
    assert escaped.startswith(r"\textbackslash{}write18")


def test_latex_escape_empty_and_none() -> None:
    assert latex_escape(None) == ""
    assert latex_escape("") == ""


def test_latex_escape_plain_text_is_unchanged() -> None:
    assert latex_escape("Software Engineer at Acme Corp") == "Software Engineer at Acme Corp"


def test_format_description_bulleted_lines_become_itemize() -> None:
    text = "• Built a thing\n• Shipped it to prod\n• 100% test coverage"
    result = format_description(text)

    assert result.startswith("\\begin{itemize}")
    assert "\\end{itemize}" in result
    assert "\\item Built a thing" in result
    assert "\\item Shipped it to prod" in result
    assert "100\\% test coverage" in result
    assert "•" not in result


def test_format_description_plain_single_sentence_still_becomes_a_one_item_list() -> None:
    # Bullets are now unconditional -- whether an item renders as a list
    # must never depend on how its text happened to be typed into the
    # profile (see description_units.py's module docstring), so even a
    # single plain sentence becomes a one-item itemize, not a paragraph.
    text = "A biometric system built on a DINOv2 backbone, trained on CEDAR & SigComp2011."
    result = format_description(text)

    assert result.startswith("\\begin{itemize}")
    assert "CEDAR \\& SigComp2011" in result


def test_format_description_ends_with_par() -> None:
    # Regression test: the .tex.jinja2 template's trim_blocks setting eats
    # the newline between this call and whatever the template puts right
    # after it (a links line, the next section) -- without an explicit
    # \par, that content gets typeset as a continuation of this same
    # paragraph, e.g. a URL butting up against the last word with no space.
    result = format_description("Some project description.")
    assert result.endswith("\\par")


def test_format_description_mixed_bulleted_and_plain_lines_becomes_one_uniform_list() -> None:
    # Only some lines are bulleted -- not confidently a pre-formatted bullet
    # list, so it's sentence-split like plain text rather than trusting the
    # stray marker. Either way it still renders as one list: the stray "•"
    # must not survive as literal text sitting next to the item's own
    # rendered bullet.
    text = "Intro sentence with no bullet.\n• Built a thing"
    result = format_description(text)

    assert result.startswith("\\begin{itemize}")
    assert "\\item Intro sentence with no bullet." in result
    assert "\\item Built a thing" in result
    assert "•" not in result


def test_format_description_empty() -> None:
    assert format_description(None) == ""
    assert format_description("   \n  ") == ""


def test_format_paragraph_never_bullets_the_summary() -> None:
    text = "Sentence one. Sentence two. Sentence three."
    result = format_paragraph(text)

    assert "\\begin{itemize}" not in result
    assert result == "Sentence one. Sentence two. Sentence three.\n\\par"


def test_format_paragraph_joins_multiple_lines_into_one() -> None:
    result = format_paragraph("Line one\nLine two")
    assert result == "Line one Line two\n\\par"


def test_format_paragraph_empty() -> None:
    assert format_paragraph(None) == ""
    assert format_paragraph("   \n  ") == ""
