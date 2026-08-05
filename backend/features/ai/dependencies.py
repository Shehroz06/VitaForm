from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.session import get_db
from features.ai.repository import (
    AIProviderLogRepository,
    GenerationHistoryRepository,
    PromptHistoryRepository,
)
from features.ai.service import GenerationService
from features.files.dependencies import get_file_upload_service
from features.files.service import FileUploadService
from features.resumes.dependencies import (
    get_resume_service,
    get_resume_template_repository,
    get_resume_version_repository,
)
from features.resumes.export_service import ResumeExportService
from features.resumes.renderer import ResumeRenderer
from features.resumes.repository import ResumeTemplateRepository, ResumeVersionRepository
from features.resumes.service import ResumeService


def get_prompt_history_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PromptHistoryRepository:
    return PromptHistoryRepository(db)


def get_generation_history_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GenerationHistoryRepository:
    return GenerationHistoryRepository(db)


def get_ai_provider_log_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIProviderLogRepository:
    return AIProviderLogRepository(db)


def get_generation_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    resume_service: Annotated[ResumeService, Depends(get_resume_service)],
    version_repository: Annotated[ResumeVersionRepository, Depends(get_resume_version_repository)],
    template_repository: Annotated[
        ResumeTemplateRepository, Depends(get_resume_template_repository)
    ],
    file_service: Annotated[FileUploadService, Depends(get_file_upload_service)],
    prompt_history_repository: Annotated[
        PromptHistoryRepository, Depends(get_prompt_history_repository)
    ],
    generation_history_repository: Annotated[
        GenerationHistoryRepository, Depends(get_generation_history_repository)
    ],
    provider_log_repository: Annotated[
        AIProviderLogRepository, Depends(get_ai_provider_log_repository)
    ],
) -> GenerationService:
    export_service = ResumeExportService(
        ResumeRenderer(db), version_repository, template_repository, file_service
    )
    return GenerationService(
        db,
        settings,
        resume_service,
        export_service,
        prompt_history_repository,
        generation_history_repository,
        provider_log_repository,
    )
