"""Rules-based relevance ranking against a job description.

Per the AI engine design doc's own checklist -- "Does it require AI? Can
rules solve it instead?" -- ranking and keyword extraction are solved with
plain keyword-overlap + recency heuristics, no model call. This keeps the
prompt small (only the top-scoring candidates per section are ever sent to
the AI) and keeps costs and latency down, matching the doc's token strategy.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.enums import SectionType

_STOPWORDS = frozenset(
    """
    a an the and or but if is are was were be been being to of in on for
    with as by at from this that these those it its it's you your we our
    they their he she his her i me my will would should could can may
    must have has had do does did not no yes about into over under than
    then so such also more most other some any all each every no nor
    """.split()
)
_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.]{1,}")


def extract_keywords(text: str) -> set[str]:
    tokens = (match.group(0).lower().strip(".") for match in _WORD_RE.finditer(text or ""))
    return {t for t in tokens if t and t not in _STOPWORDS and len(t) >= 2}


def _text_overlap_score(text: str | None, keywords: set[str]) -> float:
    if not text or not keywords:
        return 0.0
    return float(len(extract_keywords(text) & keywords))


def _recency_bonus(reference_date: date | None, *, is_current: bool = False) -> float:
    if is_current:
        return 3.0
    if reference_date is None:
        return 1.0
    years_ago = (date.today() - reference_date).days / 365
    return max(0.0, 3.0 - years_ago * 0.3)


def _score_education(item: Any, keywords: set[str]) -> float:
    text = " ".join(
        filter(None, [item.institution_name, item.degree, item.field_of_study, item.description])
    )
    return _text_overlap_score(text, keywords) + _recency_bonus(
        item.end_date, is_current=item.is_current
    )


def _score_experience(item: Any, keywords: set[str]) -> float:
    text = " ".join(filter(None, [item.job_title, item.company_name, item.description]))
    return (
        _text_overlap_score(text, keywords) * 2
        + _recency_bonus(item.end_date, is_current=item.is_current)
        + (2.0 if item.is_current else 0.0)
    )


def _score_project(item: Any, keywords: set[str]) -> float:
    text = " ".join(filter(None, [item.title, item.role, item.description]))
    skill_text = " ".join(skill.name for skill in item.skills)
    return (
        _text_overlap_score(text, keywords) * 2
        + _text_overlap_score(skill_text, keywords) * 1.5
        + (2.0 if item.is_pinned else 0.0)
        + _recency_bonus(item.end_date)
    )


_LEVEL_BONUS = {"expert": 2.0, "advanced": 1.5, "intermediate": 1.0, "beginner": 0.5}


def _score_skill(item: Any, keywords: set[str]) -> float:
    name_tokens = extract_keywords(item.name)
    match_bonus = 5.0 if name_tokens & keywords else 0.0
    level_bonus = _LEVEL_BONUS.get(item.level.value if item.level else "", 0.0)
    return match_bonus + level_bonus


def _score_certification(item: Any, keywords: set[str]) -> float:
    text = " ".join(filter(None, [item.name, item.issuing_organization]))
    return _text_overlap_score(text, keywords) * 2 + _recency_bonus(item.issue_date)


def _score_achievement(item: Any, keywords: set[str]) -> float:
    text = " ".join(filter(None, [item.title, item.issuer, item.description]))
    return _text_overlap_score(text, keywords) + _recency_bonus(item.date_achieved)


def _score_award(item: Any, keywords: set[str]) -> float:
    text = " ".join(filter(None, [item.title, item.issuer, item.description]))
    return _text_overlap_score(text, keywords) + _recency_bonus(item.date_received)


_SCORERS: dict[SectionType, Callable[[Any, set[str]], float]] = {
    SectionType.EDUCATION: _score_education,
    SectionType.EXPERIENCE: _score_experience,
    SectionType.PROJECTS: _score_project,
    SectionType.SKILLS: _score_skill,
    SectionType.CERTIFICATIONS: _score_certification,
    SectionType.ACHIEVEMENTS: _score_achievement,
    SectionType.AWARDS: _score_award,
}

_CANDIDATE_CAPS: dict[SectionType, int] = {
    SectionType.EDUCATION: 4,
    SectionType.EXPERIENCE: 6,
    SectionType.PROJECTS: 8,
    SectionType.SKILLS: 20,
    SectionType.CERTIFICATIONS: 6,
    SectionType.ACHIEVEMENTS: 6,
    SectionType.AWARDS: 6,
}


@dataclass(frozen=True)
class RankedItem:
    item: Any
    score: float


def rank_and_select(
    items_by_type: dict[SectionType, list[Any]], keywords: set[str]
) -> dict[SectionType, list[RankedItem]]:
    """Scores every candidate item and returns each section's top-N,
    highest score first -- the only items ever offered to the AI."""
    result: dict[SectionType, list[RankedItem]] = {}
    for section_type, items in items_by_type.items():
        scorer = _SCORERS.get(section_type)
        if scorer is None:
            continue
        ranked = sorted(
            (RankedItem(item, scorer(item, keywords)) for item in items),
            key=lambda ranked_item: ranked_item.score,
            reverse=True,
        )
        cap = _CANDIDATE_CAPS.get(section_type, 10)
        result[section_type] = ranked[:cap]
    return result
