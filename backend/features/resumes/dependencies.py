from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from features.files.dependencies import get_file_upload_service
from features.files.service import FileUploadService
from features.resumes.export_service import ResumeExportService
from features.resumes.renderer import ResumeRenderer
from features.resumes.repository import (
    ResumeRepository,
    ResumeTemplateRepository,
    ResumeVersionRepository,
)
from features.resumes.service import ResumeService


def get_resume_template_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeTemplateRepository:
    return ResumeTemplateRepository(db)


def get_resume_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ResumeRepository:
    return ResumeRepository(db)


def get_resume_version_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeVersionRepository:
    return ResumeVersionRepository(db)


def get_resume_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    resume_repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    version_repository: Annotated[ResumeVersionRepository, Depends(get_resume_version_repository)],
    template_repository: Annotated[
        ResumeTemplateRepository, Depends(get_resume_template_repository)
    ],
) -> ResumeService:
    return ResumeService(db, resume_repository, version_repository, template_repository)


def get_resume_renderer(db: Annotated[AsyncSession, Depends(get_db)]) -> ResumeRenderer:
    return ResumeRenderer(db)


def get_resume_export_service(
    renderer: Annotated[ResumeRenderer, Depends(get_resume_renderer)],
    version_repository: Annotated[ResumeVersionRepository, Depends(get_resume_version_repository)],
    template_repository: Annotated[
        ResumeTemplateRepository, Depends(get_resume_template_repository)
    ],
    file_service: Annotated[FileUploadService, Depends(get_file_upload_service)],
) -> ResumeExportService:
    return ResumeExportService(renderer, version_repository, template_repository, file_service)
