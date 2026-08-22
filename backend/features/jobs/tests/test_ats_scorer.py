from features.jobs.ats_scorer import compute_ats_score
from features.jobs.schemas import JobAnalysis


def test_compute_ats_score_full_match_scores_100() -> None:
    analysis = JobAnalysis(keywords=["python"], required_skills=["Python"], preferred_skills=[])
    result = compute_ats_score(analysis, {"Python"}, "")

    assert result.overall_score == 100
    assert result.matched_skills == ["Python"]
    assert result.missing_skills == []


def test_compute_ats_score_no_match_scores_0() -> None:
    analysis = JobAnalysis(keywords=["rust"], required_skills=["Rust"], preferred_skills=[])
    result = compute_ats_score(analysis, {"Python"}, "")

    assert result.overall_score == 0
    assert result.missing_skills == ["Rust"]
    assert any("Rust" in rec for rec in result.recommendations)


def test_compute_ats_score_with_no_requirements_scores_100() -> None:
    analysis = JobAnalysis(keywords=[], required_skills=[], preferred_skills=[])
    result = compute_ats_score(analysis, set(), "")
    assert result.overall_score == 100


def test_compute_ats_score_matches_via_profile_text_not_just_skill_names() -> None:
    analysis = JobAnalysis(keywords=["docker"], required_skills=["Docker"], preferred_skills=[])
    result = compute_ats_score(analysis, set(), "Built and deployed services using Docker.")
    assert result.overall_score == 100
    assert "Docker" in result.matched_skills


def test_compute_ats_score_weights_required_more_than_preferred() -> None:
    analysis = JobAnalysis(
        keywords=[], required_skills=["Python"], preferred_skills=["Kubernetes"]
    )
    result = compute_ats_score(analysis, {"Python"}, "")
    # matched required (weight 2) out of required*2 + preferred*1 = 2/3 -> 67%
    assert result.overall_score == 67


def test_compute_ats_score_ignores_stopwords_and_generic_words() -> None:
    """Regression test for the audited bug: raw keyword overlap used to flag
    words like "one"/"across"/"within" as matched or missing skills. The
    taxonomy-based matcher should never surface a non-skill token at all."""
    analysis = JobAnalysis(
        keywords=[],
        required_skills=["Python", "Docker"],
        preferred_skills=[],
    )
    profile_text = (
        "Worked across multiple teams within one organization to deliver Python "
        "and Docker services, step by step."
    )
    result = compute_ats_score(analysis, set(), profile_text)

    assert result.matched_skills == ["Docker", "Python"]
    assert result.missing_skills == []
    for junk in ("across", "one", "step", "within", "multiple", "teams"):
        assert junk not in result.matched_skills
        assert junk not in result.missing_skills
