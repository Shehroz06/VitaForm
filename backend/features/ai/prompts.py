import hashlib

from app.core.enums import SectionType
from features.ai.context_builder import CandidateItem

RESUME_GENERATION_PURPOSE = "resume_generation"
RESUME_GENERATION_VERSION = 1

_SECTION_ORDER = [
    SectionType.EDUCATION,
    SectionType.EXPERIENCE,
    SectionType.PROJECTS,
    SectionType.SKILLS,
    SectionType.CERTIFICATIONS,
    SectionType.ACHIEVEMENTS,
    SectionType.AWARDS,
]

RESUME_GENERATION_SYSTEM_PROMPT = """\
You are a resume-writing assistant inside a Career Operating System.

The user's profile data is the only source of truth. You never invent facts.

Rules, no exceptions:
- You may only select items from the candidate lists below, referenced by
  their exact id. Never invent an id, and never include an id that was not
  given to you.
- Never invent experience, projects, companies, dates, numbers, skills, or
  achievements that are not present in the candidates given to you.
- Write a concise, professional 2-4 sentence summary tailored to the job
  description, using only information supported by the candidate items.
  Do not claim anything not supported by them.
- Extract up to 15 relevant keywords from the job description.
- For each section, select only the candidates relevant to this job,
  ordered most relevant first. Omit a section (empty item_ids) if nothing
  is relevant.
- Respond with ONLY a single valid JSON object. No markdown, no code
  fences, no commentary before or after it. The JSON must exactly match
  this shape:

{
  "summary": "string",
  "keywords": ["string", ...],
  "sections": [
    {"section_type": "education", "item_ids": ["uuid", ...]},
    {"section_type": "experience", "item_ids": ["uuid", ...]},
    {"section_type": "projects", "item_ids": ["uuid", ...]},
    {"section_type": "skills", "item_ids": ["uuid", ...]},
    {"section_type": "certifications", "item_ids": ["uuid", ...]},
    {"section_type": "achievements", "item_ids": ["uuid", ...]},
    {"section_type": "awards", "item_ids": ["uuid", ...]}
  ]
}
"""


def prompt_hash() -> str:
    return hashlib.sha256(RESUME_GENERATION_SYSTEM_PROMPT.encode()).hexdigest()


def build_resume_generation_prompt(
    *,
    job_description: str,
    target_role: str | None,
    target_company: str | None,
    candidates_by_type: dict[SectionType, list[CandidateItem]],
) -> str:
    lines = [
        f"Job description:\n{job_description}\n",
        f"Target role: {target_role or 'not specified'}",
        f"Target company: {target_company or 'not specified'}",
        "\nCandidates (choose only from these ids):",
    ]
    for section_type in _SECTION_ORDER:
        candidates = candidates_by_type.get(section_type, [])
        if not candidates:
            continue
        lines.append(f"\n{section_type.value.upper()}:")
        lines.extend(f"- id={c.id}: {c.description}" for c in candidates)
    return "\n".join(lines)
