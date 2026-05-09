from coverai.api.schemas import UserResponse
from coverai.domain.enums import UserRole
from coverai.infra.db import models


def user_response(user: models.User) -> UserResponse:
    """Преобразует пользователя в API response."""
    return UserResponse(
        id=user.id,
        email=user.email,
        telegram_id=user.telegram_id,
        role=UserRole(user.role),
        credits=user.credits,
    )
