import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sorting import SortSpec
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
            await self._reconcile_item_ids(profile_id, content)

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
        self, profile_id: uuid.UUID, *, page: int = 1, limit: int = 20, sort_columns: SortSpec
    ) -> tuple[list[Resume], int]:
        return await self._resumes.list_by_owner(
            Resume.profile_id,
            profile_id,
            page=page,
            limit=limit,
            sort_columns=sort_columns,
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

    async def get_latest_versions_by_resume(
        self, resume_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ResumeVersion]:
        return await self._versions.get_latest_for_resumes(resume_ids)

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
        await self._reconcile_item_ids(resume.profile_id, content)
        latest = await self.get_latest_version(resume)
        return await self._versions.create_version(
            resume.id,
            version_number=latest.version_number + 1,
            content=content.model_dump(mode="json"),
        )

    async def autosave_content(self, resume: Resume, content: ResumeContent) -> ResumeVersion:
        """Updates the current (latest) version's content in place -- no new
        version_number, unlike create_new_version. Keeps the persisted
        content honest against whatever's on screen between explicit Saves,
        so Export always renders what the user actually sees rather than a
        stale, previously-saved snapshot."""
        await self._reconcile_item_ids(resume.profile_id, content)
        latest = await self.get_latest_version(resume)
        return await self._versions.update(latest, content=content.model_dump(mode="json"))

    async def _reconcile_item_ids(self, profile_id: uuid.UUID, content: ResumeContent) -> None:
        """Two different things can make a `section.item_ids` entry not
        resolve, and they need different responses:

        - An id that never belonged to this profile at all (forged, or from
          another profile) is a real data-integrity error -- reject the
          whole save, same as before.
        - An id that belonged to this profile but was soft-deleted since the
          resume was last saved is just a stale reference. renderer.py
          already handles this at render time by silently omitting the
          missing item (see its `if item_id in by_id` filter) -- without
          mirroring that here, a resume in this state renders fine but can
          never be saved again, permanently blocking the user from editing
          it. Pruned instead of rejected, mutating `content` in place so the
          caller's subsequent `model_dump` reflects the cleaned-up ids.
        """
        for section in content.sections:
            model = SECTION_MODELS.get(section.section_type)
            if model is None or not section.item_ids:
                continue
            stmt = select(model.id, model.deleted_at).where(
                model.id.in_(section.item_ids),
                model.profile_id == profile_id,  # type: ignore[attr-defined]
            )
            rows = (await self._db.execute(stmt)).all()
            owned_ids = {row[0] for row in rows}
            live_ids = {row[0] for row in rows if row[1] is None}

            forged = set(section.item_ids) - owned_ids
            if forged:
                raise ValidationException(
                    f"Invalid {section.section_type.value} item id(s): "
                    f"{', '.join(str(i) for i in forged)}."
                )

            section.item_ids = [item_id for item_id in section.item_ids if item_id in live_ids]
