from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import CurrentUser, require_role
from app.schemas.response import MessageResponse, SuccessResponse
from features.auth.dependencies import (
    get_admin_reset_password_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
    get_register_use_case,
    get_request_password_reset_use_case,
    get_reset_password_use_case,
    get_verify_email_use_case,
)
from features.auth.models import User
from features.auth.repository import AuthRepository
from features.auth.schemas import (
    AdminResetPasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateMeRequest,
    UserResponse,
    VerifyEmailRequest,
)
from features.auth.use_cases import (
    AdminResetPassword,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    RegisterUser,
    RequestContext,
    RequestPasswordReset,
    ResetPassword,
    VerifyEmail,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_email_verified=user.is_email_verified,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
    )


def _request_context(request: Request) -> RequestContext:
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_use_case)],
) -> SuccessResponse[UserResponse]:
    user = await use_case.execute(data)
    return SuccessResponse(
        message="Account created. Check your email to verify your account.",
        data=_to_user_response(user),
    )


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    data: LoginRequest,
    request: Request,
    use_case: Annotated[LoginUser, Depends(get_login_use_case)],
) -> SuccessResponse[TokenResponse]:
    _, tokens = await use_case.execute(data, _request_context(request))
    return SuccessResponse(message="Logged in successfully.", data=tokens)


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(
    data: RefreshRequest,
    use_case: Annotated[RefreshAccessToken, Depends(get_refresh_use_case)],
) -> SuccessResponse[TokenResponse]:
    tokens = await use_case.execute(data.refresh_token)
    return SuccessResponse(message="Token refreshed successfully.", data=tokens)


@router.post("/logout", response_model=SuccessResponse[MessageResponse])
async def logout(
    data: LogoutRequest,
    use_case: Annotated[LogoutUser, Depends(get_logout_use_case)],
) -> SuccessResponse[MessageResponse]:
    await use_case.execute(data.refresh_token)
    return SuccessResponse(
        message="Logged out successfully.", data=MessageResponse(message="Logged out.")
    )


@router.post("/verify-email", response_model=SuccessResponse[UserResponse])
async def verify_email(
    data: VerifyEmailRequest,
    use_case: Annotated[VerifyEmail, Depends(get_verify_email_use_case)],
) -> SuccessResponse[UserResponse]:
    user = await use_case.execute(data)
    return SuccessResponse(message="Email verified successfully.", data=_to_user_response(user))


@router.post("/forgot-password", response_model=SuccessResponse[MessageResponse])
async def forgot_password(
    data: ForgotPasswordRequest,
    use_case: Annotated[RequestPasswordReset, Depends(get_request_password_reset_use_case)],
) -> SuccessResponse[MessageResponse]:
    await use_case.execute(data)
    return SuccessResponse(
        message="If that email is registered, a reset link has been sent.",
        data=MessageResponse(message="Password reset requested."),
    )


@router.post("/reset-password", response_model=SuccessResponse[MessageResponse])
async def reset_password(
    data: ResetPasswordRequest,
    use_case: Annotated[ResetPassword, Depends(get_reset_password_use_case)],
) -> SuccessResponse[MessageResponse]:
    await use_case.execute(data)
    return SuccessResponse(
        message="Password reset successfully.",
        data=MessageResponse(message="Password updated."),
    )


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_me(user: CurrentUser) -> SuccessResponse[UserResponse]:
    return SuccessResponse(message="Current user retrieved.", data=_to_user_response(user))


@router.patch("/me", response_model=SuccessResponse[UserResponse])
async def update_me(
    data: UpdateMeRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[UserResponse]:
    repository = AuthRepository(db)
    await repository.update_user_name(user, data.first_name, data.last_name)
    return SuccessResponse(message="Profile updated successfully.", data=_to_user_response(user))


@router.get("/admin-check", response_model=SuccessResponse[MessageResponse])
async def admin_check(
    user: Annotated[User, Depends(require_role("admin"))],
) -> SuccessResponse[MessageResponse]:
    return SuccessResponse(
        message="Admin access confirmed.", data=MessageResponse(message="You are an admin.")
    )


@router.post("/admin/reset-password", response_model=SuccessResponse[UserResponse])
async def admin_reset_password(
    data: AdminResetPasswordRequest,
    admin: Annotated[User, Depends(require_role("admin"))],
    use_case: Annotated[AdminResetPassword, Depends(get_admin_reset_password_use_case)],
) -> SuccessResponse[UserResponse]:
    user = await use_case.execute(data)
    return SuccessResponse(
        message=f"Password reset for {user.email}. All of their sessions were signed out.",
        data=_to_user_response(user),
    )
