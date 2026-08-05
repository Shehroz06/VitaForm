import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ResourceNotFoundException, ValidationException
from features.resumes.models import Resume, ResumeVersion
from features.resumes.repository import (
    ResumeRepository,
    ResumeTemplateRepository,
    ResumeVersionRepository,
)
from features.resumes.schemas import ResumeContent
from features.resumes.section_registry import SECTION_MODELS


class ResumeService:
    def __init__(
        self,
        db: AsyncSession,
        resume_repository: ResumeRepository,
        version_repository: ResumeVersionRepository,
        template_repository: ResumeTemplateRepository,
    ) -> None:
        self._db = db
        self._resumes = resume_repository
        self._versions = version_repository
        self._templates = template_repository

    async def create_resume(
        self,
        profile_id: uuid.UUID,
        title: str,
        template_id: uuid.UUID,
        content: ResumeContent | None = None,
    ) -> Resume:
        template = await self._templates.get_by_id(template_id)
        if template is None or not template.is_active:
            raise ValidationException("Selected template is not available.")

        if content is not None:
            await self._validate_item_ownership(profile_id, content)

        resume = await self._resumes.create(
            profile_id=profile_id, template_id=template_id, title=title
        )
        await self._versions.create_version(
            resume.id,
            version_number=1,
            content=(content or ResumeContent()).model_dump(mode="json"),
        )
        return resume

    async def get_owned_resume(self, resume_id: uuid.UUID, profile_id: uuid.UUID) -> Resume:
        resume = await self._resumes.get_by_id(resume_id)
        if resume is None or resume.profile_id != profile_id:
            raise ResourceNotFoundException("Resume not found.")
        return resume

    async def list_resumes(
        self, profile_id: uuid.UUID, *, page: int = 1, limit: int = 20
    ) -> tuple[list[Resume], int]:
        return await self._resumes.list_by_owner(
            Resume.profile_id,
            profile_id,
            page=page,
            limit=limit,
            sort_column=Resume.updated_at,
            sort_desc=True,
        )

    async def update_resume(
        self, resume_id: uuid.UUID, profile_id: uuid.UUID, **values: Any
    ) -> Resume:
        resume = await self.get_owned_resume(resume_id, profile_id)
        template_id = values.get("template_id")
        if template_id is not None:
            template = await self._templates.get_by_id(template_id)
            if template is None or not template.is_active:
                raise ValidationException("Selected template is not available.")
        return await self._resumes.update(resume, **values)

    async def delete_resume(self, resume_id: uuid.UUID, profile_id: uuid.UUID) -> None:
        resume = await self.get_owned_resume(resume_id, profile_id)
        await self._resumes.soft_delete(resume)

    async def get_latest_version(self, resume: Resume) -> ResumeVersion:
        version = await self._versions.get_latest(resume.id)
        if version is None:
            raise ResourceNotFoundException("Resume has no versions.")
        return version

    async def list_versions(
        self, resume: Resume, *, page: int = 1, limit: int = 20
    ) -> tuple[list[ResumeVersion], int]:
        return await self._versions.list_by_resume(resume.id, page=page, limit=limit)

    async def get_version(self, resume: Resume, version_id: uuid.UUID) -> ResumeVersion:
        version = await self._versions.get_by_number(resume.id, version_id)
        if version is None:
            raise ResourceNotFoundException("Resume version not found.")
        return version

    async def create_new_version(self, resume: Resume, content: ResumeContent) -> ResumeVersion:
        await self._validate_item_ownership(resume.profile_id, content)
        latest = await self.get_latest_version(resume)
        return await self._versions.create_version(
            resume.id,
            version_number=latest.version_number + 1,
            content=content.model_dump(mode="json"),
        )

    async def _validate_item_ownership(
        self, profile_id: uuid.UUID, content: ResumeContent
    ) -> None:
        for section in content.sections:
            model = SECTION_MODELS.get(section.section_type)
            if model is None or not section.item_ids:
                continue
            stmt = select(model.id).where(
                model.id.in_(section.item_ids),
                model.profile_id == profile_id,  # type: ignore[attr-defined]
                model.deleted_at.is_(None),
            )
            owned_ids = {row[0] for row in (await self._db.execute(stmt)).all()}
            missing = set(section.item_ids) - owned_ids
            if missing:
                raise ValidationException(
                    f"Invalid {section.section_type.value} item id(s): "
                    f"{', '.join(str(i) for i in missing)}."
                )
