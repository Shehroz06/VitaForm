from markupsafe import Markup

from features.resumes.inline_markup import (
    render_description_inline_html,
    render_inline_html,
    split_inline_spans,
    strip_bold_markers,
)
from features.resumes.latex_utils import format_inline_description, latex_inline


def test_split_inline_spans_marks_bold_runs() -> None:
    assert split_inline_spans("led a team of **80+** members") == [
        ("led a team of ", False),
        ("80+", True),
        (" members", False),
    ]


def test_split_inline_spans_plain_text_is_a_single_non_bold_span() -> None:
    assert split_inline_spans("no markup here") == [("no markup here", False)]


def test_split_inline_spans_unbalanced_marker_stays_literal() -> None:
    # A lone ``**`` must never "eat" the rest of the line.
    assert split_inline_spans("grew by **20% through outreach") == [
        ("grew by **20% through outreach", False)
    ]


def test_split_inline_spans_ignores_empty_and_whitespace_only_spans() -> None:
    assert split_inline_spans("a **** b ** ** c") == [("a **** b ** ** c", False)]


def test_strip_bold_markers_keeps_text_drops_markers() -> None:
    assert strip_bold_markers("grew by **30%** this year") == "grew by 30% this year"


def test_strip_bold_markers_leaves_unbalanced_marker_alone() -> None:
    assert strip_bold_markers("grew by **30% this year") == "grew by **30% this year"


def test_render_inline_html_wraps_bold_and_escapes_every_segment() -> None:
    result = render_inline_html('rank **2nd** & <top> "1%"')
    assert result == Markup("rank <strong>2nd</strong> &amp; &lt;top&gt; &#34;1%&#34;")
    assert isinstance(result, Markup)


def test_render_inline_html_escapes_inside_a_bold_span() -> None:
    assert render_inline_html("**<b>x</b>**") == Markup("<strong>&lt;b&gt;x&lt;/b&gt;</strong>")


def test_render_description_inline_html_joins_units_into_one_line() -> None:
    result = render_description_inline_html("Led the chapter. Grew it by **30%**.")
    assert result == Markup("Led the chapter. Grew it by <strong>30%</strong>.")


def test_render_description_inline_html_empty() -> None:
    assert render_description_inline_html(None) == Markup("")
    assert render_description_inline_html("   ") == Markup("")


def test_latex_inline_wraps_bold_and_escapes_every_segment() -> None:
    # The ``%`` and ``&`` still get LaTeX-escaped, inside the bold span and out.
    assert latex_inline("grew **30%** & more") == r"grew \textbf{30\%} \& more"


def test_latex_inline_unbalanced_marker_is_escaped_literally() -> None:
    assert latex_inline("**oops") == r"**oops"


def test_format_inline_description_joins_units_into_one_escaped_line() -> None:
    result = format_inline_description("Ran events. Boosted turnout by **20%**.")
    assert result == r"Ran events. Boosted turnout by \textbf{20\%}."


def test_format_inline_description_empty() -> None:
    assert format_inline_description(None) == ""
    assert format_inline_description("  \n ") == ""
