"""Enforces the "resume is exactly one page" rule after the AI has picked a
set of candidates. Ranking and the AI narrow down *what's relevant*; this
module narrows down *what fits*, deterministically, by actually rendering
the candidate PDF and measuring it -- never by guessing or scaling text down
to force a fit.
"""

import uuid
from typing import Any

import pymupdf

from app.core.enums import RenderEngine, SectionType
from features.ai.description_condenser import condense_description
from features.profiles.models import Profile
from features.resumes.models import Resume, ResumeTemplate, ResumeVersion
from features.resumes.renderer import ResumeRenderer
from features.resumes.schemas import ResumeContent

# How much of an item's own description survives one condensing pass when
# a resume still overflows after spacing/density are already maxed out.
# Applied lowest-relevance item first (see _condense_lowest_relevance_
# descriptions) -- condensing is always tried before deleting an item
# outright, since it preserves at least some of the user's real content.
_CONDENSE_KEEP_RATIO = 0.5

_MAX_TRIM_ITERATIONS = 200
# pdflatex compiles are ~0.3-1.5s each, vs. WeasyPrint's near-instant
# renders -- 200 sequential LaTeX compiles in the trim loop below could
# take minutes and blow past any reasonable request timeout. Trimming more
# than this many items is already a degenerate case, so this is a latency
# guard, not a real functionality cut.
_MAX_TRIM_ITERATIONS_LATEX = 30

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
# never back, since going denser is what buys back page space. "extreme" is
# the 4th, most aggressive preset (see ResumeStyle.spacing's docstring) --
# tried automatically once "compact" alone still overflows, before falling
# to the continuous density search below.
_SPACING_LEVELS: tuple[str, ...] = ("relaxed", "cozy", "compact", "extreme")

# Continuous content-density scale, tried at the tightest spacing preset
# once the discrete presets alone aren't enough -- the LaTeX-resume-style
# lever that
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


def _items_by_relevance_ascending(
    content: ResumeContent, scores_by_item_id: dict[uuid.UUID, float]
) -> list[tuple[SectionType, uuid.UUID]]:
    scored: list[tuple[float, SectionType, uuid.UUID]] = []
    for section in content.sections:
        if section.section_type is SectionType.SUMMARY:
            continue
        for item_id in section.item_ids:
            scored.append((scores_by_item_id.get(item_id, 0.0), section.section_type, item_id))
    scored.sort(key=lambda entry: entry[0])
    return [(section_type, item_id) for _, section_type, item_id in scored]


def _with_description_override(
    content: ResumeContent, item_id: uuid.UUID, text: str
) -> ResumeContent:
    overrides = {**content.description_overrides, str(item_id): text}
    return content.model_copy(update={"description_overrides": overrides})


async def _condense_lowest_relevance_descriptions(
    *,
    renderer: ResumeRenderer,
    template: ResumeTemplate,
    profile: Profile,
    email: str,
    full_name: str,
    title: str,
    content: ResumeContent,
    scores_by_item_id: dict[uuid.UUID, float],
    descriptions_by_item_id: dict[uuid.UUID, str],
    keywords: set[str] | None = None,
) -> tuple[ResumeContent, bool]:
    """Tried before any item is deleted outright: condenses one item's
    description at a time, lowest-relevance first, re-rendering after each
    to check whether that alone bought back enough room. Every candidate
    text still comes from features.ai.description_condenser -- extractive
    only, so this can shrink an item's text but never invent content the
    user didn't already write. Items with no description, or too short to
    condense (condense_description returns None), are skipped.

    `keywords` (the job description's, when generation supplied one) makes
    the surviving sentences the JD-relevant ones rather than just "whatever
    came first" -- this replaces any reorder-only override
    _jd_tailored_overrides already set for the same item (service.py's
    caller builds descriptions_by_item_id from each item's original text,
    not from that override), so relevance still drives which sentences
    survive when both apply, not just their order."""
    for _, item_id in _items_by_relevance_ascending(content, scores_by_item_id):
        description = descriptions_by_item_id.get(item_id)
        if not description:
            continue
        condensed = condense_description(
            description, keywords=keywords, keep_ratio=_CONDENSE_KEEP_RATIO
        )
        if condensed is None:
            continue
        content = _with_description_override(content, item_id, condensed)
        if await _fits_one_page(renderer, template, profile, email, full_name, title, content):
            return content, False
    return content, True


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


