from enum import StrEnum


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    VOLUNTEER = "volunteer"


class ProjectStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


class SkillCategory(StrEnum):
    TECHNICAL = "technical"
    SOFT = "soft"
    TOOL = "tool"
    OTHER = "other"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LanguageProficiency(StrEnum):
    BASIC = "basic"
    CONVERSATIONAL = "conversational"
    PROFESSIONAL = "professional"
    FLUENT = "fluent"
    NATIVE = "native"


class PatentStatus(StrEnum):
    FILED = "filed"
    PENDING = "pending"
    GRANTED = "granted"
    REJECTED = "rejected"


class FilePurpose(StrEnum):
    AVATAR = "avatar"
    CERTIFICATE = "certificate"
    ACHIEVEMENT = "achievement"
    RESUME = "resume"


class SectionType(StrEnum):
    """Resume section types. SUMMARY is free-text; the rest reference items
    from the matching profile sub-resource by id. Deliberately scoped to the
    most common resume sections for Phase 5 -- the remaining profile modules
    (research, volunteer work, languages, etc.) use the exact same shape and
    can be added to SECTION_REGISTRY later without a schema change."""

    SUMMARY = "summary"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    AWARDS = "awards"
