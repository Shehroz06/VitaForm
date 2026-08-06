"""Rules-based job description analysis. Same philosophy as Phase 6's
ranking engine: keyword/requirement extraction is a solvable rules problem
(the design doc's own checklist -- "does this need AI?"), so this makes no
provider call, costs nothing, and is fully deterministic."""

from features.ai.ranking import extract_keywords
from features.jobs.schemas import JobAnalysis

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


def analyze_job_description(raw_text: str) -> JobAnalysis:
    keywords = extract_keywords(raw_text)

    required_words: set[str] = set()
    preferred_words: set[str] = set()
    current_bucket: str | None = None

    for line in raw_text.splitlines():
        lower = line.lower()
        is_marker_line = False
        if any(marker in lower for marker in _REQUIRED_MARKERS):
            current_bucket = "required"
            is_marker_line = True
        elif any(marker in lower for marker in _PREFERRED_MARKERS):
            current_bucket = "preferred"
            is_marker_line = True

        # Skip the heading line itself ("Requirements:", "Preferred:") --
        # only the bullets underneath it describe actual skills.
        if not line.strip() or is_marker_line:
            continue
        if current_bucket == "required":
            required_words |= extract_keywords(line)
        elif current_bucket == "preferred":
            preferred_words |= extract_keywords(line)

    if not required_words and not preferred_words:
        # No "Requirements"/"Preferred" structure detected at all -- treat
        # every extracted keyword as required so the ATS score still means
        # something instead of comparing against nothing.
        required_words = set(keywords)

    return JobAnalysis(
        keywords=sorted(keywords),
        required_skills=sorted(required_words),
        preferred_skills=sorted(preferred_words - required_words),
    )
