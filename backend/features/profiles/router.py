from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import CurrentUser
from app.schemas.response import SuccessResponse
from features.profiles.dependencies import get_profile_service
from features.profiles.models import Profile
from features.profiles.schemas import ProfileResponse, ProfileUpdateRequest
from features.profiles.service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


async def _to_response(
    profile: Profile, first_name: str | None, last_name: str | None, service: ProfileService
) -> ProfileResponse:
    completion = await service.compute_completion_percentage(profile, first_name, last_name)
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        headline=profile.headline,
        bio=profile.bio,
        phone=profile.phone,
        location=profile.location,
        website_url=profile.website_url,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        avatar_url=profile.avatar_url,
        completion_percentage=completion,
    )


@router.get("/me", response_model=SuccessResponse[ProfileResponse])
async def get_my_profile(
    user: CurrentUser,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SuccessResponse[ProfileResponse]:
    profile = await service.get_or_create(user.id)
    return SuccessResponse(
        message="Profile retrieved successfully.",
        data=await _to_response(profile, user.first_name, user.last_name, service),
    )


@router.patch("/me", response_model=SuccessResponse[ProfileResponse])
async def update_my_profile(
    data: ProfileUpdateRequest,
    user: CurrentUser,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SuccessResponse[ProfileResponse]:
    profile = await service.update(user.id, **data.model_dump(exclude_unset=True))
    return SuccessResponse(
        message="Profile updated successfully.",
        data=await _to_response(profile, user.first_name, user.last_name, service),
    )