async def fit_spacing_and_density(
    *,
    renderer: ResumeRenderer,
    template: ResumeTemplate,
    profile: Profile,
    email: str,
    full_name: str,
    title: str,
    content: ResumeContent,
) -> tuple[ResumeContent, bool]:
    """Steps 1-2 of the fit strategy, lossless and content-agnostic (no
    relevance scores needed, so this alone is exactly what the manual
    builder's "Auto-fit" action can run -- see AI generation's
    fit_resume_to_one_page below for the full strategy including the
    scored item-trimming step 3, which this intentionally does not do):

    1. Try every spacing preset from loosest to tightest (relaxed -> cozy ->
       compact) at content_density reset to its ceiling (1.0) and the full,
       untrimmed candidate set, returning the *loosest* one that fits.
       Always restarting from relaxed/1.0 rather than the content's current
       setting is what makes this reversible in both directions -- calling
       it again after removing content finds its way back to a looser
       spacing instead of staying wherever a previous, denser call left it.
    2. Still overflowing at the tightest spacing preset? Binary-search a continuous
       content_density in [0.80, 1.0) -- the LaTeX-resume-style lever that
       scales font-size and numeric spacing together, continuously, rather
       than in 3 fixed steps. This is what lets a content-heavy resume pack
       as tightly as a hand-built LaTeX CV instead of overflowing just
       because the discrete presets ran out of room. Still fully lossless.

    Returns the best-effort content and whether it still overflows one page
    -- the caller decides what to do next (AI generation trims items
    automatically; the manual builder surfaces the overflow to the user
    instead, since only a human can judge what's safe to cut)."""
    content = _with_density(content, _DENSITY_CEILING)
    for spacing in _SPACING_LEVELS:
        candidate_content = _with_spacing(content, spacing)
        pdf_bytes = await _render(
            renderer, template, profile, email, full_name, title, candidate_content
        )
        if count_pdf_pages(pdf_bytes) <= 1:
            return candidate_content, False

    # Still overflowing after every discrete preset -- continue the density
    # search from the tightest one (_SPACING_LEVELS[-1]) rather than
    # hardcoding "compact", so adding a denser preset to that tuple doesn't
    # leave this stuck one tier looser than what was just tried above.
    content = _with_spacing(content, _SPACING_LEVELS[-1])

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
        return best, False

    return floor_candidate, True


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
    descriptions_by_item_id: dict[uuid.UUID, str] | None = None,
    keywords: set[str] | None = None,
    max_iterations: int | None = None,
) -> ResumeContent:
    """AI generation's full fit strategy: fit_spacing_and_density's steps
    1-2, then (only if still overflowing) condensing descriptions
    (lowest-relevance item first, extractive only -- see
    description_condenser.py), then (only if *that* still isn't enough)
    item-removal -- repeatedly dropping the single lowest-relevance item
    and re-rendering, staying at whichever spacing/density
    fit_spacing_and_density settled on throughout.

    If it's already one page, nothing changes -- a shorter-than-a-page
    resume is left as-is; the user can add more from their profile manually.
    If nothing trimmable remains and it still overflows (e.g. one entry's
    own text is too long on its own), returns the best effort reached
    rather than truncating anyone's description text."""
    if max_iterations is None:
        max_iterations = (
            _MAX_TRIM_ITERATIONS_LATEX
            if template.render_engine is RenderEngine.LATEX
            else _MAX_TRIM_ITERATIONS
        )

    content, overflowing = await fit_spacing_and_density(
        renderer=renderer,
        template=template,
        profile=profile,
        email=email,
        full_name=full_name,
        title=title,
        content=content,
    )
    if not overflowing:
        return content

    if descriptions_by_item_id:
        content, overflowing = await _condense_lowest_relevance_descriptions(
            renderer=renderer,
            template=template,
            profile=profile,
            email=email,
            full_name=full_name,
            title=title,
            content=content,
            scores_by_item_id=scores_by_item_id,
            descriptions_by_item_id=descriptions_by_item_id,
            keywords=keywords,
        )
    if not overflowing:
        return content

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


def position_based_scores(content: ResumeContent) -> dict[uuid.UUID, float]:
    """A relevance proxy for the manual builder's "extreme fit" action: no
    job description to rank against there, so this trusts the order the
    user already put items in instead (see the builder's per-section
    reorder controls) -- items later in the content.sections/item_ids
    order score lower, so _least_relevant_trimmable_item's "lowest score
    first" trimming (and _condense_lowest_relevance_descriptions'
    ascending-score condensing) touches what the user already signaled was
    least important, not an arbitrary item."""
    scores: dict[uuid.UUID, float] = {}
    position = 0
    for section in content.sections:
        if section.section_type is SectionType.SUMMARY:
            continue
        for item_id in section.item_ids:
            scores[item_id] = -float(position)
            position += 1
    return scores


def flatten_scores(ranked_by_type: dict[SectionType, list[Any]]) -> dict[uuid.UUID, float]:
    """RankedItem carries `.item.id` and `.score`; this collapses ranking's
    per-section output into the single id->score lookup the trim loop needs,
    independent of which section a given id ended up in."""
    return {
        ranked.item.id: ranked.score
        for ranked_items in ranked_by_type.values()
        for ranked in ranked_items
    }
