from datetime import date
from types import SimpleNamespace

from app.core.enums import SectionType
from features.ai.context_builder import build_candidates
from features.ai.ranking import extract_keywords, rank_and_select


def test_rank_and_select_scores_extended_section_types_without_error() -> None:
    """Covers the 9 profile modules wired into resume generation in Phase 9 --
    each needs a working scorer + describer or ranking/prompt-building crashes."""
    items_by_type = {
        SectionType.RESEARCH: [
            SimpleNamespace(
                id="r1",
                title="Efficient Attention Mechanisms",
                publication_venue="NeurIPS",
                publication_date=date(2023, 1, 1),
                url=None,
                description="Studied transformer attention.",
            )
        ],
        SectionType.LANGUAGES: [
            SimpleNamespace(id="l1", name="Spanish", proficiency=SimpleNamespace(value="fluent")),
            SimpleNamespace(id="l2", name="French", proficiency=SimpleNamespace(value="basic")),
        ],
        SectionType.PATENTS: [
            SimpleNamespace(
                id="p1",
                title="Method for Ranking Resume Sections",
                description=None,
                filing_date=date(2022, 6, 1),
                patent_number="US123",
                status=SimpleNamespace(value="filed"),
            )
        ],
    }

    ranked = rank_and_select(items_by_type, keywords={"attention", "transformer", "ranking"})

    assert len(ranked[SectionType.RESEARCH]) == 1
    assert len(ranked[SectionType.LANGUAGES]) == 2
    # Fluent should outrank Basic when neither matches the keyword set.
    assert ranked[SectionType.LANGUAGES][0].item.name == "Spanish"
    assert len(ranked[SectionType.PATENTS]) == 1

    candidates = build_candidates(ranked)
    assert "Attention" in candidates[SectionType.RESEARCH][0].description
    assert "fluent" in candidates[SectionType.LANGUAGES][0].description
    assert "filed" in candidates[SectionType.PATENTS][0].description


def test_extract_keywords_lowercases_and_drops_stopwords() -> None:
    keywords = extract_keywords("We are looking for a Senior Python Backend Engineer with AWS.")
    assert "python" in keywords
    assert "backend" in keywords
    assert "engineer" in keywords
    assert "aws" in keywords
    assert "for" not in keywords
    assert "with" not in keywords
    assert "a" not in keywords


def test_extract_keywords_handles_empty_text() -> None:
    assert extract_keywords("") == set()
    assert extract_keywords(None) == set()  # type: ignore[arg-type]


def test_rank_and_select_gates_out_irrelevant_projects_and_certifications() -> None:
    """An accomplishment with zero keyword overlap with the job description
    must never reach the AI as a candidate -- filtering can't rely on the
    AI choosing to omit it, the rules layer must never offer it at all."""
    items_by_type = {
        SectionType.PROJECTS: [
            SimpleNamespace(
                id="p1",
                title="Real-Time Object Detection Pipeline",
                role="Lead Engineer",
                description="Built a YOLO-based computer vision pipeline for defect detection.",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 1),
                is_pinned=False,
                skills=[SimpleNamespace(name="PyTorch")],
            ),
            SimpleNamespace(
                id="p2",
                title="Personal Recipe Blog",
                role="Author",
                description="A static site listing family recipes and cooking tips.",
                start_date=date(2022, 1, 1),
                end_date=date(2022, 3, 1),
                is_pinned=False,
                skills=[SimpleNamespace(name="Jekyll")],
            ),
        ],
        SectionType.CERTIFICATIONS: [
            SimpleNamespace(
                id="c1",
                name="Deep Learning Specialization",
                issuing_organization="Coursera",
                issue_date=date(2023, 1, 1),
            ),
            SimpleNamespace(
                id="c2",
                name="Advanced Sommelier Certificate",
                issuing_organization="Wine Institute",
                issue_date=date(2023, 1, 1),
            ),
        ],
    }

    ranked = rank_and_select(
        items_by_type, keywords={"computer", "vision", "yolo", "detection", "deep", "learning"}
    )

    project_ids = {r.item.id for r in ranked[SectionType.PROJECTS]}
    cert_ids = {r.item.id for r in ranked[SectionType.CERTIFICATIONS]}
    assert project_ids == {"p1"}
    assert cert_ids == {"c1"}


def test_rank_and_select_never_gates_education_or_experience() -> None:
    """Career history integrity matters more than an exact keyword match for
    education/experience, so these sections keep every candidate (subject
    only to the existing top-N cap), unlike gated accomplishment sections."""
    items_by_type = {
        SectionType.EDUCATION: [
            SimpleNamespace(
                id="e1",
                institution_name="State University",
                degree="BA",
                field_of_study="History",
                description=None,
                start_date=date(2015, 1, 1),
                end_date=date(2019, 1, 1),
                is_current=False,
            )
        ],
        SectionType.EXPERIENCE: [
            SimpleNamespace(
                id="x1",
                job_title="Barista",
                company_name="Local Cafe",
                description=None,
                start_date=date(2019, 1, 1),
                end_date=date(2020, 1, 1),
                is_current=False,
            )
        ],
    }

    ranked = rank_and_select(items_by_type, keywords={"computer", "vision"})

    assert len(ranked[SectionType.EDUCATION]) == 1
    assert len(ranked[SectionType.EXPERIENCE]) == 1
