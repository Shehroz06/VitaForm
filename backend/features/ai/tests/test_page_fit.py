"""Unit tests for the one-page trim loop, isolated from real WeasyPrint/DB
rendering: a fake renderer reports how many items it was asked to render,
and a patched page counter turns that into a deterministic page count, so
the trimming logic (order, floor protection, termination) can be verified
fast and precisely. End-to-end proof that the real PDF ends up 1 page lives
in test_generation.py.
"""

import uuid
from types import SimpleNamespace

import pytest

import features.ai.page_fit as page_fit
from app.core.enums import RenderEngine, SectionType
from features.ai.page_fit import (
    fit_resume_to_one_page,
    fit_spacing_and_density,
    position_based_scores,
)
from features.resumes.schemas import ResumeContent, ResumeSection

_ITEMS_PER_PAGE = 3


class _FakeRenderer:
    """Reports the total item count it was asked to render, encoded as
    plain bytes -- count_pdf_pages is patched to decode it back out."""

    async def render_pdf(self, resume, version, template, profile, email, full_name) -> bytes:
        total_items = sum(len(section["item_ids"]) for section in version.content["sections"])
        return str(total_items).encode()


@pytest.fixture(autouse=True)
def _patch_page_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_count(pdf_bytes: bytes) -> int:
        total_items = int(pdf_bytes.decode())
        return max(1, -(-total_items // _ITEMS_PER_PAGE))  # ceil division

    monkeypatch.setattr(page_fit, "count_pdf_pages", _fake_count)


def _section(section_type: SectionType, count: int) -> ResumeSection:
    return ResumeSection(
        section_type=section_type,
        item_ids=[uuid.uuid4() for _ in range(count)],
        visible=count > 0,
    )


async def _fit(content: ResumeContent, scores: dict[uuid.UUID, float]) -> ResumeContent:
    return await fit_resume_to_one_page(
        renderer=_FakeRenderer(),  # type: ignore[arg-type]
        template=SimpleNamespace(
            id=uuid.uuid4(), slug="classic", render_engine=RenderEngine.HTML
        ),  # type: ignore[arg-type]
        profile=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
        content=content,
        scores_by_item_id=scores,
    )


async def test_fit_leaves_content_unchanged_when_already_one_page() -> None:
    """Content that already fits settles at "relaxed" (the loosest,
    best-looking preset) rather than staying at whatever spacing the
    content happened to arrive with -- fit_spacing_and_density always
    searches from relaxed outward, not forward from the current setting,
    which is what makes it reversible: content that gets shorter (items
    removed) finds its way back to a looser spacing on the next call
    instead of staying stuck at a denser one a previous call left behind."""
    education = _section(SectionType.EDUCATION, 1)
    projects = _section(SectionType.PROJECTS, 2)
    content = ResumeContent(sections=[education, projects])

    result = await _fit(content, scores={})

    assert result.sections == content.sections
    assert result.summary == content.summary
    assert result.style.spacing == "relaxed"
    assert result.style.content_density == 1.0


async def test_fit_trims_lowest_scored_items_first() -> None:
    project_ids = [uuid.uuid4() for _ in range(6)]
    projects = ResumeSection(
        section_type=SectionType.PROJECTS, item_ids=project_ids, visible=True
    )
    content = ResumeContent(sections=[projects])
    # Ascending relevance: project_ids[0] is least relevant, project_ids[-1] most.
    scores = {item_id: float(index) for index, item_id in enumerate(project_ids)}

    result = await _fit(content, scores)

    remaining = result.sections[0].item_ids
    assert len(remaining) == _ITEMS_PER_PAGE
    # The most relevant items (highest scores) must be the ones kept.
    assert set(remaining) == set(project_ids[-_ITEMS_PER_PAGE:])
    # This fake ignores density entirely, so it never "fits" via shrinking --
    # item removal must have continued at the density floor throughout.
    assert result.style.content_density == pytest.approx(0.8)


async def test_fit_never_empties_education_or_experience() -> None:
    education = _section(SectionType.EDUCATION, 1)
    experience = _section(SectionType.EXPERIENCE, 1)
    projects = _section(SectionType.PROJECTS, 10)
    content = ResumeContent(sections=[education, experience, projects])
    scores: dict[uuid.UUID, float] = {}  # everything scores 0 -- projects still go first

    result = await _fit(content, scores)

    by_type = {s.section_type: s for s in result.sections}
    assert len(by_type[SectionType.EDUCATION].item_ids) == 1
    assert len(by_type[SectionType.EXPERIENCE].item_ids) == 1
    assert len(by_type[SectionType.PROJECTS].item_ids) == 1


async def test_fit_never_empties_skills_below_the_soft_floor_of_three() -> None:
    skills = _section(SectionType.SKILLS, 10)
    content = ResumeContent(sections=[skills])
    scores: dict[uuid.UUID, float] = {}

    result = await _fit(content, scores)

    assert len(result.sections[0].item_ids) == 3


class _SpacingAwareFakeRenderer:
    """Like _FakeRenderer, but the simulated page also depends on
    style.spacing -- denser spacing fits more items per page, so this can
    prove the spacing pre-pass resolves overflow without removing anything."""

    _CAPACITY = {"relaxed": 2, "cozy": 4, "compact": 8}

    async def render_pdf(self, resume, version, template, profile, email, full_name) -> bytes:
        total_items = sum(len(section["item_ids"]) for section in version.content["sections"])
        spacing = version.content["style"]["spacing"]
        return f"{total_items}:{spacing}".encode()


async def test_fit_tightens_spacing_before_removing_any_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_count(pdf_bytes: bytes) -> int:
        total_items_str, spacing = pdf_bytes.decode().split(":")
        total_items = int(total_items_str)
        capacity = _SpacingAwareFakeRenderer._CAPACITY[spacing]
        return max(1, -(-total_items // capacity))

    monkeypatch.setattr(page_fit, "count_pdf_pages", _fake_count)

    # 6 items overflow at "cozy" (capacity 4) but fit at "compact" (capacity 8).
    projects = _section(SectionType.PROJECTS, 6)
    content = ResumeContent(sections=[projects])

    result = await fit_resume_to_one_page(
        renderer=_SpacingAwareFakeRenderer(),  # type: ignore[arg-type]
        template=SimpleNamespace(
            id=uuid.uuid4(), slug="classic", render_engine=RenderEngine.HTML
        ),  # type: ignore[arg-type]
        profile=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
        content=content,
        scores_by_item_id={},
    )

    # Nothing removed -- tightening spacing alone was enough to fit.
    assert len(result.sections[0].item_ids) == 6
    assert result.style.spacing == "compact"


async def test_fit_spacing_and_density_loosens_back_up_after_content_shrinks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for a real bug found in manual testing: auto-fit only
    ever tightened spacing, never loosened it back up once content that had
    forced "compact" was later removed -- because the old search started
    from the content's *current* spacing and only ever moved denser. It
    must be reversible: the same profile at 6 items settles at "compact",
    and at 2 items (after the user deletes some) settles back at "relaxed",
    not wherever a previous call happened to leave it."""

    def _fake_count(pdf_bytes: bytes) -> int:
        total_items_str, spacing = pdf_bytes.decode().split(":")
        total_items = int(total_items_str)
        capacity = _SpacingAwareFakeRenderer._CAPACITY[spacing]
        return max(1, -(-total_items // capacity))

    monkeypatch.setattr(page_fit, "count_pdf_pages", _fake_count)

    template = SimpleNamespace(
        id=uuid.uuid4(), slug="classic", render_engine=RenderEngine.HTML
    )
    profile = SimpleNamespace(id=uuid.uuid4())
    kwargs = dict(
        renderer=_SpacingAwareFakeRenderer(),
        template=template,
        profile=profile,
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
    )

    dense_content = ResumeContent(sections=[_section(SectionType.PROJECTS, 6)])
    dense_result, dense_overflowing = await fit_spacing_and_density(
        content=dense_content, **kwargs  # type: ignore[arg-type]
    )
    assert not dense_overflowing
    assert dense_result.style.spacing == "compact"

    # Same call, but starting from that "compact" result content with most
    # items removed -- simulates the user deleting projects after a
    # previous auto-fit already tightened things.
    sparse_content = dense_result.model_copy(
        update={"sections": [_section(SectionType.PROJECTS, 2)]}
    )
    sparse_result, sparse_overflowing = await fit_spacing_and_density(
        content=sparse_content, **kwargs  # type: ignore[arg-type]
    )
    assert not sparse_overflowing
    assert sparse_result.style.spacing == "relaxed"


class _DensityAwareFakeRenderer:
    """Fixed item count, ignores spacing (so the 3 discrete presets never
    resolve it) -- only fits once style.content_density drops to or below a
    threshold, simulating a LaTeX-style continuous shrink."""

    FIT_THRESHOLD = 0.9

    async def render_pdf(self, resume, version, template, profile, email, full_name) -> bytes:
        density = version.content["style"]["content_density"]
        fits = density <= self.FIT_THRESHOLD
        return b"1" if fits else b"2"


async def test_fit_scales_density_before_removing_any_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(page_fit, "count_pdf_pages", lambda pdf_bytes: int(pdf_bytes.decode()))

    project_ids = [uuid.uuid4() for _ in range(7)]
    projects = ResumeSection(section_type=SectionType.PROJECTS, item_ids=project_ids, visible=True)
    content = ResumeContent(sections=[projects])

    result = await fit_resume_to_one_page(
        renderer=_DensityAwareFakeRenderer(),  # type: ignore[arg-type]
        template=SimpleNamespace(
            id=uuid.uuid4(), slug="classic", render_engine=RenderEngine.HTML
        ),  # type: ignore[arg-type]
        profile=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
        content=content,
        scores_by_item_id={},
    )

    # Nothing removed -- density scaling alone was enough to fit. The fake
    # renderer ignores spacing entirely, so none of the discrete presets
    # ever resolve it -- the density search continues from the tightest
    # one tried (_SPACING_LEVELS[-1], "extreme"), not a hardcoded "compact".
    assert len(result.sections[0].item_ids) == 7
    assert result.style.spacing == "extreme"
    # Bisection should land close to the true fit boundary (0.9), never
    # below it (that would over-shrink) and never above (wouldn't fit).
    assert 0.8 <= result.style.content_density <= 0.9
    assert result.style.content_density == pytest.approx(0.9, abs=0.01)


async def test_fit_marks_emptied_sections_not_visible() -> None:
    # Projects isn't a protected section, so if it's the least relevant
    # content it can be trimmed away entirely -- unlike education/experience.
    project_id = uuid.uuid4()
    projects = ResumeSection(
        section_type=SectionType.PROJECTS, item_ids=[project_id], visible=True
    )
    cert_ids = [uuid.uuid4() for _ in range(6)]
    certifications = ResumeSection(
        section_type=SectionType.CERTIFICATIONS, item_ids=cert_ids, visible=True
    )
    content = ResumeContent(sections=[projects, certifications])
    scores = {project_id: -1.0, **{cert_id: 10.0 for cert_id in cert_ids}}

    result = await _fit(content, scores)

    by_type = {s.section_type: s for s in result.sections}
    assert by_type[SectionType.PROJECTS].item_ids == []
    assert by_type[SectionType.PROJECTS].visible is False


def test_position_based_scores_ranks_earlier_items_higher() -> None:
    first_id, second_id, third_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    experience = ResumeSection(
        section_type=SectionType.EXPERIENCE, item_ids=[first_id, second_id], visible=True
    )
    projects = ResumeSection(section_type=SectionType.PROJECTS, item_ids=[third_id], visible=True)
    content = ResumeContent(sections=[experience, projects])

    scores = position_based_scores(content)

    assert scores[first_id] > scores[second_id] > scores[third_id]


def test_position_based_scores_ignores_the_summary_section() -> None:
    content = ResumeContent(sections=[ResumeSection(section_type=SectionType.SUMMARY)])
    assert position_based_scores(content) == {}
