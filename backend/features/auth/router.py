from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.database.session import get_db
from app.dependencies.auth import CurrentUser, require_role
from app.dependencies.rate_limits import (
    forgot_password_rate_limit,
    login_rate_limit,
    register_rate_limit,
)
from app.exceptions.base import AuthenticationException
from app.schemas.response import MessageResponse, SuccessResponse
from features.auth.dependencies import (
    get_admin_reset_password_use_case,
    get_delete_account_use_case,
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
    AccessTokenResponse,
    AdminResetPasswordRequest,
    DeleteAccountRequest,
    ForgotPasswordRequest,
    IssuedTokenPair,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateMeRequest,
    UserResponse,
    VerifyEmailRequest,
)
from features.auth.use_cases import (
    AdminResetPassword,
    DeleteAccount,
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
settings = get_settings()

_REFRESH_COOKIE_NAME = "refresh_token"
# Scoped to /api/v1/auth so the browser only ever sends this cookie to the
# endpoints that need it (refresh, logout), not to every request on the API
# origin.
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=settings.jwt_refresh_token_expires_days * 24 * 60 * 60,
        httponly=True,
        # Lax (not None) works here because frontend and backend are
        # same-site (share a registrable domain, differing only by port/
        # subdomain) in both local dev and the intended deployment shape --
        # a genuinely cross-site deployment would need SameSite=None+Secure.
        samesite="lax",
        secure=settings.environment == "production",
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)


def _to_access_token_response(tokens: IssuedTokenPair) -> AccessTokenResponse:
    return AccessTokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


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
    dependencies=[Depends(register_rate_limit)],
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


@router.post(
    "/login",
    response_model=SuccessResponse[AccessTokenResponse],
    dependencies=[Depends(login_rate_limit)],
)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    use_case: Annotated[LoginUser, Depends(get_login_use_case)],
) -> SuccessResponse[AccessTokenResponse]:
    _, tokens = await use_case.execute(data, _request_context(request))
    _set_refresh_cookie(response, tokens.refresh_token)
    return SuccessResponse(
        message="Logged in successfully.", data=_to_access_token_response(tokens)
    )


@router.post("/refresh", response_model=SuccessResponse[AccessTokenResponse])
async def refresh(
    response: Response,
    use_case: Annotated[RefreshAccessToken, Depends(get_refresh_use_case)],
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE_NAME)] = None,
) -> SuccessResponse[AccessTokenResponse]:
    if refresh_token is None:
        raise AuthenticationException("Refresh token was not provided.")
    tokens = await use_case.execute(refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return SuccessResponse(
        message="Token refreshed successfully.", data=_to_access_token_response(tokens)
    )


@router.post("/logout", response_model=SuccessResponse[MessageResponse])
async def logout(
    response: Response,
    use_case: Annotated[LogoutUser, Depends(get_logout_use_case)],
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE_NAME)] = None,
) -> SuccessResponse[MessageResponse]:
    if refresh_token is not None:
        await use_case.execute(refresh_token)
    _clear_refresh_cookie(response)
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


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[MessageResponse],
    dependencies=[Depends(forgot_password_rate_limit)],
)
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


@router.delete("/me", response_model=SuccessResponse[MessageResponse])
async def delete_account(
    data: DeleteAccountRequest,
    user: CurrentUser,
    response: Response,
    use_case: Annotated[DeleteAccount, Depends(get_delete_account_use_case)],
) -> SuccessResponse[MessageResponse]:
    await use_case.execute(user, data)
    _clear_refresh_cookie(response)
    return SuccessResponse(
        message="Account deleted.", data=MessageResponse(message="Account deleted.")
    )


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
