from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.ai.dependencies import (
    get_ai_provider_log_repository,
    get_generation_history_repository,
    get_prompt_history_repository,
)
from features.ai.repository import (
    AIProviderLogRepository,
    GenerationHistoryRepository,
    PromptHistoryRepository,
)
from features.companion.models import CoverLetter, LinkedinGeneration
from features.companion.repository import CoverLetterRepository, LinkedinGenerationRepository
from features.companion.service import CompanionService
from features.jobs.dependencies import get_job_repository
from features.jobs.repository import JobDescriptionRepository


def get_cover_letter_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CoverLetterRepository:
    return CoverLetterRepository(db)


def get_linkedin_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LinkedinGenerationRepository:
    return LinkedinGenerationRepository(db)


def get_cover_letter_crud_service(
    repository: Annotated[CoverLetterRepository, Depends(get_cover_letter_repository)],
) -> BaseOwnedCrudService[CoverLetter]:
    return BaseOwnedCrudService(repository, CoverLetter.profile_id, "Cover letter not found.")


def get_linkedin_crud_service(
    repository: Annotated[LinkedinGenerationRepository, Depends(get_linkedin_repository)],
) -> BaseOwnedCrudService[LinkedinGeneration]:
    return BaseOwnedCrudService(
        repository, LinkedinGeneration.profile_id, "LinkedIn generation not found."
    )


def get_companion_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    cover_letter_repository: Annotated[CoverLetterRepository, Depends(get_cover_letter_repository)],
    linkedin_repository: Annotated[LinkedinGenerationRepository, Depends(get_linkedin_repository)],
    job_repository: Annotated[JobDescriptionRepository, Depends(get_job_repository)],
    prompt_history_repository: Annotated[
        PromptHistoryRepository, Depends(get_prompt_history_repository)
    ],
    generation_history_repository: Annotated[
        GenerationHistoryRepository, Depends(get_generation_history_repository)
    ],
    provider_log_repository: Annotated[
        AIProviderLogRepository, Depends(get_ai_provider_log_repository)
    ],
) -> CompanionService:
    return CompanionService(
        db,
        settings,
        cover_letter_repository,
        linkedin_repository,
        job_repository,
        prompt_history_repository,
        generation_history_repository,
        provider_log_repository,
    )
