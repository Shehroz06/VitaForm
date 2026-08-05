import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.organizations.dependencies import get_organization_service
from features.organizations.models import Organization
from features.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/organizations", tags=["organizations"])

OrganizationServiceDep = Annotated[
    BaseOwnedCrudService[Organization], Depends(get_organization_service)
]


@router.get("", response_model=SuccessResponse[list[OrganizationResponse]])
async def list_organizations(
    profile: CurrentProfile,
    service: OrganizationServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[OrganizationResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Organization.start_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Organizations retrieved successfully.",
        data=[OrganizationResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[OrganizationResponse], status_code=status.HTTP_201_CREATED
)
async def create_organization(
    data: OrganizationCreateRequest,
    profile: CurrentProfile,
    service: OrganizationServiceDep,
) -> SuccessResponse[OrganizationResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Organization created successfully.",
        data=OrganizationResponse.model_validate(entity),
    )


@router.get("/{organization_id}", response_model=SuccessResponse[OrganizationResponse])
async def get_organization(
    organization_id: uuid.UUID,
    profile: CurrentProfile,
    service: OrganizationServiceDep,
) -> SuccessResponse[OrganizationResponse]:
    entity = await service.get_owned(organization_id, profile.id)
    return SuccessResponse(
        message="Organization retrieved successfully.",
        data=OrganizationResponse.model_validate(entity),
    )


@router.patch("/{organization_id}", response_model=SuccessResponse[OrganizationResponse])
async def update_organization(
    organization_id: uuid.UUID,
    data: OrganizationUpdateRequest,
    profile: CurrentProfile,
    service: OrganizationServiceDep,
) -> SuccessResponse[OrganizationResponse]:
    entity = await service.update_owned(
        organization_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Organization updated successfully.",
        data=OrganizationResponse.model_validate(entity),
    )


@router.delete("/{organization_id}", response_model=SuccessResponse[MessageResponse])
async def delete_organization(
    organization_id: uuid.UUID,
    profile: CurrentProfile,
    service: OrganizationServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(organization_id, profile.id)
    return SuccessResponse(
        message="Organization deleted successfully.", data=MessageResponse(message="Deleted.")
    )
