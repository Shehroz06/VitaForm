"""Every user-controlled string that reaches the LaTeX renderer goes through
one of these two functions -- names, headlines, bios, company/institution
names, descriptions, URLs. Never interpolate raw text into a .tex source
file: LaTeX's own control characters (backslash, braces, $, &, #, ^, _, ~,
%) turn arbitrary profile text into arbitrary LaTeX commands otherwise.
`-no-shell-escape` at the pdflatex invocation (see latex_renderer.py) is the
hard backstop against that turning into code execution, but this is the
correctness layer: escaped text should just print as itself, verbatim."""

import re

from features.resumes.description_units import split_description_into_units

_ESCAPE_MAP: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "%": r"\%",
}
_ESCAPE_RE = re.compile("|".join(re.escape(char) for char in _ESCAPE_MAP))

# hyperref parses \href{}'s *target* argument in a special URL-catcode mode
# that already handles %, #, &, _, ~ correctly as URL characters -- running
# it through latex_escape would corrupt real URLs containing those (e.g. a
# query string's `&`). But this app's URL validator (app/core/validators.py)
# only rejects whitespace, not braces or backslashes, so an unescaped `{`,
# `}`, or `\` in a stored URL could still break brace-matching or inject a
# control sequence into the .tex source. Those three are the only
# characters this strips -- everything else passes through so the link
# actually points where it's supposed to. Display text (the visible label)
# should still go through latex_escape as normal.
_URL_UNSAFE_RE = re.compile(r"[\\{}]")


def latex_safe_url(url: str | None) -> str:
    """For \\href{}'s target argument specifically -- see module note above
    for why this is a different, narrower filter than latex_escape."""
    if not url:
        return ""
    return _URL_UNSAFE_RE.sub("", url)


def latex_escape(text: str | None) -> str:
    """Escapes LaTeX's special characters so `text` renders as literal,
    unformatted text. Must be applied to every piece of user-controlled
    content before it reaches a .tex template -- see module docstring."""
    if not text:
        return ""
    return _ESCAPE_RE.sub(lambda match: _ESCAPE_MAP[match.group(0)], text)


def format_description(text: str | None) -> str:
    """Renders a description as a LaTeX `itemize` block, one \\item per
    unit -- always, regardless of whether the stored text happens to be
    bullet-prefixed or one flowing paragraph (see description_units.py's
    module docstring for why the old bullets-vs-paragraph branch made
    output inconsistent across items). A single-unit description still
    renders as a one-item list, which is normal resume convention and
    keeps every item's structure uniform."""
    if not text or not text.strip():
        return ""

    units, _ = split_description_into_units(text)
    if not units:
        return ""

    items = "\n".join(f"  \\item {latex_escape(unit)}" for unit in units)
    # \par is required, not cosmetic: the .tex.jinja2 template's trim_blocks
    # setting eats the newline after the {% endif %} that wraps this call,
    # so whatever comes next in the template (a links line, the next
    # section) would otherwise be typeset as a continuation of this same
    # paragraph -- e.g. a URL butting up against the last word with no
    # space at all.
    return (
        f"\\begin{{itemize}}[leftmargin=*,itemsep=0pt,topsep=2pt]\n{items}\n"
        "\\end{itemize}\n\\par"
    )


def format_paragraph(text: str | None) -> str:
    """Renders text as a single flowing, escaped paragraph -- for the
    resume summary specifically, which is deliberately never bulleted
    (unlike format_description's item entries): a summary is prose, not a
    list of discrete achievements, and staying a paragraph regardless of
    length is itself part of being uniform, not an exception to it."""
    if not text or not text.strip():
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return latex_escape(" ".join(lines)) + "\n\\par"
