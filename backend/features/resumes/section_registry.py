"""Maps each item-backed SectionType to its owning model and a default
section title. The renderer and the content-validation step both use this
single registry, so adding another profile module as a resume section later
is a one-line addition here -- not a schema or endpoint change."""

from app.core.enums import SectionType
from app.database.base import CrudModelMixin
from features.achievements.models import Achievement
from features.awards.models import Award
from features.certifications.models import Certification
from features.competitions.models import Competition
from features.education.models import Education
from features.experience.models import Experience
from features.hackathons.models import Hackathon
from features.languages.models import Language
from features.leadership_roles.models import LeadershipRole
from features.organizations.models import Organization
from features.patents.models import Patent
from features.projects.models import Project
from features.references.models import Reference
from features.research.models import Research
from features.skills.models import Skill
from features.volunteer_experience.models import VolunteerExperience

SECTION_MODELS: dict[SectionType, type[CrudModelMixin]] = {
    SectionType.EDUCATION: Education,
    SectionType.EXPERIENCE: Experience,
    SectionType.PROJECTS: Project,
    SectionType.SKILLS: Skill,
    SectionType.CERTIFICATIONS: Certification,
    SectionType.ACHIEVEMENTS: Achievement,
    SectionType.AWARDS: Award,
    SectionType.RESEARCH: Research,
    SectionType.VOLUNTEER_EXPERIENCE: VolunteerExperience,
    SectionType.LEADERSHIP_ROLES: LeadershipRole,
    SectionType.ORGANIZATIONS: Organization,
    SectionType.LANGUAGES: Language,
    SectionType.REFERENCES: Reference,
    SectionType.HACKATHONS: Hackathon,
    SectionType.COMPETITIONS: Competition,
    SectionType.PATENTS: Patent,
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
    SectionType.RESEARCH: "Research & Publications",
    SectionType.VOLUNTEER_EXPERIENCE: "Volunteer Experience",
    SectionType.LEADERSHIP_ROLES: "Leadership",
    SectionType.ORGANIZATIONS: "Organizations",
    SectionType.LANGUAGES: "Languages",
    SectionType.REFERENCES: "References",
    SectionType.HACKATHONS: "Hackathons",
    SectionType.COMPETITIONS: "Competitions",
    SectionType.PATENTS: "Patents",
}
