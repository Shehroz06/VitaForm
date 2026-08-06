import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.exceptions.base import ResourceNotFoundException
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.jobs.analyzer import analyze_job_description
from features.jobs.dependencies import get_ats_scoring_service, get_job_service
from features.jobs.models import JobDescription
from features.jobs.schemas import (
    AnalyzeJobRequest,
    AtsScoreResponse,
    JobAnalysis,
    JobDescriptionCreateRequest,
    JobDescriptionResponse,
)
from features.jobs.service import AtsScoringService, JobService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(tags=["jobs"])

JobServiceDep = Annotated[JobService, Depends(get_job_service)]
AtsScoringServiceDep = Annotated[AtsScoringService, Depends(get_ats_scoring_service)]


def _to_job_response(job: JobDescription) -> JobDescriptionResponse:
    return JobDescriptionResponse(
        id=job.id,
        title=job.title,
        raw_text=job.raw_text,
        location=job.location,
        employment_type=job.employment_type,
        company_id=job.company_id,
        company_name=job.company.name if job.company else None,
        keywords=job.keywords,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/jobs/analyze", response_model=SuccessResponse[JobAnalysis])
async def analyze_job(
    data: AnalyzeJobRequest, profile: CurrentProfile
) -> SuccessResponse[JobAnalysis]:
    analysis = analyze_job_description(data.raw_text)
    return SuccessResponse(message="Job description analyzed successfully.", data=analysis)


@router.get("/jobs", response_model=SuccessResponse[list[JobDescriptionResponse]])
async def list_jobs(
    profile: CurrentProfile,
    service: JobServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[JobDescriptionResponse]]:
    items, total = await service.list_jobs(
        profile.id, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Job descriptions retrieved successfully.",
        data=[_to_job_response(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "/jobs",
    response_model=SuccessResponse[JobDescriptionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    data: JobDescriptionCreateRequest, profile: CurrentProfile, service: JobServiceDep
) -> SuccessResponse[JobDescriptionResponse]:
    job = await service.create_job(profile.id, data)
    return SuccessResponse(
        message="Job description saved successfully.",
        data=_to_job_response(job),
    )


@router.get("/jobs/{job_id}", response_model=SuccessResponse[JobDescriptionResponse])
async def get_job(
    job_id: uuid.UUID, profile: CurrentProfile, service: JobServiceDep
) -> SuccessResponse[JobDescriptionResponse]:
    job = await service.get_owned_job(job_id, profile.id)
    return SuccessResponse(
        message="Job description retrieved successfully.",
        data=_to_job_response(job),
    )


@router.delete("/jobs/{job_id}", response_model=SuccessResponse[MessageResponse])
async def delete_job(
    job_id: uuid.UUID, profile: CurrentProfile, service: JobServiceDep
) -> SuccessResponse[MessageResponse]:
    await service.delete_job(job_id, profile.id)
    return SuccessResponse(
        message="Job description deleted successfully.", data=MessageResponse(message="Deleted.")
    )


@router.post("/jobs/{job_id}/ats-score", response_model=SuccessResponse[AtsScoreResponse])
async def compute_ats_score_endpoint(
    job_id: uuid.UUID,
    profile: CurrentProfile,
    service: JobServiceDep,
    scoring_service: AtsScoringServiceDep,
) -> SuccessResponse[AtsScoreResponse]:
    job = await service.get_owned_job(job_id, profile.id)
    score = await scoring_service.score_job(job, profile)
    return SuccessResponse(
        message="ATS score computed successfully.", data=AtsScoreResponse.model_validate(score)
    )


@router.get("/jobs/{job_id}/ats-score", response_model=SuccessResponse[AtsScoreResponse])
async def get_latest_ats_score(
    job_id: uuid.UUID,
    profile: CurrentProfile,
    service: JobServiceDep,
    scoring_service: AtsScoringServiceDep,
) -> SuccessResponse[AtsScoreResponse]:
    await service.get_owned_job(job_id, profile.id)
    score = await scoring_service.get_latest_score(job_id, profile.id)
    if score is None:
        raise ResourceNotFoundException("No ATS score has been computed for this job yet.")
    return SuccessResponse(
        message="ATS score retrieved successfully.", data=AtsScoreResponse.model_validate(score)
    )
