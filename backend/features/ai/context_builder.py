import uuid
from dataclasses import dataclass
from typing import Any

from app.core.enums import SectionType
from features.ai.ranking import RankedItem


@dataclass(frozen=True)
class CandidateItem:
    id: uuid.UUID
    description: str


def _describe_education(item: Any) -> str:
    span = f"{item.start_date}–{item.end_date or 'present'}"
    field = f" in {item.field_of_study}" if item.field_of_study else ""
    return f"{item.degree}{field} at {item.institution_name} ({span})"


def _describe_experience(item: Any) -> str:
    span = f"{item.start_date}–{'present' if item.is_current else (item.end_date or 'unknown')}"
    description = f" -- {item.description}" if item.description else ""
    return f"{item.job_title} at {item.company_name} ({span}){description}"


def _describe_project(item: Any) -> str:
    skills = ", ".join(skill.name for skill in item.skills)
    tech = f" [tech: {skills}]" if skills else ""
    description = f" -- {item.description}" if item.description else ""
    return f"{item.title}{tech}{description}"


def _describe_skill(item: Any) -> str:
    level = f" ({item.level.value})" if item.level else ""
    return f"{item.name}{level}"


def _describe_certification(item: Any) -> str:
    return f"{item.name} from {item.issuing_organization} ({item.issue_date or 'date unknown'})"


def _describe_achievement(item: Any) -> str:
    issuer = f" -- {item.issuer}" if item.issuer else ""
    return f"{item.title}{issuer}"


def _describe_award(item: Any) -> str:
    issuer = f" -- {item.issuer}" if item.issuer else ""
    return f"{item.title}{issuer}"


_DESCRIBERS = {
    SectionType.EDUCATION: _describe_education,
    SectionType.EXPERIENCE: _describe_experience,
    SectionType.PROJECTS: _describe_project,
    SectionType.SKILLS: _describe_skill,
    SectionType.CERTIFICATIONS: _describe_certification,
    SectionType.ACHIEVEMENTS: _describe_achievement,
    SectionType.AWARDS: _describe_award,
}


def build_candidates(
    ranked_by_type: dict[SectionType, list[RankedItem]],
) -> dict[SectionType, list[CandidateItem]]:
    """Turns ranked DB items into compact text candidates for the prompt --
    never the whole profile, only what survived ranking's top-N cap."""
    result: dict[SectionType, list[CandidateItem]] = {}
    for section_type, ranked_items in ranked_by_type.items():
        describe = _DESCRIBERS[section_type]
        result[section_type] = [
            CandidateItem(id=ranked.item.id, description=describe(ranked.item))
            for ranked in ranked_items
        ]
    return result
