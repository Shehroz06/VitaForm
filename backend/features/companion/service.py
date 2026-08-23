from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.enums import GenerationStatus
from app.exceptions.base import ResourceNotFoundException, ServiceUnavailableException
from features.ai.candidates import load_candidate_items
from features.ai.context_builder import build_candidates
from features.ai.models import PromptHistory
from features.ai.provider_runner import run_with_fallback
from features.ai.ranking import extract_keywords, rank_and_select
from features.ai.repository import (
    AIProviderLogRepository,
    GenerationHistoryRepository,
    PromptHistoryRepository,
)
from features.companion.models import CoverLetter, LinkedinGeneration
from features.companion.prompts import (
    COVER_LETTER_PURPOSE,
    COVER_LETTER_SYSTEM_PROMPT,
    COVER_LETTER_TEMPERATURE,
    COVER_LETTER_VERSION,
    LINKEDIN_PURPOSE,
    LINKEDIN_SYSTEM_PROMPT,
    LINKEDIN_TEMPERATURE,
    LINKEDIN_VERSION,
    build_cover_letter_prompt,
    build_linkedin_prompt,
)
from features.companion.repository import CoverLetterRepository, LinkedinGenerationRepository
from features.companion.schemas import GenerateCoverLetterRequest, GenerateLinkedinRequest
from features.companion.validator import validate_cover_letter_response, validate_linkedin_response
from features.jobs.repository import JobDescriptionRepository
from features.profiles.models import Profile

_MAX_OUTPUT_TOKENS = 1500


class CompanionService:
    """Cover letter and LinkedIn generation. Reuses the exact same ranking,
    candidate-selection, and retry/fallback machinery as Phase 6's resume
    generator -- only the prompt and the persisted document type differ."""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        cover_letter_repository: CoverLetterRepository,
        linkedin_repository: LinkedinGenerationRepository,
        job_repository: JobDescriptionRepository,
        prompt_history_repository: PromptHistoryRepository,
        generation_history_repository: GenerationHistoryRepository,
        provider_log_repository: AIProviderLogRepository,
    ) -> None:
        self._db = db
        self._settings = settings
        self._cover_letters = cover_letter_repository
        self._linkedin = linkedin_repository
        self._jobs = job_repository
        self._prompt_history = prompt_history_repository
        self._generation_history = generation_history_repository
        self._provider_logs = provider_log_repository

    async def generate_cover_letter(
        self, profile: Profile, request: GenerateCoverLetterRequest
    ) -> CoverLetter:
        job_description_text = request.job_description_text
        job_description_id = request.job_description_id
        if job_description_id is not None:
            job = await self._jobs.get_by_id(job_description_id)
            if job is None or job.profile_id != profile.id:
                raise ResourceNotFoundException("Job description not found.")
            job_description_text = job_description_text or job.raw_text

        items_by_type = await load_candidate_items(self._db, profile.id)
        keywords = extract_keywords(
            job_description_text or f"{request.role_title} {request.company_name}"
        )
        ranked = rank_and_select(items_by_type, keywords)
        candidates_by_type = build_candidates(ranked)

        user_prompt = build_cover_letter_prompt(
            company_name=request.company_name,
            role_title=request.role_title,
            hiring_manager=request.hiring_manager,
            job_description=job_description_text,
            candidates_by_type=candidates_by_type,
        )
        prompt_history = await self._prompt_history.get_or_create(
            COVER_LETTER_PURPOSE, COVER_LETTER_VERSION, COVER_LETTER_SYSTEM_PROMPT
        )

        run_result = await run_with_fallback(
            self._settings,
            COVER_LETTER_SYSTEM_PROMPT,
            user_prompt,
            temperature=COVER_LETTER_TEMPERATURE,
            max_tokens=_MAX_OUTPUT_TOKENS,
            validate=lambda text: validate_cover_letter_response(text, user_prompt),
        )

        if run_result.value is None:
            await self._record_generation(
                profile,
                prompt_history,
                GenerationStatus.FAILED,
                run_result.provider,
                run_result.error_message,
                run_result.attempt_logs,
            )
            await self._db.commit()
            raise ServiceUnavailableException(
                "AI cover letter generation is temporarily unavailable. Please try again shortly."
            )

        cover_letter = await self._cover_letters.create(
            profile_id=profile.id,
            job_description_id=job_description_id,
            company_name=request.company_name,
            role_title=request.role_title,
            hiring_manager=request.hiring_manager,
            body=run_result.value.cover_letter,
        )
        await self._record_generation(
            profile,
            prompt_history,
            GenerationStatus.SUCCESS,
            run_result.provider,
            None,
            run_result.attempt_logs,
            cover_letter_id=cover_letter.id,
        )
        return cover_letter

    async def generate_linkedin(
        self, profile: Profile, request: GenerateLinkedinRequest
    ) -> LinkedinGeneration:
        items_by_type = await load_candidate_items(self._db, profile.id)
        keywords = extract_keywords(request.target_role or "")
        ranked = rank_and_select(items_by_type, keywords)
        candidates_by_type = build_candidates(ranked)

        user_prompt = build_linkedin_prompt(
            target_role=request.target_role, candidates_by_type=candidates_by_type
        )
        prompt_history = await self._prompt_history.get_or_create(
            LINKEDIN_PURPOSE, LINKEDIN_VERSION, LINKEDIN_SYSTEM_PROMPT
        )

        run_result = await run_with_fallback(
            self._settings,
            LINKEDIN_SYSTEM_PROMPT,
            user_prompt,
            temperature=LINKEDIN_TEMPERATURE,
            max_tokens=_MAX_OUTPUT_TOKENS,
            validate=lambda text: validate_linkedin_response(text, user_prompt),
        )

        if run_result.value is None:
            await self._record_generation(
                profile,
                prompt_history,
                GenerationStatus.FAILED,
                run_result.provider,
                run_result.error_message,
                run_result.attempt_logs,
            )
            await self._db.commit()
            raise ServiceUnavailableException(
                "AI LinkedIn generation is temporarily unavailable. Please try again shortly."
            )

        linkedin_generation = await self._linkedin.create(
            profile_id=profile.id,
            target_role=request.target_role,
            headline=run_result.value.headline,
            about=run_result.value.about,
        )
        await self._record_generation(
            profile,
            prompt_history,
            GenerationStatus.SUCCESS,
            run_result.provider,
            None,
            run_result.attempt_logs,
            linkedin_generation_id=linkedin_generation.id,
        )
        return linkedin_generation

    async def _record_generation(
        self,
        profile: Profile,
        prompt_history: PromptHistory,
        status: GenerationStatus,
        provider: str | None,
        error_message: str | None,
        attempt_logs: list[dict[str, Any]],
        *,
        cover_letter_id: Any | None = None,
        linkedin_generation_id: Any | None = None,
    ) -> None:
        generation = await self._generation_history.create(
            profile_id=profile.id,
            cover_letter_id=cover_letter_id,
            linkedin_generation_id=linkedin_generation_id,
            prompt_history_id=prompt_history.id,
            status=status,
            provider=provider or "none",
            model=attempt_logs[-1]["model"] if attempt_logs else "",
            error_message=error_message,
        )
        for log in attempt_logs:
            await self._provider_logs.create(generation_history_id=generation.id, **log)
