from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from coverai.api.dependencies.session import SessionDep
from coverai.domain.enums import UserRole
from coverai.infra.db import models
from coverai.services.auth import InvalidCredentialsError, decode_access_token

security = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> models.User:
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

    user = await session.get(models.User, claims.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


CurrentUserDep = Annotated[models.User, Depends(current_user)]


async def admin_user(user: CurrentUserDep) -> models.User:
    """Проверяет права администратора."""
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


AdminUserDep = Annotated[models.User, Depends(admin_user)]
