import uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from weasyprint import HTML

from app.core.enums import RenderEngine, SectionType
from app.exceptions.base import ValidationException
from features.profiles.models import Profile
from features.projects.models import Project
from features.resumes.description_units import split_description_into_units
from features.resumes.latex_renderer import LatexRenderer
from features.resumes.models import Resume, ResumeTemplate, ResumeVersion
from features.resumes.schemas import ResumeContent
from features.resumes.section_registry import (
    DEFAULT_SECTION_TITLES,
    SECTION_MODELS,
    SUBTITLE_FIELDS,
    TITLE_FIELDS,
)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "resumes"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html.jinja2"]),
)
# Mirrors latex_utils.py's format_description: every description renders as
# a uniform bulleted list regardless of how it happens to be typed in the
# profile (see description_units.py's module docstring). Returns plain
# strings, not pre-built HTML -- autoescape above still escapes each unit
# normally when the template interpolates it with `{{ }}`.
_jinja_env.filters["description_units"] = lambda text: (
    split_description_into_units(text)[0] if text else []
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
    # See ResumeStyle.spacing's docstring -- computed-only, tried by the
    # autofit search after "compact" still overflows, never a manual choice.
    "extreme": {"line_height": "1.15", "section_gap": "5pt", "entry_gap": "3pt"},
}


class _ItemOverrideView:
    """Wraps one fetched item so templates see resume-scoped overrides
    (description, and -- for section types with a sub-heading -- its own
    title/role and org/institution line) without ever touching the real
    ORM entity. This is deliberate: `item` is a SQLAlchemy object tracked
    by the request's session, and setting e.g. `item.description = ...`
    directly would mark it dirty and get written back to the real
    Experience/Project/etc. row the next time the session commits --
    silently corrupting the user's actual profile data with resume-
    specific, possibly-shortened text. Wrapping instead of mutating is
    what keeps an override resume-scoped, as promised by ResumeContent's
    docstring for these fields."""

    __slots__ = ("_item", "_overrides")

    def __init__(self, item: Any, overrides: dict[str, str]) -> None:
        self._item = item
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._item, name)


async def _fetch_section_items(
    db: AsyncSession,
    section_type: SectionType,
    model: type[Any],
    item_ids: list[uuid.UUID],
    profile_id: uuid.UUID,
    content: ResumeContent,
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
    items = [by_id[item_id] for item_id in item_ids if item_id in by_id]

    title_field = TITLE_FIELDS.get(section_type)
    subtitle_field = SUBTITLE_FIELDS.get(section_type)
    resolved = []
    for item in items:
        key = str(item.id)
        overrides: dict[str, str] = {}
        if key in content.description_overrides:
            overrides["description"] = content.description_overrides[key]
        if title_field and key in content.title_overrides:
            overrides[title_field] = content.title_overrides[key]
        if subtitle_field and key in content.subtitle_overrides:
            overrides[subtitle_field] = content.subtitle_overrides[key]
        resolved.append(_ItemOverrideView(item, overrides) if overrides else item)
    return resolved


class ResumeRenderer:
    """Resume JSON (a version's content) -> PDF, dispatching to whichever
    pipeline the chosen template declares (RenderEngine.HTML -> Jinja2 ->
    WeasyPrint; RenderEngine.LATEX -> Jinja2 -> pdflatex, see
    latex_renderer.py). Rendering never trusts the version's item_ids
    blindly: every item is re-fetched scoped to the profile, so a version
    created for one profile can never leak another profile's data even if
    IDs were tampered with."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._latex = LatexRenderer()

    async def _resolve_render_context(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> tuple[dict[str, Any], ResumeContent]:
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
                self._db, section.section_type, model, section.item_ids, profile.id, content
            )
            if not items:
                continue
            resolved_sections.append(
                {"type": section.section_type.value, "title": title, "entries": items}
            )

        render_context = dict(
            resume_title=resume.title,
            full_name=full_name or resume.title,
            profile=profile,
            email=email,
            contact_visibility=content.contact_visibility,
            sections=resolved_sections,
            style=content.style,
        )
        return render_context, content

    async def render_pdf(
        self,
        resume: Resume,
        version: ResumeVersion,
        template: ResumeTemplate,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> bytes:
        render_context, content = await self._resolve_render_context(
            resume, version, profile, email, full_name
        )

        if template.render_engine is RenderEngine.LATEX:
            return await self._latex.render(template.slug, **render_context)

        html = _jinja_env.get_template(f"{template.slug}/resume.html.jinja2").render(
            **render_context,
            font_stack=FONT_STACKS[content.style.font_family],
            spacing=SPACING_METRICS[content.style.spacing],
        )
        pdf_bytes: bytes = HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf()
        return pdf_bytes

    async def render_tex_source(
        self,
        resume: Resume,
        version: ResumeVersion,
        template: ResumeTemplate,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> str:
        """Raw .tex source, uncompiled -- lets a user verify or
        independently recompile exactly what this app renders (e.g. in
        Overleaf). Only meaningful for LATEX-engine templates; HTML-engine
        templates have no .tex source to hand back."""
        if template.render_engine is not RenderEngine.LATEX:
            raise ValidationException("This template doesn't use LaTeX rendering.")
        render_context, _content = await self._resolve_render_context(
            resume, version, profile, email, full_name
        )
        return self._latex.render_source(template.slug, **render_context)
