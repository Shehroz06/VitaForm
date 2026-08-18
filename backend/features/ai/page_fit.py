"""Enforces the "resume is exactly one page" rule after the AI has picked a
set of candidates. Ranking and the AI narrow down *what's relevant*; this
module narrows down *what fits*, deterministically, by actually rendering
the candidate PDF and measuring it -- never by guessing or scaling text down
to force a fit.
"""

import uuid
from typing import Any

import pymupdf

from app.core.enums import SectionType
from features.profiles.models import Profile
from features.resumes.models import Resume, ResumeTemplate, ResumeVersion
from features.resumes.renderer import ResumeRenderer
from features.resumes.schemas import ResumeContent

_MAX_TRIM_ITERATIONS = 200

# Per-section floors: a section is off-limits to trimming while its item
# count is at or below its floor. Education/experience get a hard floor of
# 1 (a resume always keeps at least one degree and one job). Skills gets a
# softer floor of 3 -- per standard resume-writing convention it sits
# alongside experience/education as "essential," but unlike them it's fine
# to trim down to a short core list rather than never touching it at all.
_SECTION_FLOORS: dict[SectionType, int] = {
    SectionType.EDUCATION: 1,
    SectionType.EXPERIENCE: 1,
    SectionType.SKILLS: 3,
}

# Loosest to densest -- the trim loop only ever moves rightward through this,
# never back, since going denser is what buys back page space.
_SPACING_LEVELS: tuple[str, ...] = ("relaxed", "cozy", "compact")

# Continuous content-density scale, tried at compact spacing once the 3
# discrete presets alone aren't enough -- the LaTeX-resume-style lever that
# scales font-size and numeric spacing together, continuously, based on how
# much content there is. 0.80 floor keeps even the smallest resulting font
# comfortably legible (a 10.5pt base never drops below 8.4pt). 7 bisection
# steps narrows the range to ~0.002, far more precision than matters here.
_DENSITY_FLOOR = 0.8
_DENSITY_CEILING = 1.0
_DENSITY_BISECTION_STEPS = 7


def count_pdf_pages(pdf_bytes: bytes) -> int:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return doc.page_count


async def _render(
    renderer: ResumeRenderer,
    template: ResumeTemplate,
    profile: Profile,
    email: str,
    full_name: str,
    title: str,
    content: ResumeContent,
) -> bytes:
    # Transient, never-persisted rows purely to satisfy render_pdf's shape --
    # it only reads resume.title and version.content, so no session/commit
    # is needed just to measure a candidate layout.
    resume = Resume(id=uuid.uuid4(), profile_id=profile.id, template_id=template.id, title=title)
    version = ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume.id,
        version_number=0,
        content=content.model_dump(mode="json"),
    )
    return await renderer.render_pdf(resume, version, template, profile, email, full_name)


def _least_relevant_trimmable_item(
    content: ResumeContent, scores_by_item_id: dict[uuid.UUID, float]
) -> tuple[SectionType, uuid.UUID] | None:
    best: tuple[float, SectionType, uuid.UUID] | None = None
    for section in content.sections:
        if section.section_type is SectionType.SUMMARY:
            continue
        floor = _SECTION_FLOORS.get(section.section_type, 0)
        if len(section.item_ids) <= floor:
            continue
        for item_id in section.item_ids:
            score = scores_by_item_id.get(item_id, 0.0)
            if best is None or score < best[0]:
                best = (score, section.section_type, item_id)
    if best is None:
        return None
    return best[1], best[2]


def _with_spacing(content: ResumeContent, spacing: str) -> ResumeContent:
    style = content.style.model_copy(update={"spacing": spacing})
    return content.model_copy(update={"style": style})


def _with_density(content: ResumeContent, density: float) -> ResumeContent:
    style = content.style.model_copy(update={"content_density": density})
    return content.model_copy(update={"style": style})


async def _fits_one_page(
    renderer: ResumeRenderer,
    template: ResumeTemplate,
    profile: Profile,
    email: str,
    full_name: str,
    title: str,
    content: ResumeContent,
) -> bool:
    pdf_bytes = await _render(renderer, template, profile, email, full_name, title, content)
    return count_pdf_pages(pdf_bytes) <= 1


