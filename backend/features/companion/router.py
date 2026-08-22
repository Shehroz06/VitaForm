import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.companion.dependencies import (
    get_companion_service,
    get_cover_letter_crud_service,
    get_linkedin_crud_service,
)
from features.companion.models import CoverLetter, LinkedinGeneration
from features.companion.schemas import (
    CoverLetterResponse,
    GenerateCoverLetterRequest,
    GenerateLinkedinRequest,
    LinkedinGenerationResponse,
)
from features.companion.service import CompanionService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(tags=["companion"])

CompanionServiceDep = Annotated[CompanionService, Depends(get_companion_service)]
CoverLetterCrudDep = Annotated[
    BaseOwnedCrudService[CoverLetter], Depends(get_cover_letter_crud_service)
]
LinkedinCrudDep = Annotated[
    BaseOwnedCrudService[LinkedinGeneration], Depends(get_linkedin_crud_service)
]


@router.post("/ai/generate-cover-letter", response_model=SuccessResponse[CoverLetterResponse])
async def generate_cover_letter(
    data: GenerateCoverLetterRequest, profile: CurrentProfile, service: CompanionServiceDep
) -> SuccessResponse[CoverLetterResponse]:
    cover_letter = await service.generate_cover_letter(profile, data)
    return SuccessResponse(
        message="Cover letter generated successfully.",
        data=CoverLetterResponse.model_validate(cover_letter),
    )


@router.get("/cover-letters", response_model=SuccessResponse[list[CoverLetterResponse]])
async def list_cover_letters(
    profile: CurrentProfile,
    service: CoverLetterCrudDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[CoverLetterResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=CoverLetter.created_at,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Cover letters retrieved successfully.",
        data=[CoverLetterResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.get("/cover-letters/{cover_letter_id}", response_model=SuccessResponse[CoverLetterResponse])
async def get_cover_letter(
    cover_letter_id: uuid.UUID, profile: CurrentProfile, service: CoverLetterCrudDep
) -> SuccessResponse[CoverLetterResponse]:
    item = await service.get_owned(cover_letter_id, profile.id)
    return SuccessResponse(
        message="Cover letter retrieved successfully.",
        data=CoverLetterResponse.model_validate(item),
    )


@router.delete("/cover-letters/{cover_letter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cover_letter(
    cover_letter_id: uuid.UUID, profile: CurrentProfile, service: CoverLetterCrudDep
) -> None:
    await service.delete_owned(cover_letter_id, profile.id)


@router.post("/ai/generate-linkedin", response_model=SuccessResponse[LinkedinGenerationResponse])
async def generate_linkedin(
    data: GenerateLinkedinRequest, profile: CurrentProfile, service: CompanionServiceDep
) -> SuccessResponse[LinkedinGenerationResponse]:
    generation = await service.generate_linkedin(profile, data)
    return SuccessResponse(
        message="LinkedIn content generated successfully.",
        data=LinkedinGenerationResponse.model_validate(generation),
    )


@router.get(
    "/linkedin-generations",
    response_model=SuccessResponse[list[LinkedinGenerationResponse]],
)
async def list_linkedin_generations(
    profile: CurrentProfile,
    service: LinkedinCrudDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[LinkedinGenerationResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=LinkedinGeneration.created_at,
        sort_desc=True,
    )
    return SuccessResponse(
        message="LinkedIn generations retrieved successfully.",
        data=[LinkedinGenerationResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.get(
    "/linkedin-generations/{linkedin_generation_id}",
    response_model=SuccessResponse[LinkedinGenerationResponse],
)
async def get_linkedin_generation(
    linkedin_generation_id: uuid.UUID, profile: CurrentProfile, service: LinkedinCrudDep
) -> SuccessResponse[LinkedinGenerationResponse]:
    item = await service.get_owned(linkedin_generation_id, profile.id)
    return SuccessResponse(
        message="LinkedIn generation retrieved successfully.",
        data=LinkedinGenerationResponse.model_validate(item),
    )


@router.delete(
    "/linkedin-generations/{linkedin_generation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_linkedin_generation(
    linkedin_generation_id: uuid.UUID, profile: CurrentProfile, service: LinkedinCrudDep
) -> None:
    await service.delete_owned(linkedin_generation_id, profile.id)
