import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.profiles.dependencies import CurrentProfile
from features.skills.dependencies import get_skill_service
from features.skills.models import Skill
from features.skills.schemas import SkillCreateRequest, SkillResponse, SkillUpdateRequest

router = APIRouter(prefix="/skills", tags=["skills"])

SkillServiceDep = Annotated[BaseOwnedCrudService[Skill], Depends(get_skill_service)]


@router.get("", response_model=SuccessResponse[list[SkillResponse]])
async def list_skills(
    profile: CurrentProfile,
    service: SkillServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[SkillResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Skill.name,
    )
    return SuccessResponse(
        message="Skills retrieved successfully.",
        data=[SkillResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[SkillResponse], status_code=status.HTTP_201_CREATED
)
async def create_skill(
    data: SkillCreateRequest,
    profile: CurrentProfile,
    service: SkillServiceDep,
) -> SuccessResponse[SkillResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Skill created successfully.", data=SkillResponse.model_validate(entity)
    )


@router.get("/{skill_id}", response_model=SuccessResponse[SkillResponse])
async def get_skill(
    skill_id: uuid.UUID,
    profile: CurrentProfile,
    service: SkillServiceDep,
) -> SuccessResponse[SkillResponse]:
    entity = await service.get_owned(skill_id, profile.id)
    return SuccessResponse(
        message="Skill retrieved successfully.", data=SkillResponse.model_validate(entity)
    )


@router.patch("/{skill_id}", response_model=SuccessResponse[SkillResponse])
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdateRequest,
    profile: CurrentProfile,
    service: SkillServiceDep,
) -> SuccessResponse[SkillResponse]:
    entity = await service.update_owned(skill_id, profile.id, **data.model_dump(exclude_unset=True))
    return SuccessResponse(
        message="Skill updated successfully.", data=SkillResponse.model_validate(entity)
    )


@router.delete("/{skill_id}", response_model=SuccessResponse[MessageResponse])
async def delete_skill(
    skill_id: uuid.UUID,
    profile: CurrentProfile,
    service: SkillServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(skill_id, profile.id)
    return SuccessResponse(
        message="Skill deleted successfully.", data=MessageResponse(message="Deleted.")
    )
