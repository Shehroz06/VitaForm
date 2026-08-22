import uuid
from datetime import UTC, datetime
from typing import Any

import pymupdf
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import FilePurpose, SectionType
from app.exceptions.base import ResourceNotFoundException
from features.ai.candidates import flatten_descriptions_by_item_id, load_candidate_items
from features.ai.page_fit import (
    count_pdf_pages,
    fit_resume_to_one_page,
    fit_spacing_and_density,
    position_based_scores,
)
from features.files.service import FileUploadService
from features.profiles.models import Profile
from features.resumes.models import Resume, ResumeVersion
from features.resumes.renderer import ResumeRenderer
from features.resumes.repository import ResumeTemplateRepository, ResumeVersionRepository
from features.resumes.schemas import ContactVisibility, ResumeContent, ResumeSection, ResumeStyle
from features.resumes.section_registry import SECTION_MODELS

_SAMPLE_SUMMARY = (
    "Experienced professional with a track record of delivering results across "
    "engineering, research, and product work."
)


def _build_sample_content(
    items_by_type: dict[SectionType, list[Any]], style: ResumeStyle
) -> ResumeContent:
    """Every item on the profile, in every section, visible -- there's no
    real resume to scope this preview to (see render_template_sample_image's
    docstring), so this fills every section instead of an arbitrary subset,
    the same "show a realistic amount of content" reasoning as the
    resume-builder's own template-picker preview."""
    sections = [ResumeSection(section_type=SectionType.SUMMARY, visible=True, item_ids=[])]
    for section_type in SECTION_MODELS:
        item_ids = [item.id for item in items_by_type.get(section_type, [])]
        sections.append(ResumeSection(section_type=section_type, visible=True, item_ids=item_ids))
    return ResumeContent(
        summary=_SAMPLE_SUMMARY,
        contact_visibility=ContactVisibility(),
        sections=sections,
        style=style,
    )

# 144 DPI (2x the PDF/PostScript-point default of 72) -- crisp on retina
# displays without producing an excessively large image for a browser
# preview card.
_PREVIEW_ZOOM = 144 / 72


