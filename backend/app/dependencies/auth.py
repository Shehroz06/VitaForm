import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, decode_access_token
from app.database.session import get_db
from app.exceptions.base import AuthenticationException, AuthorizationException
from features.auth.models import User
from features.auth.repository import AuthRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise AuthenticationException("Authentication credentials were not provided.")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (InvalidTokenError, ValueError) as exc:
        raise AuthenticationException("Access token is invalid.") from exc

    repository = AuthRepository(db)
    user = await repository.get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationException("User not found or inactive.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: str) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def dependency(user: CurrentUser) -> User:
        user_roles = {role.name for role in user.roles}
        if not user_roles.intersection(allowed_roles):
            raise AuthorizationException("You do not have permission to perform this action.")
        return user

    return dependency


def require_permission(*allowed_permissions: str) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def dependency(user: CurrentUser) -> User:
        user_permissions = {
            permission.name for role in user.roles for permission in role.permissions
        }
        if not user_permissions.intersection(allowed_permissions):
            raise AuthorizationException("You do not have permission to perform this action.")
        return user

    return dependency
