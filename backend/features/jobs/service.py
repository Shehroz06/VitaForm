import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ResourceNotFoundException
from features.education.models import Education
from features.experience.models import Experience
from features.jobs.analyzer import analyze_job_description
from features.jobs.ats_scorer import compute_ats_score
from features.jobs.models import AtsScore, JobDescription
from features.jobs.repository import AtsScoreRepository, CompanyRepository, JobDescriptionRepository
from features.jobs.schemas import JobAnalysis, JobDescriptionCreateRequest
from features.profiles.models import Profile
from features.projects.models import Project
from features.skills.models import Skill


class JobService:
    def __init__(
        self,
        job_repository: JobDescriptionRepository,
        company_repository: CompanyRepository,
    ) -> None:
        self._jobs = job_repository
        self._companies = company_repository

    async def create_job(
        self, profile_id: uuid.UUID, data: JobDescriptionCreateRequest
    ) -> JobDescription:
        raw_text_hash = hashlib.sha256(data.raw_text.encode("utf-8")).hexdigest()
        existing = await self._jobs.get_by_hash(profile_id, raw_text_hash)
        if existing is not None:
            # Resubmitting the exact same JD text is a no-op, not a new
            # posting -- return the saved analysis instead of duplicating it.
            return existing

        company = None
        if data.company_name:
            company = await self._companies.get_or_create_by_name(profile_id, data.company_name)

        analysis = analyze_job_description(data.raw_text)
        job = await self._jobs.create(
            profile_id=profile_id,
            company_id=company.id if company else None,
            title=data.title,
            raw_text=data.raw_text,
            raw_text_hash=raw_text_hash,
            location=data.location,
            employment_type=data.employment_type,
            keywords=analysis.keywords,
            required_skills=analysis.required_skills,
            preferred_skills=analysis.preferred_skills,
        )
        # Set the relationship in memory rather than re-querying: avoids an
        # async lazy-load (which would raise) when the router reads
        # job.company right after creation.
        job.company = company
        return job

    async def get_owned_job(self, job_id: uuid.UUID, profile_id: uuid.UUID) -> JobDescription:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.profile_id != profile_id:
            raise ResourceNotFoundException("Job description not found.")
        return job

    async def list_jobs(
        self, profile_id: uuid.UUID, *, page: int = 1, limit: int = 20
    ) -> tuple[list[JobDescription], int]:
        return await self._jobs.list_by_owner(
            JobDescription.profile_id,
            profile_id,
            page=page,
            limit=limit,
            sort_column=JobDescription.created_at,
            sort_desc=True,
        )

    async def delete_job(self, job_id: uuid.UUID, profile_id: uuid.UUID) -> None:
        job = await self.get_owned_job(job_id, profile_id)
        await self._jobs.soft_delete(job)


class AtsScoringService:
    """Computes an ATS match score for a saved job description against the
    caller's current profile -- rules-based (keyword coverage), no AI call,
    same philosophy as the ranking engine in Phase 6."""

    def __init__(self, db: AsyncSession, score_repository: AtsScoreRepository) -> None:
        self._db = db
        self._scores = score_repository

    async def score_job(self, job: JobDescription, profile: Profile) -> AtsScore:
        skill_names, profile_text = await self._gather_profile_text(profile)
        analysis_input = _job_to_analysis(job)
        result = compute_ats_score(analysis_input, skill_names, profile_text)

        return await self._scores.create(
            profile_id=profile.id,
            job_description_id=job.id,
            overall_score=result.overall_score,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            recommendations=result.recommendations,
        )

    async def get_latest_score(
        self, job_id: uuid.UUID, profile_id: uuid.UUID
    ) -> AtsScore | None:
        return await self._scores.get_latest_for_job(job_id, profile_id)

    async def _gather_profile_text(self, profile: Profile) -> tuple[set[str], str]:
        skills = (
            await self._db.execute(
                select(Skill.name).where(
                    Skill.profile_id == profile.id, Skill.deleted_at.is_(None)
                )
            )
        ).scalars().all()

        experiences = (
            await self._db.execute(
                select(Experience.job_title, Experience.description).where(
                    Experience.profile_id == profile.id, Experience.deleted_at.is_(None)
                )
            )
        ).all()

        projects = (
            await self._db.execute(
                select(Project.title, Project.description).where(
                    Project.profile_id == profile.id, Project.deleted_at.is_(None)
                )
            )
        ).all()

        education = (
            await self._db.execute(
                select(Education.degree, Education.field_of_study, Education.description).where(
                    Education.profile_id == profile.id, Education.deleted_at.is_(None)
                )
            )
        ).all()

        text_parts: list[str] = [profile.headline or "", profile.bio or ""]
        for experience_row in experiences:
            text_parts.extend(value for value in experience_row if value)
        for project_row in projects:
            text_parts.extend(value for value in project_row if value)
        for education_row in education:
            text_parts.extend(value for value in education_row if value)

        return set(skills), " ".join(text_parts)


def _job_to_analysis(job: JobDescription) -> JobAnalysis:
    return JobAnalysis(
        keywords=job.keywords,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
    )
