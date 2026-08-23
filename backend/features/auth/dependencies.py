from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import EmailSender, get_email_sender
from app.database.session import get_db
from features.auth.repository import AuthRepository
from features.auth.service import AuthService
from features.auth.use_cases import (
    AdminResetPassword,
    DeleteAccount,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    RegisterUser,
    RequestPasswordReset,
    ResetPassword,
    VerifyEmail,
)


def get_auth_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthRepository:
    return AuthRepository(db)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> AuthService:
    return AuthService(repository)


def get_register_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> RegisterUser:
    return RegisterUser(repository, email_sender)


def get_login_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginUser:
    return LoginUser(repository, service)


def get_refresh_use_case(
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RefreshAccessToken:
    return RefreshAccessToken(service)


def get_logout_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> LogoutUser:
    return LogoutUser(repository)


def get_verify_email_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> VerifyEmail:
    return VerifyEmail(repository)


def get_request_password_reset_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> RequestPasswordReset:
    return RequestPasswordReset(repository, email_sender)


def get_reset_password_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> ResetPassword:
    return ResetPassword(repository)


def get_admin_reset_password_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> AdminResetPassword:
    return AdminResetPassword(repository)


def get_delete_account_use_case(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> DeleteAccount:
    return DeleteAccount(repository)
