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
    from the matching profile sub-resource by id. All sections are optional
    and selected per-resume -- inclusion depends on what the user picks and
    what fits the CV they're building (e.g. Research/Patents suit an
    academic CV, Hackathons/Competitions suit an early-career CV)."""

    SUMMARY = "summary"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    AWARDS = "awards"
    RESEARCH = "research"
    VOLUNTEER_EXPERIENCE = "volunteer_experience"
    LEADERSHIP_ROLES = "leadership_roles"
    ORGANIZATIONS = "organizations"
    LANGUAGES = "languages"
    REFERENCES = "references"
    HACKATHONS = "hackathons"
    COMPETITIONS = "competitions"
    PATENTS = "patents"


class GenerationStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class ImportSessionStatus(StrEnum):
    """Lifecycle of a CV-import review session. Nothing reaches the real
    profile tables until CONFIRMED -- PENDING/FAILED sessions are pure
    staging, safe to discard."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FAILED = "failed"


class RenderEngine(StrEnum):
    """Which pipeline a resume template compiles through. HTML -> Jinja2 ->
    WeasyPrint (every template so far); LATEX -> Jinja2 -> pdflatex, for
    templates that need to be an actual LaTeX document rather than an
    HTML approximation of one."""

    HTML = "html"
    LATEX = "latex"
