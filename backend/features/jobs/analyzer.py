"""Rules-based job description analysis. Same philosophy as Phase 6's
ranking engine: keyword/requirement extraction is a solvable rules problem
(the design doc's own checklist -- "does this need AI?"), so this makes no
provider call, costs nothing, and is fully deterministic."""

import re

from features.ai.ranking import extract_keywords
from features.jobs.schemas import JobAnalysis
from features.jobs.skills_taxonomy import match_skills

_REQUIRED_MARKERS = (
    "required",
    "requirements",
    "must have",
    "minimum qualifications",
    "you must",
    "must possess",
    "you have",
)
_PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "bonus",
    "plus if",
    "desirable",
    "good to have",
    "a plus",
)

# A pasted job description is often one long paragraph rather than a
# bulleted list -- splitting on newlines alone would treat the whole
# paragraph as a single "clause" and, worse, as a bare heading the moment it
# contains a word like "required" anywhere in it. Long lines get split into
# sentences too, so a clause is roughly "one bullet, or one sentence".
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_LONG_LINE_WORD_THRESHOLD = 12


def _split_into_clauses(raw_text: str) -> list[str]:
    clauses: list[str] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line.split()) > _LONG_LINE_WORD_THRESHOLD:
            clauses.extend(clause for clause in _SENTENCE_SPLIT_RE.split(line) if clause.strip())
        else:
            clauses.append(line)
    return clauses


def analyze_job_description(raw_text: str) -> JobAnalysis:
    keywords = extract_keywords(raw_text)

    required: set[str] = set()
    preferred: set[str] = set()
    # Undifferentiated JD text describes what's wanted -- default to
    # "required" so skills mentioned before any heading (very common in a
    # pasted paragraph, which rarely bothers with headings at all) still
    # count instead of being silently dropped. A "preferred"/"nice to
    # have"/"bonus" cue is what demotes the skills after it, not the other
    # way around.
    current_bucket = "required"

    for clause in _split_into_clauses(raw_text):
        lower = clause.lower()
        if any(marker in lower for marker in _REQUIRED_MARKERS):
            current_bucket = "required"
        elif any(marker in lower for marker in _PREFERRED_MARKERS):
            current_bucket = "preferred"

        # A clause that names the current bucket (e.g. "...Docker and Git
        # is required.") still describes real skills -- only the bucket
        # assignment above depends on the marker, extraction never skips
        # the clause just because it contains one.
        clause_skills = match_skills(clause)
        if current_bucket == "required":
            required |= clause_skills
        else:
            preferred |= clause_skills

    return JobAnalysis(
        keywords=sorted(keywords),
        required_skills=sorted(required),
        preferred_skills=sorted(preferred - required),
    )
