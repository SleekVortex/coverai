from coverai.api.schemas import TokenResponse
from coverai.configs import Settings
from coverai.domain.entities import User as DomainUser
from coverai.domain.enums import UserRole
from coverai.infra.db import models
from coverai.services.auth import create_access_token


def token_for_user(user: models.User | DomainUser, settings: Settings) -> TokenResponse:
    """Создает token response для пользователя."""
    if user.id is None:
        raise RuntimeError("user id is not assigned")
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.id,
            role=UserRole(user.role),
            email=user.email,
            settings=settings.auth,
        ),
    )
