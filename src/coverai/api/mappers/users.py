from coverai.api.schemas import UserResponse
from coverai.domain.entities import User
from coverai.domain.enums import UserRole
from coverai.domain.ids import required_id


def user_response(user: User) -> UserResponse:
    """Преобразует пользователя в API response."""
    return UserResponse(
        id=required_id(user),
        email=user.email,
        telegram_id=user.telegram_id,
        role=UserRole(user.role),
        credits=user.credits,
    )
