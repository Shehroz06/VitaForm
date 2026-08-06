from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from features.jobs.repository import AtsScoreRepository, CompanyRepository, JobDescriptionRepository
from features.jobs.service import AtsScoringService, JobService


def get_company_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> CompanyRepository:
    return CompanyRepository(db)


def get_job_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobDescriptionRepository:
    return JobDescriptionRepository(db)


def get_ats_score_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AtsScoreRepository:
    return AtsScoreRepository(db)


def get_job_service(
    job_repository: Annotated[JobDescriptionRepository, Depends(get_job_repository)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> JobService:
    return JobService(job_repository, company_repository)


def get_ats_scoring_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    score_repository: Annotated[AtsScoreRepository, Depends(get_ats_score_repository)],
) -> AtsScoringService:
    return AtsScoringService(db, score_repository)
