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
from app.core.enums import SectionType
from features.ai.page_fit import fit_resume_to_one_page
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
        template=SimpleNamespace(id=uuid.uuid4(), slug="classic"),  # type: ignore[arg-type]
        profile=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
        content=content,
        scores_by_item_id=scores,
    )


async def test_fit_leaves_content_unchanged_when_already_one_page() -> None:
    education = _section(SectionType.EDUCATION, 1)
    projects = _section(SectionType.PROJECTS, 2)
    content = ResumeContent(sections=[education, projects])

    result = await _fit(content, scores={})

    assert result == content


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
        template=SimpleNamespace(id=uuid.uuid4(), slug="classic"),  # type: ignore[arg-type]
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
        template=SimpleNamespace(id=uuid.uuid4(), slug="classic"),  # type: ignore[arg-type]
        profile=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        email="user@example.com",
        full_name="Ada Lovelace",
        title="AI Resume",
        content=content,
        scores_by_item_id={},
    )

    # Nothing removed -- density scaling alone was enough to fit.
    assert len(result.sections[0].item_ids) == 7
    assert result.style.spacing == "compact"
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
