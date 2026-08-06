import hashlib

from app.core.enums import SectionType
from features.ai.context_builder import CandidateItem

COVER_LETTER_PURPOSE = "cover_letter_generation"
COVER_LETTER_VERSION = 1
COVER_LETTER_TEMPERATURE = 0.5

LINKEDIN_PURPOSE = "linkedin_generation"
LINKEDIN_VERSION = 1
LINKEDIN_TEMPERATURE = 0.6

_SECTION_ORDER = [
    SectionType.EXPERIENCE,
    SectionType.PROJECTS,
    SectionType.EDUCATION,
    SectionType.SKILLS,
    SectionType.CERTIFICATIONS,
    SectionType.ACHIEVEMENTS,
    SectionType.AWARDS,
]

COVER_LETTER_SYSTEM_PROMPT = """\
You are a professional cover letter writer inside a Career Operating System.

The candidate summary below is the only source of truth. You never invent facts.

Rules, no exceptions:
- Only reference experience, projects, skills, education, and achievements
  present in the candidate summary given to you. Never invent a company,
  role, date, number, or motivation not present in it.
- Write a complete, professional cover letter (3-4 paragraphs) addressed to
  the hiring manager if named, otherwise "Dear Hiring Manager".
- Tailor it to the target role, company, and job description if given.
- Respond with ONLY a single valid JSON object. No markdown, no code
  fences, no commentary. The JSON must exactly match this shape:

{"cover_letter": "string, the full letter body"}
"""

LINKEDIN_SYSTEM_PROMPT = """\
You are a LinkedIn profile writer inside a Career Operating System.

The candidate summary below is the only source of truth. You never invent facts.

Rules, no exceptions:
- Only reference experience, projects, skills, education, and achievements
  present in the candidate summary given to you. Never invent a company,
  role, date, number, or accomplishment not present in it.
- Write a concise, compelling LinkedIn headline (under 220 characters).
- Write a LinkedIn "About" section (2-4 short paragraphs, first person,
  professional but personable tone).
- Respond with ONLY a single valid JSON object. No markdown, no code
  fences, no commentary. The JSON must exactly match this shape:

{"headline": "string", "about": "string"}
"""


def cover_letter_prompt_hash() -> str:
    return hashlib.sha256(COVER_LETTER_SYSTEM_PROMPT.encode()).hexdigest()


def linkedin_prompt_hash() -> str:
    return hashlib.sha256(LINKEDIN_SYSTEM_PROMPT.encode()).hexdigest()


def _render_candidates(candidates_by_type: dict[SectionType, list[CandidateItem]]) -> str:
    lines: list[str] = []
    for section_type in _SECTION_ORDER:
        candidates = candidates_by_type.get(section_type, [])
        if not candidates:
            continue
        lines.append(f"\n{section_type.value.upper()}:")
        lines.extend(f"- {c.description}" for c in candidates)
    return "\n".join(lines)


def build_cover_letter_prompt(
    *,
    company_name: str,
    role_title: str,
    hiring_manager: str | None,
    job_description: str | None,
    candidates_by_type: dict[SectionType, list[CandidateItem]],
) -> str:
    lines = [
        f"Target company: {company_name}",
        f"Target role: {role_title}",
        f"Hiring manager: {hiring_manager or 'not specified'}",
    ]
    if job_description:
        lines.append(f"\nJob description:\n{job_description}")
    lines.append("\nCandidate summary:")
    lines.append(_render_candidates(candidates_by_type))
    return "\n".join(lines)


def build_linkedin_prompt(
    *,
    target_role: str | None,
    candidates_by_type: dict[SectionType, list[CandidateItem]],
) -> str:
    lines = [f"Target role: {target_role or 'not specified'}", "\nCandidate summary:"]
    lines.append(_render_candidates(candidates_by_type))
    return "\n".join(lines)
