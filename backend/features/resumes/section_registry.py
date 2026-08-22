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

# The model attribute holding an item's "sub-heading" (its own title/role,
# as opposed to the section's title) -- used by renderer.py to know which
# attribute name a per-resume title_override actually replaces. Skills,
# Languages, and References render as simple inline lists with no
# sub-heading concept, so they're intentionally absent here.
TITLE_FIELDS: dict[SectionType, str] = {
    SectionType.EDUCATION: "degree",
    SectionType.EXPERIENCE: "job_title",
    SectionType.PROJECTS: "title",
    SectionType.CERTIFICATIONS: "name",
    SectionType.ACHIEVEMENTS: "title",
    SectionType.AWARDS: "title",
    SectionType.RESEARCH: "title",
    SectionType.VOLUNTEER_EXPERIENCE: "role",
    SectionType.LEADERSHIP_ROLES: "title",
    SectionType.ORGANIZATIONS: "role",
    SectionType.HACKATHONS: "name",
    SectionType.COMPETITIONS: "name",
    SectionType.PATENTS: "title",
}

# The model attribute holding an item's organization/institution line --
# the second half of a sub-heading (e.g. Experience's "job_title" +
# "company_name"). Absent for section types with no separate org concept
# (Projects, Patents, Competitions, Hackathons) -- those items have only a
# title, so `subtitle_override` is simply not offered for them.
SUBTITLE_FIELDS: dict[SectionType, str] = {
    SectionType.EDUCATION: "institution_name",
    SectionType.EXPERIENCE: "company_name",
    SectionType.CERTIFICATIONS: "issuing_organization",
    SectionType.ACHIEVEMENTS: "issuer",
    SectionType.AWARDS: "issuer",
    SectionType.RESEARCH: "publication_venue",
    SectionType.VOLUNTEER_EXPERIENCE: "organization_name",
    SectionType.LEADERSHIP_ROLES: "organization_name",
    SectionType.ORGANIZATIONS: "organization_name",
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