class ResumeExportService:
    """Renders a resume version to PDF and records the result on that
    version. Re-exporting replaces the version's previous rendered file
    (soft-deleted + removed from storage) rather than accumulating copies --
    a version's PDF is a deterministic function of its content, so only the
    latest render is ever worth keeping."""

    def __init__(
        self,
        db: AsyncSession,
        renderer: ResumeRenderer,
        version_repository: ResumeVersionRepository,
        template_repository: ResumeTemplateRepository,
        file_service: FileUploadService,
    ) -> None:
        self._db = db
        self._renderer = renderer
        self._versions = version_repository
        self._templates = template_repository
        self._files = file_service

    async def export(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> ResumeVersion:
        template = await self._templates.get_by_id(resume.template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        pdf_bytes = await self._renderer.render_pdf(
            resume, version, template, profile, email, full_name
        )

        if version.rendered_file_id is not None:
            await self._files.delete(version.rendered_file_id, profile.id)

        filename = f"{resume.title}.pdf".replace("/", "-")
        stored = await self._files.store_generated(
            profile.id, FilePurpose.RESUME, filename, "application/pdf", pdf_bytes
        )
        return await self._versions.update(
            version, rendered_file_id=stored.id, rendered_at=datetime.now(UTC)
        )

    async def render_preview_image(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
        page_number: int = 1,
    ) -> tuple[bytes, int]:
        """Renders the resume through the exact same pipeline as export()
        (same template, same render_engine dispatch) but returns a
        rasterized PNG of one page instead of persisting a File row -- a
        live preview fires on every autosave, and export()'s File-per-render
        bookkeeping (rendered_file_id/rendered_at, deleting the previous
        stored file) is for real, deliberate exports, not this. Also always
        returns the real page count, so a resume that overflows to 2+ pages
        can say so honestly -- the builder fetches page_number 2, 3, ... to
        show the rest in a scrollable preview instead of silently cropping
        to page 1.

        page_number is 1-indexed (matches how a person would refer to "page
        2 of my resume") and clamped into range rather than rejected: an
        edit that shrinks the resume out from under an already-open page-3
        view shouldn't 404 the preview mid-edit, it should just show the
        new last page."""
        template = await self._templates.get_by_id(resume.template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        pdf_bytes = await self._renderer.render_pdf(
            resume, version, template, profile, email, full_name
        )

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            page_count = doc.page_count
            page_index = min(max(page_number, 1), page_count) - 1
            pixmap = doc[page_index].get_pixmap(matrix=pymupdf.Matrix(_PREVIEW_ZOOM, _PREVIEW_ZOOM))
            png_bytes: bytes = pixmap.tobytes("png")

        return png_bytes, page_count

    async def export_tex_source(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> str:
        """Raw .tex source for a LaTeX-engine resume (ats_safe) -- lets a
        user verify or independently recompile exactly what this app
        renders, e.g. in Overleaf. Not persisted as a File row, same
        reasoning as render_preview_image: this is a read-only artifact of
        already-saved content, not a deliberate "export" event."""
        template = await self._templates.get_by_id(resume.template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        return await self._renderer.render_tex_source(
            resume, version, template, profile, email, full_name
        )

    async def render_preview_image_with_content(
        self,
        resume: Resume,
        content: ResumeContent,
        template_id: uuid.UUID,
        profile: Profile,
        email: str,
        full_name: str,
        page_number: int = 1,
    ) -> tuple[bytes, int]:
        """Same rasterized-PNG contract as render_preview_image, but for
        arbitrary content against a candidate template rather than the
        resume's own saved version/template -- the template picker's "real
        A4 preview per template" comparison. Nothing here touches the
        database: `transient_version` is a plain in-memory ResumeVersion,
        never added to a session or committed, that exists only to satisfy
        ResumeRenderer.render_pdf's signature (it reads version.content and
        nothing else persistence-related)."""
        template = await self._templates.get_by_id(template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        transient_version = ResumeVersion(content=content.model_dump(mode="json"))
        pdf_bytes = await self._renderer.render_pdf(
            resume, transient_version, template, profile, email, full_name
        )

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            page_count = doc.page_count
            page_index = min(max(page_number, 1), page_count) - 1
            pixmap = doc[page_index].get_pixmap(matrix=pymupdf.Matrix(_PREVIEW_ZOOM, _PREVIEW_ZOOM))
            png_bytes: bytes = pixmap.tobytes("png")

        return png_bytes, page_count

    async def render_template_sample_image(
        self,
        profile: Profile,
        template_id: uuid.UUID,
        style: ResumeStyle,
        email: str,
        full_name: str,
    ) -> bytes:
        """Real-rendered PNG (page 1 only) of the given template filled
        with the caller's own profile -- the pre-resume-creation template
        browser's equivalent of render_preview_image_with_content, which
        needs an existing resume to scope to. Nothing here touches the
        database: both `resume` and `version` are plain in-memory objects
        that exist only to satisfy ResumeRenderer.render_pdf's signature."""
        template = await self._templates.get_by_id(template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        items_by_type = await load_candidate_items(self._db, profile.id)
        content = _build_sample_content(items_by_type, style)

        resume = Resume(
            id=uuid.uuid4(), profile_id=profile.id, template_id=template.id, title="Preview"
        )
        version = ResumeVersion(content=content.model_dump(mode="json"))
        pdf_bytes = await self._renderer.render_pdf(
            resume, version, template, profile, email, full_name
        )

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            pixmap = doc[0].get_pixmap(matrix=pymupdf.Matrix(_PREVIEW_ZOOM, _PREVIEW_ZOOM))
            return pixmap.tobytes("png")

    async def autofit(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> tuple[ResumeVersion, bool]:
        """The manual builder's "Auto-fit" action: the same lossless
        spacing/density search AI generation uses (features/ai/page_fit.py),
        without that pipeline's item-trimming step -- only a human should
        decide what real content is safe to cut, so this stops and reports
        overflow instead of silently deleting anything. Persists the
        adjusted style in place (no new version, matching autosave's
        behavior) so Export and the preview immediately reflect it."""
        template = await self._templates.get_by_id(resume.template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        content = ResumeContent.model_validate(version.content)
        fitted_content, overflowing = await fit_spacing_and_density(
            renderer=self._renderer,
            template=template,
            profile=profile,
            email=email,
            full_name=full_name,
            title=resume.title,
            content=content,
        )
        updated_version = await self._versions.update(
            version, content=fitted_content.model_dump(mode="json")
        )
        return updated_version, overflowing

    async def autofit_aggressive(
        self,
        resume: Resume,
        version: ResumeVersion,
        profile: Profile,
        email: str,
        full_name: str,
    ) -> tuple[ResumeVersion, bool]:
        """The manual builder's opt-in escalation beyond autofit()'s
        lossless-only search -- explicitly triggered by the user (never
        run automatically), since only a human should decide real content
        is safe to shorten or remove. Runs the exact same condense-then-
        delete pipeline AI generation uses (fit_resume_to_one_page), scored
        by the order the user already put items in
        (page_fit.position_based_scores) rather than job-description
        relevance, since there's no job description in this context."""
        template = await self._templates.get_by_id(resume.template_id)
        if template is None:
            raise ResourceNotFoundException("Resume template not found.")

        content = ResumeContent.model_validate(version.content)
        items_by_type = await load_candidate_items(self._db, profile.id)
        descriptions_by_item_id = flatten_descriptions_by_item_id(items_by_type)
        scores_by_item_id = position_based_scores(content)

        fitted_content = await fit_resume_to_one_page(
            renderer=self._renderer,
            template=template,
            profile=profile,
            email=email,
            full_name=full_name,
            title=resume.title,
            content=content,
            scores_by_item_id=scores_by_item_id,
            descriptions_by_item_id=descriptions_by_item_id,
        )
        updated_version = await self._versions.update(
            version, content=fitted_content.model_dump(mode="json")
        )

        pdf_bytes = await self._renderer.render_pdf(
            resume, updated_version, template, profile, email, full_name
        )
        overflowing = count_pdf_pages(pdf_bytes) > 1
        return updated_version, overflowing