def _without_item(
    content: ResumeContent, section_type: SectionType, item_id: uuid.UUID
) -> ResumeContent:
    sections = []
    for section in content.sections:
        if section.section_type is section_type:
            item_ids = [i for i in section.item_ids if i != item_id]
            sections.append(
                section.model_copy(update={"item_ids": item_ids, "visible": bool(item_ids)})
            )
        else:
            sections.append(section)
    return content.model_copy(update={"sections": sections})


async def fit_resume_to_one_page(
    *,
    renderer: ResumeRenderer,
    template: ResumeTemplate,
    profile: Profile,
    email: str,
    full_name: str,
    title: str,
    content: ResumeContent,
    scores_by_item_id: dict[uuid.UUID, float],
    max_iterations: int = _MAX_TRIM_ITERATIONS,
) -> ResumeContent:
    """Uses the page efficiently before cutting anything real off it:

    1. Try progressively denser spacing (relaxed -> cozy -> compact, never
       looser than the content's current setting) at the full, untrimmed
       candidate set. Tightening spacing is cheap and fully reversible, so
       it's always preferred over dropping a real project or certification.
    2. Still overflowing at compact spacing? Binary-search a continuous
       content_density in [0.80, 1.0) -- the LaTeX-resume-style lever that
       scales font-size and numeric spacing together, continuously, rather
       than in 3 fixed steps. This is what lets a content-heavy resume pack
       as tightly as a hand-built LaTeX CV instead of overflowing just
       because the discrete presets ran out of room. Still fully lossless.
    3. Only if it still overflows at the density floor does item-removal
       begin -- repeatedly dropping the single lowest-relevance item and
       re-rendering, staying at compact spacing + floor density throughout.

    If it's already one page, nothing changes -- a shorter-than-a-page
    resume is left as-is; the user can add more from their profile manually.
    If nothing trimmable remains and it still overflows (e.g. one entry's
    own text is too long on its own), returns the best effort reached
    rather than truncating anyone's description text."""
    start_index = _SPACING_LEVELS.index(content.style.spacing)
    for spacing in _SPACING_LEVELS[start_index:]:
        candidate_content = (
            content if spacing == content.style.spacing else _with_spacing(content, spacing)
        )
        pdf_bytes = await _render(
            renderer, template, profile, email, full_name, title, candidate_content
        )
        if count_pdf_pages(pdf_bytes) <= 1:
            return candidate_content

    content = _with_spacing(content, "compact")

    floor_candidate = _with_density(content, _DENSITY_FLOOR)
    if await _fits_one_page(renderer, template, profile, email, full_name, title, floor_candidate):
        low, high = _DENSITY_FLOOR, _DENSITY_CEILING
        best = floor_candidate
        for _ in range(_DENSITY_BISECTION_STEPS):
            mid = (low + high) / 2
            mid_candidate = _with_density(content, mid)
            if await _fits_one_page(
                renderer, template, profile, email, full_name, title, mid_candidate
            ):
                best = mid_candidate
                low = mid
            else:
                high = mid
        return best

    content = floor_candidate
    for _ in range(max_iterations):
        pdf_bytes = await _render(renderer, template, profile, email, full_name, title, content)
        if count_pdf_pages(pdf_bytes) <= 1:
            return content
        candidate = _least_relevant_trimmable_item(content, scores_by_item_id)
        if candidate is None:
            return content
        section_type, item_id = candidate
        content = _without_item(content, section_type, item_id)
    return content


def flatten_scores(ranked_by_type: dict[SectionType, list[Any]]) -> dict[uuid.UUID, float]:
    """RankedItem carries `.item.id` and `.score`; this collapses ranking's
    per-section output into the single id->score lookup the trim loop needs,
    independent of which section a given id ended up in."""
    return {
        ranked.item.id: ranked.score
        for ranked_items in ranked_by_type.values()
        for ranked in ranked_items
    }
