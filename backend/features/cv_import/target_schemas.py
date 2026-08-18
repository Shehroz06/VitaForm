"""Maps each item-backed SectionType to the exact Pydantic CreateRequest
schema already used by that resource's own router. The AI classifier's
output is validated against these -- never a bespoke import-only schema --
so an imported item can never carry a shape the real create endpoint
wouldn't also accept. Mirrors features/resumes/section_registry.py's
single-dict-registry pattern."""

from pydantic import BaseModel

from app.core.enums import SectionType
from features.achievements.schemas import AchievementCreateRequest
from features.awards.schemas import AwardCreateRequest
from features.certifications.schemas import CertificationCreateRequest
from features.competitions.schemas import CompetitionCreateRequest
from features.education.schemas import EducationCreateRequest
from features.experience.schemas import ExperienceCreateRequest
from features.hackathons.schemas import HackathonCreateRequest
from features.languages.schemas import LanguageCreateRequest
from features.leadership_roles.schemas import LeadershipRoleCreateRequest
from features.organizations.schemas import OrganizationCreateRequest
from features.patents.schemas import PatentCreateRequest
from features.projects.schemas import ProjectCreateRequest
from features.references.schemas import ReferenceCreateRequest
from features.research.schemas import ResearchCreateRequest
from features.skills.schemas import SkillCreateRequest
from features.volunteer_experience.schemas import VolunteerExperienceCreateRequest

IMPORT_TARGET_SCHEMAS: dict[SectionType, type[BaseModel]] = {
    SectionType.EDUCATION: EducationCreateRequest,
    SectionType.EXPERIENCE: ExperienceCreateRequest,
    SectionType.PROJECTS: ProjectCreateRequest,
    SectionType.SKILLS: SkillCreateRequest,
    SectionType.CERTIFICATIONS: CertificationCreateRequest,
    SectionType.ACHIEVEMENTS: AchievementCreateRequest,
    SectionType.AWARDS: AwardCreateRequest,
    SectionType.RESEARCH: ResearchCreateRequest,
    SectionType.VOLUNTEER_EXPERIENCE: VolunteerExperienceCreateRequest,
    SectionType.LEADERSHIP_ROLES: LeadershipRoleCreateRequest,
    SectionType.ORGANIZATIONS: OrganizationCreateRequest,
    SectionType.LANGUAGES: LanguageCreateRequest,
    SectionType.REFERENCES: ReferenceCreateRequest,
    SectionType.HACKATHONS: HackathonCreateRequest,
    SectionType.COMPETITIONS: CompetitionCreateRequest,
    SectionType.PATENTS: PatentCreateRequest,
}
