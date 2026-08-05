"""Maps each item-backed SectionType to its owning model and a default
section title. The renderer and the content-validation step both use this
single registry, so adding another profile module as a resume section later
is a one-line addition here -- not a schema or endpoint change."""

from app.core.enums import SectionType
from app.database.base import CrudModelMixin
from features.achievements.models import Achievement
from features.awards.models import Award
from features.certifications.models import Certification
from features.education.models import Education
from features.experience.models import Experience
from features.projects.models import Project
from features.skills.models import Skill

SECTION_MODELS: dict[SectionType, type[CrudModelMixin]] = {
    SectionType.EDUCATION: Education,
    SectionType.EXPERIENCE: Experience,
    SectionType.PROJECTS: Project,
    SectionType.SKILLS: Skill,
    SectionType.CERTIFICATIONS: Certification,
    SectionType.ACHIEVEMENTS: Achievement,
    SectionType.AWARDS: Award,
}

DEFAULT_SECTION_TITLES: dict[SectionType, str] = {
    SectionType.SUMMARY: "Summary",
    SectionType.EDUCATION: "Education",
    SectionType.EXPERIENCE: "Experience",
    SectionType.PROJECTS: "Projects",
    SectionType.SKILLS: "Skills",
    SectionType.CERTIFICATIONS: "Certifications",
    SectionType.ACHIEVEMENTS: "Achievements",
    SectionType.AWARDS: "Awards",
}
