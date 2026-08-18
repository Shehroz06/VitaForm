import uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from weasyprint import HTML

from app.core.enums import SectionType
from features.profiles.models import Profile
from features.projects.models import Project
from features.resumes.models import Resume, ResumeTemplate, ResumeVersion
from features.resumes.schemas import ResumeContent
from features.resumes.section_registry import DEFAULT_SECTION_TITLES, SECTION_MODELS

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "resumes"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html.jinja2"]),
)

# Single source of truth for style.font_family -> real installed font stack,
# so every Jinja2 template consumes the same resolved CSS value instead of
# each re-implementing this lookup. arial/times are Liberation fonts, already
# installed via the `fonts-liberation` apt package; calibri/georgia are
# metric-compatible open-license substitutes installed via
# `fonts-crosextra-carlito`/`fonts-crosextra-caladea` (see backend.Dockerfile).
FONT_STACKS: dict[str, str] = {
    "arial": '"Liberation Sans", Arial, Helvetica, sans-serif',
    "calibri": '"Carlito", Calibri, sans-serif',
    "times": '"Liberation Serif", "Times New Roman", Times, serif',
    "georgia": '"Caladea", Georgia, "Cambria", serif',
}

# Same idea for style.spacing -- one resolved set of CSS values per density
# level, shared by every template rather than re-derived per file.
SPACING_METRICS: dict[str, dict[str, str]] = {
    "compact": {"line_height": "1.3", "section_gap": "8pt", "entry_gap": "5pt"},
    "cozy": {"line_height": "1.45", "section_gap": "12pt", "entry_gap": "8pt"},
    "relaxed": {"line_height": "1.6", "section_gap": "16pt", "entry_gap": "11pt"},
}


async def _fetch_section_items(
    db: AsyncSession, model: type[Any], item_ids: list[uuid.UUID], profile_id: uuid.UUID
) -> list[Any]:
    if not item_ids:
        return []
    stmt = select(model).where(
        model.id.in_(item_ids), model.profile_id == profile_id, model.deleted_at.is_(None)
    )
    if model is Project:
        stmt = stmt.options(selectinload(Project.skills))
    rows = (await db.execute(stmt)).scalars().all()
    by_id = {row.id: row for row in rows}
    return [by_id[item_id] for item_id in item_ids if item_id in by_id]


class ResumeRenderer:
    """Resume JSON (a version's content) -> Jinja2 HTML -> WeasyPrint PDF.
    Rendering never trusts the version's item_ids blindly: every item is
    re-fetched scoped to the profile, so a version created for one profile
    can never leak another profile's data even if IDs were tampered with."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def render_pdf(
        self,
        resume: Resume,
        version: ResumeVersion,
        template: ResumeTemplate,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> bytes:
        content = ResumeContent.model_validate(version.content)

        resolved_sections: list[dict[str, Any]] = []
        for section in content.sections:
            if not section.visible:
                continue
            title = section.custom_title or DEFAULT_SECTION_TITLES[section.section_type]
            if section.section_type is SectionType.SUMMARY:
                if content.summary:
                    resolved_sections.append(
                        {"type": "summary", "title": title, "text": content.summary}
                    )
                continue

            model = SECTION_MODELS[section.section_type]
            items = await _fetch_section_items(
                self._db, model, section.item_ids, profile.id
            )
            if not items:
                continue
            resolved_sections.append(
                {"type": section.section_type.value, "title": title, "entries": items}
            )

        html = _jinja_env.get_template(f"{template.slug}/resume.html.jinja2").render(
            resume_title=resume.title,
            full_name=full_name or resume.title,
            profile=profile,
            email=email,
            contact_visibility=content.contact_visibility,
            sections=resolved_sections,
            style=content.style,
            font_stack=FONT_STACKS[content.style.font_family],
            spacing=SPACING_METRICS[content.style.spacing],
        )
        pdf_bytes: bytes = HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf()
        return pdf_bytes
