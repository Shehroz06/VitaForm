"""Splits a description into its natural bullet/sentence units -- the one
place this decision is made, shared by everything that needs to reformat a
description without inventing text: extractive condensing
(features/ai/description_condenser.py) and rendering a description as a
uniformly bulleted list in both resume render engines (latex_utils.py's
format_description, renderer.py's HTML `description_units` filter).

Previously each render engine decided bullets-vs-paragraph independently,
and only when every line of the *stored* text already happened to start
with a marker -- so whether an item rendered as bullets or one flowing
paragraph depended on how it was originally typed into the profile, not on
any deliberate choice. Two different items in the same resume could
therefore render in two different styles. Splitting into units and always
rendering as a list (both engines now do this) removes that inconsistency:
the same stored text always becomes the same structure."""

import re

_BULLET_PREFIX_RE = re.compile(r"^\s*[•\-*]\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_description_into_units(text: str) -> tuple[list[str], bool]:
    """Splits already-bullet-formatted text into its bullet lines (marker
    stripped), otherwise into sentences. Every returned unit is exact
    substring content from `text` -- never invented, only split. Returns
    the units plus whether the source was already bullet-formatted, since
    `condense_description` needs that to rejoin in the same style."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bulleted = [line for line in lines if _BULLET_PREFIX_RE.match(line)]
    if bulleted and len(bulleted) == len(lines):
        return [_BULLET_PREFIX_RE.sub("", line).strip() for line in lines], True

    # Not uniformly bulleted (e.g. one stray bulleted line mixed into
    # otherwise plain text) -- still strip any bullet marker a line starts
    # with, so it never survives as literal text sitting inside a rendered
    # list item next to that item's own bullet.
    sentences = [
        _BULLET_PREFIX_RE.sub("", s.strip()).strip()
        for s in _SENTENCE_SPLIT_RE.split(text.strip())
        if s.strip()
    ]
    return sentences, False
