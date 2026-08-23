from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.base_crud import BaseOwnedCrudService, BaseRepository
from app.core.enums import GenerationStatus, ImportSessionStatus, SectionType
from app.core.sorting import SortSpec
from app.exceptions.base import (
    BusinessRuleException,
    ResourceNotFoundException,
    ServiceUnavailableException,
    ValidationException,
)
from features.ai.models import PromptHistory
from features.ai.repository import (
    AIProviderLogRepository,
    GenerationHistoryRepository,
    PromptHistoryRepository,
)
from features.cv_import.classifier import ClassifyOutcome, classify_pdf
from features.cv_import.extraction import validate_pdf_upload
from features.cv_import.models import ImportSession
from features.cv_import.prompts import CLASSIFY_PURPOSE, CLASSIFY_SYSTEM_PROMPT, CLASSIFY_VERSION
from features.cv_import.repository import ImportSessionRepository
from features.cv_import.schemas import ImportConfirmRequest
from features.cv_import.target_schemas import IMPORT_TARGET_SCHEMAS
from features.profiles.models import Profile
from features.profiles.repository import ProfileRepository
from features.resumes.section_registry import SECTION_MODELS


def _serialize_proposed_data(
    bio: str | None, items_by_section: dict[SectionType, list[Any]]
) -> dict[str, Any]:
    return {
        "bio": bio,
        "sections": {
            section_type.value: [item.model_dump(mode="json") for item in items]
            for section_type, items in items_by_section.items()
        },
    }


class ImportService:
    """Upload -> extract -> classify -> stage for review -> confirm-write.
    Nothing reaches the real profile tables except through confirm(), and
    confirm() re-validates every item against the same CreateRequest schema
    the resource's own create endpoint uses -- the staged proposal is never
    trusted as already-valid, even though the classifier validated it once
    on the way in."""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        repository: ImportSessionRepository,
        profile_repository: ProfileRepository,
        prompt_history_repository: PromptHistoryRepository,
        generation_history_repository: GenerationHistoryRepository,
        provider_log_repository: AIProviderLogRepository,
    ) -> None:
        self._db = db
        self._settings = settings
        self._repository = repository
        self._profiles = profile_repository
        self._prompt_history = prompt_history_repository
        self._generation_history = generation_history_repository
        self._provider_logs = provider_log_repository

    async def create_session(
        self, profile: Profile, filename: str | None, content: bytes
    ) -> ImportSession:
        validate_pdf_upload(filename, content, self._settings.max_cv_import_size_mb)
        assert filename is not None  # validated above

        outcome = await classify_pdf(self._settings, content)
        prompt_history = await self._prompt_history.get_or_create(
            CLASSIFY_PURPOSE, CLASSIFY_VERSION, CLASSIFY_SYSTEM_PROMPT
        )

        if outcome.result is None:
            session = await self._repository.create(
                profile_id=profile.id,
                source_filename=filename,
                status=ImportSessionStatus.FAILED,
                proposed_data={},
                error_message=outcome.error_message,
            )
            await self._record_generation(
                profile, prompt_history, GenerationStatus.FAILED, outcome, session.id
            )
            await self._db.commit()
            raise ServiceUnavailableException(
                "AI CV import is temporarily unavailable. Please try again shortly."
            )

        proposed_data = _serialize_proposed_data(
            outcome.result.bio, outcome.result.items_by_section
        )
        session = await self._repository.create(
            profile_id=profile.id,
            source_filename=filename,
            status=ImportSessionStatus.PENDING,
            proposed_data=proposed_data,
        )
        await self._record_generation(
            profile, prompt_history, GenerationStatus.SUCCESS, outcome, session.id
        )
        return session

    async def get_owned_session(self, session_id: Any, profile_id: Any) -> ImportSession:
        session = await self._repository.get_by_id(session_id)
        if session is None or session.profile_id != profile_id:
            raise ResourceNotFoundException("Import session not found.")
        return session

    async def list_sessions(
        self, profile_id: Any, *, page: int, limit: int, sort_columns: SortSpec
    ) -> tuple[list[ImportSession], int]:
        return await self._repository.list_by_owner(
            ImportSession.profile_id,
            profile_id,
            page=page,
            limit=limit,
            sort_columns=sort_columns,
        )

    async def confirm(
        self, session: ImportSession, profile: Profile, payload: ImportConfirmRequest
    ) -> tuple[dict[str, int], bool]:
        if session.status != ImportSessionStatus.PENDING:
            raise BusinessRuleException("This import has already been reviewed.")

        created_counts: dict[str, int] = {}
        for section_key, raw_items in payload.sections.items():
            try:
                section_type = SectionType(section_key)
            except ValueError as exc:
                raise ValidationException(f"Unknown section '{section_key}'.") from exc
            schema = IMPORT_TARGET_SCHEMAS.get(section_type)
            model = SECTION_MODELS.get(section_type)
            if schema is None or model is None:
                raise ValidationException(f"Section '{section_key}' is not importable.")

            write_service: BaseOwnedCrudService[Any] = BaseOwnedCrudService(
                BaseRepository(self._db, model),
                model.profile_id,  # type: ignore[attr-defined]
                f"{section_key} not found.",
            )
            count = 0
            for raw_item in raw_items:
                validated = _validate_item(schema, section_key, raw_item)
                values = validated.model_dump(exclude={"skill_ids"})
                if section_type is SectionType.PROJECTS:
                    values["skills"] = []
                await write_service.create_owned(profile.id, **values)
                count += 1
            created_counts[section_key] = count

        profile_bio_updated = False
        if payload.bio and not profile.bio:
            await self._profiles.update(profile, bio=payload.bio)
            profile_bio_updated = True

        session.status = ImportSessionStatus.CONFIRMED
        await self._db.flush()
        return created_counts, profile_bio_updated

    async def reject(self, session: ImportSession) -> None:
        if session.status != ImportSessionStatus.PENDING:
            raise BusinessRuleException("This import has already been reviewed.")
        session.status = ImportSessionStatus.REJECTED
        await self._db.flush()

    async def delete(self, session: ImportSession) -> None:
        await self._repository.soft_delete(session)

    async def _record_generation(
        self,
        profile: Profile,
        prompt_history: PromptHistory,
        status: GenerationStatus,
        outcome: ClassifyOutcome,
        import_session_id: Any,
    ) -> None:
        generation = await self._generation_history.create(
            profile_id=profile.id,
            import_session_id=import_session_id,
            prompt_history_id=prompt_history.id,
            status=status,
            provider=outcome.provider or "none",
            model=outcome.attempt_logs[-1]["model"] if outcome.attempt_logs else "",
            error_message=outcome.error_message,
        )
        for log in outcome.attempt_logs:
            await self._provider_logs.create(generation_history_id=generation.id, **log)


def _validate_item(
    schema: type[BaseModel], section_key: str, raw_item: dict[str, Any]
) -> BaseModel:
    try:
        return schema.model_validate(raw_item)
    except ValidationError as exc:
        raise ValidationException(f"Invalid {section_key} item: {exc}") from exc
