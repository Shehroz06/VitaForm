import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import Settings
from app.core.ai_provider import ProviderNotConfiguredError, build_provider
from app.core.enums import GenerationStatus, SectionType
from app.exceptions.base import BusinessRuleException
from features.ai.context_builder import build_candidates
from features.ai.prompts import (
    RESUME_GENERATION_PURPOSE,
    RESUME_GENERATION_SYSTEM_PROMPT,
    RESUME_GENERATION_VERSION,
    build_resume_generation_prompt,
)
from features.ai.ranking import extract_keywords, rank_and_select
from features.ai.repository import (
    AIProviderLogRepository,
    GenerationHistoryRepository,
    PromptHistoryRepository,
)
from features.ai.schemas import AIResumeResponse, ResumeGenerateRequest
from features.ai.validator import AIResponseValidationError, validate_ai_response
from features.profiles.models import Profile
from features.projects.models import Project
from features.resumes.export_service import ResumeExportService
from features.resumes.models import Resume, ResumeVersion
from features.resumes.schemas import ContactVisibility, ResumeContent, ResumeSection
from features.resumes.section_registry import SECTION_MODELS
from features.resumes.service import ResumeService

_RESUME_TEMPERATURE = 0.2
_MAX_OUTPUT_TOKENS = 2000
_RESUME_SECTION_ORDER = [
    SectionType.SUMMARY,
    SectionType.EDUCATION,
    SectionType.EXPERIENCE,
    SectionType.PROJECTS,
    SectionType.SKILLS,
    SectionType.CERTIFICATIONS,
    SectionType.ACHIEVEMENTS,
    SectionType.AWARDS,
]


