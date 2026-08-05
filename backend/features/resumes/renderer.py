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
            profile=profile,
            email=email,
            contact_visibility=content.contact_visibility,
            sections=resolved_sections,
        )
        pdf_bytes: bytes = HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf()
        return pdf_bytes
