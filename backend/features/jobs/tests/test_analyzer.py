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

    assert "Python" in analysis.required_skills
    assert "PostgreSQL" in analysis.required_skills
    assert "Docker" in analysis.required_skills
    assert "Kubernetes" in analysis.preferred_skills
    assert "GraphQL" in analysis.preferred_skills
    assert "Kubernetes" not in analysis.required_skills


def test_analyze_job_description_without_sections_treats_all_as_required() -> None:
    analysis = analyze_job_description(
        "We need someone great at Python and AWS to build backend services for our team."
    )

    assert "Python" in analysis.required_skills
    assert analysis.preferred_skills == []


def test_analyze_job_description_extracts_keywords() -> None:
    analysis = analyze_job_description(_JD_WITH_SECTIONS)
    assert "python" in analysis.keywords
    assert "kubernetes" in analysis.keywords


def test_analyze_job_description_does_not_flag_stopwords_as_skills() -> None:
    """Regression test for the audited bug: raw stopword-filtered keyword
    extraction used to surface junk like "one"/"across"/"within" as
    required/missing skills. Skill extraction is taxonomy-based now, so
    generic words never appear in either bucket."""
    analysis = analyze_job_description(
        "We need someone who can work across multiple teams within one "
        "organization, delivering results step by step using Python and Docker."
    )

    all_skills = set(analysis.required_skills) | set(analysis.preferred_skills)
    assert all_skills == {"Python", "Docker"}


def test_analyze_job_description_paragraph_matches_bulleted_equivalent() -> None:
    """Regression test for the audited bug: a job description pasted as one
    paragraph used to have its entire bucketing collapse because the
    paragraph (being a single line) got treated as a bare heading the
    moment it contained the word "required" anywhere in it. A paragraph and
    its bulleted equivalent should now extract the same required skills."""
    paragraph = (
        "We are looking for a Software Engineer with strong experience in Python "
        "and JavaScript. The ideal candidate has worked with React, Node.js, and "
        "SQL databases. Experience with Docker and Git is required."
    )
    bulleted = """Requirements:
- Python and JavaScript
- React, Node.js, and SQL databases
- Docker and Git
"""

    paragraph_analysis = analyze_job_description(paragraph)
    bulleted_analysis = analyze_job_description(bulleted)

    assert set(paragraph_analysis.required_skills) == set(bulleted_analysis.required_skills)
    assert set(paragraph_analysis.required_skills) == {
        "Python",
        "JavaScript",
        "React",
        "Node.js",
        "SQL",
        "Docker",
        "Git",
    }
