from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
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
from features.cv_import.repository import ImportSessionRepository
from features.cv_import.service import ImportService
from features.profiles.dependencies import get_profile_repository
from features.profiles.repository import ProfileRepository


def get_import_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportSessionRepository:
    return ImportSessionRepository(db)


def get_import_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[ImportSessionRepository, Depends(get_import_session_repository)],
    profile_repository: Annotated[ProfileRepository, Depends(get_profile_repository)],
    prompt_history_repository: Annotated[
        PromptHistoryRepository, Depends(get_prompt_history_repository)
    ],
    generation_history_repository: Annotated[
        GenerationHistoryRepository, Depends(get_generation_history_repository)
    ],
    provider_log_repository: Annotated[
        AIProviderLogRepository, Depends(get_ai_provider_log_repository)
    ],
) -> ImportService:
    return ImportService(
        db,
        settings,
        repository,
        profile_repository,
        prompt_history_repository,
        generation_history_repository,
        provider_log_repository,
    )
