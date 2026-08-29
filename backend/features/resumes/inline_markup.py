"""Inline text formatting a user may type into any free-text resume field
(an item description, the summary): the one place that decides what marks
are supported and how they tokenise.

Supported today: ``**bold**``.

`split_inline_spans` tokenises the *raw* text into ``(segment, is_bold)``
pairs and does no escaping itself. Each render engine then escapes every
segment with its own escaper before wrapping the bold ones -- HTML-escape
then ``<strong>`` (here), `latex_escape` then ``\\textbf{}`` (latex_utils.py).
That ordering is deliberate and is what keeps the "never interpolate raw
user text into the output" guarantee that renderer.py and latex_utils.py
both rely on: a ``**`` marker never reaches the output, and the text
between markers is escaped exactly as any other user text is.

Edge cases, by design:
- A ``**`` with no matching partner renders as literal asterisks (the
  span regex simply doesn't match), so a stray marker can't "eat" the
  rest of the line.
- A bold span is only recognised within a single run of text. The
  sentence splitter in description_units.py can cut a span that straddles
  a sentence boundary (``**A. B**``); keep a bold span inside one
  sentence to be safe.
"""

import re

from markupsafe import Markup, escape

from features.resumes.description_units import split_description_into_units

# Non-greedy, dot matches newline so a span may wrap across a soft line
# break. The `(?=\S)` / `(?<=\S)` lookarounds keep `** **` (whitespace
# only) and `****` (empty) from being treated as spans.
_BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.DOTALL)


def strip_bold_markers(text: str) -> str:
    """Remove the ``**`` markers of every matched bold span, keeping the
    text between them. For rendering with bold markup turned off -- the
    user still gets clean prose, never literal asterisks."""
    return _BOLD_RE.sub(r"\1", text)


def split_inline_spans(text: str) -> list[tuple[str, bool]]:
    """Tokenise `text` into ``(segment, is_bold)`` pairs. Concatenating
    every segment in order reproduces `text` with only the ``**`` markers
    of matched bold spans removed. No escaping happens here."""
    spans: list[tuple[str, bool]] = []
    cursor = 0
    for match in _BOLD_RE.finditer(text):
        if match.start() > cursor:
            spans.append((text[cursor : match.start()], False))
        spans.append((match.group(1), True))
        cursor = match.end()
    if cursor < len(text):
        spans.append((text[cursor:], False))
    return spans


def join_description_units(text: str | None) -> str:
    """The description's natural units (see description_units.py) rejoined
    into one flowing line -- for the sections that render an entry as a
    single bullet rather than a sub-list."""
    if not text or not text.strip():
        return ""
    units, _ = split_description_into_units(text)
    return " ".join(units)


def render_inline_html(text: str) -> Markup:
    """HTML for one run of user text: every segment HTML-escaped, bold
    segments wrapped in ``<strong>``. Safe to interpolate as-is."""
    parts: list[str] = []
    for segment, is_bold in split_inline_spans(text):
        rendered = escape(segment)
        parts.append(f"<strong>{rendered}</strong>" if is_bold else str(rendered))
    return Markup("".join(parts))


def render_description_inline_html(text: str | None) -> Markup:
    """A whole description as one escaped, bold-aware HTML line."""
    joined = join_description_units(text)
    return render_inline_html(joined) if joined else Markup("")
