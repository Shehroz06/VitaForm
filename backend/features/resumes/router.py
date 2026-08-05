import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import CurrentUser
from app.exceptions.base import ResourceNotFoundException
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.files.dependencies import get_file_repository
from features.files.repository import FileRepository
from features.files.schemas import FileResponse as FileAttachmentResponse
from features.profiles.dependencies import CurrentProfile
from features.resumes.dependencies import (
    get_resume_export_service,
    get_resume_service,
    get_resume_template_repository,
)
from features.resumes.export_service import ResumeExportService
from features.resumes.models import Resume
from features.resumes.repository import ResumeTemplateRepository
from features.resumes.schemas import (
    ResumeContent,
    ResumeCreateRequest,
    ResumeResponse,
    ResumeTemplateResponse,
    ResumeUpdateRequest,
    ResumeVersionResponse,
    ResumeVersionSummaryResponse,
)
from features.resumes.service import ResumeService

router = APIRouter(tags=["resumes"])

ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]
ResumeExportServiceDep = Annotated[ResumeExportService, Depends(get_resume_export_service)]
ResumeTemplateRepositoryDep = Annotated[
    ResumeTemplateRepository, Depends(get_resume_template_repository)
]


async def _to_resume_response(resume: Resume, service: ResumeService) -> ResumeResponse:
    latest = await service.get_latest_version(resume)
    return ResumeResponse(
        id=resume.id,
        title=resume.title,
        template_id=resume.template_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        latest_version_number=latest.version_number,
    )


@router.get("/resume-templates", response_model=SuccessResponse[list[ResumeTemplateResponse]])
async def list_resume_templates(
    repository: ResumeTemplateRepositoryDep,
) -> SuccessResponse[list[ResumeTemplateResponse]]:
    templates = await repository.list_active()
    return SuccessResponse(
        message="Resume templates retrieved successfully.",
        data=[ResumeTemplateResponse.model_validate(t) for t in templates],
    )


@router.get("/resumes", response_model=SuccessResponse[list[ResumeResponse]])
async def list_resumes(
    profile: CurrentProfile,
    service: ResumeServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ResumeResponse]]:
    items, total = await service.list_resumes(
        profile.id, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Resumes retrieved successfully.",
        data=[await _to_resume_response(item, service) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "/resumes", response_model=SuccessResponse[ResumeResponse], status_code=status.HTTP_201_CREATED
)
async def create_resume(
    data: ResumeCreateRequest,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.create_resume(profile.id, data.title, data.template_id)
    return SuccessResponse(
        message="Resume created successfully.", data=await _to_resume_response(resume, service)
    )


@router.get("/resumes/{resume_id}", response_model=SuccessResponse[ResumeResponse])
async def get_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    return SuccessResponse(
        message="Resume retrieved successfully.", data=await _to_resume_response(resume, service)
    )


@router.patch("/resumes/{resume_id}", response_model=SuccessResponse[ResumeResponse])
async def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdateRequest,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeResponse]:
    resume = await service.update_resume(
        resume_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Resume updated successfully.", data=await _to_resume_response(resume, service)
    )


@router.delete("/resumes/{resume_id}", response_model=SuccessResponse[MessageResponse])
async def delete_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_resume(resume_id, profile.id)
    return SuccessResponse(
        message="Resume deleted successfully.", data=MessageResponse(message="Deleted.")
    )


@router.get("/resumes/{resume_id}/content", response_model=SuccessResponse[ResumeVersionResponse])
async def get_resume_content(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    return SuccessResponse(
        message="Resume content retrieved successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.put("/resumes/{resume_id}/content", response_model=SuccessResponse[ResumeVersionResponse])
async def update_resume_content(
    resume_id: uuid.UUID,
    data: ResumeContent,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.create_new_version(resume, data)
    return SuccessResponse(
        message="New resume version created successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.get(
    "/resumes/{resume_id}/versions",
    response_model=SuccessResponse[list[ResumeVersionSummaryResponse]],
)
async def list_resume_versions(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ResumeVersionSummaryResponse]]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    items, total = await service.list_versions(
        resume, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Resume versions retrieved successfully.",
        data=[ResumeVersionSummaryResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.get(
    "/resumes/{resume_id}/versions/{version_id}",
    response_model=SuccessResponse[ResumeVersionResponse],
)
async def get_resume_version(
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResumeServiceDep,
) -> SuccessResponse[ResumeVersionResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_version(resume, version_id)
    return SuccessResponse(
        message="Resume version retrieved successfully.",
        data=ResumeVersionResponse.model_validate(version),
    )


@router.post("/resumes/{resume_id}/export", response_model=SuccessResponse[FileAttachmentResponse])
async def export_resume(
    resume_id: uuid.UUID,
    profile: CurrentProfile,
    user: CurrentUser,
    service: ResumeServiceDep,
    export_service: ResumeExportServiceDep,
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
) -> SuccessResponse[FileAttachmentResponse]:
    resume = await service.get_owned_resume(resume_id, profile.id)
    version = await service.get_latest_version(resume)
    updated_version = await export_service.export(resume, version, profile, user.email)

    assert updated_version.rendered_file_id is not None
    rendered_file = await file_repository.get_by_id(updated_version.rendered_file_id)
    if rendered_file is None:
        raise ResourceNotFoundException("Rendered resume file not found.")

    return SuccessResponse(
        message="Resume exported successfully.",
        data=FileAttachmentResponse.model_validate(rendered_file),
    )
