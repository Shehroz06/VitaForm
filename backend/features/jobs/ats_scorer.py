from dataclasses import dataclass

from features.jobs.schemas import JobAnalysis
from features.jobs.skills_taxonomy import canonicalize, match_skills

_MAX_LISTED_SKILLS = 10


@dataclass(frozen=True)
class AtsResult:
    overall_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]


def compute_ats_score(
    analysis: JobAnalysis, profile_skill_names: set[str], profile_text: str
) -> AtsResult:
    # Canonicalize both sides through the same taxonomy so "React.js" in a
    # profile's Skills list and "React" in a job description count as the
    # same skill. A profile skill outside the taxonomy still counts under
    # its own normalized name rather than being silently dropped.
    profile_skills = match_skills(profile_text) | {
        canonicalize(name) for name in profile_skill_names
    }

    required = set(analysis.required_skills)
    preferred = set(analysis.preferred_skills)

    matched_required = required & profile_skills
    matched_preferred = preferred & profile_skills
    missing_required = required - profile_skills
    missing_preferred = preferred - profile_skills

    total_weight = len(required) * 2 + len(preferred)
    matched_weight = len(matched_required) * 2 + len(matched_preferred)
    overall_score = round((matched_weight / total_weight) * 100) if total_weight else 100

    recommendations: list[str] = []
    if missing_required:
        listed = ", ".join(sorted(missing_required)[:_MAX_LISTED_SKILLS])
        recommendations.append(
            f"Add these required skills to your profile if you have them: {listed}."
        )
    if missing_preferred:
        listed = ", ".join(sorted(missing_preferred)[:_MAX_LISTED_SKILLS])
        recommendations.append(f"Consider highlighting these preferred skills too: {listed}.")
    if overall_score >= 80:
        recommendations.append(
            "Strong match -- your profile covers most of this job's requirements."
        )
    elif overall_score < 40:
        recommendations.append(
            "Low match -- consider whether this role aligns with your current profile."
        )

    return AtsResult(
        overall_score=overall_score,
        matched_skills=sorted(matched_required | matched_preferred),
        missing_skills=sorted(missing_required | missing_preferred),
        recommendations=recommendations,
    )
