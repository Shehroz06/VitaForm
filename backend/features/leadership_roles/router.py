import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.leadership_roles.dependencies import get_leadership_role_service
from features.leadership_roles.models import LeadershipRole
from features.leadership_roles.schemas import (
    LeadershipRoleCreateRequest,
    LeadershipRoleResponse,
    LeadershipRoleUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/leadership-roles", tags=["leadership-roles"])

LeadershipRoleServiceDep = Annotated[
    BaseOwnedCrudService[LeadershipRole], Depends(get_leadership_role_service)
]


@router.get("", response_model=SuccessResponse[list[LeadershipRoleResponse]])
async def list_leadership_roles(
    profile: CurrentProfile,
    service: LeadershipRoleServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[LeadershipRoleResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=LeadershipRole.start_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Leadership roles retrieved successfully.",
        data=[LeadershipRoleResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "",
    response_model=SuccessResponse[LeadershipRoleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_leadership_role(
    data: LeadershipRoleCreateRequest,
    profile: CurrentProfile,
    service: LeadershipRoleServiceDep,
) -> SuccessResponse[LeadershipRoleResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Leadership role created successfully.",
        data=LeadershipRoleResponse.model_validate(entity),
    )


@router.get("/{role_id}", response_model=SuccessResponse[LeadershipRoleResponse])
async def get_leadership_role(
    role_id: uuid.UUID,
    profile: CurrentProfile,
    service: LeadershipRoleServiceDep,
) -> SuccessResponse[LeadershipRoleResponse]:
    entity = await service.get_owned(role_id, profile.id)
    return SuccessResponse(
        message="Leadership role retrieved successfully.",
        data=LeadershipRoleResponse.model_validate(entity),
    )


@router.patch("/{role_id}", response_model=SuccessResponse[LeadershipRoleResponse])
async def update_leadership_role(
    role_id: uuid.UUID,
    data: LeadershipRoleUpdateRequest,
    profile: CurrentProfile,
    service: LeadershipRoleServiceDep,
) -> SuccessResponse[LeadershipRoleResponse]:
    entity = await service.update_owned(
        role_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Leadership role updated successfully.",
        data=LeadershipRoleResponse.model_validate(entity),
    )


@router.delete("/{role_id}", response_model=SuccessResponse[MessageResponse])
async def delete_leadership_role(
    role_id: uuid.UUID,
    profile: CurrentProfile,
    service: LeadershipRoleServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(role_id, profile.id)
    return SuccessResponse(
        message="Leadership role deleted successfully.", data=MessageResponse(message="Deleted.")
    )
