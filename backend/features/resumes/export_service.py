from datetime import UTC, datetime

from app.core.enums import FilePurpose
from app.exceptions.base import ResourceNotFoundException
from features.files.service import FileUploadService
from features.profiles.models import Profile
from features.resumes.models import Resume, ResumeVersion
from features.resumes.renderer import ResumeRenderer
from features.resumes.repository import ResumeTemplateRepository, ResumeVersionRepository


class ResumeExportService:
    """Renders a resume version to PDF and records the result on that
    version. Re-exporting replaces the version's previous rendered file
    (soft-deleted + removed from storage) rather than accumulating copies --
    a version's PDF is a deterministic function of its content, so only the
    latest render is ever worth keeping."""

    def __init__(
        self,
        renderer: ResumeRenderer,
        version_repository: ResumeVersionRepository,
        template_repository: ResumeTemplateRepository,
        file_service: FileUploadService,
    ) -> None:
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
