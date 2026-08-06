from features.jobs.analyzer import analyze_job_description

_JD_WITH_SECTIONS = """
We are looking for a Backend Engineer to join our platform team.

Requirements:
- 5+ years of Python experience
- Strong knowledge of PostgreSQL and Docker

Preferred:
- Experience with Kubernetes
- Familiarity with GraphQL
"""


def test_analyze_job_description_splits_required_and_preferred() -> None:
    analysis = analyze_job_description(_JD_WITH_SECTIONS)

    assert "python" in analysis.required_skills
    assert "postgresql" in analysis.required_skills
    assert "docker" in analysis.required_skills
    assert "kubernetes" in analysis.preferred_skills
    assert "graphql" in analysis.preferred_skills
    assert "kubernetes" not in analysis.required_skills


def test_analyze_job_description_without_sections_treats_all_as_required() -> None:
    analysis = analyze_job_description(
        "We need someone great at Python and AWS to build backend services for our team."
    )

    assert "python" in analysis.required_skills
    assert analysis.preferred_skills == []


def test_analyze_job_description_extracts_keywords() -> None:
    analysis = analyze_job_description(_JD_WITH_SECTIONS)
    assert "python" in analysis.keywords
    assert "kubernetes" in analysis.keywords
