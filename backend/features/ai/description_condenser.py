"""Extractive-only description tailoring: selects and reorders sentences
that already exist in an item's own description text -- never writes a new
one. Two callers, same mechanism:

- `page_fit.py` calls this with `keep_ratio < 1.0` (no keywords) when a
  resume still overflows one page after spacing/density are already
  maxed out, to shrink the lowest-relevance item's text before resorting
  to deleting it outright.
- `ai/service.py` calls this with `keep_ratio=1.0` and the job description's
  keywords during generation, purely to reorder each item's own sentences
  so the most JD-relevant one leads -- length is unchanged, only emphasis.

Both are deliberately incapable of inventing content: the worst either can
do is drop or reorder sentences the user already wrote. This is the
`condense_description` boundary CLAUDE.md's "AI never invents" principle
draws for resume text -- and it's why this needs no AI provider call at
all, matching this codebase's existing "rules first" pattern
(ranking.py/analyzer.py/ats_scorer.py)."""

from features.ai.ranking import extract_keywords
from features.resumes.description_units import split_description_into_units


def condense_description(
    text: str | None,
    *,
    keywords: set[str] | None = None,
    keep_ratio: float = 1.0,
) -> str | None:
    """Returns None when there's nothing to change (no text, or only one
    unit to select from) so callers can tell "no override needed" apart
    from "override is the same text" without a string comparison."""
    if not text or not text.strip():
        return None

    units, was_bulleted = split_description_into_units(text)
    if len(units) <= 1:
        return None

    target_count = max(1, round(len(units) * keep_ratio))

    if keywords:
        # Stable sort by relevance (descending) -- ties keep their
        # original relative order rather than an arbitrary one.
        ranked = sorted(
            enumerate(units),
            key=lambda pair: len(extract_keywords(pair[1]) & keywords),
            reverse=True,
        )
        kept_indices = sorted(i for i, _ in ranked[:target_count])
    else:
        # No JD signal to rank by -- keep the writer's own first N units;
        # resume convention already puts the strongest point first.
        kept_indices = list(range(min(target_count, len(units))))

    if kept_indices == list(range(len(units))):
        return None  # every unit survived -- not actually a change

    kept = [units[i] for i in kept_indices]
    if was_bulleted:
        return "\n".join(f"• {unit}" for unit in kept)
    return " ".join(kept)
