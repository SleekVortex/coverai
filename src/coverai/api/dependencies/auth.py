from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from coverai.api.dependencies.services import UserServiceDep
from coverai.domain.entities import User
from coverai.domain.enums import UserRole
from coverai.services.auth import InvalidCredentialsError, decode_access_token
from coverai.services.users.errors import UserNotFoundError

security = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    user_service: UserServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    """Возвращает текущего пользователя."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        claims = decode_access_token(
            credentials.credentials,
            request.app.state.settings.auth,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    try:
        user = await user_service.get_by_id(claims.user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=401, detail="User not found") from error
    return user


CurrentUserDep = Annotated[User, Depends(current_user)]


async def admin_user(user: CurrentUserDep) -> User:
    """Проверяет права администратора."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


AdminUserDep = Annotated[User, Depends(admin_user)]
