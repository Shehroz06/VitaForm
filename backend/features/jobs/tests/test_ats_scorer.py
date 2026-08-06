from features.jobs.ats_scorer import compute_ats_score
from features.jobs.schemas import JobAnalysis


def test_compute_ats_score_full_match_scores_100() -> None:
    analysis = JobAnalysis(keywords=["python"], required_skills=["python"], preferred_skills=[])
    result = compute_ats_score(analysis, {"Python"}, "")

    assert result.overall_score == 100
    assert result.matched_skills == ["python"]
    assert result.missing_skills == []


def test_compute_ats_score_no_match_scores_0() -> None:
    analysis = JobAnalysis(keywords=["rust"], required_skills=["rust"], preferred_skills=[])
    result = compute_ats_score(analysis, {"Python"}, "")

    assert result.overall_score == 0
    assert result.missing_skills == ["rust"]
    assert any("rust" in rec for rec in result.recommendations)


def test_compute_ats_score_with_no_requirements_scores_100() -> None:
    analysis = JobAnalysis(keywords=[], required_skills=[], preferred_skills=[])
    result = compute_ats_score(analysis, set(), "")
    assert result.overall_score == 100


def test_compute_ats_score_matches_via_profile_text_not_just_skill_names() -> None:
    analysis = JobAnalysis(keywords=["docker"], required_skills=["docker"], preferred_skills=[])
    result = compute_ats_score(analysis, set(), "Built and deployed services using Docker.")
    assert result.overall_score == 100
    assert "docker" in result.matched_skills


def test_compute_ats_score_weights_required_more_than_preferred() -> None:
    analysis = JobAnalysis(
        keywords=[], required_skills=["python"], preferred_skills=["kubernetes"]
    )
    result = compute_ats_score(analysis, {"Python"}, "")
    # matched required (weight 2) out of required*2 + preferred*1 = 2/3 -> 67%
    assert result.overall_score == 67