class GenerationService:
    """Orchestrates the full AI resume pipeline: load -> rank -> build
    context -> prompt -> provider (with retry + fallback) -> validate ->
    map into the existing Phase 5 ResumeContent shape -> render -> PDF.

    The AI never supplies factual content -- only which existing items to
    include and a synthesized summary. Phase 5's renderer re-resolves every
    item from the database at render time, so nothing the AI writes can end
    up in the rendered PDF except a selection of real, owned records."""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        resume_service: ResumeService,
        export_service: ResumeExportService,
        prompt_history_repository: PromptHistoryRepository,
        generation_history_repository: GenerationHistoryRepository,
        provider_log_repository: AIProviderLogRepository,
    ) -> None:
        self._db = db
        self._settings = settings
        self._resume_service = resume_service
        self._export_service = export_service
        self._prompt_history = prompt_history_repository
        self._generation_history = generation_history_repository
        self._provider_logs = provider_log_repository

    async def generate_resume(
        self, profile: Profile, user_email: str, request: ResumeGenerateRequest
    ) -> ResumeVersion:
        items_by_type = await self._load_candidate_items(profile.id)
        keywords = extract_keywords(request.job_description)
        ranked = rank_and_select(items_by_type, keywords)
        candidates_by_type = build_candidates(ranked)
        candidate_ids_by_section = {
            section_type: {c.id for c in candidates}
            for section_type, candidates in candidates_by_type.items()
        }

        user_prompt = build_resume_generation_prompt(
            job_description=request.job_description,
            target_role=request.target_role,
            target_company=request.target_company,
            candidates_by_type=candidates_by_type,
        )
        prompt_history = await self._prompt_history.get_or_create(
            RESUME_GENERATION_PURPOSE, RESUME_GENERATION_VERSION, RESUME_GENERATION_SYSTEM_PROMPT
        )

        ai_response, used_provider, attempt_logs, error_message = await self._run_provider_attempts(
            user_prompt, candidate_ids_by_section
        )

        if ai_response is None:
            await self._record_generation(
                None, profile, prompt_history, GenerationStatus.FAILED, None, None, error_message,
                attempt_logs,
            )
            # Commit the failure log explicitly: the exception raised below
            # triggers a rollback in get_db's error handling, which would
            # otherwise discard the very audit trail this call just wrote.
            await self._db.commit()
            raise BusinessRuleException(
                "AI resume generation is temporarily unavailable. Please try again shortly."
            )

        content = self._to_resume_content(ai_response)
        title = request.title or (
            f"AI Resume — {request.target_role or request.target_company or 'Untitled'}"
        )
        resume = await self._resume_service.create_resume(
            profile.id, title, request.template_id, content
        )
        version = await self._resume_service.get_latest_version(resume)

        await self._record_generation(
            resume, profile, prompt_history, GenerationStatus.SUCCESS, version, used_provider,
            None, attempt_logs,
        )
        await self._export_service.export(resume, version, profile, user_email)
        return version

    async def _load_candidate_items(self, profile_id: uuid.UUID) -> dict[SectionType, list[Any]]:
        result: dict[SectionType, list[Any]] = {}
        for section_type, model in SECTION_MODELS.items():
            stmt = select(model).where(
                model.profile_id == profile_id,  # type: ignore[attr-defined]
                model.deleted_at.is_(None),
            )
            if model is Project:
                stmt = stmt.options(selectinload(Project.skills))
            items = (await self._db.execute(stmt)).scalars().all()
            result[section_type] = list(items)
        return result

    def _provider_order(self) -> list[str]:
        order = [self._settings.ai_default_provider]
        for name in self._settings.ai_fallback_providers:
            if name not in order:
                order.append(name)
        return order

    async def _run_provider_attempts(
        self, user_prompt: str, candidate_ids_by_section: dict[SectionType, set[uuid.UUID]]
    ) -> tuple[AIResumeResponse | None, str | None, list[dict[str, Any]], str | None]:
        attempt_logs: list[dict[str, Any]] = []
        error_message: str | None = None

        for provider_name in self._provider_order():
            try:
                provider = build_provider(provider_name, self._settings)
            except ProviderNotConfiguredError as exc:
                error_message = str(exc)
                continue

            for attempt in range(self._settings.ai_max_retries + 1):
                try:
                    result = await provider.generate(
                        RESUME_GENERATION_SYSTEM_PROMPT,
                        user_prompt,
                        temperature=_RESUME_TEMPERATURE,
                        max_tokens=_MAX_OUTPUT_TOKENS,
                    )
                    ai_response = validate_ai_response(result.text, candidate_ids_by_section)
                except (AIResponseValidationError, Exception) as exc:  # noqa: BLE001
                    error_message = str(exc)[:2000]
                    attempt_logs.append(
                        {
                            "provider": provider_name,
                            "model": getattr(provider, "model", ""),
                            "latency_ms": 0,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "retry_attempt": attempt,
                            "success": False,
                            "error_message": error_message,
                        }
                    )
                    continue
                else:
                    attempt_logs.append(
                        {
                            "provider": result.provider,
                            "model": result.model,
                            "latency_ms": result.latency_ms,
                            "prompt_tokens": result.prompt_tokens,
                            "completion_tokens": result.completion_tokens,
                            "retry_attempt": attempt,
                            "success": True,
                            "error_message": None,
                        }
                    )
                    return ai_response, provider_name, attempt_logs, None

        return None, None, attempt_logs, error_message

    async def _record_generation(
        self,
        resume: Resume | None,
        profile: Profile,
        prompt_history: Any,
        status: GenerationStatus,
        version: ResumeVersion | None,
        provider: str | None,
        error_message: str | None,
        attempt_logs: list[dict[str, Any]],
    ) -> None:
        generation = await self._generation_history.create(
            profile_id=profile.id,
            resume_id=resume.id if resume else None,
            resume_version_id=version.id if version else None,
            prompt_history_id=prompt_history.id,
            status=status,
            provider=provider or "none",
            model=attempt_logs[-1]["model"] if attempt_logs else "",
            error_message=error_message,
        )
        for log in attempt_logs:
            await self._provider_logs.create(generation_history_id=generation.id, **log)

    def _to_resume_content(self, ai_response: AIResumeResponse) -> ResumeContent:
        by_type = {section.section_type: section for section in ai_response.sections}
        sections = []
        for section_type in _RESUME_SECTION_ORDER:
            if section_type is SectionType.SUMMARY:
                sections.append(
                    ResumeSection(
                        section_type=SectionType.SUMMARY, custom_title=None, visible=True,
                        item_ids=[],
                    )
                )
                continue
            ai_section = by_type.get(section_type)
            item_ids = ai_section.item_ids if ai_section else []
            sections.append(
                ResumeSection(
                    section_type=section_type,
                    custom_title=None,
                    visible=bool(item_ids),
                    item_ids=item_ids,
                )
            )
        return ResumeContent(
            summary=ai_response.summary,
            contact_visibility=ContactVisibility(),
            sections=sections,
        )
